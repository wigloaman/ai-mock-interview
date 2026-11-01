from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from datetime import timedelta


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


class UserInterview(models.Model):
    choices_for_difficulty = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard')
    )

    choices_for_question_type = (
        ('all', 'All'),
        ('coding', 'Coding'),
        ('theory', 'Theory'),
        ('behavioural', 'Behavioural'),
        ('puzzle', 'Puzzle'),
        ('design', 'Design')
    )

    choice_for_duration = (
        (timedelta(minutes=30), '30 minutes'),
        # (timedelta(minutes=60), '1 hour'),
        # (timedelta(minutes=90), '1 hour 30 minutes'),
        # (timedelta(minutes=120), '2 hours')
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    score = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    review = models.TextField(null=True, blank=True)
    strong_points = models.TextField(null=True, blank=True)
    weak_points = models.TextField(null=True, blank=True)
    improvements = models.TextField(null=True, blank=True)
    is_selected = models.BooleanField(null=True)
    reason_selection = models.TextField(null=True, blank=True)
    company = models.CharField(max_length=128, null=True, blank=True)
    job_role = models.CharField(max_length=128)
    interview_round = models.PositiveIntegerField(default=1,
                                                  validators=[MinValueValidator(1),
                                                              MaxValueValidator(10)],
                                                  null=True, blank=True)
    job_description = models.TextField(max_length=5000, null=True, blank=True)
    subject = models.CharField(max_length=128, null=True, blank=True,
                               help_text="Put a comma after each subject")
    topic = models.CharField(max_length=128, null=True, blank=True,
                             help_text="Put a comma after each topic")
    tools = models.CharField(max_length=512, null=True, blank=True,
                             help_text="Put a comma after each tool")
    difficulty_level = models.CharField(max_length=6, null=True,
                                        blank=True, choices=choices_for_difficulty)
    question_type = models.CharField(max_length=12, null=True, default="all",
                                     blank=True, choices=choices_for_question_type)
    user_instructions = models.TextField(null=True, blank=True,)  # To get custom user instructions
    cross_question = models.BooleanField(default=True)
    tags = models.CharField(max_length=500, null=True, blank=True,
                            help_text="Put a comma after each tag")
    duration = models.DurationField(default=timedelta(minutes=30), choices=choice_for_duration)
    auto_answer = models.BooleanField(default=False,
                                      help_text="Automatically answers all questions using AI.")
    is_complete = models.BooleanField(default=False)
    review_generated = models.BooleanField(default=False)
    error_present = models.BooleanField(default=False)
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class UserQuestionAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session = models.ForeignKey(UserInterview, on_delete=models.CASCADE)
    pos = models.FloatField(default=0.0)
    question = models.TextField()
    answer = models.TextField(null=True, blank=True)
    perfect_answer = models.TextField(null=True, blank=True)
    score = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(0), MaxValueValidator(10)]
    )
    is_asked = models.BooleanField(default=False)
    review = models.TextField(null=True, blank=True)
    improvements = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ContactUs(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField()
    contact_no = models.CharField(max_length=25, null=True, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Feedback(models.Model):
    EMOJI_CHOICES = [
        ('1', 'Very Poor'),
        ('2', 'Poor'),
        ('3', 'Good'),
        ('4', 'Very Good'),
        ('5', 'Excellent'),
    ]

    question_rating = models.CharField(max_length=1, choices=EMOJI_CHOICES)
    helpfulness_rating = models.CharField(max_length=1, choices=EMOJI_CHOICES)
    interface_rating = models.CharField(max_length=1, choices=EMOJI_CHOICES)
    reviewer_rating = models.CharField(max_length=1, choices=EMOJI_CHOICES)
    website_rating = models.CharField(max_length=1, choices=EMOJI_CHOICES)
    improvements = models.TextField(blank=True)
    email = models.EmailField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
