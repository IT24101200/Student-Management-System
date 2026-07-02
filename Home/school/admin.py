from django.contrib import admin
from .models import (
    User, Department, Subject, ClassRoom, Parent,
    Student, Teacher, Notification, Fee, Expense, Salary,
    PasswordResetToken,
)


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'is_student', 'is_teacher', 'is_admin']
    list_filter = ['is_student', 'is_teacher', 'is_admin']


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'head', 'created_at']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'department']
    list_filter = ['department']


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ['name', 'section', 'department']


@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    list_display = ['father_name', 'mother_name', 'mobile_number', 'email']


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['student_id', 'first_name', 'last_name', 'gender', 'classroom', 'admission_number']
    list_filter = ['gender', 'classroom']
    search_fields = ['first_name', 'last_name', 'student_id']


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'department', 'mobile_number']
    list_filter = ['department']


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'message', 'is_read', 'created_at']
    list_filter = ['is_read']


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ['student', 'fee_type', 'amount', 'date', 'status']
    list_filter = ['status']


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'date']


@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'amount', 'month', 'year', 'status']
    list_filter = ['status', 'year']


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'created_at', 'is_used']
