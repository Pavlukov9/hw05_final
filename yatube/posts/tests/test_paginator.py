from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group


User = get_user_model()


class PaginatorViewsTest(TestCase):

    QUANTITY_OF_POSTS_ON_THE_SECOND_PAGE = 3

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = Group.objects.create(title='Тестовая группа',
                                          slug='test-group')
        bilk_post: list = []
        for i in range(settings.QUANTITY_OF_POSTS
                       + self.QUANTITY_OF_POSTS_ON_THE_SECOND_PAGE):
            bilk_post.append(Post(text=f'Тестовый текст {i}',
                             group=self.group,
                             author=self.user))
        Post.objects.bulk_create(bilk_post)

        self.INDEX = reverse('posts:index')
        self.GROUP_LIST = reverse('posts:group_list', kwargs={'slug':
                                  f'{self.group.slug}'})
        self.USERNAME = reverse('posts:profile', kwargs={'username':
                                f'{self.user.username}'})

    def test_page_context_guest_client(self):
        """Количество постов на страницах index, group_list, profile
        для неавторизованного и авторизованного пользователя.
        """
        pages = (
            self.INDEX,
            self.GROUP_LIST,
            self.USERNAME,
        )

        users = (self.guest_client, self.authorized_client)

        for page in pages:
            with self.subTest(page=page):
                for user in users:
                    response1 = user.get(page)
                    response2 = user.get(page + '?page=2')
                    self.assertEqual(len(response1.context['page_obj']),
                                     settings.QUANTITY_OF_POSTS)
                    self.assertEqual(len(response2.context['page_obj']),
                                     self.QUANTITY_OF_POSTS_ON_THE_SECOND_PAGE)
