from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from datetime import datetime, date
from django_ckeditor_5.fields import CKEditor5Field  

# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        #return reverse("model_detail", kwargs={"pk": self.pk})
        return reverse('home')

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='myapp_profile')
    bio = models.TextField()
    profile_pic = models.ImageField(null=True, blank=True, upload_to='images/profile')
    website_url = models.CharField(max_length=255, null=True, blank=True)
    facebook_url = models.CharField(max_length=255, null=True, blank=True)
    x_url = models.CharField(max_length=255, null=True, blank=True)
    instagram_url = models.CharField(max_length=255, null=True, blank=True)
    pinterest_url = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return str(self.user)
    
    def get_absolute_url(self):
        #return reverse("model_detail", kwargs={"pk": self.pk})
        return reverse('home')




class Post(models.Model):
    title = models.CharField(max_length=255)
    header_image = models.ImageField(null=True, blank=True, upload_to='images/')
    title_tag = models.CharField(max_length=255)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = CKEditor5Field('Text', config_name='default')
    #body = models.TextField()
    post_date = models.DateField(auto_now_add=True)
    category = models.CharField(max_length=255, default='uncategorized')
    snippet = models.CharField(max_length=255)
    likes = models.ManyToManyField(User, related_name='blog_posts')


    def total_likes(self):
        return self.likes.count()

    def __str__(self):
        return self.title + '|' + str(self.author)
    
    def get_absolute_url(self):
        #return reverse('article-detail', args=(str(self.id)))
        return reverse('home')
    

class Comment(models.Model):
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    body = models.TextField()
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return '%s - %s' % (self.post.title, self.name)
    


    