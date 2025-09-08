# Add these to your myapp/urls.py

from django.urls import path
from . import views

app_name = 'myapp'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('posts/', views.AllPostsView.as_view(), name='all_posts'),
    path('post/create/', views.PostCreateView.as_view(), name='post_create'),
    path('post/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('category/<slug:slug>/', views.CategoryPostsView.as_view(), name='category_posts'),
    path('search/', views.SearchView.as_view(), name='search'),

    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),

    path('subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
    path('like/', views.like_post, name='like_post'),
    path('post/<slug:slug>/comment/', views.add_comment, name='add_comment'),

]