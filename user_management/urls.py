from django.urls import path

from user_management.views import login_view, logout_view, signin_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('signin/', signin_view, name='signin'),
]