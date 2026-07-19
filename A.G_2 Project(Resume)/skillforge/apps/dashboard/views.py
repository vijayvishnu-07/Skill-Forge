from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Avg, Q, Sum
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta
import json

from apps.courses.models import Course, Category, Enrollment, Progress, History, Bookmark
from apps.feedback.models import Feedback
from apps.notifications.models import Notification
from apps.certificates.models import Certificate
from apps.accounts.models import User


@login_required
def dashboard_redirect(request):
    """Redirect to appropriate dashboard based on role."""
    if request.user.is_admin_user:
        return redirect('admin_dashboard')
    elif request.user.is_instructor:
        return redirect('instructor_dashboard')
    return redirect('student_dashboard')


@login_required
def student_dashboard_view(request):
    """Student dashboard with learning progress."""
    enrollments = Enrollment.objects.filter(
        student=request.user
    ).select_related('course', 'course__instructor', 'course__category').order_by('-enrolled_at')

    # In-progress courses
    in_progress = []
    for e in enrollments.filter(completed=False):
        in_progress.append({
            'enrollment': e,
            'progress': e.progress_percentage,
        })

    # Recently viewed
    recent_history = History.objects.filter(
        user=request.user
    ).select_related('course').order_by('-last_accessed')[:5]

    # Bookmarks
    bookmarks = Bookmark.objects.filter(
        user=request.user
    ).select_related('lesson', 'lesson__module__course').order_by('-created_at')[:10]

    # Certificates
    certificates = Certificate.objects.filter(
        enrollment__student=request.user
    ).select_related('enrollment__course')

    # Stats
    stats = {
        'enrolled_courses': enrollments.count(),
        'completed_courses': enrollments.filter(completed=True).count(),
        'certificates': certificates.count(),
        'bookmarks': Bookmark.objects.filter(user=request.user).count(),
    }

    context = {
        'in_progress': in_progress,
        'recent_history': recent_history,
        'bookmarks': bookmarks,
        'certificates': certificates,
        'completed_enrollments': enrollments.filter(completed=True),
        'stats': stats,
    }
    return render(request, 'dashboard/student.html', context)


@login_required
def instructor_dashboard_view(request):
    """Instructor dashboard with analytics."""
    if not request.user.is_instructor and not request.user.is_admin_user:
        return redirect('student_dashboard')

    courses = Course.objects.filter(instructor=request.user)

    # Stats
    total_students = Enrollment.objects.filter(course__instructor=request.user).count()
    avg_rating = courses.aggregate(avg=Avg('average_rating'))['avg'] or 0
    total_views = courses.aggregate(total=Sum('view_count'))['total'] or 0

    # Recent feedback
    recent_feedback = Feedback.objects.filter(
        course__instructor=request.user
    ).select_related('student', 'course').order_by('-created_at')[:10]

    # Recent enrollments (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_enrollments = Enrollment.objects.filter(
        course__instructor=request.user,
        enrolled_at__gte=thirty_days_ago
    ).select_related('student', 'course').order_by('-enrolled_at')[:20]

    # Enrollment chart data (last 7 days)
    chart_data = []
    for i in range(6, -1, -1):
        day = timezone.now().date() - timedelta(days=i)
        count = Enrollment.objects.filter(
            course__instructor=request.user,
            enrolled_at__date=day
        ).count()
        chart_data.append({
            'date': day.strftime('%b %d'),
            'count': count,
        })

    context = {
        'courses': courses,
        'stats': {
            'total_courses': courses.count(),
            'total_students': total_students,
            'avg_rating': round(avg_rating, 1),
            'total_views': total_views,
        },
        'recent_feedback': recent_feedback,
        'recent_enrollments': recent_enrollments,
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'dashboard/instructor.html', context)


