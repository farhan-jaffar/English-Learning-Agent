from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Language, UserLanguage

class UserLanguageInline(admin.TabularInline):
    model = UserLanguage
    extra = 1
    fields = ('language', 'current_cefr_level', 'target_goal', 'is_primary', 'is_learning', 'is_native', 'total_practice_seconds', 'total_sessions_completed')
    readonly_fields = ('total_practice_seconds', 'total_sessions_completed')

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')

@admin.register(UserLanguage)
class UserLanguageAdmin(admin.ModelAdmin):
    list_display = ('user', 'language', 'current_cefr_level', 'is_primary', 'is_learning', 'is_native', 'total_sessions_completed', 'created_at')
    list_filter = ('current_cefr_level', 'is_primary', 'is_learning', 'is_native', 'language')
    search_fields = ('user__username', 'user__email', 'language__name', 'language__code')

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'cefr_level', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    inlines = [UserLanguageInline]
