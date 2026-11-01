from django import forms
from interview import models

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = models.UserProfile
        fields = ('intro', 'location', 'sex', 'dob', 'current_job_role', 'current_company',
                  'highest_degree', 'linkedin_profile_url', 'github_profile_url'
                  )


class SignupForm(forms.Form):
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)

    def signup(self, request, user):
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()


class UserInterviewForm(forms.ModelForm):
    class Meta:
        model = models.UserInterview
        fields = ('job_role', 'job_description', 'company', 'auto_answer')

    def clean(self):
        cleaned_data = super().clean()

        # Clean job_role
        job_role = cleaned_data.get('job_role')
        if job_role:
            cleaned_data['job_role'] = self.clean_text(job_role)

        # Clean job_description
        job_description = cleaned_data.get('job_description')
        if job_description:
            cleaned_data['job_description'] = self.clean_text(job_description)

        # Clean company
        company = cleaned_data.get('company')
        if company:
            cleaned_data['company'] = self.clean_text(company)

        return cleaned_data

    def clean_text(self, text):
        # Remove curly brackets, double quotes, and single quotes
        return text.replace('{', '').replace('}', '').replace('"', '').replace("'", '')


class ContactUsForm(forms.ModelForm):
    class Meta:
        model = models.ContactUs
        fields = ('name', 'email', 'contact_no', 'message')
        labels = {
            'name': 'Name',
            'email': 'Email',
            'contact_no': 'Phone Number (Include your country code)',
            'message': 'Message',
        }
