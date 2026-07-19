import json
import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Course, Module, Lesson, Category, Enrollment, Progress, Bookmark, History
from apps.videos.models import Video
from apps.quizzes.models import Quiz, Question, Option
from apps.feedback.models import Feedback
from apps.notifications.models import Notification
from utils.ai_services import SkillForgeAI

logger = logging.getLogger(__name__)


# ─── Landing & Browse ────────────────────────────────────────────────

def landing_view(request):
    """Landing page with featured courses, categories, and stats."""
    featured_courses = Course.objects.filter(
        status='published', is_featured=True
    ).select_related('instructor', 'category')[:6]

    popular_courses = Course.objects.filter(
        status='published'
    ).order_by('-student_count')[:8]

    categories = Category.objects.filter(is_featured=True)[:8]

    stats = {
        'courses': Course.objects.filter(status='published').count(),
        'students': Enrollment.objects.values('student').distinct().count(),
        'creators': Course.objects.values('instructor').distinct().count(),
        'hours': Course.objects.filter(status='published').aggregate(
            total=Count('total_duration')
        )['total'] or 0,
    }

    context = {
        'featured_courses': featured_courses,
        'popular_courses': popular_courses,
        'categories': categories,
        'stats': stats,
    }
    return render(request, 'landing/index.html', context)


def browse_courses_view(request):
    """Browse courses with filtering, sorting, and pagination."""
    courses = Course.objects.filter(status='published').select_related('instructor', 'category')

    # Filters
    category_slug = request.GET.get('category')
    level = request.GET.get('level')
    sort_by = request.GET.get('sort', 'popular')

    if category_slug:
        courses = courses.filter(category__slug=category_slug)
    if level:
        courses = courses.filter(skill_level=level)

    # Sort
    if sort_by == 'newest':
        courses = courses.order_by('-created_at')
    elif sort_by == 'rating':
        courses = courses.order_by('-average_rating')
    elif sort_by == 'students':
        courses = courses.order_by('-student_count')
    else:
        courses = courses.order_by('-student_count', '-average_rating')

    # Pagination
    paginator = Paginator(courses, 12)
    page = request.GET.get('page', 1)
    courses_page = paginator.get_page(page)

    categories = Category.objects.all()

    context = {
        'courses': courses_page,
        'categories': categories,
        'current_category': category_slug,
        'current_level': level,
        'current_sort': sort_by,
    }
    return render(request, 'courses/browse.html', context)


def search_courses_view(request):
    """Search courses with instant results."""
    query = request.GET.get('q', '').strip()
    courses = Course.objects.filter(status='published')

    if query:
        courses = courses.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__icontains=query) |
            Q(instructor__first_name__icontains=query) |
            Q(instructor__last_name__icontains=query) |
            Q(category__name__icontains=query)
        ).select_related('instructor', 'category')

    paginator = Paginator(courses, 12)
    page = request.GET.get('page', 1)
    courses_page = paginator.get_page(page)

    # API response for instant search
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        results = [{
            'id': str(c.id),
            'title': c.title,
            'slug': c.slug,
            'thumbnail': c.thumbnail.url if c.thumbnail else '',
            'instructor': c.instructor.get_full_name(),
            'rating': float(c.average_rating),
            'students': c.student_count,
            'duration': c.duration_display,
            'level': c.get_skill_level_display(),
        } for c in courses_page]
        return JsonResponse({'results': results, 'has_next': courses_page.has_next()})

    categories = Category.objects.all()
    context = {
        'courses': courses_page,
        'query': query,
        'categories': categories,
    }
    return render(request, 'courses/search.html', context)


def course_detail_view(request, slug):
    """Course detail/preview page."""
    course = get_object_or_404(
        Course.objects.select_related('instructor', 'category'),
        slug=slug
    )

    # Increment view count
    course.view_count += 1
    course.save(update_fields=['view_count'])

    modules = course.modules.prefetch_related('lessons').all()
    feedbacks = course.feedback.select_related('student').order_by('-created_at')[:10]

    is_enrolled = False
    enrollment = None
    if request.user.is_authenticated:
        enrollment = Enrollment.objects.filter(student=request.user, course=course).first()
        is_enrolled = enrollment is not None

        # Update history
        History.objects.update_or_create(
            user=request.user, course=course,
            defaults={'last_accessed': timezone.now()}
        )

    context = {
        'course': course,
        'modules': modules,
        'feedbacks': feedbacks,
        'is_enrolled': is_enrolled,
        'enrollment': enrollment,
        'related_courses': Course.objects.filter(
            category=course.category, status='published'
        ).exclude(pk=course.pk)[:4],
    }
    return render(request, 'courses/detail.html', context)


