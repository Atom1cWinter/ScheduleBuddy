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
    name = models.CharField(max_length=200, default='Untitled Course')
    credits = models.IntegerField(default=0)
    prerequisites = models.TextField(blank=True, default='')
    corequisites = models.TextField(blank=True, default='')
    crosslisted_courses = models.TextField(blank=True, default='')
    description = models.TextField(blank=True, default='No description provided.')

    def __str__(self):
        return f"{self.code}: {self.name}"


class Section(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    term = models.CharField(max_length=20, default='TBD')
    crn = models.CharField(max_length=10, default='00000')
    section_code = models.CharField(max_length=10, default='A')
    instructor_first_name = models.CharField(max_length=100, blank=True, default='')
    instructor_last_name = models.CharField(max_length=100, blank=True, default='')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    begins = models.TimeField(null=True, blank=True)
    ends = models.TimeField(null=True, blank=True)
    mo = models.BooleanField(default=False)
    tu = models.BooleanField(default=False)
    we = models.BooleanField(default=False)
    th = models.BooleanField(default=False)
    fr = models.BooleanField(default=False)
    sa = models.BooleanField(default=False)
    su = models.BooleanField(default=False)
    building = models.CharField(max_length=100, blank=True, default='')
    room = models.CharField(max_length=50, blank=True, default='')
    mode = models.CharField(max_length=100, blank=True, default='In-Person')
    instructional_method = models.CharField(max_length=100, blank=True, default='Standard')
    campus = models.CharField(max_length=100, blank=True, default='Main')
    college = models.CharField(max_length=100, blank=True, default='Undeclared')

    def __str__(self):
        return f"{self.course.code} - {self.section_code} ({self.term})"
    
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
    
# Calendar Implementation
class Schedule(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    sections = models.ManyToManyField(Section)
    created_at = models.DateTimeField(auto_now_add=True)
    google_calendar_event_id = models.CharField(max_length=255, blank=True, null=True)

    def clean(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise Validationerror("End date must be after start date.")
        if self.begins and self.ends and self.begins >= self.ends:
            raise ValidationError("End time must be after start time.")
        
    def __str__(self):
        return f"{self.name} ({self.user.username})"