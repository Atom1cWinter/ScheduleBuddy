from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Q
from django.contrib.auth.forms import UserCreationForm

from .models import Profile, Course, Section, Schedule, SchedulingSurvey
from .forms import ProfileForm, SchedulingSurveyForm, CourseForm
from .utils import sort_sections_by_survey  # Ensure this utility function exists
import random
import datetime
from datetime import time

# -------------------------------------------------
# Utility Functions
# -------------------------------------------------

def filter_sections_by_survey(survey, sections):
    """Filter sections based on survey preferences."""
    # Exclude night classes if the user prefers not to take them
    if not survey.night_classes_ok:
        sections = sections.filter(begins__lt="18:00:00")

    # Filter by preferred time distribution
    if survey.time_distribution == "morning":
        sections = sections.filter(begins__lt="12:00:00")
    elif survey.time_distribution == "afternoon":
        sections = sections.filter(begins__gte="12:00:00", begins__lt="16:00:00")
    elif survey.time_distribution == "evening":
        sections = sections.filter(begins__gte="16:00:00")

    # Filter by preferred meeting days
    preferred_days = {
        'MWF': ['mo', 'we', 'fr'],
        'TTH': ['tu', 'th'],
        'Spread': ['mo', 'tu', 'we', 'th', 'fr']
    }.get(survey.preferred_distribution, [])

    if preferred_days:
        day_filters = Q()
        if 'mo' in preferred_days:
            day_filters |= Q(mo=True)
        if 'tu' in preferred_days:
            day_filters |= Q(tu=True)
        if 'we' in preferred_days:
            day_filters |= Q(we=True)
        if 'th' in preferred_days:
            day_filters |= Q(th=True)
        if 'fr' in preferred_days:
            day_filters |= Q(fr=True)
        sections = sections.filter(day_filters)

    return sections.order_by('begins')


def calculate_score(survey, section):
    score = 0

    # Time preference scoring
    if survey.time_distribution == "morning" and section.begins and section.begins < time(12, 0):
        score += 3
    elif survey.time_distribution == "afternoon" and section.begins and time(12, 0) <= section.begins < time(16, 0):
        score += 2
    elif survey.time_distribution == "evening" and section.begins and section.begins >= time(16, 0):
        score += 1

    # Night class preference
    if not survey.night_classes_ok and section.begins and section.begins >= time(18, 0):
        score -= 5

    # Day preference scoring
    preferred_days = {
        'MWF': ['mo', 'we', 'fr'],
        'TTH': ['tu', 'th'],
        'Spread': ['mo', 'tu', 'we', 'th', 'fr']
    }.get(survey.preferred_distribution, [])

    if section.mo and 'mo' in preferred_days:
        score += 1
    if section.tu and 'tu' in preferred_days:
        score += 1
    if section.we and 'we' in preferred_days:
        score += 1
    if section.th and 'th' in preferred_days:
        score += 1
    if section.fr and 'fr' in preferred_days:
        score += 1

    return score


def sort_sections_by_survey(survey, sections):
    """Sort sections based on how well they match the user's survey preferences."""
    # Annotate sections with scores and sort them
    sections_with_scores = [(section, calculate_score(survey, section)) for section in sections]
    sorted_sections = sorted(sections_with_scores, key=lambda x: x[1], reverse=True)

    return [section for section, score in sorted_sections]


# Temporarily removed export_schedule_to_google_calendar function

# -------------------------------------------------
# Views: Home and Authentication
# -------------------------------------------------

def home(request):
    return render(request, 'base/home.html')


def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your account has been created! You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'base/register.html', {'form': form})


@login_required
def profile_view(request):
    schedules = Schedule.objects.filter(user=request.user)
    last_schedule = schedules.last()

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = ProfileForm(instance=request.user.profile)

    return render(request, 'base/profile.html', {
        'schedules': schedules,
        'last_schedule': last_schedule,
        'form': form,
    })

