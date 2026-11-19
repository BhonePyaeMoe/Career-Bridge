from io import BytesIO

from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image, ImageOps, UnidentifiedImageError

from accounts.forms import RegistrationForm, StudentProfileForm
from companies.forms import CompanyForm
from core.profile_images import profile_picture_validators


class ProfilePictureField(forms.FileField):
    def __init__(self):
        super().__init__(required=False, validators=profile_picture_validators)

    def clean(self, data, initial=None):
        picture = super().clean(data, initial)
        if not data or not picture:
            return picture
        try:
            with Image.open(picture, formats=("JPEG", "PNG", "WEBP")) as image:
                if image.width * image.height > 16_000_000:
                    raise forms.ValidationError("Use an image of 16 megapixels or less.")
                if getattr(image, "is_animated", False):
                    raise forms.ValidationError("Use a still image, not an animation.")
                pixels = ImageOps.exif_transpose(image).convert("RGBA")
                pixels.thumbnail((1024, 1024), Image.Resampling.LANCZOS)
                # Fresh pixels only: do not retain original metadata or trailing data.
                normalized = Image.new("RGBA", pixels.size)
                normalized.paste(pixels)
                output = BytesIO()
                normalized.save(output, "WEBP", quality=85)
        except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
            raise forms.ValidationError("Upload a valid JPG, PNG or WebP image.") from exc
        result = SimpleUploadedFile("profile.webp", output.getvalue(), content_type="image/webp")
        for validator in profile_picture_validators:
            validator(result)
        return result


class ImageRegistrationForm(RegistrationForm):
    profile_picture = ProfilePictureField()


class ImageStudentProfileForm(StudentProfileForm):
    profile_picture = ProfilePictureField()

    class Meta(StudentProfileForm.Meta):
        fields = StudentProfileForm.Meta.fields + ["profile_picture"]


class ImageCompanyForm(CompanyForm):
    profile_picture = ProfilePictureField()

    class Meta(CompanyForm.Meta):
        fields = CompanyForm.Meta.fields + ["profile_picture"]
