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


# Model for course template
# params:
# course title, number, professor, start date, meeting dates, meeting times, class type

class Course(models.Model): 
    title = models.CharField(max_length=200)
    course_number = models.CharField(max_length=50)
    professor = models.CharField(max_length=100)
    start_date = models.DateField() # Dates saved as YYYY-MM-DD
    meeting_dates = models.CharField(
        max_length=20, 
        choices=[
            ('Monday', 'Monday'),
            ('Tuesday', 'Tuesday'),
            ('Wednesday', 'Wednesday'),
            ('Thursday', 'Thursday'),
            ('Friday', 'Friday'),
            ('Saturday', 'Saturday'),
            ('Sunday', 'Sunday'),
            ]) 
    meeting_times = models.TimeField() # Time is saved in HH:MM:SS format
    end_date = models.DateField() # YYYY-MM-DD
    class_type = models.CharField(max_length=50, choices=[('In-Class', 'In-Class'), ('Virtual', 'Virtual'), ('Mixed', 'Mixed')])

    def __str__(self):
        return f"{self.title} ({self.course_number})"