@login_required
def admin_dashboard_view(request):
    """Admin dashboard with system overview."""
    if not request.user.is_admin_user and not request.user.is_superuser:
        return redirect('dashboard')

    # System stats
    stats = {
        'total_users': User.objects.count(),
        'total_students': User.objects.filter(role='student').count(),
        'total_instructors': User.objects.filter(role='instructor').count(),
        'total_courses': Course.objects.count(),
        'published_courses': Course.objects.filter(status='published').count(),
        'total_enrollments': Enrollment.objects.count(),
        'total_feedback': Feedback.objects.count(),
    }

    # Recent activity
    recent_users = User.objects.order_by('-date_joined')[:10]
    recent_courses = Course.objects.select_related('instructor').order_by('-created_at')[:10]
    recent_feedback = Feedback.objects.select_related('student', 'course').order_by('-created_at')[:10]
    categories = Category.objects.annotate(num_courses=Count('courses'))

    context = {
        'stats': stats,
        'recent_users': recent_users,
        'recent_courses': recent_courses,
        'recent_feedback': recent_feedback,
        'categories': categories,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@login_required
def admin_users_view(request):
    """Admin: Manage users."""
    if not request.user.is_admin_user and not request.user.is_superuser:
        return redirect('dashboard')

    users = User.objects.all().order_by('-date_joined')

    # Filters
    role = request.GET.get('role')
    search = request.GET.get('q', '')
    if role:
        users = users.filter(role=role)
    if search:
        users = users.filter(
            Q(email__icontains=search) | Q(first_name__icontains=search) | Q(last_name__icontains=search)
        )

    paginator = Paginator(users, 20)
    page = request.GET.get('page', 1)
    users_page = paginator.get_page(page)

    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        try:
            target_user = User.objects.get(id=user_id)
            if action == 'change_role':
                new_role = request.POST.get('new_role')
                target_user.role = new_role
                target_user.save()
                messages.success(request, f'Role updated for {target_user.email}')
            elif action == 'toggle_active':
                target_user.is_active = not target_user.is_active
                target_user.save()
                status = 'activated' if target_user.is_active else 'deactivated'
                messages.success(request, f'User {target_user.email} {status}')
            elif action == 'delete':
                target_user.delete()
                messages.success(request, 'User deleted.')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
        return redirect('admin_users')

    return render(request, 'admin_panel/users.html', {'users': users_page, 'search': search, 'current_role': role})


@login_required
def admin_courses_view(request):
    """Admin: Manage courses."""
    if not request.user.is_admin_user and not request.user.is_superuser:
        return redirect('dashboard')

    courses = Course.objects.select_related('instructor', 'category').order_by('-created_at')
    search = request.GET.get('q', '')
    status_filter = request.GET.get('status')

    if search:
        courses = courses.filter(Q(title__icontains=search) | Q(instructor__email__icontains=search))
    if status_filter:
        courses = courses.filter(status=status_filter)

    paginator = Paginator(courses, 20)
    page = request.GET.get('page', 1)
    courses_page = paginator.get_page(page)

    if request.method == 'POST':
        action = request.POST.get('action')
        course_id = request.POST.get('course_id')
        try:
            course = Course.objects.get(id=course_id)
            if action == 'approve':
                course.status = 'published'
                course.save()
                messages.success(request, f'Course "{course.title}" approved.')
            elif action == 'feature':
                course.is_featured = not course.is_featured
                course.save()
                messages.success(request, f'Feature status toggled for "{course.title}".')
            elif action == 'delete':
                course.delete()
                messages.success(request, 'Course deleted.')
        except Course.DoesNotExist:
            messages.error(request, 'Course not found.')
        return redirect('admin_courses')

    return render(request, 'admin_panel/courses.html', {'courses': courses_page, 'search': search, 'status_filter': status_filter})


@login_required
def admin_categories_view(request):
    """Admin: Manage categories."""
    if not request.user.is_admin_user and not request.user.is_superuser:
        return redirect('dashboard')

    categories = Category.objects.annotate(num_courses=Count('courses')).order_by('name')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            name = request.POST.get('name', '').strip()
            icon = request.POST.get('icon', '📚')
            description = request.POST.get('description', '')
            is_featured = request.POST.get('is_featured') == 'on'
            if name:
                Category.objects.create(name=name, icon=icon, description=description, is_featured=is_featured)
                messages.success(request, f'Category "{name}" created.')
        elif action == 'delete':
            cat_id = request.POST.get('category_id')
            Category.objects.filter(id=cat_id).delete()
            messages.success(request, 'Category deleted.')
        elif action == 'edit':
            cat_id = request.POST.get('category_id')
            try:
                cat = Category.objects.get(id=cat_id)
                cat.name = request.POST.get('name', cat.name)
                cat.icon = request.POST.get('icon', cat.icon)
                cat.description = request.POST.get('description', cat.description)
                cat.is_featured = request.POST.get('is_featured') == 'on'
                cat.save()
                messages.success(request, f'Category "{cat.name}" updated.')
            except Category.DoesNotExist:
                messages.error(request, 'Category not found.')
        return redirect('admin_categories')

    return render(request, 'admin_panel/categories.html', {'categories': categories})


@login_required
def admin_feedback_view(request):
    """Admin: Review feedback."""
    if not request.user.is_admin_user and not request.user.is_superuser:
        return redirect('dashboard')

    feedbacks = Feedback.objects.select_related('student', 'course').order_by('-created_at')
    paginator = Paginator(feedbacks, 20)
    page = request.GET.get('page', 1)
    feedbacks_page = paginator.get_page(page)

    if request.method == 'POST' and request.POST.get('action') == 'delete':
        feedback_id = request.POST.get('feedback_id')
        Feedback.objects.filter(id=feedback_id).delete()
        messages.success(request, 'Feedback deleted.')
        return redirect('admin_feedback')

    return render(request, 'admin_panel/feedback.html', {'feedbacks': feedbacks_page})


@login_required
def admin_settings_view(request):
    """Admin: System settings."""
    if not request.user.is_admin_user and not request.user.is_superuser:
        return redirect('dashboard')
    return render(request, 'admin_panel/settings.html')
