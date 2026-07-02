import secrets
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from django.utils import timezone

import json
from .models import (
    User, Student, Parent, Teacher, Department, Subject,
    ClassRoom, Notification, Fee, Expense, Salary, PasswordResetToken,
)
from .forms import (
    SignUpForm, LoginForm, PasswordResetRequestForm, PasswordResetConfirmForm,
    StudentForm, ParentForm, TeacherForm, DepartmentForm, SubjectForm,
    FeeForm, ExpenseForm, SalaryForm,
)


# ════════════════════════════════════════════════════════
#  Helper: Role-based access decorators
# ════════════════════════════════════════════════════════

def admin_required(view_func):
    """Decorator: only allow users with is_admin=True or is_superuser."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not (request.user.is_admin or request.user.is_superuser):
            messages.error(request, "You do not have permission to access this page.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def teacher_required(view_func):
    """Decorator: only allow users with is_teacher=True."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_teacher:
            messages.error(request, "You do not have permission to access this page.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def student_required(view_func):
    """Decorator: only allow users with is_student=True."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_student:
            messages.error(request, "You do not have permission to access this page.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


def create_notification(user, message):
    """Helper to create a notification for a specific user."""
    Notification.objects.create(user=user, message=message)


def notify_admins(message):
    """Create a notification for all admin users."""
    admins = User.objects.filter(is_admin=True)
    for admin_user in admins:
        create_notification(admin_user, message)


# ════════════════════════════════════════════════════════
#  Index / Landing
# ════════════════════════════════════════════════════════

def index(request):
    """Landing page — redirect authenticated users to their dashboard."""
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)
    return redirect('login')


def redirect_to_dashboard(user):
    """Redirect user to their role-specific dashboard."""
    if user.is_admin or user.is_superuser:
        return redirect('admin_dashboard')
    elif user.is_teacher:
        return redirect('teacher_dashboard')
    elif user.is_student:
        return redirect('student_dashboard')
    return redirect('login')


# ════════════════════════════════════════════════════════
#  Authentication Views
# ════════════════════════════════════════════════════════

def signup_view(request):
    """User registration with role selection."""
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Account created successfully! Please login.")
            return redirect('login')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = SignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


def login_view(request):
    """Login with role-based redirection."""
    if request.user.is_authenticated:
        return redirect_to_dashboard(request.user)

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
                return redirect_to_dashboard(user)
            else:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form})


def logout_view(request):
    """Log out and redirect to login."""
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')


def password_reset_request(request):
    """Generate a secure reset token and send via email."""
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                token = secrets.token_urlsafe(32)
                PasswordResetToken.objects.create(user=user, token=token)
                reset_link = request.build_absolute_uri(f'/password-reset-confirm/{token}/')
                send_mail(
                    subject='Password Reset Request',
                    message=f'Click the link to reset your password: {reset_link}',
                    from_email='noreply@schoolms.com',
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.success(request, "A password reset link has been sent to your email.")
            except User.DoesNotExist:
                messages.success(
                    request,
                    "If an account with that email exists, a reset link has been sent."
                )
            return redirect('login')
    else:
        form = PasswordResetRequestForm()
    return render(request, 'registration/password_reset.html', {'form': form})


def password_reset_confirm(request, token):
    """Validate token and allow user to set a new password."""
    reset_token = get_object_or_404(PasswordResetToken, token=token, is_used=False)

    # Token expires after 1 hour
    if (timezone.now() - reset_token.created_at).total_seconds() > 3600:
        messages.error(request, "This reset link has expired.")
        return redirect('password_reset')

    if request.method == 'POST':
        form = PasswordResetConfirmForm(request.POST)
        if form.is_valid():
            reset_token.user.set_password(form.cleaned_data['new_password'])
            reset_token.user.save()
            reset_token.is_used = True
            reset_token.save()
            messages.success(request, "Password has been reset successfully! Please login.")
            return redirect('login')
    else:
        form = PasswordResetConfirmForm()
    return render(request, 'registration/password_reset_confirm.html', {'form': form})


# ════════════════════════════════════════════════════════
#  Dashboard Views
# ════════════════════════════════════════════════════════

@login_required
@admin_required
def admin_dashboard(request):
    """Admin dashboard with stats, charts, and recent activity."""
    from datetime import timedelta
    from django.db.models.functions import TruncMonth

    now = timezone.now()

    # ── Core counts ──
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_departments = Department.objects.count()
    total_subjects = Subject.objects.count()
    total_classrooms = ClassRoom.objects.count()

    # ── Financial analytics ──
    total_revenue = Fee.objects.filter(status='Paid').aggregate(
        total=Sum('amount')
    )['total'] or 0
    total_pending_fees = Fee.objects.filter(status='Unpaid').aggregate(
        total=Sum('amount')
    )['total'] or 0
    pending_fee_count = Fee.objects.filter(status='Unpaid').count()
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_salaries_paid = Salary.objects.filter(status='Paid').aggregate(
        total=Sum('amount')
    )['total'] or 0
    total_salaries_pending = Salary.objects.filter(status='Pending').aggregate(
        total=Sum('amount')
    )['total'] or 0
    net_income = total_revenue - total_expenses - total_salaries_paid

    # ── Teacher-student ratio ──
    ts_ratio = round(total_students / total_teachers, 1) if total_teachers > 0 else 0

    # ── Monthly revenue trend (last 6 months) ──
    six_months_ago = now - timedelta(days=180)
    monthly_revenue = (
        Fee.objects
        .filter(status='Paid', date__gte=six_months_ago)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    revenue_trend_labels = [item['month'].strftime('%b %Y') for item in monthly_revenue]
    revenue_trend_data = [float(item['total']) for item in monthly_revenue]

    # ── Monthly expense trend (last 6 months) ──
    monthly_expenses = (
        Expense.objects
        .filter(date__gte=six_months_ago)
        .annotate(month=TruncMonth('date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    expense_trend_labels = [item['month'].strftime('%b %Y') for item in monthly_expenses]
    expense_trend_data = [float(item['total']) for item in monthly_expenses]

    # ── Gender distribution for chart ──
    gender_data = Student.objects.values('gender').annotate(count=Count('id'))
    gender_labels = [item['gender'] for item in gender_data]
    gender_counts = [item['count'] for item in gender_data]

    # ── Department-wise student count ──
    dept_data = Department.objects.annotate(
        student_count=Count('classrooms__students')
    ).values('name', 'student_count')
    dept_labels = [item['name'] for item in dept_data]
    dept_counts = [item['student_count'] for item in dept_data]

    # ── Recent students ──
    recent_students = Student.objects.order_by('-joining_date')[:5]

    # ── Recent teachers ──
    recent_teachers = Teacher.objects.order_by('-joining_date')[:3]

    # ── Recent fee payments ──
    recent_fees = Fee.objects.filter(status='Paid').select_related('student').order_by('-date')[:5]

    # ── Recent notifications (activity feed) ──
    recent_notifications = Notification.objects.filter(
        user__is_admin=True
    ).order_by('-created_at')[:8]

    context = {
        # Counts
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_departments': total_departments,
        'total_subjects': total_subjects,
        'total_classrooms': total_classrooms,
        # Financial
        'total_revenue': total_revenue,
        'total_pending_fees': total_pending_fees,
        'pending_fee_count': pending_fee_count,
        'total_expenses': total_expenses,
        'total_salaries_paid': total_salaries_paid,
        'total_salaries_pending': total_salaries_pending,
        'net_income': net_income,
        # Ratio
        'ts_ratio': ts_ratio,
        # Charts
        'gender_labels': json.dumps(gender_labels),
        'gender_counts': json.dumps(gender_counts),
        'dept_labels': json.dumps(dept_labels),
        'dept_counts': json.dumps(dept_counts),
        'revenue_trend_labels': json.dumps(revenue_trend_labels),
        'revenue_trend_data': json.dumps(revenue_trend_data),
        'expense_trend_labels': json.dumps(expense_trend_labels),
        'expense_trend_data': json.dumps(expense_trend_data),
        # Recents
        'recent_students': recent_students,
        'recent_teachers': recent_teachers,
        'recent_fees': recent_fees,
        'recent_notifications': recent_notifications,
        # Time
        'current_time': now,
    }
    return render(request, 'dashboards/admin_dashboard.html', context)


@login_required
@teacher_required
def teacher_dashboard(request):
    """Teacher dashboard with classes, students, and schedule."""
    teacher = getattr(request.user, 'teacher_profile', None)
    total_subjects = 0
    total_students = 0
    classrooms = []

    if teacher:
        total_subjects = teacher.subjects.count()
        classrooms = ClassRoom.objects.filter(
            department=teacher.department
        ) if teacher.department else ClassRoom.objects.none()
        total_students = Student.objects.filter(
            classroom__in=classrooms
        ).count()

    context = {
        'teacher': teacher,
        'total_subjects': total_subjects,
        'total_students': total_students,
        'total_classes': classrooms.count() if classrooms else 0,
        'classrooms': classrooms,
    }
    return render(request, 'dashboards/teacher_dashboard.html', context)


@login_required
@student_required
def student_dashboard(request):
    """Student dashboard with courses, attendance, and records."""
    student = getattr(request.user, 'student_profile', None)
    subjects = []
    fees = []

    if student and student.classroom and student.classroom.department:
        subjects = Subject.objects.filter(
            department=student.classroom.department
        )
        fees = Fee.objects.filter(student=student)

    context = {
        'student': student,
        'subjects': subjects,
        'fees': fees,
        'total_subjects': len(subjects),
    }
    return render(request, 'dashboards/student_dashboard.html', context)


# ════════════════════════════════════════════════════════
#  Student CRUD
# ════════════════════════════════════════════════════════

@login_required
@admin_required
def student_list(request):
    """List all students with search and pagination."""
    query = request.GET.get('q', '')
    students = Student.objects.select_related('parent', 'classroom').all()
    if query:
        students = students.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(student_id__icontains=query) |
            Q(admission_number__icontains=query)
        )
    paginator = Paginator(students, 10)
    page = request.GET.get('page')
    students = paginator.get_page(page)
    return render(request, 'students/student_list.html', {
        'students': students, 'query': query
    })


@login_required
@admin_required
def add_student(request):
    """Add a new student along with parent details."""
    if request.method == 'POST':
        student_form = StudentForm(request.POST, request.FILES)
        parent_form = ParentForm(request.POST)
        if student_form.is_valid() and parent_form.is_valid():
            parent = parent_form.save()
            student = student_form.save(commit=False)
            student.parent = parent
            student.save()
            notify_admins(f"New student added: {student.full_name} (ID: {student.student_id})")
            messages.success(request, "Student added successfully!")
            return redirect('student_list')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        student_form = StudentForm()
        parent_form = ParentForm()
    return render(request, 'students/student_form.html', {
        'student_form': student_form,
        'parent_form': parent_form,
        'title': 'Add Student',
    })


@login_required
@admin_required
def edit_student(request, pk):
    """Edit an existing student and their parent details."""
    student = get_object_or_404(Student, pk=pk)
    parent = student.parent

    if request.method == 'POST':
        student_form = StudentForm(request.POST, request.FILES, instance=student)
        parent_form = ParentForm(request.POST, instance=parent)
        if student_form.is_valid() and parent_form.is_valid():
            parent_form.save()
            student_form.save()
            notify_admins(f"Student updated: {student.full_name} (ID: {student.student_id})")
            messages.success(request, "Student updated successfully!")
            return redirect('student_list')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        student_form = StudentForm(instance=student)
        parent_form = ParentForm(instance=parent)
    return render(request, 'students/student_form.html', {
        'student_form': student_form,
        'parent_form': parent_form,
        'title': 'Edit Student',
        'student': student,
    })


@login_required
@admin_required
def delete_student(request, pk):
    """Delete a student (with confirmation)."""
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        name = student.full_name
        sid = student.student_id
        student.parent.delete()
        student.delete()
        notify_admins(f"Student deleted: {name} (ID: {sid})")
        messages.success(request, "Student deleted successfully!")
        return redirect('student_list')
    return render(request, 'students/student_confirm_delete.html', {'student': student})


# ════════════════════════════════════════════════════════
#  Teacher CRUD
# ════════════════════════════════════════════════════════

@login_required
@admin_required
def teacher_list(request):
    """List all teachers."""
    query = request.GET.get('q', '')
    teachers = Teacher.objects.select_related('department').all()
    if query:
        teachers = teachers.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query)
        )
    paginator = Paginator(teachers, 10)
    page = request.GET.get('page')
    teachers = paginator.get_page(page)
    return render(request, 'teachers/teacher_list.html', {
        'teachers': teachers, 'query': query
    })


@login_required
@admin_required
def add_teacher(request):
    """Add a new teacher."""
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Teacher added successfully!")
            return redirect('teacher_list')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = TeacherForm()
    return render(request, 'teachers/teacher_form.html', {
        'form': form, 'title': 'Add Teacher'
    })


@login_required
@admin_required
def edit_teacher(request, pk):
    """Edit an existing teacher."""
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, "Teacher updated successfully!")
            return redirect('teacher_list')
        else:
            messages.error(request, "Please fix the errors below.")
    else:
        form = TeacherForm(instance=teacher)
    return render(request, 'teachers/teacher_form.html', {
        'form': form, 'title': 'Edit Teacher', 'teacher': teacher
    })


@login_required
@admin_required
def delete_teacher(request, pk):
    """Delete a teacher (with confirmation)."""
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        teacher.delete()
        messages.success(request, "Teacher deleted successfully!")
        return redirect('teacher_list')
    return render(request, 'teachers/teacher_confirm_delete.html', {'teacher': teacher})


# ════════════════════════════════════════════════════════
#  Department CRUD
# ════════════════════════════════════════════════════════

@login_required
@admin_required
def department_list(request):
    """List all departments."""
    departments = Department.objects.annotate(
        teacher_count=Count('teachers'),
        student_count=Count('classrooms__students'),
    )
    return render(request, 'departments/department_list.html', {
        'departments': departments
    })


@login_required
@admin_required
def add_department(request):
    """Add a new department."""
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Department added successfully!")
            return redirect('department_list')
    else:
        form = DepartmentForm()
    return render(request, 'departments/department_form.html', {
        'form': form, 'title': 'Add Department'
    })


@login_required
@admin_required
def edit_department(request, pk):
    """Edit an existing department."""
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, "Department updated successfully!")
            return redirect('department_list')
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'departments/department_form.html', {
        'form': form, 'title': 'Edit Department', 'department': department
    })


@login_required
@admin_required
def delete_department(request, pk):
    """Delete a department (with confirmation)."""
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        messages.success(request, "Department deleted successfully!")
        return redirect('department_list')
    return render(request, 'departments/department_confirm_delete.html', {
        'department': department
    })


# ════════════════════════════════════════════════════════
#  Subject CRUD
# ════════════════════════════════════════════════════════

@login_required
@admin_required
def subject_list(request):
    """List all subjects."""
    subjects = Subject.objects.select_related('department').all()
    return render(request, 'subjects/subject_list.html', {'subjects': subjects})


@login_required
@admin_required
def add_subject(request):
    """Add a new subject."""
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Subject added successfully!")
            return redirect('subject_list')
    else:
        form = SubjectForm()
    return render(request, 'subjects/subject_form.html', {
        'form': form, 'title': 'Add Subject'
    })


@login_required
@admin_required
def edit_subject(request, pk):
    """Edit an existing subject."""
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, "Subject updated successfully!")
            return redirect('subject_list')
    else:
        form = SubjectForm(instance=subject)
    return render(request, 'subjects/subject_form.html', {
        'form': form, 'title': 'Edit Subject', 'subject': subject
    })


@login_required
@admin_required
def delete_subject(request, pk):
    """Delete a subject (with confirmation)."""
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        subject.delete()
        messages.success(request, "Subject deleted successfully!")
        return redirect('subject_list')
    return render(request, 'subjects/subject_confirm_delete.html', {
        'subject': subject
    })


# ════════════════════════════════════════════════════════
#  Accounts Views (Fees, Expenses, Salaries)
# ════════════════════════════════════════════════════════

@login_required
@admin_required
def fee_list(request):
    """List all fee records."""
    fees = Fee.objects.select_related('student').all().order_by('-date')
    total_collected = fees.filter(status='Paid').aggregate(t=Sum('amount'))['t'] or 0
    total_pending = fees.filter(status='Unpaid').aggregate(t=Sum('amount'))['t'] or 0
    return render(request, 'accounts/fee_list.html', {
        'fees': fees,
        'total_collected': total_collected,
        'total_pending': total_pending,
    })


@login_required
@admin_required
def add_fee(request):
    """Add a new fee record."""
    if request.method == 'POST':
        form = FeeForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Fee record added successfully!")
            return redirect('fee_list')
    else:
        form = FeeForm()
    return render(request, 'accounts/fee_form.html', {
        'form': form, 'title': 'Add Fee Record'
    })


@login_required
@admin_required
def expense_list(request):
    """List all expense records."""
    expenses = Expense.objects.all().order_by('-date')
    total_expenses = expenses.aggregate(t=Sum('amount'))['t'] or 0
    return render(request, 'accounts/expense_list.html', {
        'expenses': expenses,
        'total_expenses': total_expenses,
    })


@login_required
@admin_required
def add_expense(request):
    """Add a new expense record."""
    if request.method == 'POST':
        form = ExpenseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Expense recorded successfully!")
            return redirect('expense_list')
    else:
        form = ExpenseForm()
    return render(request, 'accounts/expense_form.html', {
        'form': form, 'title': 'Add Expense'
    })


@login_required
@admin_required
def salary_list(request):
    """List all salary records."""
    salaries = Salary.objects.select_related('teacher').all().order_by('-year', '-month')
    total_paid = salaries.filter(status='Paid').aggregate(t=Sum('amount'))['t'] or 0
    total_pending = salaries.filter(status='Pending').aggregate(t=Sum('amount'))['t'] or 0
    return render(request, 'accounts/salary_list.html', {
        'salaries': salaries,
        'total_paid': total_paid,
        'total_pending': total_pending,
    })


@login_required
@admin_required
def add_salary(request):
    """Add a new salary record."""
    if request.method == 'POST':
        form = SalaryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Salary record added successfully!")
            return redirect('salary_list')
    else:
        form = SalaryForm()
    return render(request, 'accounts/salary_form.html', {
        'form': form, 'title': 'Add Salary Record'
    })


# ════════════════════════════════════════════════════════
#  Notification Views
# ════════════════════════════════════════════════════════

@login_required
def notification_list(request):
    """List all notifications for the current user."""
    notifications = Notification.objects.filter(user=request.user)
    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications
    })


@login_required
def mark_notification_read(request, pk):
    """Mark a single notification as read."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    messages.success(request, "Notification marked as read.")
    return redirect('notification_list')


@login_required
def clear_all_notifications(request):
    """Delete all notifications for the current user."""
    Notification.objects.filter(user=request.user).delete()
    messages.success(request, "All notifications cleared.")
    return redirect('notification_list')
