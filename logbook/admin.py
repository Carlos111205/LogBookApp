from django.contrib import admin
from .models import LogEntry, StudentProfile
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display=("student_name","student_number","organisation","start_date","end_date")
@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display=("entry_date","department","created_at")
    list_filter=("entry_date","department")
    search_fields=("activities","skills","department")
