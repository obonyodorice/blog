from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserFollowing

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Profile Info', {
            'fields': ('bio', 'birth_date', 'profile_picture', 'website', 'location')
        }),
    )

@admin.register(UserFollowing)
class UserFollowingAdmin(admin.ModelAdmin):
    list_display = ('user', 'following_user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'following_user__username')
    ordering = ('-created_at',)