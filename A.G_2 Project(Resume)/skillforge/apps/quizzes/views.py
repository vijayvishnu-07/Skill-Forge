import json
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

from .models import Quiz, Question, Option, QuizAttempt
from apps.courses.models import Progress, Enrollment
from apps.notifications.models import Notification
from django.utils import timezone


@login_required
def get_quiz_view(request, quiz_id):
    """Get quiz questions for taking."""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    questions = quiz.questions.prefetch_related('options').all()

    data = {
        'quiz_id': str(quiz.id),
        'lesson_title': quiz.lesson.title,
        'pass_percentage': quiz.pass_percentage,
        'time_limit': quiz.time_limit,
        'questions': [{
            'id': str(q.id),
            'text': q.text,
            'marks': q.marks,
            'order': q.order,
            'options': [{
                'label': o.label,
                'text': o.text,
            } for o in q.options.all()]
        } for q in questions]
    }
    return JsonResponse(data)


@login_required
def submit_quiz_view(request, quiz_id):
    """Submit quiz answers and get instant results."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error'}, status=405)

    quiz = get_object_or_404(Quiz, id=quiz_id)
    data = json.loads(request.body)
    answers = data.get('answers', {})

    score = 0
    total_marks = 0
    results = []

    questions = quiz.questions.prefetch_related('options').all()
    for question in questions:
        total_marks += question.marks
        selected = answers.get(str(question.id))
        correct_option = question.options.filter(is_correct=True).first()
        is_correct = selected == correct_option.label if correct_option else False

        if is_correct:
            score += question.marks

        results.append({
            'question_id': str(question.id),
            'question_text': question.text,
            'selected': selected,
            'correct': correct_option.label if correct_option else '',
            'correct_text': correct_option.text if correct_option else '',
            'is_correct': is_correct,
            'explanation': question.explanation,
            'marks': question.marks,
        })

    percentage = round((score / total_marks * 100), 2) if total_marks > 0 else 0
    passed = percentage >= quiz.pass_percentage

    # Save attempt
    attempt = QuizAttempt.objects.create(
        student=request.user,
        quiz=quiz,
        score=score,
        total_marks=total_marks,
        percentage=percentage,
        passed=passed,
        answers=answers,
    )

    # Update lesson progress if passed
    if passed:
        enrollment = Enrollment.objects.filter(
            student=request.user,
            course=quiz.lesson.module.course
        ).first()
        if enrollment:
            progress, _ = Progress.objects.get_or_create(
                enrollment=enrollment,
                lesson=quiz.lesson,
            )
            progress.completed = True
            progress.completed_at = timezone.now()
            progress.save()

    # Notify
    Notification.objects.create(
        user=request.user,
        notification_type='quiz_result',
        title=f'Quiz Result: {"Passed ✅" if passed else "Not Passed ❌"}',
        message=f'You scored {score}/{total_marks} ({percentage}%) on "{quiz.lesson.title}"',
        link=f'/courses/{quiz.lesson.module.course.slug}/watch/?lesson={quiz.lesson.id}',
    )

    return JsonResponse({
        'status': 'ok',
        'score': score,
        'total_marks': total_marks,
        'percentage': percentage,
        'passed': passed,
        'pass_percentage': quiz.pass_percentage,
        'results': results,
    })
