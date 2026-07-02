from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


class User(AbstractUser):
    """Custom User model with role-based boolean fields."""
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    def __str__(self):
        return self.username


class Department(models.Model):
    """Academic department model."""
    name = models.CharField(max_length=200)
    head = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Subject(models.Model):
    """Subject/Course model linked to a department."""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name='subjects'
    )
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.code} — {self.name}"


class ClassRoom(models.Model):
    """Classroom model representing a class section."""
    name = models.CharField(max_length=100)
    section = models.CharField(max_length=10, blank=True)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='classrooms'
    )

    def __str__(self):
        section_str = f" ({self.section})" if self.section else ""
        return f"{self.name}{section_str}"


class Parent(models.Model):
    """Parent/Guardian information model."""
    father_name = models.CharField(max_length=200)
    mother_name = models.CharField(max_length=200, blank=True)
    father_occupation = models.CharField(max_length=200, blank=True)
    mother_occupation = models.CharField(max_length=200, blank=True)
    mobile_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    present_address = models.TextField()
    permanent_address = models.TextField(blank=True)

    def __str__(self):
        return self.father_name


GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
    ('Other', 'Other'),
]


class Student(models.Model):
    """Student model with One-to-One relationship to Parent and User."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='student_profile', null=True, blank=True
    )
    parent = models.OneToOneField(
        Parent, on_delete=models.CASCADE, related_name='student'
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    student_id = models.CharField(max_length=20, unique=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    classroom = models.ForeignKey(
        ClassRoom, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='students'
    )
    religion = models.CharField(max_length=50, blank=True)
    joining_date = models.DateField()
    mobile_number = models.CharField(max_length=20, blank=True)
    admission_number = models.CharField(max_length=20, unique=True)
    section = models.CharField(max_length=10, blank=True)
    profile_image = models.ImageField(
        upload_to='students/profiles/', blank=True, null=True
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.student_id})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Teacher(models.Model):
    """Teacher model linked to User."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='teacher_profile', null=True, blank=True
    )
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=20, blank=True)
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='teachers'
    )
    subjects = models.ManyToManyField(Subject, blank=True, related_name='teachers')
    profile_image = models.ImageField(
        upload_to='teachers/profiles/', blank=True, null=True
    )
    joining_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class Notification(models.Model):
    """Notification model for system-wide alerts."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notifications'
    )
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{'[Read]' if self.is_read else '[Unread]'} {self.message[:50]}"


FEE_STATUS_CHOICES = [
    ('Paid', 'Paid'),
    ('Unpaid', 'Unpaid'),
    ('Partial', 'Partial'),
]


class Fee(models.Model):
    """Fee/Payment tracking model."""
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='fees'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    fee_type = models.CharField(max_length=100)
    date = models.DateField()
    status = models.CharField(
        max_length=10, choices=FEE_STATUS_CHOICES, default='Unpaid'
    )

    def __str__(self):
        return f"{self.student} — {self.fee_type} — {self.amount}"


class Expense(models.Model):
    """Institutional expense tracking model."""
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.title} — {self.amount}"


SALARY_STATUS_CHOICES = [
    ('Paid', 'Paid'),
    ('Pending', 'Pending'),
]


class Salary(models.Model):
    """Teacher salary tracking model."""
    teacher = models.ForeignKey(
        Teacher, on_delete=models.CASCADE, related_name='salaries'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.CharField(max_length=20)
    year = models.IntegerField()
    status = models.CharField(
        max_length=10, choices=SALARY_STATUS_CHOICES, default='Pending'
    )

    class Meta:
        verbose_name_plural = 'Salaries'

    def __str__(self):
        return f"{self.teacher} — {self.month}/{self.year} — {self.amount}"


class PasswordResetToken(models.Model):
    """Secure token for password reset flow."""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='password_reset_tokens'
    )
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Reset token for {self.user.username}"
