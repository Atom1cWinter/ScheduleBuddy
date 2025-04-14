from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from .models import Profile  #need to import your Profile model
from .forms import ProfileForm  # need to create this form
from .models import Course # course template import

def home(request):
    return render(request, 'base/home.html')

def calendarSync(request):
    return render(request, 'base/calendarSync.html')

def courseLoad(request):
    return render(request, 'base/courseLoad.html')

def roadMap(request):
    return render(request, 'base/roadMap.html')

def waitListClearance(request):
    return render(request, 'base/waitListClearance.html')

def openSeat(request):
    return render(request, 'base/openSeat.html')

def sectionRec(request):
    return render(request, 'base/sectionRec.html')

@login_required
def profile_view(request):
    try:
        profile = request.user.profile
    except Profile.DoesNotExist:
        # Create profile if it doesn't exist
        Profile.objects.create(user=request.user)
        profile = request.user.profile
    
    return render(request, 'profiles/profile.html', {'profile': profile})

@login_required
def profile_edit(request):
    # Ensure profile exists
    if not hasattr(request.user, 'profile'):
        Profile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user.profile)
    
    return render(request, 'profiles/profile_edit.html', {'form': form})


def course_list(request):
    courses = Course.objects.all()
    return render(request, 'course_list.html', {'courses': courses})

def add_course(request):
    if request.method == 'POST':
        # Extract data from request
        title = request.POST.get('title')
        course_number = request.POST.get('course_number')
        professor = request.POST.get('professor')
        start_date = request.POST.get('start_date')
        meeting_dates = request.POST.get('meeting_dates')
        meeting_times = request.POST.get('meeting_times')
        end_date = request.POST.get('end_date')
        class_type = request.POST.get('class_type')
        location = request.POST.get('location')

        # create and save course
        course = Course.objects.create(
            title = title,
            course_number = course_number,
            professor = professor,
            start_date = start_date,
            meeting_dates = meeting_dates,
            meeting_times = meeting_times,
            end_date = end_date,
            class_type = class_type,
            location = location
        )
        return JsonResponse({'message' : 'Course added successfully!', 'course_id' : course.id})
    else:
        return JsonResponse({'error' : 'Invalid request method. Use POST.'}, status = 400)
    
    def get_courses(request):
        # Function requires course grabbing course ID using dynamic URL parameter
        # Add course ID at the end of URL request
        if request.method == 'GET':
            # retrieve the course by its ID
            course = get_object_or_404(Course, id=course_id)
            # return course details as JSON
            course_data = {
                'id' : course.id,
                'title' : course.title,
                'course_number' : course.course_number,
                'professor' : course.professor,
                'start_date' : course.start_date,
                'meeting_dates' : course.meeting_dates,
                'meeting_times' : course.meeting_times,
                'end_date' : course.end_date,
                'class_type' : course.class_type,
                'location' : course.location,
            }
            return JsonResponse(course_data)
        else:
            return JsonResponse({'error': 'Invalid request method. Use GET'}, status = 400)