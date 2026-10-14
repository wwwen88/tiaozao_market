from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views import View
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
import re

from .models import UserProfile
from .forms import ProfileForm


class RegisterView(View):
    """用户注册视图"""

    def get(self, request):
        state = request.GET.get('state', '')
        return render(request, 'register.html', {'state': state})

    def post(self, request):
        # 接收请求参数
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        check_password = request.POST.get('check_password', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()

        # 校验请求参数
        if not all([username, password, check_password, email, phone]):
            state = '所有字段均为必填项，请完整填写！'
            return render(request, 'register.html', {'state': state})

        if len(username) < 3 or len(username) > 20:
            state = '用户名长度需在3-20位之间！'
            return render(request, 'register.html', {'state': state})

        if password != check_password:
            state = '两次密码输入不一致，请重新输入！'
            return render(request, 'register.html', {'state': state})

        if len(password) < 8 or not re.match(r'^(?=.*[a-zA-Z])(?=.*\d).+$', password):
            state = '密码强度不足！需至少8位，包含字母和数字！'
            return render(request, 'register.html', {'state': state})

        if not re.match(r'^1[3-9]\d{9}$', phone):
            state = '手机号格式错误！请输入11位有效手机号！'
            return render(request, 'register.html', {'state': state})

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            state = '邮箱格式错误！请输入有效邮箱！'
            return render(request, 'register.html', {'state': state})

        if User.objects.filter(username=username).exists():
            state = '该用户名已被注册，请更换用户名！'
            return render(request, 'register.html', {'state': state})

        if User.objects.filter(email=email).exists():
            state = '该邮箱已被注册，请更换邮箱！'
            return render(request, 'register.html', {'state': state})

        try:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email
            )
            # 创建用户资料
            UserProfile.objects.get_or_create(user=user, defaults={'phone': phone, 'email': email})

            print(f"用户{username}注册成功，手机号：{phone}，邮箱：{email}")
            state = '注册成功！请前往登录页面登录！'
            return redirect(reverse('auth_app:login') + f'?state={state}')

        except Exception as e:
            print(f"注册失败：{str(e)}")
            state = '注册失败！服务器异常，请稍后重试！'
            return render(request, 'register.html', {'state': state})


class LoginView(View):
    """用户登录视图"""

    def get(self, request):
        state = request.GET.get('state', '')
        return render(request, 'login.html', {'state': state})

    def post(self, request):
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '').strip()
        remembered = request.POST.get('remembered')
        role = request.POST.get('role', 'user')

        if not username or not password:
            return render(request, 'login.html', {
                'account_errmsg': '用户名和密码不能为空！'
            })

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(request, 'login.html', {
                'account_errmsg': '用户名或密码错误，请重新输入！'
            })

        login(request, user)

        if remembered == 'on':
            request.session.set_expiry(60 * 60 * 24 * 14)
        else:
            request.session.set_expiry(0)

        # 根据角色跳转
        if role == 'admin' and user.is_superuser:
            response = redirect('/admin/')
        else:
            response = redirect(reverse('goods:index'))

        response.set_cookie('username', user.username, max_age=60 * 60 * 24 * 15)
        response.set_cookie('userid', user.id, max_age=60 * 60 * 24 * 15)

        return response


class LogoutView(View):
    """用户退出登录"""

    def get(self, request):
        logout(request)
        response = redirect(reverse('auth_app:login'))
        response.delete_cookie('username')
        response.delete_cookie('userid')
        return response


@login_required(login_url='/login/')
def profile_view(request):
    """个人资料页面"""
    profile, created = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            if form.cleaned_data.get('email'):
                request.user.email = form.cleaned_data['email']
                request.user.save()
            messages.success(request, '个人资料修改成功！')
            return redirect('auth_app:profile')
    else:
        form = ProfileForm(instance=profile)

    context = {
        'form': form,
        'profile': profile,
        'user': request.user
    }
    return render(request, 'profile.html', context)


# ===================== 密码管理功能 =====================

@login_required(login_url='/login/')
def change_password(request):
    """修改密码"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # 保持用户登录状态
            update_session_auth_hash(request, user)
            messages.success(request, '✅ 密码修改成功！请使用新密码登录')
            return redirect('auth_app:profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{error}')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'change_password.html', {'form': form})


def forgot_password(request):
    """忘记密码 - 重置密码"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()

        if not email:
            messages.error(request, '❌ 请输入邮箱地址')
            return render(request, 'forgot_password.html')

        try:
            user = User.objects.get(email=email)
            # 生成随机密码
            import random
            import string
            new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
            user.set_password(new_password)
            user.save()

            messages.success(request, f'✅ 密码已重置！新密码：{new_password}')
            messages.success(request, '💡 请使用新密码登录，建议登录后修改密码')
        except User.DoesNotExist:
            messages.error(request, '❌ 该邮箱未注册，请检查输入')
        except Exception as e:
            messages.error(request, f'❌ 重置密码失败：{str(e)}')

    return render(request, 'forgot_password.html')