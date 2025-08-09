# Update your myapp/admin.py with these enhancements

from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Post, Comment, Like, Newsletter

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'is_featured', 'featured_badge', 'views', 'created_at')
    list_filter = ('status', 'is_featured', 'category', 'created_at')
    search_fields = ('title', 'content')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('status', 'is_featured')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    actions = ['make_featured', 'make_not_featured', 'reset_featured_posts']
    
    def featured_badge(self, obj):
        """Display a nice badge for featured posts"""
        if obj.is_featured:
            return format_html(
                '<span style="background: #ffc107; color: #212529; padding: 2px 6px; border-radius: 3px; font-size: 11px;">⭐ FEATURED</span>'
            )
        return format_html(
            '<span style="background: #6c757d; color: white; padding: 2px 6px; border-radius: 3px; font-size: 11px;">Regular</span>'
        )
    featured_badge.short_description = 'Featured Status'
    
    def make_featured(self, request, queryset):
        """Action to make selected posts featured"""
        count = queryset.update(is_featured=True)
        self.message_user(request, f'{count} posts marked as featured.')
    make_featured.short_description = "Mark selected posts as featured"
    
    def make_not_featured(self, request, queryset):
        """Action to remove featured status"""
        count = queryset.update(is_featured=False)
        self.message_user(request, f'{count} posts removed from featured.')
    make_not_featured.short_description = "Remove featured status from selected posts"
    
    def reset_featured_posts(self, request, queryset):
        """Reset all featured posts and feature top 3 by views"""
        # Reset all
        Post.objects.all().update(is_featured=False)
        
        # Feature top 3 by views
        top_posts = Post.objects.filter(status='published').order_by('-views')[:3]
        for post in top_posts:
            post.is_featured = True
            post.save()
        
        self.message_user(
            request, 
            f'Reset featured posts. Now featuring top 3 posts by views: {", ".join([p.title for p in top_posts])}'
        )
    reset_featured_posts.short_description = "Reset and auto-select top 3 featured posts"

# Keep your other admin classes as they are
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

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