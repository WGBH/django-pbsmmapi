# Generated by Django 2.2 on 2019-05-02 16:29

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("season", "0004_auto_20190430_1949"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="pbsmmseason",
            options={
                "ordering": ["-ordinal"],
                "verbose_name": "PBS MM Season",
                "verbose_name_plural": "PBS MM Seasons",
            },
        ),
    ]
