import django.core.validators
import django.db.models
from django.db import migrations, models


def copy_existing_ratings_to_stars(apps, schema_editor):
    Review = apps.get_model("product", "Review")
    database = schema_editor.connection.alias
    Review.objects.using(database).update(stars=django.db.models.F("rating"))


class Migration(migrations.Migration):

    dependencies = [
        ("product", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="review",
            name="stars",
            field=models.IntegerField(
                null=True,
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(5),
                ],
                verbose_name="Количество звёзд",
            ),
        ),
        migrations.RunPython(copy_existing_ratings_to_stars, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="review",
            name="stars",
            field=models.IntegerField(
                validators=[
                    django.core.validators.MinValueValidator(1),
                    django.core.validators.MaxValueValidator(5),
                ],
                verbose_name="Количество звёзд",
            ),
        ),
    ]
