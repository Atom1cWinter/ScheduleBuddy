from django.contrib import admin
from .models import Course, Profile

# -------------------------------------------------
# Admin: Course
# -------------------------------------------------

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    search_fields = ('title', 'course_number', 'professor')

# -------------------------------------------------
# Admin: Profile
# -------------------------------------------------

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'full_name', 'survey_results')  # Display user, full name, and survey results

admin.site.register(Profile, ProfileAdmin)
