import core.profile_images
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("companies", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="company",
            name="profile_picture",
            field=models.ImageField(
                blank=True,
                max_length=255,
                upload_to=core.profile_images.company_picture_path,
                validators=[
                    django.core.validators.FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
                    core.profile_images.validate_profile_picture_size,
                ],
            ),
        ),
    ]
