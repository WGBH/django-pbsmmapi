# Generated by Django 2.2 on 2019-04-30 18:53

from django.db import (
    migrations,
    models,
)
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("season", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="pbsmmseason",
            name="show",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="seasons",
                to="show.PBSMMShow",
            ),
        ),
    ]
