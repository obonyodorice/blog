from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import DetailView, UpdateView, ListView,CreateView
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import CustomUser, UserFollowing
from .forms import UserRegistrationForm, UserUpdateForm, ProfileUpdateForm
from myapp.models import Post, Category, Newsletter
from django.db.models import Sum

class SignUpView(CreateView):
    """User registration view"""
    form_class = UserRegistrationForm
    template_name = 'members/signup.html'
    success_url = reverse_lazy('members:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, 'Account created successfully! You can now log in.')
        return response

class ProfileView(DetailView):
    """User profile view"""
    model = CustomUser
    template_name = 'members/profile.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add statistics
        context['total_posts'] = Post.objects.filter(status='published').count()
        context['total_categories'] = Category.objects.count()
        context['total_views'] = Post.objects.aggregate(Sum('views'))['views__sum'] or 0
        context['total_subscribers'] = Newsletter.objects.filter(is_active=True).count()
        
        return context

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """Update user profile"""
    model = CustomUser
    form_class = ProfileUpdateForm
    template_name = 'members/edit_profile.html'
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

class FollowersListView(LoginRequiredMixin, ListView):
    """List user's followers"""
    template_name = 'members/followers.html'
    context_object_name = 'followers'
    paginate_by = 20
    
    def get_queryset(self):
        username = self.kwargs['username']
        user = get_object_or_404(CustomUser, username=username)
        return user.followers.select_related('user').order_by('-created_at')

@login_required
@require_POST
def follow_unfollow_user(request):
    """AJAX view to follow/unfollow users"""
    user_id = request.POST.get('user_id')
    user_to_follow = get_object_or_404(CustomUser, id=user_id)
    
    if user_to_follow == request.user:
        return JsonResponse({'error': 'Cannot follow yourself'}, status=400)
    
    following, created = UserFollowing.objects.get_or_create(
        user=request.user,
        following_user=user_to_follow
    )
    
    if not created:
        following.delete()
        is_following = False
        action = 'unfollowed'
    else:
        is_following = True
        action = 'followed'
    
    return JsonResponse({
        'is_following': is_following,
        'action': action,
        'followers_count': user_to_follow.followers.count()
    })