from django import forms
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from yatube.settings import POSTS_PER_PAGE
from ..models import Post, Group

EXPECTED_POST_FORM_FIELDS = {
    'text': forms.fields.CharField,
    'group': forms.fields.ChoiceField,
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
        self.authorized_client.force_login(user=PostsPagesTests.user)

    def test_pages_uses_correct_template(self):
        """Проверка используемого шаблона для URL-адреса."""
        pages_templates_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsPagesTests.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostsPagesTests.user.get_username()},
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsPagesTests.post.id},
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsPagesTests.post.id},
            ): 'posts/create_post.html',
        }
        for reverse_name, template in pages_templates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Проверка контекста для view-index."""
        response = self.authorized_client.get(reverse('posts:index'))
        post_object = response.context.get('page_obj')[0]
        context_obj_data = {
            'text': {
                'expected': PostsPagesTests.post.text,
                'received': post_object.text,
            },
            'pub_date': {
                'expected': PostsPagesTests.post.pub_date,
                'received': post_object.pub_date,
            },
            'author': {
                'expected': PostsPagesTests.post.author,
                'received': post_object.author,
            },
            'group': {
                'expected': PostsPagesTests.post.group,
                'received': post_object.group,
            },
        }
        for field, details in context_obj_data.items():
            with self.subTest(field=field):
                self.assertEqual(details['received'], details['expected'])

    def test_group_posts_page_show_correct_context(self):
        """Проверка контекста для view-group_posts."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsPagesTests.group.slug},
            ),
        )
        self.assertEqual(
            response.context.get('group'),
            PostsPagesTests.group,
        )
        for post_obj in response.context.get('page_obj'):
            with self.subTest(post=str(post_obj)):
                self.assertEqual(
                    post_obj.group,
                    PostsPagesTests.post.group,
                )

    def test_profile_page_show_correct_context(self):
        """Проверка контекста для view-profile."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostsPagesTests.user.get_username()},
            ),
        )
        self.assertEqual(
            response.context.get('author'),
            PostsPagesTests.post.author,
        )
        for post_obj in response.context.get('page_obj'):
            with self.subTest(post=str(post_obj)):
                self.assertEqual(
                    post_obj.author,
                    PostsPagesTests.post.author,
                )

    def test_post_detail_page_show_correct_context(self):
        """Проверка контекста для view-post_detail."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostsPagesTests.post.id},
            ),
        )
        self.assertEqual(
            response.context.get('post'),
            PostsPagesTests.post,
        )

    def test_post_create_page_show_correct_context(self):
        """Проверка контекста для view-post_create."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        self._form_fields_testing(response)

    def test_post_edit_page_show_correct_context(self):
        """Проверка контекста для view-post_edit."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostsPagesTests.post.id},
            ),
        )
        form_instance = response.context.get('form').instance
        self.assertEqual(form_instance, PostsPagesTests.post)
        self._form_fields_testing(response)

    def test_new_post_on_correct_pages(self):
        """Пост появляется на где должен."""
        pages_which_post = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsPagesTests.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostsPagesTests.user.get_username()},
            ),
        ]
        for page in pages_which_post:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertIn(
                    PostsPagesTests.post,
                    response.context.get('page_obj'),
                )

    def test_post_in_correct_group(self):
        """Пост в правильной группе."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostsPagesTests.other_group.slug}
            ),
        )
        self.assertNotIn(
            PostsPagesTests.post,
            response.context.get('page_obj'),
        )

    def _form_fields_testing(self, response):
        """Сравнивает поля формы с ожидаемыми."""
        for field, expected_type in (
                PostsPagesTests.EXPECTED_POST_FORM_FIELDS.items()):
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected_type)


POST_PER_TEST = 15


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
        cls.posts = [
            Post.objects.create(
                text='TestText',
                author=cls.user,
                group=cls.group,
            ) for _ in range(POST_PER_TEST)
        ]

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(user=PaginatorViewsTest.user)

    def test_index_page_pagination(self):
        """Проверка первой пагинации главной страницы."""
        self._check_pagination(reverse('posts:index'))

    def test_group_post_page_pagination(self):
        """Проверка первой пагинации страницы группы."""
        self._check_pagination(
            reverse(
                'posts:group_list',
                kwargs={'slug': PaginatorViewsTest.group.slug}),
        )

    def test_profile_page_pagination(self):
        """Проверка первой пагинации страницы профиля автора."""
        self._check_pagination(
            reverse(
                'posts:profile',
                kwargs={'username': PaginatorViewsTest.user.get_username()},
            )
        )

    def _check_pagination(self, url):
        first_page_response = self.authorized_client.get(url)
        second_page_response = self.authorized_client.get(url + '?page=2')
        self.assertEqual(
            len(first_page_response.context.get('page_obj')),
            POSTS_PER_PAGE,
        )
        self.assertEqual(
            len(second_page_response.context.get('page_obj')),
            POST_PER_TEST % POSTS_PER_PAGE,
        )
