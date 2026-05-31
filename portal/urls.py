from django.urls import path
from . import views

app_name = "portal"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_step1_view, name="register"),
    path("verify-otp/", views.verify_otp_view, name="verify_otp"),
    path("register-step2/", views.register_step2_view, name="register_step2"),
    path("logout/", views.logout_view, name="logout"),
    path("profile/", views.profile_view, name="profile"),
    path("advisor/", views.advisor_view, name="advisor"),
    path("interview/", views.interview_view, name="interview"),
    path("cover-letter/", views.cover_letter_view, name="cover_letter"),
    path("job-match/", views.job_match_view, name="job_match"),
    path("api/interview/", views.interview_api, name="interview_api"),
]
