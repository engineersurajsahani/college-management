from django.contrib import admin
from .models import Assignment, AssignmentSubmission, CourseMaterial, Department, Course, Exam, ExamResult, Notice, Student, Faculty, Enrollment, Attendance

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'credits', 'department')
    list_filter = ('department', 'credits')
    search_fields = ('name', 'code')

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'user', 'department')
    list_filter = ('department',)
    search_fields = ('student_id', 'user__username', 'user__first_name', 'user__last_name')

@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('faculty_id', 'user', 'department', 'designation')
    list_filter = ('department', 'designation')
    search_fields = ('faculty_id', 'user__username', 'user__first_name', 'user__last_name')

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrollment_date', 'grade')
    list_filter = ('course', 'enrollment_date')
    search_fields = ('student__student_id', 'course__name')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'date', 'is_present', 'marked_by')
    list_filter = ('course', 'date', 'is_present', 'marked_by')
    search_fields = ('student__student_id', 'course__name')

@admin.register(CourseMaterial)
class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'uploaded_by', 'upload_date')
    list_filter = ('course', 'uploaded_by')
    search_fields = ('title', 'course__name')

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'due_date', 'total_marks', 'created_by')
    list_filter = ('course', 'due_date', 'created_by')
    search_fields = ('title', 'course__name')

@admin.register(AssignmentSubmission)
class AssignmentSubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'submitted_at', 'marks_obtained')
    list_filter = ('assignment', 'submitted_at')
    search_fields = ('student__student_id', 'assignment__title')

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('course', 'exam_type', 'title', 'date', 'total_marks')
    list_filter = ('course', 'exam_type', 'date')
    search_fields = ('title', 'course__name')

@admin.register(ExamResult)
class ExamResultAdmin(admin.ModelAdmin):
    list_display = ('exam', 'student', 'marks_obtained')
    list_filter = ('exam', 'student')
    search_fields = ('student__student_id', 'exam__title')

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority', 'created_by', 'created_at', 'valid_until')
    list_filter = ('priority', 'departments', 'created_at')
    search_fields = ('title', 'content')
    filter_horizontal = ('departments',)