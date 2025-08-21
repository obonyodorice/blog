from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'members'

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.SimpleLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    # path('password-reset/', 
    #      auth_views.PasswordResetView.as_view(
    #          template_name='members/password_reset.html',
    #          email_template_name='members/password_reset_email.html'
    #      ), 
    #      name='password_reset'),
    # path('password-reset/done/', 
    #      auth_views.PasswordResetDoneView.as_view(
    #          template_name='members/password_reset_done.html'
    #      ), 
    #      name='password_reset_done'),
    # path('reset/<uidb64>/<token>/', 
    #      auth_views.PasswordResetConfirmView.as_view(
    #          template_name='members/password_reset_confirm.html'
    #      ), 
    #      name='password_reset_confirm'),
    # path('reset/done/', 
    #      auth_views.PasswordResetCompleteView.as_view(
    #          template_name='members/password_reset_complete.html'
    #      ), 
    #      name='password_reset_complete'),

    path('profile/<str:username>/', views.ProfileView.as_view(), name='profile'),
    path('edit-profile/', views.ProfileUpdateView.as_view(), name='edit_profile'),
    path('followers/<str:username>/', views.FollowersListView.as_view(), name='followers'),
    
    # AJAX URLs
    path('follow/', views.follow_unfollow_user, name='follow_unfollow'),
]