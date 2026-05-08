from django.urls import path

from . import views

urlpatterns = [
    path('', views.role_login, name='role_login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('events/', views.event_list, name='event_list'),
    path('events/new/', views.event_create, name='event_create'),
    path('events/<int:event_id>/edit/', views.event_edit, name='event_edit'),
    path('events/<int:event_id>/delete/', views.event_delete, name='event_delete'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    path('logout/', views.logout_view, name='logout'),
]
