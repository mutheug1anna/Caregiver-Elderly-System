from django.urls import path
from .views import  signUp_view, login_view, home_view, logout_view, schedule_view, adherence_view, admin_dashboard_view 
from . import views
urlpatterns = [
     path('signup/', signUp_view, name='signup_caregiver'),
    path('login/', login_view, name='login'),
    path('home/', home_view, name='home'),
    path('logout/', logout_view, name='logout'), 
    
    path('schedule/', schedule_view, name='schedule'),   
    path('adherence/', adherence_view, name='adherence'), 
   path('master/control/', admin_dashboard_view, name='admin_dashboard'),
  path('at-webhook/', views.africas_talking_webhook, name='at_webhook'),
]


