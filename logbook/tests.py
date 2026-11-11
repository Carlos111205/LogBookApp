from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from docx import Document

from .models import LogEntry, StudentProfile


class AccountIsolationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.alice = User.objects.create_user(username="alice", password="Strong-test-pass-93")
        self.bob = User.objects.create_user(username="bob", password="Strong-test-pass-94")
        StudentProfile.objects.create(user=self.alice, student_name="Alice Student", student_number="A100", organisation="Alpha Host")
        StudentProfile.objects.create(user=self.bob, student_name="Bob Student", student_number="B200", organisation="Beta Host")
        self.alice_entry = LogEntry.objects.create(user=self.alice, department="Alpha Team", activities="ALPHA PRIVATE TASK")
        self.bob_entry = LogEntry.objects.create(user=self.bob, department="Beta Team", activities="BETA PRIVATE TASK")
        self.alice_client = self.client_class()
        self.bob_client = self.client_class()
        self.alice_client.force_login(self.alice)
        self.bob_client.force_login(self.bob)

    def test_private_pages_require_sign_in(self):
        anonymous = self.client_class()
        for path in ("/", "/profile/", "/logbook/", "/report/", "/download/report/pdf/"):
            with self.subTest(path=path):
                response = anonymous.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/accounts/login/", response["Location"])

    def test_signup_creates_a_separate_account_and_profile(self):
        client = self.client_class()
        response = client.post("/accounts/signup/", {
            "username": "newstudent",
            "email": "newstudent@example.test",
            "password1": "A-new-student-pass-846!",
            "password2": "A-new-student-pass-846!",
        })
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username="newstudent")
        self.assertTrue(StudentProfile.objects.filter(user=user).exists())
        self.assertContains(client.get("/"), "Start with your placement details")

    def test_legacy_records_can_be_assigned_only_to_the_chosen_account(self):
        legacy = StudentProfile.objects.create(student_name="Legacy Owner", student_number="L300")
        entry = LogEntry.objects.create(activities="LEGACY PRIVATE TASK")
        owner = get_user_model().objects.create_user(username="carol", password="Strong-test-pass-95")
        empty_profile = StudentProfile.objects.create(user=owner)
        call_command("assign_legacy_data", "carol", verbosity=0)
        empty_profile.refresh_from_db()
        self.assertEqual(empty_profile.student_name, "Legacy Owner")
        self.assertFalse(StudentProfile.objects.filter(pk=legacy.pk).exists())
        entry.refresh_from_db()
        self.assertEqual(entry.user, owner)
        self.assertFalse(StudentProfile.objects.filter(user=self.bob, student_name="Legacy Owner").exists())

    def test_legacy_transfer_refuses_to_overwrite_existing_profile(self):
        StudentProfile.objects.create(student_name="Unclaimed Legacy")
        LogEntry.objects.create(activities="UNCLAIMED ENTRY")
        with self.assertRaises(CommandError):
            call_command("assign_legacy_data", "alice", verbosity=0)
        self.assertTrue(StudentProfile.objects.filter(user__isnull=True, student_name="Unclaimed Legacy").exists())

    def test_dashboard_and_logbook_show_only_signed_in_users_data(self):
        for client, own_name, own_entry, other_name, other_entry in (
            (self.alice_client, "Alice Student", "ALPHA PRIVATE TASK", "Bob Student", "BETA PRIVATE TASK"),
            (self.bob_client, "Bob Student", "BETA PRIVATE TASK", "Alice Student", "ALPHA PRIVATE TASK"),
        ):
            dashboard = client.get("/")
            profile = client.get("/profile/")
            logbook = client.get("/logbook/")
            self.assertContains(dashboard, own_entry)
            self.assertNotContains(dashboard, other_name)
            self.assertNotContains(dashboard, other_entry)
            self.assertContains(profile, own_name)
            self.assertNotContains(profile, other_name)
            self.assertContains(logbook, own_entry)
            self.assertNotContains(logbook, other_entry)

    def test_user_cannot_delete_another_users_entry(self):
        response = self.bob_client.post(f"/logbook/{self.alice_entry.pk}/delete/")
        self.assertEqual(response.status_code, 404)
        self.assertTrue(LogEntry.objects.filter(pk=self.alice_entry.pk).exists())

    def test_word_exports_contain_only_the_signed_in_users_information(self):
        for kind in ("logbook", "report"):
            response = self.alice_client.get(f"/download/{kind}/docx/")
            self.assertEqual(response.status_code, 200)
            doc = Document(BytesIO(response.content))
            pieces = [paragraph.text for paragraph in doc.paragraphs]
            pieces += [cell.text for table in doc.tables for row in table.rows for cell in row.cells]
            content = "\n".join(pieces)
            self.assertIn("ALPHA PRIVATE TASK", content)
            self.assertNotIn("BETA PRIVATE TASK", content)
            self.assertNotIn("Bob Student", content)

    def test_pdf_exports_are_user_scoped(self):
        for kind in ("logbook", "report"):
            alice_pdf = self.alice_client.get(f"/download/{kind}/pdf/")
            bob_pdf = self.bob_client.get(f"/download/{kind}/pdf/")
            self.assertEqual(alice_pdf.status_code, 200)
            self.assertEqual(bob_pdf.status_code, 200)
            self.assertTrue(alice_pdf.content.startswith(b"%PDF-"))
            self.assertTrue(bob_pdf.content.startswith(b"%PDF-"))
            self.assertNotEqual(alice_pdf.content, bob_pdf.content)