@login_required
def enroll_course_view(request, slug):
    """Enroll student in a course."""
    course = get_object_or_404(Course, slug=slug, status='published')

    enrollment, created = Enrollment.objects.get_or_create(
        student=request.user,
        course=course
    )

    if created:
        course.student_count += 1
        course.save(update_fields=['student_count'])

        # Notify instructor
        Notification.objects.create(
            user=course.instructor,
            notification_type='enrollment',
            title='New Student Enrolled',
            message=f'{request.user.get_full_name()} enrolled in "{course.title}"',
            link=f'/courses/{course.slug}/',
        )
        messages.success(request, f'Successfully enrolled in "{course.title}"!')
    else:
        messages.info(request, 'You are already enrolled in this course.')

    return redirect('course_watch', slug=course.slug)


@login_required
def course_watch_view(request, slug):
    """Course player page (YouTube Learning style)."""
    course = get_object_or_404(
        Course.objects.select_related('instructor', 'category'),
        slug=slug
    )

    enrollment = get_object_or_404(Enrollment, student=request.user, course=course)

    modules = course.modules.prefetch_related(
        'lessons__video', 'lessons__quiz'
    ).all()

    # Get current lesson
    lesson_id = request.GET.get('lesson')
    current_lesson = None
    if lesson_id:
        current_lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
    else:
        # Find last watched or first lesson
        last_progress = Progress.objects.filter(
            enrollment=enrollment, completed=False
        ).order_by('lesson__module__order', 'lesson__order').first()
        if last_progress:
            current_lesson = last_progress.lesson
        else:
            first_module = modules.first()
            if first_module:
                current_lesson = first_module.lessons.first()

    # Get/create progress for current lesson
    progress = None
    if current_lesson:
        progress, _ = Progress.objects.get_or_create(
            enrollment=enrollment,
            lesson=current_lesson
        )

    # Get all progress for sidebar
    all_progress = {
        str(p.lesson_id): p
        for p in Progress.objects.filter(enrollment=enrollment)
    }

    # Get bookmarks
    bookmarks = {
        str(b.lesson_id): b
        for b in Bookmark.objects.filter(user=request.user, lesson__module__course=course)
    }

    # Update history
    History.objects.update_or_create(
        user=request.user, course=course,
        defaults={'last_accessed': timezone.now()}
    )

    context = {
        'course': course,
        'enrollment': enrollment,
        'modules': modules,
        'current_lesson': current_lesson,
        'progress': progress,
        'all_progress': all_progress,
        'bookmarks': bookmarks,
        'progress_percentage': enrollment.progress_percentage,
    }
    return render(request, 'courses/watch.html', context)


@login_required
def update_progress_view(request):
    """API: Update lesson watch progress."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lesson_id = data.get('lesson_id')
            watch_duration = data.get('watch_duration', 0)
            last_position = data.get('last_position', 0)
            completed = data.get('completed', False)

            lesson = get_object_or_404(Lesson, id=lesson_id)
            enrollment = get_object_or_404(
                Enrollment, student=request.user, course=lesson.module.course
            )

            progress, _ = Progress.objects.get_or_create(
                enrollment=enrollment, lesson=lesson
            )
            progress.watch_duration = watch_duration
            progress.last_position = last_position

            if completed and not progress.completed:
                progress.completed = True
                progress.completed_at = timezone.now()

            progress.save()

            # Check if course is complete
            total_lessons = enrollment.course.total_lessons
            completed_count = Progress.objects.filter(
                enrollment=enrollment, completed=True
            ).count()

            if total_lessons > 0 and completed_count >= total_lessons and not enrollment.completed:
                enrollment.completed = True
                enrollment.completed_at = timezone.now()
                enrollment.save()

            return JsonResponse({
                'status': 'ok',
                'progress_percentage': enrollment.progress_percentage,
                'course_completed': enrollment.completed,
            })
        except Exception as e:
            logger.error(f"Progress update error: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error'}, status=405)


@login_required
def toggle_bookmark_view(request):
    """API: Toggle bookmark on a lesson."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lesson_id = data.get('lesson_id')
            note = data.get('note', '')

            lesson = get_object_or_404(Lesson, id=lesson_id)
            bookmark, created = Bookmark.objects.get_or_create(
                user=request.user, lesson=lesson,
                defaults={'note': note}
            )

            if not created:
                bookmark.delete()
                return JsonResponse({'status': 'removed'})

            return JsonResponse({'status': 'added', 'id': str(bookmark.id)})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error'}, status=405)


