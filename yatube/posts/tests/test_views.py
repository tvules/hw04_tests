from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from yatube.settings import POSTS_PER_PAGE
from ..models import Post, Group
from ..forms import PostForm

EXPECTED_POST_FORM_FIELDS = {
    'text': forms.CharField,
    'group': forms.ModelChoiceField,
}

User = get_user_model()


class PostsPagesTests(TestCase):
    """Тест view приложения posts."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='TestTitle',
            slug='test_slug',
            description='TestDescription',
        )
        cls.other_group = Group.objects.create(
            title='TestTitleOther',
            slug='test_slug_other',
            description='TestDescriptionOther',
        )
        cls.post = Post.objects.create(
            text='TestText',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(user=self.user)

    def test_pages_uses_correct_template(self):
        """Проверка используемого шаблона для URL-адреса."""
        pages_templates_names = {
            reverse(
                'posts:index'
            ): 'posts/index.html',
            reverse(
                'posts:post_create'
            ): 'posts/create_post.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': self.user.get_username()},
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id},
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id},
            ): 'posts/create_post.html',
        }
        for reverse_name, template in pages_templates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Проверка контекста для view-index."""
        response = self.authorized_client.get(reverse('posts:index'))
        post_obj = response.context.get('page_obj')[0]
        self._post_fields_testing(post_obj)

    def test_group_posts_page_show_correct_context(self):
        """Проверка контекста для view-group_posts."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug},
            ),
        )
        self.assertEqual(
            response.context.get('group'),
            self.group,
        )
        post_obj = response.context.get('page_obj')[0]
        self._post_fields_testing(post_obj)

    def test_profile_page_show_correct_context(self):
        """Проверка контекста для view-profile."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': self.user.get_username()},
            ),
        )
        self.assertEqual(
            response.context.get('author'),
            self.post.author,
        )
        post_obj = response.context.get('page_obj')[0]
        self._post_fields_testing(post_obj)

    def test_post_detail_page_show_correct_context(self):
        """Проверка контекста для view-post_detail."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id},
            ),
        )
        post_obj = response.context.get('post')
        self._post_fields_testing(post_obj)

    def test_post_create_page_show_correct_context(self):
        """Проверка контекста для view-post_create."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_obj = response.context.get('form')
        self._post_form_fields_testing(form_obj)

    def test_post_edit_page_show_correct_context(self):
        """Проверка контекста для view-post_edit."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.id},
            ),
        )
        post_obj = response.context.get('form').instance
        self._post_fields_testing(post_obj)
        form_obj = response.context.get('form')
        self._post_form_fields_testing(form_obj)

    def test_new_post_on_correct_pages(self):
        """Пост появляется на где должен."""
        pages_which_post = [
            reverse(
                'posts:index'
            ),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.get_username()},
            ),
        ]
        for page in pages_which_post:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertIn(
                    self.post,
                    response.context.get('page_obj'),
                )

    def test_post_in_correct_group(self):
        """Пост в правильной группе."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': self.other_group.slug}
            ),
        )
        self.assertNotIn(
            self.post,
            response.context.get('page_obj'),
        )

    def _post_fields_testing(self, post_obj: Post):
        """Сравнивает значения полей с ожидаемыми."""
        expected_field_value = {
            'text': self.post.text,
            'pub_date': self.post.pub_date,
            'author': self.post.author,
            'group': self.post.group,
        }
        for field, expected_value in expected_field_value.items():
            self.assertEqual(getattr(post_obj, field), expected_value)

    def _post_form_fields_testing(self, form_obj: PostForm):
        """Сравнивает поля формы с ожидаемыми."""
        post_obj = form_obj.instance
        if post_obj.id is not None:
            self._post_fields_testing(post_obj)
        for field, expected_type in EXPECTED_POST_FORM_FIELDS.items():
            form_field = form_obj.fields.get(field)
            self.assertIsInstance(form_field, expected_type)


class PaginatorViewsTest(TestCase):
    """Тест пагинатора."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='TestTitle',
            slug='test_slug',
            description='TestDescription',
        )
        posts_obj = [
            Post(text='TestText', author=cls.user, group=cls.group)
            for _ in range(POSTS_PER_PAGE * 2)
        ]
        cls.posts = Post.objects.bulk_create(posts_obj)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(user=self.user)

    def test_page_pagination(self):
        """Проверяет пагинацию страницы."""
        urls = {
            'index': reverse(
                'posts:index'
            ),
            'group_posts': reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': self.user.get_username()},
            ),
        }
        for view, url in urls.items():
            with self.subTest(view=view):
                self._pagination_testing(url)

    def _pagination_testing(self, url):
        first_page_response = self.authorized_client.get(url)
        second_page_response = self.authorized_client.get(url + '?page=2')
        self.assertEqual(
            len(first_page_response.context.get('page_obj')),
            POSTS_PER_PAGE,
        )
        self.assertEqual(
            len(second_page_response.context.get('page_obj')),
            POSTS_PER_PAGE,
        )
