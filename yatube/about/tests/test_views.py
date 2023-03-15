from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse


User = get_user_model()


class AboutTests(TestCase):
    def setUp(self):
        self.authorized_client = Client()
        self.user = User.objects.create(username='TestAuthor')
        self.authorized_client.force_login(self.user)

    def test_url_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""

        templates_names = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
        }

        for template, reverse_name in templates_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
