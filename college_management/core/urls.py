from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('courses/', views.course_list, name='course_list'),
    path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
    path('courses/<int:course_id>/students/', views.course_students, name='course_students'),
    path('courses/<int:course_id>/materials/', views.course_materials, name='course_materials'),
    path('courses/<int:course_id>/assignments/', views.course_assignments, name='course_assignments'),
    path('courses/<int:course_id>/attendance/', views.course_attendance, name='course_attendance'),
    path('assignments/<int:assignment_id>/', views.assignment_detail, name='assignment_detail'),
    path('assignments/<int:assignment_id>/submit/', views.submit_assignment, name='submit_assignment'),
    path('exams/', views.exam_list, name='exam_list'),
    path('exams/<int:exam_id>/', views.exam_detail, name='exam_detail'),
    path('notices/', views.notice_list, name='notice_list'),
    path('students/', views.student_list, name='student_list'),
    path('students/<int:student_id>/', views.student_detail, name='student_detail'),
    path('mark-attendance/', views.mark_attendance, name='mark_attendance'),
]