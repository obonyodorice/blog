from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'members'

urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.SimpleLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('profile/<str:username>/', views.ProfileView.as_view(), name='profile'),
    path('edit-profile/', views.ProfileUpdateView.as_view(), name='edit_profile'),
    path('followers/<str:username>/', views.FollowersListView.as_view(), name='followers'),

    path('follow/', views.follow_unfollow_user, name='follow_unfollow'),
]