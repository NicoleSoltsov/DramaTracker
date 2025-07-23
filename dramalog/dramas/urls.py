from django.urls import path
from . import views
urlpatterns = [
    path('', views.index, name='index'),
    path('drama/<int:drama_id>/', views.drama_detail, name='drama_detail'),
    path('drama/add/', views.add_drama, name='add_drama'),
    path('drama/<int:drama_id>/edit/', views.edit_drama, name='edit_drama'),
    path('drama/<int:drama_id>/delete/', views.delete_drama, name='delete_drama'),
]