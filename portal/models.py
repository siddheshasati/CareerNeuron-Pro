from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class UserProfile(models.Model):
    GENDER_CHOICES = (
        ('', 'Select gender'),
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Prefer not to say', 'Prefer not to say'),
    )
    YES_NO_CHOICES = (
        ('', 'Select option'),
        ('Yes', 'Yes'),
        ('No', 'No'),
    )
    ROLE_CHOICES = (
        ('User', 'User'),
        ('Admin', 'Admin'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    mobile = models.CharField(max_length=20, blank=True, null=True)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='User')
    profile_completed = models.BooleanField(default=False)
    full_name = models.CharField(max_length=150, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=30, choices=GENDER_CHOICES, blank=True, default='')
    disability = models.CharField(max_length=10, choices=YES_NO_CHOICES, blank=True, default='')
    country = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    pincode = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    linkedin_url = models.URLField(max_length=500, blank=True, null=True)
    github_url = models.URLField(max_length=500, blank=True, null=True)
    portfolio_url = models.URLField(max_length=500, blank=True, null=True)
    additional_url_name = models.CharField(max_length=100, blank=True, null=True)
    additional_url = models.URLField(max_length=500, blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    ai_suggestions = models.TextField(blank=True, null=True)
    resume = models.FileField(upload_to='resumes/', blank=True, null=True)
    resume_data = models.TextField(blank=True, null=True) # Will store JSON
    ats_score = models.IntegerField(blank=True, null=True)
    def __str__(self):
        return f"{self.user.username}'s Profile"

class Education(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='educations')
    institution = models.CharField(max_length=200)
    city = models.CharField(max_length=100, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    degree = models.CharField(max_length=100)
    specialization = models.CharField(max_length=150, blank=True, null=True)
    education_type = models.CharField(max_length=50, blank=True, null=True)
    stream = models.CharField(max_length=100, blank=True, null=True)
    start_date = models.CharField(max_length=20, blank=True, null=True)
    end_date = models.CharField(max_length=20, blank=True, null=True)
    currently_pursuing = models.BooleanField(default=False)
    grade = models.CharField(max_length=20, blank=True, null=True)
    skills = models.CharField(max_length=255, blank=True, null=True)

class Experience(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='experiences')
    company = models.CharField(max_length=200)
    organization = models.CharField(max_length=200, blank=True, null=True)
    location = models.CharField(max_length=100, blank=True, null=True)
    role = models.CharField(max_length=100)
    job_type = models.CharField(max_length=50, blank=True, null=True)
    ctc = models.CharField(max_length=50, blank=True, null=True)
    current_ctc = models.CharField(max_length=50, blank=True, null=True)
    start_date = models.CharField(max_length=20, blank=True, null=True)
    end_date = models.CharField(max_length=20, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)

class Job(models.Model):
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True, null=True)
    link = models.URLField(max_length=500)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title


class OTPToken(models.Model):
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_verified = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)

    def is_valid(self):
        return (
            not self.is_verified and
            self.attempts < 5 and
            timezone.now() <= self.expires_at
        )

    def __str__(self):
        return f"OTP for {self.email}"


class Interview(models.Model):
    profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='interviews')
    role = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    question_count = models.IntegerField(default=0)
    duration_seconds = models.IntegerField(default=0)
    transcript = models.TextField(blank=True, null=True)
    ats_feedback = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Interview - {self.role} at {self.company} ({self.created_at.strftime('%Y-%m-%d')})"
