from django.contrib import admin
from .models import Course, Profile

# Register your models here.

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    #list_display = ('title', 'course_number', 'professor', 'start_date', 'end_date', 'class_type', 'location')
    #list_filter = ('class_type', 'meeting_dates')
    search_fields = ('title', 'course_number', 'professor')

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'survey_results')  # Add 'survey_results' here

admin.site.register(Profile, ProfileAdmin)