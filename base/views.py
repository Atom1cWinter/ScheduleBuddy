from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
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