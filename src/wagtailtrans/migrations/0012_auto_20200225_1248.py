# Generated by Django 3.0.3 on 2020-02-25 12:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailtrans', '0011_auto_20200224_1043'),
    ]

    operations = [
        migrations.AlterField(
            model_name='translatablepageitem',
            name='page',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='translatable_page_item', to='wagtailcore.Page'),
        ),
    ]
