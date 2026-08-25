from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('',   views.login_view,   name='login'),
    path('login/',   views.login_view,   name='login'),
    path('logout/',  views.logout_view,  name='logout'),
    path('access-denied/', views.access_denied_view, name='access_denied'),

    # Profile
    path('profile/',          views.profile_view,         name='profile'),
    path('profile/edit/',     views.profile_update_view,  name='profile_update'),
    path('profile/password/', views.change_password_view, name='change_password'),

    # User management
    path('users/',                      views.user_list_view,         name='user_list'),
    path('users/create/',               views.user_create_view,       name='user_create'),
    path('users/<int:pk>/edit/',        views.user_update_view,       name='user_update'),
    path('users/<int:pk>/toggle/',      views.user_toggle_active_view,name='user_toggle'),
]