import core.profile_images
import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0003_alter_studentprofile_cv"),
    ]

    operations = [
        migrations.AddField(
            model_name="studentprofile",
            name="profile_picture",
            field=models.ImageField(
                blank=True,
                max_length=255,
                upload_to=core.profile_images.student_picture_path,
                validators=[
                    django.core.validators.FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
                    core.profile_images.validate_profile_picture_size,
                ],
            ),
        ),
    ]
