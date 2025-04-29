from django.db import models

from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    email = models.EmailField(unique=True)  
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return self.user.username


# Model for course template and section
# split them for easier integration

class Course(models.Model):
    code = models.CharField(max_length=20, default='UNKN')
    title = models.CharField(max_length=200)
    credits = models.IntegerField( default=-1)
    prerequisites = models.TextField(blank=True)
    corerequistes = models.TextField(blank=True)
    crossListed = models.TextField(blank=True)
    description = models.TextField(default='UNKN')

    def __str__(self):
        return f"{self.code}: {self.title}"

class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    section_id = models.CharField(max_length=10)
    instructor = models.CharField(max_length=100)
    days = models.CharField(max_length=10)
    time = models.CharField(max_length=20)
    location = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.course.code} - Section {self.section_id}"
    
class SchedulingSurvey(models.Model):
    YEAR_CHOICES = [
        ('FR', 'Freshman'),
        ('SO', 'Sophomore'),
        ('JR', 'Junior'),
        ('SR', 'Senior'),
        ('GR', 'Graduate'),
    ]

    name = models.CharField(max_length=100)
    email = models.EmailField()
    year = models.CharField(max_length=2, choices=YEAR_CHOICES)
    major = models.CharField(max_length=100)
    minor = models.CharField(max_length=100, blank=True, null=True)
    special_programs = models.CharField(max_length=200, blank=True, null=True)

    preferred_times = models.CharField(max_length=200)
    preferred_days = models.CharField(max_length=200)
    days_off = models.CharField(max_length=200, blank=True)
    class_spacing = models.CharField(max_length=50)

    learning_style = models.CharField(max_length=50)
    format_preference = models.CharField(max_length=50)
    professor_notes = models.TextField(blank=True)
    must_have_courses = models.TextField(blank=True)

    work_schedule = models.TextField(blank=True)
    other_commitments = models.TextField(blank=True)
    commute_time = models.CharField(max_length=100, blank=True)

    academic_interests = models.TextField()
    career_goals = models.TextField(blank=True)
    elective_interests = models.TextField(blank=True)

    preferred_distribution = models.CharField(max_length=50)
    max_classes_per_day = models.IntegerField()
    min_gap_minutes = models.IntegerField()
    clustered_or_spread = models.CharField(max_length=50)
    heavy_load_preference = models.BooleanField(default=False)
    night_classes_ok = models.BooleanField(default=False)

    other_notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.email})"