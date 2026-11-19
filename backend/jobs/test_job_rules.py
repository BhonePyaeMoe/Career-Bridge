from datetime import date, timedelta

import pytest
from django.core.exceptions import ValidationError

from jobs.models import Job


@pytest.fixture
def today(monkeypatch):
    fixed_date = date(2026, 1, 15)
    monkeypatch.setattr("jobs.models.timezone.localdate", lambda: fixed_date)
    return fixed_date


@pytest.mark.parametrize(
    ("approval_status", "days_from_today", "expected"),
    [
        pytest.param(Job.ApprovalStatus.APPROVED, -1, False, id="expired-yesterday"),
        pytest.param(Job.ApprovalStatus.APPROVED, 0, True, id="deadline-today"),
        pytest.param(Job.ApprovalStatus.APPROVED, 1, True, id="deadline-tomorrow"),
        pytest.param(Job.ApprovalStatus.PENDING, 1, False, id="pending-approval"),
    ],
)
def test_job_is_open(today, approval_status, days_from_today, expected):
    job = Job(approval_status=approval_status, deadline=today + timedelta(days=days_from_today))

    assert job.is_open is expected


@pytest.mark.parametrize("work_mode", [Job.WorkMode.ONSITE, Job.WorkMode.HYBRID])
def test_job_requires_location_unless_remote(today, work_mode):
    job = Job(
        title="Software internship",
        description="Build and test features.",
        requirements="Basic Python.",
        job_type=Job.JobType.INTERNSHIP,
        work_mode=work_mode,
        location="",
        deadline=today + timedelta(days=1),
    )

    # Skip company validation so this unsaved job can be tested without the database.
    with pytest.raises(ValidationError) as error:
        job.full_clean(exclude={"company"})

    assert set(error.value.message_dict) == {"location"}
