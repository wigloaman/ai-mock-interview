from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):

    choices_for_sex = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('not_disclosed', 'Rather not disclose'))

    user = models.OneToOneField(
        User, related_name='userprofile', on_delete=models.CASCADE)
    token = models.IntegerField(default=0)
    intro = models.CharField(max_length=200, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    sex = models.CharField(max_length=15, null=True,
                           blank=True, choices=choices_for_sex)
    dob = models.DateTimeField(null=True, blank=True)
    current_job_role = models.CharField(max_length=100, null=True, blank=True)
    current_company = models.CharField(max_length=100, null=True, blank=True)
    highest_degree = models.CharField(max_length=100, null=True, blank=True)
    linkedin_profile_url = models.URLField(null=True, blank=True)
    github_profile_url = models.URLField(null=True, blank=True)
    last_seen = models.DateTimeField(blank=True, null=True)
    percent_profile_completed = models.IntegerField(default=0)
    # profile_picture = models.ImageField(
    #     blank=True, null=True,)  #upload_to=settings.PROFILE_PICTURE_UPLOAD_PATH, validators=[custom_validators.validate_image_extension])
    # resume = models.FileField(
    #     blank=True, null=True,
    #     upload_to='resumes',)
    #     #validators=[custom_validators.validate_pdf_extension, custom_validators.validate_file_size])
    device = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.CharField(max_length=255, null=True, blank=True)
    country = models.CharField(max_length=100, blank=True, default='')
    city = models.CharField(max_length=100, blank=True, default='')
    region = models.CharField(max_length=100, blank=True, default='')
    postal_code = models.CharField(max_length=15, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
