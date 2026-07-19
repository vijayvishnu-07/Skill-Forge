import random
import logging
from datetime import timedelta

from django import forms
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect

from .models import User, Profile

logger = logging.getLogger(__name__)


# ─── Forms ───────────────────────────────────────────────────────────

class RegisterForm(forms.Form):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)
    email = forms.EmailField()
    password = forms.CharField(min_length=8, widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    role = forms.ChoiceField(choices=[('student', 'Student'), ('instructor', 'Instructor')])

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('confirm_password'):
            raise forms.ValidationError("Passwords do not match.")
        if User.objects.filter(email=cleaned.get('email')).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return cleaned


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)


class OTPForm(forms.Form):
    otp = forms.CharField(max_length=6, min_length=6)


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField()


class ResetPasswordForm(forms.Form):
    password = forms.CharField(min_length=8, widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('confirm_password'):
            raise forms.ValidationError("Passwords do not match.")
        return cleaned


class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=50)
    last_name = forms.CharField(max_length=50)

    class Meta:
        model = Profile
        fields = ['avatar', 'headline', 'bio', 'location', 'website']


# ─── Helper ─────────────────────────────────────────────────────────

def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(user, otp):
    try:
        send_mail(
            subject='Skill Forge — Verify Your Email',
            message=f'Your verification code is: {otp}\n\nThis code expires in 10 minutes.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as e:
        logger.error(f"Failed to send OTP email to {user.email}: {e}")


# ─── Views ───────────────────────────────────────────────────────────

@csrf_protect
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = User.objects.create_user(
                username=data['email'].split('@')[0] + str(random.randint(100, 999)),
                email=data['email'],
                password=data['password'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                role=data['role'],
                is_active=True,
                is_email_verified=False,
            )
            otp = generate_otp()
            user.otp_code = otp
            user.otp_created_at = timezone.now()
            user.save()
            send_otp_email(user, otp)

            request.session['verify_email'] = user.email
            messages.success(request, 'Account created! Check your email for the verification code.')
            return redirect('verify_otp')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@csrf_protect
def verify_otp_view(request):
    email = request.session.get('verify_email')
    if not email:
        messages.error(request, 'No email to verify.')
        return redirect('register')

    if request.method == 'POST':
        form = OTPForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            try:
                user = User.objects.get(email=email)
                if user.otp_code == otp:
                    # Check expiry (10 minutes)
                    if user.otp_created_at and timezone.now() - user.otp_created_at < timedelta(minutes=10):
                        user.is_email_verified = True
                        user.otp_code = None
                        user.otp_created_at = None
                        user.save()
                        del request.session['verify_email']
                        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                        messages.success(request, 'Email verified! Welcome to Skill Forge.')
                        return redirect('dashboard')
                    else:
                        messages.error(request, 'OTP has expired. Please request a new one.')
                else:
                    messages.error(request, 'Invalid OTP. Please try again.')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
    else:
        form = OTPForm()

    return render(request, 'accounts/verify_otp.html', {'form': form, 'email': email})


def resend_otp_view(request):
    email = request.session.get('verify_email')
    if email:
        try:
            user = User.objects.get(email=email)
            otp = generate_otp()
            user.otp_code = otp
            user.otp_created_at = timezone.now()
            user.save()
            send_otp_email(user, otp)
            messages.success(request, 'New verification code sent!')
        except User.DoesNotExist:
            messages.error(request, 'User not found.')
    return redirect('verify_otp')


@csrf_protect
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if not user.is_email_verified:
                    request.session['verify_email'] = user.email
                    otp = generate_otp()
                    user.otp_code = otp
                    user.otp_created_at = timezone.now()
                    user.save()
                    send_otp_email(user, otp)
                    messages.warning(request, 'Please verify your email first.')
                    return redirect('verify_otp')
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f'Welcome back, {user.first_name}!')
                next_url = request.GET.get('next', 'dashboard')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid email or password.')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('landing')


@csrf_protect
def forgot_password_view(request):
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                otp = generate_otp()
                user.otp_code = otp
                user.otp_created_at = timezone.now()
                user.save()
                send_otp_email(user, otp)
                request.session['reset_email'] = email
                messages.success(request, 'Password reset code sent to your email.')
                return redirect('reset_password')
            except User.DoesNotExist:
                messages.error(request, 'No account found with this email.')
    else:
        form = ForgotPasswordForm()

    return render(request, 'accounts/forgot_password.html', {'form': form})


@csrf_protect
def reset_password_view(request):
    email = request.session.get('reset_email')
    if not email:
        return redirect('forgot_password')

    if request.method == 'POST':
        otp = request.POST.get('otp', '')
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
        elif len(password) < 8:
            messages.error(request, 'Password must be at least 8 characters.')
        else:
            try:
                user = User.objects.get(email=email)
                if user.otp_code == otp and user.otp_created_at and timezone.now() - user.otp_created_at < timedelta(minutes=10):
                    user.set_password(password)
                    user.otp_code = None
                    user.otp_created_at = None
                    user.save()
                    del request.session['reset_email']
                    messages.success(request, 'Password reset successful! Please log in.')
                    return redirect('login')
                else:
                    messages.error(request, 'Invalid or expired code.')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')

    return render(request, 'accounts/reset_password.html', {'email': email})


@login_required
def profile_view(request):
    profile = request.user.profile

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.save()
            form.save()

            # Handle skills (comma-separated)
            skills_str = request.POST.get('skills', '')
            profile.skills = [s.strip() for s in skills_str.split(',') if s.strip()]

            # Handle social links
            profile.social_links = {
                'linkedin': request.POST.get('linkedin', ''),
                'twitter': request.POST.get('twitter', ''),
                'github': request.POST.get('github', ''),
                'website': request.POST.get('website_url', ''),
            }
            profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileForm(instance=profile, initial={
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        })

    # Get user stats
    enrollments = request.user.enrollments.select_related('course')
    created_courses = request.user.created_courses.all() if request.user.is_instructor else []
    certificates = []
    for enrollment in enrollments.filter(completed=True):
        if hasattr(enrollment, 'certificate'):
            certificates.append(enrollment.certificate)

    context = {
        'form': form,
        'profile': profile,
        'enrollments': enrollments,
        'created_courses': created_courses,
        'certificates': certificates,
    }
    return render(request, 'accounts/profile.html', context)
