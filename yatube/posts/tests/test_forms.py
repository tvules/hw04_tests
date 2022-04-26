from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Post, Group

User = get_user_model()


class PostFormTests(TestCase):
    """Тестирование формы PostForm."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title='TestTitle',
            slug='test_slug',
            description='TestDescription',
        )
        cls.post = Post.objects.create(
            text='TestText',
            author=cls.user,
            group=cls.group,
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(user=PostFormTests.user)

    def test_create_new_post_form(self):
        """Тестирование формы создания нового поста."""
        form_data = {
            'text': 'NewPostTest',
            'group': PostFormTests.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile',
                kwargs={'username': PostFormTests.user.get_username()}
            ),
        )
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
            ).exists()
        )

    def test_edit_post_form(self):
        """Тестирование формы редактирования поста."""
        form_data = {
            'text': 'EditPostTest',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': PostFormTests.post.id}
            ),
            form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail', kwargs={'post_id': PostFormTests.post.id}
            )
        )
        self.assertTrue(
            Post.objects.filter(
                id=PostFormTests.post.id,
                text=form_data['text'],
            ).exists()
        )
