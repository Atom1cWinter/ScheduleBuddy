from django import forms
from .models import Profile
from .models import SchedulingSurvey

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['full_name', 'date_of_birth', 'email', 'phone_number', 'profile_picture']
        
class SchedulingSurveyForm(forms.ModelForm):
    class Meta:
        model = SchedulingSurvey
        fields = '__all__'
        widgets = {
            'preferred_times': forms.CheckboxSelectMultiple(choices=[
                ('8-10', '8 AM - 10 AM'), ('10-12', '10 AM - 12 PM'),
                ('12-2', '12 PM - 2 PM'), ('2-4', '2 PM - 4 PM'),
                ('4+', '4 PM or later'),
            ]),
            'preferred_days': forms.CheckboxSelectMultiple(choices=[
                ('M', 'Monday'), ('T', 'Tuesday'), ('W', 'Wednesday'),
                ('Th', 'Thursday'), ('F', 'Friday'),
            ]),
            'days_off': forms.CheckboxSelectMultiple(choices=[
                ('M', 'Monday'), ('T', 'Tuesday'), ('W', 'Wednesday'),
                ('Th', 'Thursday'), ('F', 'Friday'),
            ]),
            'class_spacing': forms.RadioSelect(choices=[
                ('back_to_back', 'Back-to-back'), 
                ('gaps', 'Gaps between classes'),
                ('no_pref', 'No preference')
            ]),
            'learning_style': forms.RadioSelect(choices=[
                ('lecture', 'Lecture-based'), 
                ('hands_on', 'Hands-on / Lab'),
                ('discussion', 'Discussion-based'), 
                ('project', 'Project-based')
            ]),
            'format_preference': forms.RadioSelect(choices=[
                ('in_person', 'In-person'), 
                ('online_live', 'Online (live)'), 
                ('online_async', 'Online (asynchronous)'), 
                ('hybrid', 'Hybrid')
            ]),
            'preferred_distribution': forms.RadioSelect(choices=[
                ('morning', 'Morning-heavy'), 
                ('afternoon', 'Afternoon-heavy'),
                ('even', 'Evenly distributed')
            ]),
            'clustered_or_spread': forms.RadioSelect(choices=[
                ('clustered', 'Clustered on fewer days'),
                ('spread', 'Spread throughout the week')
            ]),
        }