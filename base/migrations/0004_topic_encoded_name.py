# Generated by Django 4.1.4 on 2023-06-08 05:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_alter_user_bio'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='encoded_name',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
