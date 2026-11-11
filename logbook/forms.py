from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import LogEntry, StudentProfile

User=get_user_model()

class SignUpForm(UserCreationForm):
    email=forms.EmailField(required=True)
    class Meta(UserCreationForm.Meta):
        model=User
        fields=("username","email")
    def clean_email(self):
        email=self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email address already exists.")
        return email
    def save(self,commit=True):
        user=super().save(commit=False)
        user.email=self.cleaned_data["email"].strip()
        if commit: user.save()
        return user
class DateInput(forms.DateInput):
    input_type="date"
class StudentProfileForm(forms.ModelForm):
    class Meta:
        model=StudentProfile
        fields=["student_name","student_number","programme","organisation","department","workplace_supervisor","academic_supervisor","start_date","end_date"]
        widgets={"start_date":DateInput(),"end_date":DateInput()}
    def clean(self):
        cleaned=super().clean()
        start,end=cleaned.get("start_date"),cleaned.get("end_date")
        if start and end and end < start:
            self.add_error("end_date","End date must be on or after the start date.")
        return cleaned
class LogEntryForm(forms.ModelForm):
    class Meta:
        model=LogEntry
        fields=["entry_date","department","activities","skills","challenges","reflection"]
        widgets={"entry_date":DateInput(),"activities":forms.Textarea(attrs={"rows":4}),"skills":forms.Textarea(attrs={"rows":3}),"challenges":forms.Textarea(attrs={"rows":3}),"reflection":forms.Textarea(attrs={"rows":2})}
class ReportForm(forms.ModelForm):
    class Meta:
        model=StudentProfile
        fields=["report_title","objectives","organisation_background","conclusion","recommendations"]
        widgets={f:forms.Textarea(attrs={"rows":n}) for f,n in (("objectives",5),("organisation_background",5),("conclusion",4),("recommendations",4))}
