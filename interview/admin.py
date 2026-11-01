from django.contrib import admin
from interview import models

# Register your models here.


class UserProfileAdmin(admin.ModelAdmin):
    raw_id_fields = ('user',)
    list_display = ('user', 'token','location', 'current_job_role', 'current_company',
                    'highest_degree', 'last_seen', 'percent_profile_completed', 'created_at', 'updated_at')
    list_filter = ['created_at', 'updated_at']
    search_fields = ['user__username', 'user__email']


admin.site.register(models.UserProfile, UserProfileAdmin)