# ─── Instructor: Course Creation ────────────────────────────────────

@login_required
def course_create_step1_view(request):
    """Step 1: Upload thumbnail."""
    if not request.user.is_instructor and not request.user.is_admin_user:
        messages.error(request, 'You need an instructor account to create courses.')
        return redirect('dashboard')

    course_id = request.session.get('creating_course_id')
    course = None
    if course_id:
        course = Course.objects.filter(id=course_id, instructor=request.user).first()

    if request.method == 'POST':
        if not course:
            course = Course(instructor=request.user, title='Untitled Course')
            course.save()
            request.session['creating_course_id'] = str(course.id)

        if 'thumbnail' in request.FILES:
            course.thumbnail = request.FILES['thumbnail']
            course.save()
            messages.success(request, 'Thumbnail uploaded!')

        return redirect('course_create_step2')

    return render(request, 'courses/create/step1_thumbnail.html', {'course': course})


@login_required
def course_create_step2_view(request):
    """Step 2: Course information."""
    course_id = request.session.get('creating_course_id')
    if not course_id:
        return redirect('course_create_step1')

    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    categories = Category.objects.all()

    if request.method == 'POST':
        course.title = request.POST.get('title', course.title)
        course.caption = request.POST.get('caption', '')
        course.description = request.POST.get('description', '')
        course.skill_level = request.POST.get('skill_level', 'all_levels')
        course.language = request.POST.get('language', 'English')

        category_id = request.POST.get('category')
        if category_id:
            course.category_id = category_id

        tags_str = request.POST.get('tags', '')
        course.tags = [t.strip() for t in tags_str.split(',') if t.strip()]

        course.save()

        # Generate AI suggestions
        ai = SkillForgeAI()
        if not course.learning_outcomes:
            course.learning_outcomes = ai.generate_learning_outcomes(course.title, course.category.name if course.category else '')
        if not course.prerequisites:
            course.prerequisites = ai.generate_prerequisites(course.title, course.skill_level)
        if not course.highlights:
            course.highlights = ai.generate_highlights(course.title, course.description)
        if not course.ai_summary:
            course.ai_summary = ai.generate_summary(course.title, course.description)
        if not course.tags:
            course.tags = ai.generate_tags(course.title, course.description)

        course.save()
        messages.success(request, 'Course information saved!')
        return redirect('course_create_step3')

    context = {
        'course': course,
        'categories': categories,
        'skill_levels': Course.SkillLevel.choices,
    }
    return render(request, 'courses/create/step2_info.html', context)


@login_required
def course_create_step3_view(request):
    """Step 3: Modules, videos, and quizzes."""
    course_id = request.session.get('creating_course_id')
    if not course_id:
        return redirect('course_create_step1')

    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    modules = course.modules.prefetch_related('lessons__video', 'lessons__quiz').all()

    context = {
        'course': course,
        'modules': modules,
    }
    return render(request, 'courses/create/step3_modules.html', context)


