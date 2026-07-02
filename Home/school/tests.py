from django.test import TestCase, Client
from django.urls import reverse
from .models import User

class RBACTests(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create roles
        self.admin_user = User.objects.create_user(
            username='admin_test', password='password123', is_admin=True
        )
        self.teacher_user = User.objects.create_user(
            username='teacher_test', password='password123', is_teacher=True
        )
        self.student_user = User.objects.create_user(
            username='student_test', password='password123', is_student=True
        )
        
        # URLs
        self.admin_url = reverse('admin_dashboard')
        self.teacher_url = reverse('teacher_dashboard')
        self.student_url = reverse('student_dashboard')

    def test_admin_access(self):
        """Admin should access admin dashboard, but others should be denied."""
        # Admin
        self.client.login(username='admin_test', password='password123')
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        # Teacher trying to access Admin
        self.client.login(username='teacher_test', password='password123')
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, 302)  # Should redirect or 403
        self.client.logout()

        # Student trying to access Admin
        self.client.login(username='student_test', password='password123')
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, 302)

    def test_teacher_access(self):
        """Teacher should access teacher dashboard, but student shouldn't."""
        # Teacher
        self.client.login(username='teacher_test', password='password123')
        response = self.client.get(self.teacher_url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        # Student trying to access Teacher
        self.client.login(username='student_test', password='password123')
        response = self.client.get(self.teacher_url)
        self.assertEqual(response.status_code, 302)

    def test_student_access(self):
        """Student should access student dashboard, but teacher shouldn't."""
        # Student
        self.client.login(username='student_test', password='password123')
        response = self.client.get(self.student_url)
        self.assertEqual(response.status_code, 200)
        self.client.logout()

        # Teacher trying to access Student
        self.client.login(username='teacher_test', password='password123')
        response = self.client.get(self.student_url)
        self.assertEqual(response.status_code, 302)

    def test_unauthenticated_access(self):
        """Unauthenticated users should be redirected to login."""
        response = self.client.get(self.admin_url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse('login')))
