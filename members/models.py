from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from PIL import Image
import os

class CustomUser(AbstractUser):
    """Extended user model with additional profile fields"""
    email = models.EmailField(unique=True)
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        default='profile_pics/default.jpg',
        blank=True
    )
    website = models.URLField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    # is_verified = models.BooleanField(default=False)
    # date_updated = models.DateTimeField(auto_now=True)
    
    # USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS = ['username']
    
    # def __str__(self):
    #     return self.username
    
    # def get_absolute_url(self):
    #     return reverse('members:profile', kwargs={'username': self.username})
    
    # def save(self, *args, **kwargs):
    #     super().save(*args, **kwargs)
    #     if self.profile_picture:
    #         img = Image.open(self.profile_picture.path)
    #         if img.height > 300 or img.width > 300:
    #             output_size = (300, 300)
    #             img.thumbnail(output_size)
    #             img.save(self.profile_picture.path)

class UserFollowing(models.Model):
    """Model for user following system"""
    user = models.ForeignKey(
        CustomUser, 
        related_name='following', 
        on_delete=models.CASCADE
    )
    following_user = models.ForeignKey(
        CustomUser, 
        related_name='followers', 
        on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'following_user')
        
    def __str__(self):
        return f'{self.user} follows {self.following_user}'