from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _


class UserProfile(models.Model):
    """扩展用户资料表，和内置User一对一关联"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    nickname = models.CharField(_('昵称'), max_length=20, blank=True, null=True)
    avatar = models.ImageField(
        _('头像'),
        upload_to='user_avatar/',
        default='user_avatar/default.png',
        blank=True,
        null=True
    )
    phone = models.CharField(_('手机号'), max_length=11, blank=True, null=True, unique=True)
    GENDER_CHOICES = (
        (0, _('未知')),
        (1, _('男')),
        (2, _('女')),
    )
    gender = models.IntegerField(_('性别'), choices=GENDER_CHOICES, default=0)
    email = models.EmailField(_('邮箱'), blank=True, null=True)
    updated_time = models.DateTimeField(_('更新时间'), auto_now=True)

    class Meta:
        verbose_name = _('用户资料')
        verbose_name_plural = _('用户资料')

    def __str__(self):
        return f"{self.user.username}的资料"