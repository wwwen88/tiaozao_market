from django import forms
from .models import ProductReview


class ReviewForm(forms.ModelForm):
    """商品评价表单"""

    class Meta:
        model = ProductReview
        fields = ['rating', 'content', 'is_anonymous']
        widgets = {
            'content': forms.Textarea(attrs={
                'rows': 5,
                'placeholder': '请分享您对商品的真实体验...',
                'class': 'form-control'
            }),
            'rating': forms.RadioSelect(attrs={
                'class': 'rating-radio'
            }),
            'is_anonymous': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'content': '评价内容',
            'is_anonymous': '匿名评价'
        }