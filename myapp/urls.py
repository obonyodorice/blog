from django import forms
from .models import Post, Comment, Newsletter

class PostForm(forms.ModelForm):
    """Form for creating/editing posts"""
    class Meta:
        model = Post
        fields = [
            'title', 'category', 'content', 'excerpt', 
            'featured_image', 'tags', 'status', 'is_featured'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'excerpt': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter tags separated by commas'
            }),
        }

class CommentForm(forms.ModelForm):
    """Form for adding comments"""
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Write your comment here...'
            })
        }

class NewsletterForm(forms.ModelForm):
    """Newsletter subscription form"""
    class Meta:
        model = Newsletter
        fields = ['email']
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter your email'
            })
        }