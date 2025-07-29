from django.urls import path
from .views import UserListCreateView, RegisterView, LoginView, LogoutView

urlpatterns = [
    path('', UserListCreateView.as_view()),
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
]
