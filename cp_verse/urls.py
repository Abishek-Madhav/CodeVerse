from django.contrib import admin
from django.urls import path
from app1 import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('leetcode/', views.leetcode_view, name='leetcode'),
    path('codechef/', views.codechef_view, name='codechef'),
    path('codeforces/', views.codeforces_view, name='codeforces'),
    path('geeksforgeeks/', views.geeksforgeeks_view, name='geeksforgeeks'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]
