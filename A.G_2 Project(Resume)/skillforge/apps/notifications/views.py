from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Notification


@login_required
def notifications_view(request):
    """Get user notifications."""
    notifications = Notification.objects.filter(user=request.user)[:20]
    unread = Notification.objects.filter(user=request.user, is_read=False).count()

    data = [{
        'id': str(n.id),
        'type': n.notification_type,
        'title': n.title,
        'message': n.message,
        'link': n.link,
        'is_read': n.is_read,
        'created_at': n.created_at.isoformat(),
    } for n in notifications]

    return JsonResponse({'notifications': data, 'unread_count': unread})


@login_required
def mark_read_view(request, notification_id):
    """Mark a notification as read."""
    try:
        notification = Notification.objects.get(id=notification_id, user=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'ok'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error'}, status=404)


@login_required
def mark_all_read_view(request):
    """Mark all notifications as read."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'ok'})
