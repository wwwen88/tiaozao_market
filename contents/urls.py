from django.urls import path
from . import views

app_name = 'contents'

urlpatterns = [
    path("base/", views.IndexView.as_view(), name='base'),
]