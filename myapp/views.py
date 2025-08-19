from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.db.models import Q, Count, F
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.utils import timezone
from .models import Post, Category, Comment, Like, Newsletter
from .forms import PostForm, CommentForm, NewsletterForm
from django.db.models import Count, Sum

class HomeView(ListView):
    """Homepage with featured and recent posts"""
    model = Post
    template_name = 'myapp/../home.html'  # Updated template path
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
        
        # Statistics for the homepage
        context['total_posts'] = Post.objects.filter(status='published').count()
        context['total_categories'] = Category.objects.count()
        context['total_views'] = Post.objects.filter(status='published').aggregate(
            total=Sum('views')
        )['total'] or 0
        context['total_subscribers'] = Newsletter.objects.filter(is_active=True).count()
        
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

from django.views.decorators.http import require_POST

@require_POST
def add_comment(request, slug):
    """Add comment to post (supports guests)"""
    post = get_object_or_404(Post, slug=slug, status='published')
    form = CommentForm(request.POST, user=request.user)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post

        if request.user.is_authenticated:
            comment.author = request.user  # Logged-in user
        else:
            # Guest user – require name & email
            comment.guest_name = form.cleaned_data.get('guest_name')
            comment.guest_email = form.cleaned_data.get('guest_email')

        # Handle reply to comment
        parent_id = request.POST.get('parent_id')
        if parent_id:
            comment.parent = get_object_or_404(Comment, id=parent_id)

        comment.save()
        messages.success(request, 'Comment added successfully!')
    else:
        messages.error(request, 'Error adding comment. Please try again.')

    return redirect('myapp:post_detail', slug=slug)


from django.views.decorators.http import require_POST

@require_POST
def like_post(request):
    """AJAX view to like/unlike posts (supports guests via session)"""
    post_id = request.POST.get('post_id')
    post = get_object_or_404(Post, id=post_id, status='published')

    if request.user.is_authenticated:
        # Logged-in user
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
    else:
        # Guest user – use session
        liked_posts = request.session.get('liked_posts', [])
        if post_id in liked_posts:
            liked_posts.remove(post_id)
            liked = False
        else:
            liked_posts.append(post_id)
            liked = True
        request.session['liked_posts'] = liked_posts

    return JsonResponse({
        'liked': liked,
        'likes_count': post.likes.count() + len(request.session.get('liked_posts', []))
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
class AllPostsView(ListView):
    """Archive/All posts view with filtering and different view modes"""
    model = Post
    template_name = 'myapp/all_posts.html'
    context_object_name = 'posts'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Post.objects.filter(status='published').select_related('author', 'category')
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Sort options
        sort = self.request.GET.get('sort', 'latest')
        if sort == 'latest':
            queryset = queryset.order_by('-published_at')
        elif sort == 'oldest':
            queryset = queryset.order_by('published_at')
        elif sort == 'popular':
            queryset = queryset.annotate(
                comment_count=Count('comments')
            ).order_by('-comment_count')
        elif sort == 'views':
            queryset = queryset.order_by('-views')
        elif sort == 'title':
            queryset = queryset.order_by('title')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Categories for filter dropdown
        context['categories'] = Category.objects.annotate(
            post_count=Count('post', filter=Q(post__status='published'))
        ).filter(post_count__gt=0).order_by('name')
        
        # Statistics
        context['total_posts'] = Post.objects.filter(status='published').count()
        context['total_views'] = Post.objects.filter(status='published').aggregate(
            total=Sum('views')
        )['total'] or 0
        context['total_categories'] = Category.objects.count()
        
        # This month's posts
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        context['this_month_posts'] = Post.objects.filter(
            status='published',
            published_at__gte=start_of_month
        ).count()
        
        return context

# Custom 404 view (optional - Django handles this automatically if DEBUG=False)
def custom_404_view(request, exception=None):
    """Custom 404 error page"""
    return render(request, '404.html', status=404)

@require_POST 
def ajax_subscribe_newsletter(request):
    """AJAX newsletter subscription"""
    form = NewsletterForm(request.POST)
    
    if form.is_valid():
        email = form.cleaned_data['email']
        newsletter, created = Newsletter.objects.get_or_create(email=email)
        
        if created:
            return JsonResponse({
                'success': True, 
                'message': 'Successfully subscribed to newsletter!'
            })
        else:
            return JsonResponse({
                'success': True, 
                'message': 'You are already subscribed!'
            })
    else:
        return JsonResponse({
            'success': False, 
            'message': 'Please enter a valid email address.'
        })

def about_view(request):
    """About page view"""
    context = {
        'total_posts': Post.objects.filter(status='published').count(),
        'total_categories': Category.objects.count(),
        'total_views': Post.objects.filter(status='published').aggregate(
            total=Sum('views')
        )['total'] or 0,
        'total_subscribers': Newsletter.objects.filter(is_active=True).count(),
        'this_month_posts': Post.objects.filter(
            status='published',
            published_at__gte=timezone.now().replace(day=1)
        ).count(),
    }
    return render(request, 'myapp/about.html', context)

def contact_view(request):
    """Contact page view"""
    if request.method == 'POST':
        # Handle contact form submission
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        if name and email and subject and message:
            # Here you would typically save to a Contact model or send an email
            # For now, we'll just show a success message
            messages.success(request, 'Thank you for your message! I\'ll get back to you soon.')
            return redirect('myapp:contact')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return render(request, 'myapp/contact.html')
