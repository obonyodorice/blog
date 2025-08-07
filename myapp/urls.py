from django.urls import path
from . import views

app_name = 'myapp'

urlpatterns = [
    # Home and main pages
    path('', views.HomeView.as_view(), name='home'),
    path('search/', views.SearchView.as_view(), name='search'),
    
    # Post URLs
    path('post/create/', views.PostCreateView.as_view(), name='post_create'),
    path('post/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('post/<slug:slug>/edit/', views.PostUpdateView.as_view(), name='post_edit'),
    
    # Category URLs
    path('category/<slug:slug>/', views.CategoryPostsView.as_view(), name='category_posts'),
    
    # AJAX URLs
    path('like/', views.like_post, name='like_post'),
    path('comment/<slug:slug>/', views.add_comment, name='add_comment'),
    path('newsletter/subscribe/', views.subscribe_newsletter, name='subscribe_newsletter'),
]