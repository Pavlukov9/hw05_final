# Generated by Django 2.2.19 on 2023-03-15 14:37

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0006_follow'),
    ]

    operations = [
        migrations.RenameField(
            model_name='comment',
            old_name='create',
            new_name='created',
        ),
    ]
