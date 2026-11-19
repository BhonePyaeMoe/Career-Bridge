from pathlib import Path
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator


def validate_profile_picture_size(value):
    if value.size > 2 * 1024 * 1024:
        raise ValidationError("Profile pictures must be 2 MB or smaller.")


profile_picture_validators = [
    FileExtensionValidator(["jpg", "jpeg", "png", "webp"]),
    validate_profile_picture_size,
]


def student_picture_path(instance, filename):
    return f"profile_pictures/students/{instance.user_id}/{uuid4().hex}{Path(filename).suffix.lower()}"


def company_picture_path(instance, filename):
    return f"profile_pictures/companies/{instance.user_id}/{uuid4().hex}{Path(filename).suffix.lower()}"
