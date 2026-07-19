from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'username', 'role', 'is_email_verified', 'is_active', 'date_joined')
    list_filter = ('role', 'is_email_verified', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    inlines = [ProfileInline]

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Skill Forge', {'fields': ('role', 'is_email_verified', 'otp_code', 'otp_created_at')}),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'headline', 'location', 'created_at')
    search_fields = ('user__email', 'headline')
