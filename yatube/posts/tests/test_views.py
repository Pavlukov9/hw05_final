import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group


User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostTests(TestCase):

    INDEX_URL = reverse('posts:index')
    GROUP_LIST_URL = reverse('posts:group_list',
                             kwargs={'slug': 'test-slug'})
    USERNAME_URL = reverse('posts:profile',
                           kwargs={'username': 'TestAuthor'})

    POST_CREATE_URL = reverse('posts:post_create')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestAuthor')
        cls.auth_user = User.objects.create_user(username='TestAuthUser')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )

        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded,
        )

        cls.POST_DETAIL_URL = reverse('posts:post_detail',
                                      kwargs={'post_id': cls.post.pk})
        cls.POST_EDIT_URL = reverse('posts:post_edit',
                                    kwargs={'post_id': cls.post.pk})

        cls.POST_COMMET = reverse('posts:add_comment',
                                  kwargs={'post_id': cls.post.pk})

        cls.POST_FOLLOW = reverse('posts:follow_index')

        cls.PROFILE_FOLLOW = reverse('posts:profile_follow',
                                     kwargs={'username': cls.author})

        cls.PROFILE_UNFOLLOW = reverse('posts:profile_unfollow',
                                       kwargs={'username': cls.author})

        cls.names = (
            cls.INDEX_URL,
            cls.GROUP_LIST_URL,
            cls.USERNAME_URL,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.auth_user)
        self.authorized_client_author = Client()
        self.authorized_client_author.force_login(self.author)

    def test_url_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        GENERAL_LIST_OF_PAGES_AND_TEMPLATES_FOR_THEM = {
            self.INDEX_URL: 'posts/index.html',
            self.GROUP_LIST_URL: 'posts/group_list.html',
            self.USERNAME_URL: 'posts/profile.html',
            self.POST_DETAIL_URL: 'posts/post_detail.html',
            self.POST_EDIT_URL: 'posts/post_create.html',
            self.POST_CREATE_URL: 'posts/post_create.html',
            self.POST_FOLLOW: 'posts/follow.html'
        }

        for reverse_name, template in (
                GENERAL_LIST_OF_PAGES_AND_TEMPLATES_FOR_THEM.items()):
            with self.subTest(template=template):
                response = self.authorized_client_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_correct_context(self):
        """Проверим правильность контекста на страницах :posts/index,
        posts/group_list и posts/profile
        """

        test_dictionary = {
            'text': 'Тестовый пост',
            'group.title': 'Тестовая группа',
            'group.slug': 'test-slug',
            'author.username': 'TestAuthor',
            'image': self.post.image,
        }

        for name in self.names:
            with self.subTest(name=name):
                response = self.authorized_client.get(name)
                object = response.context.get('page_obj')[0]
                post_group = response.context.get('group')
                post_author = response.context.get('post')

                self.assertEqual(test_dictionary['text'],
                                 object.text, 'Ошибка!')
                self.assertEqual(test_dictionary['group.title'],
                                 object.group.title, 'Ошибка!')
                self.assertEqual(test_dictionary['author.username'],
                                 object.author.username, 'Ошибка!')
                self.assertEqual(test_dictionary['image'],
                                 object.image, 'Ошибка!')

                if name == '/group/testslug/':
                    self.assertEqual(test_dictionary['group.slug'],
                                     post_group.slug, 'Ошибка!')

                if name == '/group/testslug/':
                    self.assertEqual(test_dictionary['author.username'],
                                     post_author.username, 'Ошибка!')

    def test_post_detail_show_correct_context(self):
        """Шаблон posts/post_detail сформирован с правильным контекстом."""

        response = self.authorized_client.get(self.POST_DETAIL_URL)
        object = response.context.get('post')
        post_text = object.text
        post_author = object.author.username
        group_post = object.group.title
        image = object.image
        self.assertEqual(post_text, 'Тестовый пост')
        self.assertEqual(post_author, 'TestAuthor')
        self.assertEqual(group_post, 'Тестовая группа')
        self.assertEqual(image, self.post.image)

    def test_post_edit_show_correct_context(self):
        """Шаблон posts/post_edit сформирован с правильным контекстом."""

        response = self.authorized_client_author.get(self.POST_EDIT_URL)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)

    def test_post_create_show_correct_context(self):
        """Шаблон posts/post_create сформирован с правильным контекстом."""

        response = self.authorized_client.get(self.POST_CREATE_URL)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

        for field, expected in form_fields.items():
            with self.subTest(field=field):
                form_field = response.context.get('form').fields.get(field)
                self.assertIsInstance(form_field, expected)

    def test_page_does_not_contain_an_unnecessary_post(self):
        """Созданный пост не попал в группу, для которой не предназначался."""

        another_group = Group.objects.create(
            title='Другая тестовая группа',
            slug='another-test-slug',
            description='Тестовое описание другой группы',
        )

        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': another_group.slug}))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_create_post_show_home_group_list_profile_pages(self):
        """Проверим, что пост отобразился на главной странице,
        на странице группы, в профиле пользователя.
        """

        for url in self.names:
            response = self.authorized_client_author.get(url)
            self.assertEqual(len(response.context['page_obj'].object_list), 1)

    def test_cahce_index(self):
        """Проверка работы кеша."""
        post = Post.objects.create(
            text='Текст для кэша',
            author=self.author)

        response = self.authorized_client.get(self.INDEX_URL)
        posts = response.content
        post.delete()

        response_old = self.authorized_client.get(self.INDEX_URL)
        old_posts = response_old.content

        self.assertEqual(posts, old_posts)
        cache.clear()

        response_new = self.authorized_client.get(self.INDEX_URL)
        new_posts = response_new.content

        self.assertNotEqual(posts, new_posts)
