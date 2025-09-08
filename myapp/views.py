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
    model = Post
    template_name = 'myapp/../home.html'
    context_object_name = 'posts'
    paginate_by = 6
    
    def get_queryset(self):
        return Post.objects.filter(status='published').select_related('author', 'category')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['featured_posts'] = Post.objects.filter(
            status='published', 
            is_featured=True
        ).select_related('author', 'category')[:3]

        context['popular_posts'] = Post.objects.filter(
            status='published'
        ).order_by('-views')[:5]

        context['recent_posts'] = Post.objects.filter(
            status='published'
        ).order_by('-published_at')[:5]

        context['categories'] = Category.objects.annotate(
            post_count=Count('post', filter=Q(post__status='published'))
        ).filter(post_count__gt=0)
        
        context['total_posts'] = Post.objects.filter(status='published').count()
        context['total_categories'] = Category.objects.count()
        context['total_views'] = Post.objects.filter(status='published').aggregate(
            total=Sum('views')
        )['total'] or 0
        context['total_subscribers'] = Newsletter.objects.filter(is_active=True).count()
        
        return context

class PostDetailView(DetailView):
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

        context['comments'] = post.comments.filter(
            parent=None, 
            is_approved=True
        ).select_related('author').prefetch_related('replies')
        
        context['comment_form'] = CommentForm(user=self.request.user)

        context['related_posts'] = Post.objects.filter(
            category=post.category,
            status='published'
        ).exclude(id=post.id)[:4]

        if self.request.user.is_authenticated:
            context['user_liked'] = Like.objects.filter(
                user=self.request.user,
                post=post
            ).exists()

        context['likes_count'] = post.likes.count()
        
        return context

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'myapp/post_form.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, 'Post created successfully!')
        return super().form_valid(form)

class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'myapp/post_form.html'
    
    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)
    
    def form_valid(self, form):
        messages.success(self.request, 'Post updated successfully!')
        return super().form_valid(form)

class CategoryPostsView(ListView):
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
    
class AllPostsView(ListView):
    model = Post
    template_name = 'myapp/all_posts.html'
    context_object_name = 'posts'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Post.objects.filter(status='published').select_related('author', 'category')
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)

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

        context['categories'] = Category.objects.annotate(
            post_count=Count('post', filter=Q(post__status='published'))
        ).filter(post_count__gt=0).order_by('name')
        
        context['total_posts'] = Post.objects.filter(status='published').count()
        context['total_views'] = Post.objects.filter(status='published').aggregate(
            total=Sum('views')
        )['total'] or 0
        context['total_categories'] = Category.objects.count()
 
        now = timezone.now()
        start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        context['this_month_posts'] = Post.objects.filter(
            status='published',
            published_at__gte=start_of_month
        ).count()
        
        return context

class SearchView(ListView):
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

@require_POST
def add_comment(request, slug):
    post = get_object_or_404(Post, slug=slug, status='published')
    
    # Create form with POST data and current user
    form = CommentForm(request.POST, user=request.user)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post

        # Handle authenticated vs guest users
        if request.user.is_authenticated:
            comment.author = request.user
            # Clear guest fields for authenticated users
            comment.guest_name = None
            comment.guest_email = None
        else:
            # For guest users, get the data from the cleaned form
            comment.guest_name = form.cleaned_data.get('guest_name')
            comment.guest_email = form.cleaned_data.get('guest_email')
            comment.author = None

        # Handle reply to another comment
        parent_id = request.POST.get('parent_id')
        if parent_id:
            try:
                parent_comment = get_object_or_404(Comment, id=parent_id, post=post)
                comment.parent = parent_comment
            except (ValueError, Comment.DoesNotExist):
                messages.error(request, 'Invalid parent comment.')
                return redirect('myapp:post_detail', slug=slug)

        comment.save()
        
        # Success message varies based on user type
        if request.user.is_authenticated:
            messages.success(request, 'Comment added successfully!')
        else:
            messages.success(request, 'Comment added successfully! It may take some time to appear.')
    else:
        # Handle form errors
        error_messages = []
        for field, errors in form.errors.items():
            for error in errors:
                error_messages.append(f"{field.replace('_', ' ').title()}: {error}")
        
        if error_messages:
            messages.error(request, 'Please correct the following errors: ' + '; '.join(error_messages))
        else:
            messages.error(request, 'Error adding comment. Please try again.')

    return redirect('myapp:post_detail', slug=slug)

@require_POST
def like_post(request):
    post_id = request.POST.get('post_id')
    post = get_object_or_404(Post, id=post_id, status='published')

    if request.user.is_authenticated:
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
    else:
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

def custom_404_view(request, exception=None):
    return render(request, '404.html', status=404)

def about_view(request):
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
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        if name and email and subject and message:
            messages.success(request, 'Thank you for your message! I\'ll get back to you soon.')
            return redirect('myapp:contact')
        else:
            messages.error(request, 'Please fill in all required fields.')
    
    return render(request, 'myapp/contact.html')