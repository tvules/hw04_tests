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

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(user=self.user)

    def test_create_new_post_form(self):
        """Тестирование формы создания нового поста."""
        form_data = {
            'text': 'NewPostTest',
            'group': self.group.id,
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
                kwargs={'username': self.user.get_username()}
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
        post = Post.objects.create(
            text='TestText',
            author=self.user,
            group=self.group,
        )
        form_data = {
            'text': 'EditPostTest',
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit', kwargs={'post_id': post.id}
            ),
            form_data,
            follow=True,
        )
        post.refresh_from_db()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group, form_data.get('group'))
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail', kwargs={'post_id': post.id}
            )
        )
        self.assertTrue(
            Post.objects.filter(
                id=post.id,
                text=form_data['text'],
            ).exists()
        )
