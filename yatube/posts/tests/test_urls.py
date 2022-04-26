from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse

from yatube.settings import LOGIN_URL
from ..models import Post, Group

User = get_user_model()


class StaticURLTests(TestCase):

    def setUp(self) -> None:
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)


class PostsURLTests(TestCase):
    """Тесты URLs."""

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
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)
        self.author_client = Client()
        self.author_client.force_login(PostsURLTests.post.author)
        self.URLS = {
            f'/group/{PostsURLTests.group.slug}/': {
                'access': 'free',
                'url_path': '/group/<slug>/',
                'template': 'posts/group_list.html',
            },
            f'/profile/{PostsURLTests.user.get_username()}/': {
                'access': 'free',
                'url_path': '/profile/<username>/',
                'template': 'posts/profile.html',
            },
            f'/posts/{PostsURLTests.post.id}/': {
                'access': 'free',
                'url_path': '/posts/<post_id>/',
                'template': 'posts/post_detail.html',
            },
            f'/posts/{PostsURLTests.post.id}/edit/': {
                'access': 'author',
                'url_path': '/posts/<post_id>/edit/',
                'template': 'posts/create_post.html',
            },
            '/create/': {
                'access': 'auth',
                'template': 'posts/create_post.html',
            },
        }

    def test_non_existent_url(self):
        """Проверка несуществующего url."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_exists_at_desired_location(self):
        """Проверка доступности ожидаемых urls."""
        for url, details in self.URLS.items():
            with self.subTest(url=url):
                if details['access'] == 'auth':
                    response = self.authorized_client.get(url)
                elif details['access'] == 'author':
                    response = self.author_client.get(url)
                else:
                    response = self.guest_client.get(url)
                self.assertNotEqual(
                    response.status_code,
                    HTTPStatus.NOT_FOUND,
                    (f'Страница `{details.get("url_path", url)}` не найдена, '
                     f'проверьте этот адрес в *urls.py*')
                )

    def test_urls_uses_correct_template(self):
        """Проверка используемого шаблона для URL-адреса."""
        for url, details in self.URLS.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(
                    response,
                    details['template'],
                    (f'URL-адрес `{details.get("url_path", url)}` использует '
                     f'не соответствующий html-шаблон.')
                )

    def test_urls_redirect_anonymous_on_login(self):
        """Проверка редиректа для неавторизованных пользователей."""
        for url, details in self.URLS.items():
            with self.subTest(url=url):
                if details['access'] != 'free':
                    response = self.guest_client.get(url)
                    self.assertRedirects(
                        response,
                        reverse(LOGIN_URL) + f'?next={url}',
                    )