# -------------------------------------------------
# Views: Survey and Recommendations
# -------------------------------------------------

def survey_view(request):
    if request.method == 'POST':
        form = SchedulingSurveyForm(request.POST)
        if form.is_valid():
            survey = form.save(commit=False)
            survey.user = request.user
            survey.save()

            profile = request.user.profile
            profile.survey = survey
            profile.save()

            return redirect('survey_thankyou')
    else:
        profile = request.user.profile
        form = SchedulingSurveyForm(instance=profile.survey if profile.survey else None)

    return render(request, 'base/survey.html', {'form': form})


@login_required
def recommend_sections(request):
    survey = request.user.profile.survey
    if not survey:
        return render(request, 'base/recommended_section.html', {'error': 'No survey found. Please complete the survey first.'})

    course_code = request.GET.get('course_code', '').strip()
    if not course_code:
        return render(request, 'base/recommended_section.html', {'error': 'No course code provided.'})

    sections = Section.objects.filter(course_code__iexact=course_code)
    if not sections.exists():
        return render(request, 'base/recommended_section.html', {'error': f'No sections found for course code: {course_code}'})

    sorted_sections = sort_sections_by_survey(survey, sections)

    return render(request, 'base/recommended_section.html', {
        'course_code': course_code,
        'sections': sorted_sections,
    })


@login_required
def recommend_section(request, course_id):
    """Recommend a specific section for a given course."""
    survey = request.user.profile.survey
    if not survey:
        return render(request, 'base/recommended_section.html', {'error': 'No survey found. Please complete the survey first.'})

    # Get the course and its sections
    course = get_object_or_404(Course, id=course_id)
    sections = Section.objects.filter(course=course)

    if not sections.exists():
        return render(request, 'base/recommended_section.html', {'error': f'No sections found for course: {course.name}'})

    # Sort sections based on survey preferences
    sorted_sections = sort_sections_by_survey(survey, sections)

    return render(request, 'base/recommended_section.html', {
        'course': course,
        'sections': sorted_sections,
    })


def thank_you(request):
    """Render a thank-you page after completing the survey."""
    return render(request, 'base/thank_you.html')

# -------------------------------------------------
# Views: Schedule Management
# -------------------------------------------------

@login_required
def create_schedule(request):
    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_course':
            section_id = request.POST.get('section_id')
            if 'selected_courses' not in request.session:
                request.session['selected_courses'] = []
            if section_id not in request.session['selected_courses']:
                request.session['selected_courses'].append(section_id)
                request.session.modified = True
            return redirect('create_schedule')

        elif action == 'create_schedule':
            schedule_name = request.POST.get('schedule_name', 'My Schedule')
            section_ids = request.session.get('selected_courses', [])

            schedule = Schedule.objects.create(user=request.user, name=schedule_name)
            sections = Section.objects.filter(id__in=section_ids)
            schedule.sections.set(sections)

            request.session['selected_courses'] = []
            return redirect('view_schedule', schedule_id=schedule.id)

    else:
        query = request.GET.get('query', '').strip()
        sections = Section.objects.all()

        if query:
            query_no_space = query.replace(' ', '')
            sections = sections.filter(
                Q(subject__icontains=query) |
                Q(course_number__icontains=query) |
                Q(course_code__icontains=query_no_space)
            )

        selected_courses = Section.objects.filter(id__in=request.session.get('selected_courses', []))

        return render(request, 'base/create_schedule.html', {
            'sections': sections,
            'selected_courses': selected_courses,
            'query': query,
        })


@login_required
def export_schedule(request, schedule_id):
    """Inform the user that exporting schedules is not currently available."""
    return JsonResponse({'message': 'Exporting schedules to Google Calendar is currently not available.'}, status=503)


@login_required
def view_schedule(request, schedule_id):
    schedule = get_object_or_404(Schedule, id=schedule_id, user=request.user)
    return render(request, 'base/view_schedule.html', {'schedule': schedule})


