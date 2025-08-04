from django.urls import path
from .views import UserListCreateView, RegisterView, LoginView, LogoutView, dashboard_view

urlpatterns = [
    path('', UserListCreateView.as_view()),
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('dashboard/', dashboard_view, name='dashboard'),  
]