@login_required
def add_module_view(request):
    """API: Add a module to a course."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            course_id = data.get('course_id')
            course = get_object_or_404(Course, id=course_id, instructor=request.user)

            if course.modules.count() >= 8:
                return JsonResponse({'status': 'error', 'message': 'Maximum 8 modules allowed.'}, status=400)

            module = Module.objects.create(
                course=course,
                title=data.get('title', f'Module {course.modules.count() + 1}'),
                description=data.get('description', ''),
                order=course.modules.count(),
            )

            return JsonResponse({
                'status': 'ok',
                'module': {
                    'id': str(module.id),
                    'title': module.title,
                    'description': module.description,
                    'order': module.order,
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error'}, status=405)


@login_required
def update_module_view(request, module_id):
    """API: Update or delete a module."""
    module = get_object_or_404(Module, id=module_id, course__instructor=request.user)

    if request.method == 'PUT':
        data = json.loads(request.body)
        module.title = data.get('title', module.title)
        module.description = data.get('description', module.description)
        module.order = data.get('order', module.order)
        module.save()
        return JsonResponse({'status': 'ok'})

    elif request.method == 'DELETE':
        module.delete()
        return JsonResponse({'status': 'ok'})

    return JsonResponse({'status': 'error'}, status=405)


@login_required
def add_lesson_view(request):
    """API: Add a lesson (video or quiz) to a module."""
    if request.method == 'POST':
        module_id = request.POST.get('module_id')
        module = get_object_or_404(Module, id=module_id, course__instructor=request.user)

        lesson_type = request.POST.get('lesson_type', 'video')
        title = request.POST.get('title', f'Lesson {module.lessons.count() + 1}')

        lesson = Lesson.objects.create(
            module=module,
            title=title,
            lesson_type=lesson_type,
            order=module.lessons.count(),
        )

        if lesson_type == 'video' and 'video_file' in request.FILES:
            video_file = request.FILES['video_file']
            video = Video.objects.create(
                lesson=lesson,
                file=video_file,
                file_size=video_file.size,
                duration=0,  # Will be calculated client-side
            )

            # Update duration if provided
            duration = request.POST.get('duration', 0)
            if duration:
                video.duration = int(duration)
                video.save()

            # Update module and course stats
            module.update_duration()
            module.course.update_stats()

        elif lesson_type == 'quiz':
            Quiz.objects.create(
                lesson=lesson,
                pass_percentage=int(request.POST.get('pass_percentage', 70)),
            )

        return JsonResponse({
            'status': 'ok',
            'lesson': {
                'id': str(lesson.id),
                'title': lesson.title,
                'type': lesson.lesson_type,
                'order': lesson.order,
            }
        })

    return JsonResponse({'status': 'error'}, status=405)


@login_required
def delete_lesson_view(request, lesson_id):
    """API: Delete a lesson."""
    if request.method == 'DELETE':
        lesson = get_object_or_404(Lesson, id=lesson_id, module__course__instructor=request.user)
        course = lesson.module.course
        lesson.delete()
        course.update_stats()
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=405)


@login_required
def add_quiz_question_view(request):
    """API: Add a question to a quiz."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            quiz_id = data.get('quiz_id')
            quiz = get_object_or_404(Quiz, id=quiz_id, lesson__module__course__instructor=request.user)

            if quiz.questions.count() >= 8:
                return JsonResponse({'status': 'error', 'message': 'Maximum 8 questions per quiz.'}, status=400)

            question = Question.objects.create(
                quiz=quiz,
                text=data.get('text', ''),
                explanation=data.get('explanation', ''),
                marks=int(data.get('marks', 1)),
                order=quiz.questions.count(),
            )

            # Create options A-D
            options_data = data.get('options', [])
            correct_answer = data.get('correct_answer', 'A')
            for i, label in enumerate(['A', 'B', 'C', 'D']):
                Option.objects.create(
                    question=question,
                    label=label,
                    text=options_data[i] if i < len(options_data) else '',
                    is_correct=(label == correct_answer),
                )

            return JsonResponse({
                'status': 'ok',
                'question': {
                    'id': str(question.id),
                    'text': question.text,
                    'order': question.order,
                }
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

    return JsonResponse({'status': 'error'}, status=405)


@login_required
def course_review_view(request):
    """Review course before publishing."""
    course_id = request.session.get('creating_course_id')
    if not course_id:
        return redirect('course_create_step1')

    course = get_object_or_404(Course, id=course_id, instructor=request.user)
    modules = course.modules.prefetch_related('lessons__video', 'lessons__quiz__questions').all()

    # Recalculate stats
    course.update_stats()

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'publish':
            if course.total_lessons == 0:
                messages.error(request, 'Add at least one lesson before publishing.')
            elif not course.thumbnail:
                messages.error(request, 'Please upload a course thumbnail.')
            else:
                course.status = 'published'
                course.save()
                if 'creating_course_id' in request.session:
                    del request.session['creating_course_id']
                messages.success(request, f'🎉 "{course.title}" is now published!')
                return redirect('instructor_dashboard')
        elif action == 'draft':
            course.status = 'draft'
            course.save()
            messages.info(request, 'Course saved as draft.')
        elif action == 'private':
            course.status = 'private'
            course.save()
            messages.info(request, 'Course set to private.')

    context = {
        'course': course,
        'modules': modules,
    }
    return render(request, 'courses/create/review.html', context)


@login_required
def course_edit_view(request, slug):
    """Edit an existing course."""
    course = get_object_or_404(Course, slug=slug, instructor=request.user)
    request.session['creating_course_id'] = str(course.id)
    return redirect('course_create_step1')


@login_required
def course_delete_view(request, slug):
    """Delete a course."""
    if request.method == 'POST':
        course = get_object_or_404(Course, slug=slug, instructor=request.user)
        title = course.title
        course.delete()
        messages.success(request, f'Course "{title}" has been deleted.')
        return redirect('instructor_dashboard')
    return redirect('instructor_dashboard')
