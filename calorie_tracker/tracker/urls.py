from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
    path('set-goal/', views.set_goal, name='set_goal'),
    path('add-food/', views.add_food, name='add_food'),
    path('goal-reached/', views.goal_reached, name='goal_reached'),
    path('history/', views.history, name='history'),
    path('reset-today/', views.reset_today, name='reset_today'),
    path('reset-all/', views.reset_all_history, name='reset_all'),
]