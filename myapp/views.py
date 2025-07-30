from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q, Count, F
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.utils import timezone
from taggit.models import Tag
from .models import Post, Category, Comment, Like, Newsletter
from .forms import PostForm, CommentForm, NewsletterForm

class HomeView(ListView):
    """Homepage with featured and recent posts"""
    model = Post
    template_name = 'myapp/home.html'
    context_object_name = 'posts'
    paginate_by = 6
    
    def get_queryset(self):
        return Post.objects.filter(status='published').select_related('author', 'category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Featured posts
        context['featured_posts'] = Post.objects.filter(
            status='published', 
            is_featured=True
        ).select_related('author', 'category')[:3]
        
        # Popular posts (by views)
        context['popular_posts'] = Post.objects.filter(
            status='published'
        ).order_by('-views')[:5]
        
        # Recent posts
        context['recent_posts'] = Post.objects.filter(
            status='published'
        ).order_by('-published_at')[:5]
        
        # Categories with post counts
        context['categories'] = Category.objects.annotate(
            post_count=Count('post', filter=Q(post__status='published'))
        ).filter(post_count__gt=0)
        
        # Popular tags
        context['popular_tags'] = Tag.objects.most_common()[:10]
        
        return context

class PostDetailView(DetailView):
    """Individual post detail view"""
    model = Post
    template_name = 'myapp/post_detail.html'
    context_object_name = 'post'
    
    def get_queryset(self):
        return Post.objects.filter(status='published').select_related('author', 'category')
    
    def get_object(self):
        post = super().get_object()
        # Increment views
        post.increment_views()
        return post
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        
        # Comments
        context['comments'] = post.comments.filter(
            parent=None, 
            is_approved=True
        ).select_related('author').prefetch_related('replies')
        
        # Comment form
        context['comment_form'] = CommentForm()
        
        # Related posts
        context['related_posts'] = Post.objects.filter(
            category=post.category,
            status='published'
        ).exclude(id=post.id)[:4]
        
        # Check if user liked the post
        if self.request.user.is_authenticated:
            context['user_liked'] = Like.objects.filter(
                user=self.request.user,
                post=post
            ).exists()
        
        # Like count
        context['likes_count'] = post.likes.count()
        
        return context

class PostCreateView(LoginRequiredMixin, CreateView):
    """Create new blog post"""
    model = Post
    form_class = PostForm
    template_name = 'myapp/post_form.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Post created successfully!')
        return super().form_valid(form)

class PostUpdateView(LoginRequiredMixin, UpdateView):
    """Update existing post"""
    model = Post
    form_class = PostForm
    template_name = 'myapp/post_form.html'
    
    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Post updated successfully!')
        return super().form_valid(form)

class CategoryPostsView(ListView):
    """Posts by category"""
    model = Post
    template_name = 'myapp/category_posts.html'
    context_object_name = 'posts'
    paginate_by = 9
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return Post.objects.filter(
            category=self.category,
            status='published'
        ).select_related('author')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context

class SearchView(ListView):
    """Search posts"""
    model = Post
    template_name = 'myapp/search_results.html'
    context_object_name = 'posts'
    paginate_by = 9
    
    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return Post.objects.filter(
                Q(title__icontains=query) | 
                Q(content__icontains=query) |
                Q(tags__icontains=query),
                status='published'
            ).distinct().select_related('author', 'category')
        return Post.objects.none()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        return context

@login_required
@require_POST
def add_comment(request, slug):
    """Add comment to post"""
    post = get_object_or_404(Post, slug=slug, status='published')
    form = CommentForm(request.POST)
    
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        
        # Handle reply to comment
        parent_id = request.POST.get('parent_id')
        if parent_id:
            comment.parent = get_object_or_404(Comment, id=parent_id)
        
        comment.save()
        messages.success(request, 'Comment added successfully!')
    else:
        messages.error(request, 'Error adding comment. Please try again.')
    
    return redirect('myapp:post_detail', slug=slug)

@login_required
@require_POST
def like_post(request):
    """AJAX view to like/unlike posts"""
    post_id = request.POST.get('post_id')
    post = get_object_or_404(Post, id=post_id, status='published')
    
    like, created = Like.objects.get_or_create(
        user=request.user,
        post=post
    )
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'likes_count': post.likes.count()
    })

def subscribe_newsletter(request):
    """Newsletter subscription"""
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            newsletter, created = Newsletter.objects.get_or_create(email=email)
            
            if created:
                messages.success(request, 'Successfully subscribed to newsletter!')
            else:
                messages.info(request, 'You are already subscribed!')
        else:
            messages.error(request, 'Please enter a valid email address.')
    
    return redirect('myapp:home')