@login_required
def add_to_schedule(request):
    """Add a section to the user's schedule."""
    if request.method == 'POST':
        section_id = request.POST.get('section_id')
        schedule_id = request.POST.get('schedule_id')

        if not section_id or not schedule_id:
            return JsonResponse({'error': 'Section ID and Schedule ID are required.'}, status=400)

        try:
            schedule = Schedule.objects.get(id=schedule_id, user=request.user)
            section = Section.objects.get(id=section_id)
            schedule.sections.add(section)
            return JsonResponse({'message': 'Section added to schedule successfully!'})
        except Schedule.DoesNotExist:
            return JsonResponse({'error': 'Schedule not found.'}, status=404)
        except Section.DoesNotExist:
            return JsonResponse({'error': 'Section not found.'}, status=404)

    return JsonResponse({'error': 'Invalid request method.'}, status=405)

# -------------------------------------------------
# Views: Miscellaneous
# -------------------------------------------------

@login_required
def courseLoad(request):
    user = request.user
    try:
        survey = SchedulingSurvey.objects.get(user=user)
    except SchedulingSurvey.DoesNotExist:
        return render(request, 'base/no_survey.html')

    sections = Section.objects.all()

    # Apply format preference filter
    if survey.format_preference:
        sections = sections.filter(mode=survey.format_preference)

    # Apply preferred days filter
    preferred_days = survey.preferred_days or []
    day_fields = {'M': 'mo', 'T': 'tu', 'W': 'we', 'Th': 'th', 'F': 'fr'}
    day_filters = {f"{day_fields[d]}__isnull": False for d in preferred_days if d in day_fields}
    for day, value in day_filters.items():
        sections = sections.filter(**{day: True})  # Filter to include only sections that meet the preferred days

    # Apply preferred times filter
    preferred_times = survey.preferred_times or []
    time_ranges = {
        '8-10': (8, 10), '10-12': (10, 12),
        '12-2': (12, 14), '2-4': (14, 16), '4+': (16, 24)
    }

    filtered_sections = []
    for section in sections:
        try:
            hour = int(section.begins.strftime('%H'))  # Extract hour correctly from TimeField
            for pref in preferred_times:
                low, high = time_ranges.get(pref, (0, 24))
                if low <= hour < high:
                    filtered_sections.append(section)
                    break
        except Exception as e:
            print(f"Error processing section {section}: {e}")
            continue

    # Remove duplicates and limit to 5 courses
    seen_courses = set()
    final_schedule = []
    for section in filtered_sections:
        if section.course.id not in seen_courses:
            final_schedule.append(section)
            seen_courses.add(section.course.id)
        if len(final_schedule) == 5:
            break

    return render(request, 'base/course_load.html', {
        'survey': survey,
        'schedule': final_schedule,
    })


def filter_courses(request):
    """Filter courses based on a query parameter."""
    query = request.GET.get('query', '').strip()
    if query:
        courses = Course.objects.filter(name__icontains=query)
    else:
        courses = Course.objects.all()

    return render(request, 'base/course_list.html', {'courses': courses})


@login_required
def add_course(request):
    """Add a new course to the system."""
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course added successfully!')
            return redirect('course_list')  # Redirect to the course list page
    else:
        form = CourseForm()

    return render(request, 'base/add_course.html', {'form': form})


def get_courses(request, ids):
    """Retrieve courses based on a list of IDs."""
    course_ids = ids.split(',')
    courses = Course.objects.filter(id__in=course_ids).values('id', 'code', 'name', 'credits', 'description')
    return JsonResponse(list(courses), safe=False)


@login_required
def course_list(request):
    """Display a list of all courses."""
    courses = Course.objects.all()
    return render(request, 'base/course_list.html', {'courses': courses})


@login_required
def calendarSync(request):
    """Inform the user that calendar sync is not currently available."""
    return render(request, 'base/calendar_sync_unavailable.html', {
        'message': 'Calendar sync is still in development. Please try again later.'
    })


