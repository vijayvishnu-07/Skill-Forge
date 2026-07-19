import json
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Avg

from .models import Feedback
from apps.courses.models import Course, Enrollment
from apps.notifications.models import Notification


@login_required
def submit_feedback_view(request, course_id):
    """Submit or update feedback for a course."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)

    course = get_object_or_404(Course, id=course_id)

    # Check enrollment
    if not Enrollment.objects.filter(student=request.user, course=course).exists():
        return JsonResponse({'status': 'error', 'message': 'You must be enrolled to leave feedback.'}, status=403)

    data = json.loads(request.body)
    rating = int(data.get('rating', 5))
    text = data.get('text', '')

    if rating < 1 or rating > 5:
        return JsonResponse({'status': 'error', 'message': 'Rating must be 1-5.'}, status=400)

    feedback, created = Feedback.objects.update_or_create(
        student=request.user,
        course=course,
        defaults={'rating': rating, 'text': text}
    )

    # Update course average rating
    avg = Feedback.objects.filter(course=course).aggregate(avg=Avg('rating'))['avg'] or 0
    course.average_rating = round(avg, 2)
    course.rating_count = Feedback.objects.filter(course=course).count()
    course.save(update_fields=['average_rating', 'rating_count'])

    # Notify instructor
    Notification.objects.create(
        user=course.instructor,
        notification_type='feedback',
        title='New Course Feedback',
        message=f'{request.user.get_full_name()} rated "{course.title}" {rating}★: "{text[:100]}"',
        link=f'/courses/{course.slug}/',
    )

    return JsonResponse({
        'status': 'ok',
        'feedback': {
            'id': str(feedback.id),
            'rating': feedback.rating,
            'text': feedback.text,
            'created_at': feedback.created_at.isoformat(),
        }
    })


@login_required
def get_feedback_view(request, course_id):
    """Get all feedback for a course."""
    course = get_object_or_404(Course, id=course_id)
    feedbacks = Feedback.objects.filter(course=course).select_related('student')

    data = [{
        'id': str(f.id),
        'student_name': f.student.get_full_name(),
        'student_avatar': f.student.profile.avatar_url if hasattr(f.student, 'profile') else '',
        'rating': f.rating,
        'text': f.text,
        'created_at': f.created_at.isoformat(),
    } for f in feedbacks]

    return JsonResponse({'feedback': data, 'average': float(course.average_rating), 'count': course.rating_count})
