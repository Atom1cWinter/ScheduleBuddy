from django.db import models
from django.contrib.auth.models import User
from django.forms import ValidationError


# User Profile Model
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    additional_info = models.TextField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    survey = models.OneToOneField('SchedulingSurvey', on_delete=models.SET_NULL, null=True, blank=True)

    def survey_results(self):
        if self.survey:
            return f"{self.survey.name} ({self.survey.email})"
        return "No survey results"

    survey_results.short_description = "Survey Results"  # This sets the column name in the admin panel

    def __str__(self):
        return self.user.username


# Course Model
class Course(models.Model):
    code = models.CharField(max_length=20, default='UNKN')  # e.g., "MATH101"
    name = models.CharField(max_length=200, default='Untitled Course')
    credits = models.IntegerField(default=0)
    prerequisites = models.TextField(blank=True, default='')
    corequisites = models.TextField(blank=True, default='')
    crosslisted_courses = models.TextField(blank=True, default='')
    description = models.TextField(blank=True, default='No description provided.')

    def __str__(self):
        return f"{self.code}: {self.name}"


# Section Model
class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    term = models.CharField(max_length=20, default='TBD')  # e.g., "Fall 2025"
    crn = models.CharField(max_length=10, default='00000')  # Course Registration Number
    section_code = models.CharField(max_length=10, default='A')
    subject = models.CharField(max_length=10, null=True, blank=True)  # e.g., "CS"
    course_number = models.CharField(max_length=10, null=True, blank=True)  # e.g., "101"
    course_code = models.CharField(max_length=20, null=True, blank=True) # e.g., "ITSC 3155"
    begins = models.TimeField(null=True, blank=True)
    ends = models.TimeField(null=True, blank=True)
    mo = models.BooleanField(default=False)  # Monday
    tu = models.BooleanField(default=False)  # Tuesday
    we = models.BooleanField(default=False)  # Wednesday
    th = models.BooleanField(default=False)  # Thursday
    fr = models.BooleanField(default=False)  # Friday
    sa = models.BooleanField(default=False)  # Saturday
    su = models.BooleanField(default=False)  # Sunday

    def __str__(self):
        days = []
        if self.mo: days.append('Monday')
        if self.tu: days.append('Tuesday')
        if self.we: days.append('Wednesday')
        if self.th: days.append('Thursday')
        if self.fr: days.append('Friday')
        if self.sa: days.append('Saturday')
        if self.su: days.append('Sunday')
        return f"{self.course.code} - {self.section_code} ({', '.join(days)})"


# Scheduling Survey Model
class SchedulingSurvey(models.Model):
    # Choices
    YEAR_CHOICES = [
        ('FR', 'Freshman'),
        ('SO', 'Sophomore'),
        ('JR', 'Junior'),
        ('SR', 'Senior'),
        ('GR', 'Graduate'),
    ]
    PREFERRED_DISTRIBUTION_CHOICES = [
        ('MWF', 'Monday/Wednesday/Friday'),
        ('TTH', 'Tuesday/Thursday'),
        ('Spread', 'Spread Across Week'),
    ]
    TIME_DISTRIBUTION_CHOICES = [
        ('morning', 'Morning-heavy'),
        ('afternoon', 'Afternoon-heavy'),
        ('even', 'Evenly distributed'),
    ]

    # Link to the user
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)  # Add this field

    # Basic Information
    name = models.CharField(max_length=100)
    email = models.EmailField()
    year = models.CharField(max_length=2, choices=YEAR_CHOICES)
    major = models.CharField(max_length=100)
    minor = models.CharField(max_length=100, blank=True, null=True)
    special_programs = models.CharField(max_length=200, blank=True, null=True)

    # Preferences
    preferred_times = models.CharField(max_length=200)
    preferred_days = models.CharField(max_length=200)
    days_off = models.CharField(max_length=200, blank=True)
    class_spacing = models.CharField(max_length=50)
    learning_style = models.CharField(max_length=50)
    format_preference = models.CharField(max_length=50)
    preferred_distribution = models.CharField(
        max_length=50,
        choices=PREFERRED_DISTRIBUTION_CHOICES,
        default='Spread'
    )
    time_distribution = models.CharField(
        max_length=50,
        choices=TIME_DISTRIBUTION_CHOICES,
        default='even'
    )
    clustered_or_spread = models.CharField(max_length=50)
    heavy_load_preference = models.BooleanField(default=False)
    night_classes_ok = models.BooleanField(default=False)

    # Additional Information
    professor_notes = models.TextField(blank=True)
    must_have_courses = models.TextField(blank=True)
    work_schedule = models.TextField(blank=True)
    other_commitments = models.TextField(blank=True)
    commute_time = models.CharField(max_length=100, blank=True)
    academic_interests = models.TextField()
    career_goals = models.TextField(blank=True)
    elective_interests = models.TextField(blank=True)
    other_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.email})"


# Schedule Model
class Schedule(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    sections = models.ManyToManyField(Section)
    created_at = models.DateTimeField(auto_now_add=True)
    google_calendar_event_id = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"