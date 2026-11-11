import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="StudentProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("student_name", models.CharField(blank=True, max_length=160, verbose_name="full name")),
                ("student_number", models.CharField(blank=True, max_length=40, verbose_name="student number")),
                ("programme", models.CharField(blank=True, default="BSc Computer Science", max_length=160)),
                ("organisation", models.CharField(blank=True, max_length=180, verbose_name="host organisation")),
                ("department", models.CharField(blank=True, max_length=160, verbose_name="department / unit")),
                ("workplace_supervisor", models.CharField(blank=True, max_length=160)),
                ("academic_supervisor", models.CharField(blank=True, max_length=160)),
                ("start_date", models.DateField(blank=True, null=True)),
                ("end_date", models.DateField(blank=True, null=True)),
                ("report_title", models.CharField(default="Industrial Attachment Report", max_length=200)),
                ("objectives", models.TextField(blank=True)),
                ("organisation_background", models.TextField(blank=True)),
                ("conclusion", models.TextField(blank=True)),
                ("recommendations", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "student and placement profile"},
        ),
        migrations.CreateModel(
            name="LogEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("entry_date", models.DateField(default=django.utils.timezone.localdate)),
                ("department", models.CharField(blank=True, max_length=160)),
                ("activities", models.TextField()),
                ("skills", models.TextField(blank=True, verbose_name="skills or knowledge gained")),
                ("challenges", models.TextField(blank=True)),
                ("reflection", models.TextField(blank=True, verbose_name="reflection / supervisor comments")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"ordering": ["-entry_date", "-pk"], "verbose_name": "log book entry"},
        ),
    ]
