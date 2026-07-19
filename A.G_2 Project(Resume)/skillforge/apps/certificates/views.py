import io
import os
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponse, FileResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings

from .models import Certificate
from apps.courses.models import Enrollment
from apps.notifications.models import Notification


def generate_certificate_pdf(certificate):
    """Generate a professional PDF certificate using ReportLab."""
    try:
        from reportlab.lib.pagesizes import landscape, A4
        from reportlab.lib.units import inch
        from reportlab.lib.colors import HexColor
        from reportlab.pdfgen import canvas

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=landscape(A4))
        width, height = landscape(A4)

        # Background
        c.setFillColor(HexColor('#F8FAFC'))
        c.rect(0, 0, width, height, fill=1, stroke=0)

        # Border
        c.setStrokeColor(HexColor('#2563EB'))
        c.setLineWidth(3)
        c.rect(30, 30, width - 60, height - 60, fill=0, stroke=1)

        # Inner border
        c.setStrokeColor(HexColor('#14B8A6'))
        c.setLineWidth(1)
        c.rect(40, 40, width - 80, height - 80, fill=0, stroke=1)

        # Logo text
        c.setFillColor(HexColor('#2563EB'))
        c.setFont('Helvetica-Bold', 28)
        c.drawCentredString(width / 2, height - 100, '⚡ Skill Forge')

        # Title
        c.setFillColor(HexColor('#0F172A'))
        c.setFont('Helvetica-Bold', 36)
        c.drawCentredString(width / 2, height - 160, 'Certificate of Completion')

        # Divider
        c.setStrokeColor(HexColor('#14B8A6'))
        c.setLineWidth(2)
        c.line(width / 2 - 100, height - 175, width / 2 + 100, height - 175)

        # Presented to
        c.setFillColor(HexColor('#64748B'))
        c.setFont('Helvetica', 16)
        c.drawCentredString(width / 2, height - 210, 'This is proudly presented to')

        # Student name
        student_name = certificate.enrollment.student.get_full_name()
        c.setFillColor(HexColor('#0F172A'))
        c.setFont('Helvetica-Bold', 32)
        c.drawCentredString(width / 2, height - 255, student_name)

        # Course completion text
        c.setFillColor(HexColor('#64748B'))
        c.setFont('Helvetica', 14)
        c.drawCentredString(width / 2, height - 290, 'for successfully completing the course')

        # Course title
        course_title = certificate.enrollment.course.title
        c.setFillColor(HexColor('#2563EB'))
        c.setFont('Helvetica-Bold', 22)
        # Wrap long titles
        if len(course_title) > 50:
            c.drawCentredString(width / 2, height - 325, course_title[:50])
            c.drawCentredString(width / 2, height - 350, course_title[50:])
        else:
            c.drawCentredString(width / 2, height - 330, course_title)

        # Date and Certificate ID
        c.setFillColor(HexColor('#64748B'))
        c.setFont('Helvetica', 12)
        date_str = certificate.issued_at.strftime('%B %d, %Y')
        c.drawCentredString(width / 2, 100, f'Date: {date_str}')
        c.drawCentredString(width / 2, 80, f'Certificate ID: {certificate.certificate_id}')

        # Instructor signature line
        c.setStrokeColor(HexColor('#CBD5E1'))
        c.line(width / 2 - 80, 130, width / 2 + 80, 130)
        c.setFont('Helvetica', 10)
        instructor_name = certificate.enrollment.course.instructor.get_full_name()
        c.drawCentredString(width / 2, 115, f'Instructor: {instructor_name}')

        c.save()
        buffer.seek(0)
        return buffer

    except ImportError:
        return None


@login_required
def generate_certificate_view(request, enrollment_id):
    """Generate or retrieve certificate for a completed enrollment."""
    enrollment = get_object_or_404(
        Enrollment,
        id=enrollment_id,
        student=request.user,
        completed=True
    )

    # Get or create certificate
    certificate, created = Certificate.objects.get_or_create(enrollment=enrollment)

    if created or not certificate.file:
        pdf_buffer = generate_certificate_pdf(certificate)
        if pdf_buffer:
            from django.core.files.base import ContentFile
            filename = f'certificate_{certificate.certificate_id}.pdf'
            certificate.file.save(filename, ContentFile(pdf_buffer.read()), save=True)

            # Notify
            Notification.objects.create(
                user=request.user,
                notification_type='certificate',
                title='Certificate Issued! 🎓',
                message=f'Your certificate for "{enrollment.course.title}" is ready.',
                link=f'/certificates/{certificate.id}/download/',
            )

    return JsonResponse({
        'status': 'ok',
        'certificate': {
            'id': str(certificate.id),
            'certificate_id': certificate.certificate_id,
            'download_url': f'/certificates/{certificate.id}/download/',
            'issued_at': certificate.issued_at.isoformat(),
        }
    })


@login_required
def download_certificate_view(request, certificate_id):
    """Download certificate PDF."""
    certificate = get_object_or_404(
        Certificate,
        id=certificate_id,
        enrollment__student=request.user
    )

    if certificate.file:
        return FileResponse(
            certificate.file.open('rb'),
            content_type='application/pdf',
            as_attachment=True,
            filename=f'SkillForge_Certificate_{certificate.certificate_id}.pdf'
        )

    return JsonResponse({'status': 'error', 'message': 'Certificate file not found.'}, status=404)


def verify_certificate_view(request, certificate_id_str):
    """Public verification of a certificate."""
    try:
        certificate = Certificate.objects.get(certificate_id=certificate_id_str)
        return JsonResponse({
            'valid': True,
            'student': certificate.enrollment.student.get_full_name(),
            'course': certificate.enrollment.course.title,
            'issued_at': certificate.issued_at.isoformat(),
            'certificate_id': certificate.certificate_id,
        })
    except Certificate.DoesNotExist:
        return JsonResponse({'valid': False, 'message': 'Certificate not found.'}, status=404)
