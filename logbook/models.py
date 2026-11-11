from django.core.exceptions import ValidationError
from django.conf import settings
from django.db import models
from django.utils import timezone

class StudentProfile(models.Model):
    user=models.OneToOneField(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="attachment_profile",null=True,blank=True)
    student_name=models.CharField("full name",max_length=160,blank=True)
    student_number=models.CharField("student number",max_length=40,blank=True)
    programme=models.CharField(max_length=160,default="BSc Computer Science",blank=True)
    organisation=models.CharField("host organisation",max_length=180,blank=True)
    department=models.CharField("department / unit",max_length=160,blank=True)
    workplace_supervisor=models.CharField(max_length=160,blank=True)
    academic_supervisor=models.CharField(max_length=160,blank=True)
    start_date=models.DateField(null=True,blank=True)
    end_date=models.DateField(null=True,blank=True)
    report_title=models.CharField(max_length=200,default="Industrial Attachment Report")
    objectives=models.TextField(blank=True)
    organisation_background=models.TextField(blank=True)
    conclusion=models.TextField(blank=True)
    recommendations=models.TextField(blank=True)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name="student and placement profile"
    def __str__(self):
        return self.student_name or "Student profile"
    @classmethod
    def for_user(cls,user):
        return cls.objects.get_or_create(user=user)[0]
    def clean(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValidationError({"end_date":"End date must be on or after the start date."})

class LogEntry(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE,related_name="attachment_entries",null=True,blank=True)
    entry_date=models.DateField(default=timezone.localdate)
    department=models.CharField(max_length=160,blank=True)
    activities=models.TextField()
    skills=models.TextField(blank=True,verbose_name="skills or knowledge gained")
    challenges=models.TextField(blank=True)
    reflection=models.TextField(blank=True,verbose_name="reflection / supervisor comments")
    created_at=models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering=["-entry_date","-pk"]
        verbose_name="log book entry"
    def __str__(self):
        return f"{self.entry_date}: {self.department or 'Work activities'}"
