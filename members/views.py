from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib import messages
from django.views.generic import DetailView, UpdateView, ListView,CreateView
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import CustomUser, UserFollowing
from .forms import UserRegistrationForm, ProfileUpdateForm
from myapp.models import Post, Category, Newsletter
from django.db.models import Sum

class SignUpView(UserPassesTestMixin, CreateView):
    model = CustomUser
    form_class = UserRegistrationForm
    template_name = 'members/signup.html'
    success_url = reverse_lazy('members:login')

    def test_func(self):
        return self.request.user.is_superuser

    def handle_no_permission(self):
        messages.error(self.request, "You don’t have permission to access signup.")
        return redirect("myapp:home")
    
class SimpleLoginView(LoginView):
    template_name = "members/login.html"
    success_url = reverse_lazy('myapp:home')

class ProfileView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = CustomUser
    template_name = 'members/profile.html'
    context_object_name = 'profile_user'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object() 

        user_posts = Post.objects.filter(author=user, status='published')
        context['total_posts'] = user_posts.count()
        context['total_categories'] = Category.objects.filter(post__author=user).distinct().count()
        context['total_views'] = user_posts.aggregate(Sum('views'))['views__sum'] or 0
        context['total_subscribers'] = Newsletter.objects.filter(is_active=True).count()
        context['average_views'] = (
            context['total_views'] / context['total_posts']
            if context['total_posts'] > 0 else 0
        )

        return context

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = CustomUser
    form_class = ProfileUpdateForm
    template_name = 'members/edit_profile.html'

    def test_func(self):
        return self.request.user.is_superuser or self.request.user.is_staff
    
    def get_object(self):
        return self.request.user
    
    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("members:profile", kwargs={"username": self.object.username})
    
class FollowersListView(LoginRequiredMixin, ListView):
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