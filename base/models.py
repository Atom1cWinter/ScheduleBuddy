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
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200)
    credits = models.IntegerField()
    description = models.TextField()
    prerequisites = models.TextField(blank=True)
    corerequistes = models.TextField(blank=True)
    crossListed = models.TextField(blank=True)

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