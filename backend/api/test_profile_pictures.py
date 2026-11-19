from io import BytesIO
from tempfile import TemporaryDirectory

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from PIL import Image

from accounts.models import StudentProfile, User
from companies.models import Company


def sample_picture(color="green"):
    content = BytesIO()
    Image.new("RGB", (20, 12), color).save(content, "PNG")
    return SimpleUploadedFile("picture.png", content.getvalue(), "image/png")


class ProfilePictureTests(TestCase):
    password = "TestOnly-Profile-145!"

    def setUp(self):
        storage = self.enterContext(TemporaryDirectory())
        self.enterContext(override_settings(MEDIA_ROOT=storage))
        self.browser = Client(enforce_csrf_checks=True)

    def post(self, route, data, *args):
        self.browser.get(reverse("api:csrf"))
        return self.browser.post(reverse(f"api:{route}", args=args), data,
                                 HTTP_X_CSRFTOKEN=self.browser.cookies["csrftoken"].value)

    def registration(self, role):
        return {"username": f"picture_{role}", "email": f"{role}@example.test", "role": role,
                "password1": self.password, "password2": self.password}

    def test_signup_and_edit_for_both_roles(self):
        roles = [
            ("student", StudentProfile, {"full_name": "Test Student", "university": "Asian Institute of Technology",
                                         "degree": "Computing"}),
            ("company", Company, {"company_name": "Test Company", "industry": "IT", "phone": "012345",
                                  "description": "Description", "address": "Bangkok"}),
        ]
        for role, model, details in roles:
            with self.subTest(role=role):
                registered = self.post("register", self.registration(role) | {"profile_picture": sample_picture()})
                self.assertEqual(registered.status_code, 201, registered.content)
                original = model.objects.get(user__username=f"picture_{role}").profile_picture
                self.assertTrue(original.name.endswith(".webp"))
                url = self.browser.get(reverse(f"api:{role}-profile")).json()["profile"]["profile_picture_url"]
                response = self.browser.get(url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Content-Type"], "image/webp")
                with Image.open(BytesIO(b"".join(response.streaming_content))) as picture:
                    self.assertEqual(picture.size, (20, 12))
                self.assertEqual(self.post(f"{role}-profile-save", details).status_code, 200)
                self.assertEqual(model.objects.get(pk=model.objects.get(user__username=f"picture_{role}").pk).profile_picture.name, original.name)
                with self.captureOnCommitCallbacks(execute=True):
                    edited = self.post(f"{role}-profile-save", details | {"profile_picture": sample_picture("blue")})
                    self.assertEqual(edited.status_code, 200, edited.content)
                self.assertFalse(original.storage.exists(original.name))
                self.assertNotEqual(self.browser.get(reverse(f"api:{role}-profile")).json()["profile"]["profile_picture_url"], url)
                self.assertEqual(self.post("sign-out", {}).status_code, 200)
                self.assertEqual(self.browser.get(url).status_code, 403)

    def test_registration_picture_is_optional_and_invalid_upload_is_rejected(self):
        data = self.registration("student")
        for payload in (b"not a real image", b"x" * (2 * 1024 * 1024 + 1)):
            response = self.post("register", data | {"profile_picture": SimpleUploadedFile("invalid.png", payload)})
            self.assertEqual(response.status_code, 400)
            self.assertIn("profile_picture", response.json()["errors"])
            self.assertFalse(User.objects.filter(username=data["username"]).exists())
        self.assertEqual(self.post("register", data).status_code, 201)
        self.assertFalse(StudentProfile.objects.filter(user__username=data["username"]).exists())

    def test_signup_photo_does_not_complete_the_student_profile(self):
        response = self.post("register", self.registration("student") | {"profile_picture": sample_picture()})
        self.assertEqual(response.status_code, 201)
        result = self.post("apply", {}, 1)
        self.assertEqual(result.status_code, 400)
        self.assertIn("Complete your student profile", result.json()["detail"])
