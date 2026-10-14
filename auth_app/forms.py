from django import forms
from .models import UserProfile
import re


class ProfileForm(forms.ModelForm):
    """个人资料修改表单"""
    phone = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入11位手机号'}),
    )

    class Meta:
        model = UserProfile
        fields = ['nickname', 'avatar', 'phone', 'gender', 'email']
        widgets = {
            'nickname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '请输入昵称（不超过20字）'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '请输入邮箱'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control-file'}),
        }

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            if not re.match(r'^1[3-9]\d{9}$', phone):
                raise forms.ValidationError('请输入正确的11位手机号')
        return phone