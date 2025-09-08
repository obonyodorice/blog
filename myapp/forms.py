from django import forms
from .models import Post, Comment, Newsletter

class PostForm(forms.ModelForm):
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
    # Add fields for guest comments
    guest_name = forms.CharField(
        max_length=100, 
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Name'
        })
    )
    guest_email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Your Email'
        })
    )

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Make guest fields required if user is not authenticated
        if not self.user or not self.user.is_authenticated:
            self.fields['guest_name'].required = True
            self.fields['guest_email'].required = True

    class Meta:
        model = Comment
        fields = ['content', 'guest_name', 'guest_email']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Write your comment here...'
            })
        }

    def clean(self):
        cleaned_data = super().clean()
        user = self.user
        guest_name = cleaned_data.get('guest_name')
        guest_email = cleaned_data.get('guest_email')
        
        # If user is not authenticated, require guest fields
        if not user or not user.is_authenticated:
            if not guest_name:
                raise forms.ValidationError("Name is required for guest comments.")
            if not guest_email:
                raise forms.ValidationError("Email is required for guest comments.")
        
        return cleaned_data


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