from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import (
    User, Student, Parent, Teacher, Department, Subject,
    ClassRoom, Fee, Expense, Salary,
)


# ──────────────────────────────────────────────
#  Authentication Forms
# ──────────────────────────────────────────────

class SignUpForm(UserCreationForm):
    """Registration form with role selection."""
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'role':
                field.widget.attrs.update({'class': 'form-input'})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        role = self.cleaned_data['role']
        if role == 'student':
            user.is_student = True
        elif role == 'teacher':
            user.is_teacher = True
        elif role == 'admin':
            user.is_admin = True
        if commit:
            user.save()
        return user


class LoginForm(forms.Form):
    """Simple login form."""
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Password'})
    )


class PasswordResetRequestForm(forms.Form):
    """Form to request a password reset link."""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Enter your email'})
    )


class PasswordResetConfirmForm(forms.Form):
    """Form to set a new password via reset token."""
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'New Password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirm Password'})
    )

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get('new_password')
        cpw = cleaned_data.get('confirm_password')
        if pw and cpw and pw != cpw:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data


# ──────────────────────────────────────────────
#  Student & Parent Forms
# ──────────────────────────────────────────────

class StudentForm(forms.ModelForm):
    """Form for creating/editing a Student."""

    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'student_id', 'gender',
            'date_of_birth', 'classroom', 'religion', 'joining_date',
            'mobile_number', 'admission_number', 'section', 'profile_image',
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'joining_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-input'})


class ParentForm(forms.ModelForm):
    """Form for creating/editing Parent information."""

    class Meta:
        model = Parent
        fields = [
            'father_name', 'mother_name', 'father_occupation',
            'mother_occupation', 'mobile_number', 'email',
            'present_address', 'permanent_address',
        ]
        widgets = {
            'present_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
            'permanent_address': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-input'})


# ──────────────────────────────────────────────
#  Teacher Form
# ──────────────────────────────────────────────

class TeacherForm(forms.ModelForm):
    """Form for creating/editing a Teacher."""

    class Meta:
        model = Teacher
        fields = [
            'first_name', 'last_name', 'mobile_number', 'department',
            'subjects', 'profile_image', 'joining_date',
        ]
        widgets = {
            'joining_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'subjects': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'subjects' and 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-input'})


# ──────────────────────────────────────────────
#  Department & Subject Forms
# ──────────────────────────────────────────────

class DepartmentForm(forms.ModelForm):
    """Form for creating/editing a Department."""

    class Meta:
        model = Department
        fields = ['name', 'head', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-input'})


class SubjectForm(forms.ModelForm):
    """Form for creating/editing a Subject."""

    class Meta:
        model = Subject
        fields = ['name', 'code', 'department', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-input'})


# ──────────────────────────────────────────────
#  Accounts Forms (Fee, Expense, Salary)
# ──────────────────────────────────────────────

class FeeForm(forms.ModelForm):
    """Form for creating/editing Fee records."""

    class Meta:
        model = Fee
        fields = ['student', 'amount', 'fee_type', 'date', 'status']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-input'})


class ExpenseForm(forms.ModelForm):
    """Form for creating/editing Expense records."""

    class Meta:
        model = Expense
        fields = ['title', 'amount', 'date', 'description']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-input'})


class SalaryForm(forms.ModelForm):
    """Form for creating/editing Salary records."""

    class Meta:
        model = Salary
        fields = ['teacher', 'amount', 'month', 'year', 'status']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if 'class' not in field.widget.attrs:
                field.widget.attrs.update({'class': 'form-input'})
