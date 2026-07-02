from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Student, Notification, User


@receiver(post_save, sender=Student)
def student_saved_notification(sender, instance, created, **kwargs):
    """Create a notification for all admins when a student is added or updated."""
    admins = User.objects.filter(is_admin=True)
    if created:
        message = f"📋 New student enrolled: {instance.full_name} (ID: {instance.student_id})"
    else:
        message = f"✏️ Student updated: {instance.full_name} (ID: {instance.student_id})"
    for admin_user in admins:
        Notification.objects.create(user=admin_user, message=message)


@receiver(post_delete, sender=Student)
def student_deleted_notification(sender, instance, **kwargs):
    """Create a notification for all admins when a student is deleted."""
    admins = User.objects.filter(is_admin=True)
    message = f"🗑️ Student removed: {instance.full_name} (ID: {instance.student_id})"
    for admin_user in admins:
        Notification.objects.create(user=admin_user, message=message)
