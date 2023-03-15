import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post, User, Comment

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostCreateFormTests(TestCase):

    USERNAME_URL = reverse('posts:profile',
                           kwargs={'username': 'TestAuthor'})
    POST_CREATE_URL = reverse('posts:post_create')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='TestAuthor')

        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
        )

        cls.POST_EDIT_URL = reverse('posts:post_edit',
                                    kwargs={'post_id': cls.post.pk})
        cls.POST_DETAIL_URL = reverse('posts:post_detail',
                                      kwargs={'post_id': cls.post.pk})

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post(self):
        """Валидная форма со страницы создания поста
        создает новую запись в Posts.
        """
        posts_count = Post.objects.count()

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
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.pk,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            self.POST_CREATE_URL,
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, self.USERNAME_URL)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(Post.objects.filter(text=form_data['text'],
                                            group=form_data['group']).exists())

    def test_author_edit_post(self):
        """При редактировании происходит изменение поста с post_id в БД"""

        self.post = Post.objects.create(
            text='Тестовый текст',
            author=self.author
        )

        form_data = {
            'text': 'Отредактированный текст',
        }

        response = self.authorized_client.post(
            self.POST_EDIT_URL,
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, self.POST_DETAIL_URL)
        self.assertTrue(Post.objects.filter(
                        text=form_data['text']).exists())

    def test_create_comment(self):
        """Проверим, что при успешной отправки
        комментарий появляется на странице поста.
        """
        comments_count = Comment.objects.count()

        form_data = {
            'text': 'Тестовый комментарий'
        }

        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )

        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertRedirects(response,
                             reverse('posts:post_detail', args={self.post.id}))

    def test_create_comment_guest_client(self):
        """Проверим, комментарии оставлять может только
        авторизованный пользователь.
        """
        comments_count = Comment.objects.count()

        form_data = {
            'text': 'Тестовый комментарий'
        }

        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )

        self.assertEqual(Comment.objects.count(), comments_count)
        self.assertEqual(response.status_code, 200)
