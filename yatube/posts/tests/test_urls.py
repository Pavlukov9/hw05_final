from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from ..models import Group, Post


User = get_user_model()


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestAuthor')
        cls.user_not_author = User.objects.create_user(
            username='TestNotAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='testslug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Текстовый пост',
        )

        cls.INDEX = '/'
        cls.GROUP_LIST = '/group/testslug/'
        cls.USERNAME = '/profile/TestAuthor/'
        cls.POST_DETAIL = f'/posts/{cls.post.pk}/'
        cls.POST_EDIT = f'/posts/{cls.post.pk}/edit/'
        cls.POST_CREATE = '/create/'
        cls.UNEXISTING_PAGE = '/unexisting_page/'
        cls.FAKE_PAGE = '/fake/page'
        cls.POST_COMMET = f'/posts/{cls.post.pk}/comment/'
        cls.POST_FOLLOW = '/follow/'
        cls.PROFILE_FOLLOW = f'/profile/{cls.user}/follow/'
        cls.PROFILE_UNFOLLOW = f'/profile/{cls.user}/unfollow/'

        cls.FAKE = {
            cls.FAKE_PAGE: 'core/404.html',
        }

        cls.PUBLIC_URLS = {
            cls.INDEX: 'posts/index.html',
            cls.GROUP_LIST: 'posts/group_list.html',
            cls.USERNAME: 'posts/profile.html',
            cls.POST_DETAIL: 'posts/post_detail.html',
        }

        cls.AUTH_URLS = {
            cls.POST_EDIT: 'posts/post_create.html',
            cls.POST_CREATE: 'posts/post_create.html',
            cls.POST_FOLLOW: 'posts/follow.html',
        }

        cls.REDIRECTION = '/auth/login/?next='

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.user_not_author)

    def test_url_available_to_all_users(self):
        """Страницы доступные любому пользователю."""

        for address in self.PUBLIC_URLS.keys():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, 200)

    def test_url_available_to_authorized_users(self):
        """Страницы доступные авторизованному пользователю."""

        for address in self.AUTH_URLS.keys():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, 200)

    def test_url_redirect_quest(self):
        """Страницы перенаправляют анонимного пользовател
        на страницу логина.
        """

        url_names_redirects = {
            self.POST_EDIT: f'{self.REDIRECTION}{self.POST_EDIT}',
            self.POST_CREATE: f'{self.REDIRECTION}{self.POST_CREATE}',
        }

        for address, redirect_address in url_names_redirects.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect_address)

    def test_url_redirect_not_author(self):
        """Редирект при попытке редактирования поста не автором"""

        response = self.authorized_client_not_author.get(
            self.POST_EDIT, follow=True)
        self.assertRedirects(response, self.POST_DETAIL)

    def test_url_templates(self):
        """Проверяем правильность вызванных шаблонов"""

        result = self.PUBLIC_URLS | self.AUTH_URLS | self.FAKE
        for address, template in result.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_not_found(self):
        """Страница не найденна."""

        response = self.guest_client.get(self.UNEXISTING_PAGE)
        self.assertEqual(response.status_code, 404)

    def test_url_redirect(self):

        url_names_redirects = {
            self.PROFILE_FOLLOW: f'{self.REDIRECTION}{self.PROFILE_FOLLOW}',
            self.PROFILE_UNFOLLOW:
                f'{self.REDIRECTION}{self.PROFILE_UNFOLLOW}',
        }

        for address, redirect_address in url_names_redirects.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(response, redirect_address)
