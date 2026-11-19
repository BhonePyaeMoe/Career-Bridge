import pytest
from django.urls import reverse


@pytest.fixture(params=["admin", "student", "company"])
def account(request, db, django_user_model):
    role = request.param
    fields = {"username": role, "email": f"{role}@example.test", "role": role}
    if role == "admin":
        return django_user_model.objects.create_superuser(**fields)
    return django_user_model.objects.create_user(**fields)


def test_only_admin_account_can_open_admin_dashboard(client, account):
    client.force_login(account)
    dashboard_url = reverse("admin:index")

    response = client.get(dashboard_url)

    if account.role == "admin":
        assert response.status_code == 200
    else:
        assert response.status_code == 302
        assert response.url == f"{reverse('admin:login')}?next={dashboard_url}"
