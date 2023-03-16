from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group, Follow

User = get_user_model()


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.username = 'TestAuthor'
        cls.username_one = 'TestAuthor1'
        cls.username_two = 'TestAuthor2'
        cls.user = User.objects.create_user(username=cls.username)

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

        cls.reverse_follow_index = (
            reverse('posts:follow_index'))

        cls.profile_follow = 'posts:profile_follow'
        cls.profile_unfollow = 'posts:profile_unfollow'

    def setUp(self):
        self.guest_client = Client()
        self.user1 = User.objects.create(username=self.username_one)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user1)

        self.user2 = User.objects.create(username=self.username_two)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_authorized_client_add_follow(self):
        """Авторизованный пользователь
        может подписываться на других пользователей
        """
        self.authorized_client.post(
            reverse(self.profile_follow, kwargs={
                    'username': self.user})
        )

        follow_count = Follow.objects.filter(
            user=self.user1,
            author=self.user).count()

        self.assertEqual(follow_count, 1)

    def test_authorized_client_delete_follow(self):
        """Авторизованный пользователь
        может удалять из подписок других пользователей
        """
        self.authorized_client.post(
            reverse(self.profile_unfollow, kwargs={
                    'username': self.user})
        )

        follow_count = Follow.objects.filter(
            user=self.user1,
            author=self.user).count()

        self.assertEqual(follow_count, 0)

    def test_new_post_follow(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан и не появляется в ленте тех,
        кто не подписан."""
        self.authorized_client.post(
            reverse(self.profile_follow, kwargs={
                    'username': self.username}),
        )

        self.authorized_client2.post(
            reverse(self.profile_follow, kwargs={
                    'username': self.username_one}),
        )

        Post.objects.create(
            author=self.user1,
            text='Старый пост',
            group=self.group,
        )

        new_post = Post.objects.create(
            author=self.user,
            text='Новый пост',
            group=self.group,
        )

        post_from_context = self.authorized_client.get(
            self.reverse_follow_index).context['page_obj'][0]

        self.assertEqual(new_post, post_from_context)

        post_from_context = self.authorized_client2.get(
            self.reverse_follow_index).context['page_obj'][0]

        self.assertNotEqual(new_post, post_from_context)
