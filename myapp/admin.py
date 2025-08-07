from django.contrib import admin
from .models import Category, Post, Comment, Like, Newsletter

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'is_featured', 'views', 'created_at')
    list_filter = ('status', 'is_featured', 'category', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('status', 'is_featured')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('author__username', 'content')
    list_editable = ('is_approved',)
    ordering = ('-created_at',)

@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'subscribed_at')
    list_filter = ('is_active', 'subscribed_at')
    search_fields = ('email',)
    list_editable = ('is_active',)

admin.site.register(Like)