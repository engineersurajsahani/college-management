from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.db.models import Avg, Count, Q
from django.core.paginator import Paginator
import json
from datetime import datetime, timedelta

from .models import (
    Student, Course, Enrollment, Attendance, Department,
    Faculty, CourseMaterial, Assignment, AssignmentSubmission,
    Exam, ExamResult, Notice
)

@login_required
def dashboard(request):
    user = request.user
    context = {}
    
    try:
        if hasattr(user, 'student'):
            student = user.student
            enrollments = Enrollment.objects.filter(student=student)
            upcoming_assignments = Assignment.objects.filter(
                course__in=student.courses.all(),
                due_date__gte=timezone.now()
            ).order_by('due_date')[:5]
            upcoming_exams = Exam.objects.filter(
                course__in=student.courses.all(),
                date__gte=timezone.now()
            ).order_by('date')[:5]
            
            context.update({
                'enrollments': enrollments,
                'upcoming_assignments': upcoming_assignments,
                'upcoming_exams': upcoming_exams,
                'user_type': 'student'
            })
            
        elif hasattr(user, 'faculty'):
            faculty = user.faculty
            courses = Course.objects.filter(department=faculty.department)
            pending_assignments = Assignment.objects.filter(
                course__in=courses,
                created_by=faculty,
                assignmentsubmission__marks_obtained__isnull=True
            ).distinct()
            
            context.update({
                'courses': courses,
                'pending_assignments': pending_assignments,
                'user_type': 'faculty'
            })
            
        else:  # Admin view
            total_students = Student.objects.count()
            total_courses = Course.objects.count()
            total_faculty = Faculty.objects.count()
            recent_enrollments = Enrollment.objects.order_by('-enrollment_date')[:10]
            
            context.update({
                'total_students': total_students,
                'total_courses': total_courses,
                'total_faculty': total_faculty,
                'recent_enrollments': recent_enrollments,
                'user_type': 'admin'
            })
            
    except Exception as e:
        messages.error(request, f"Error loading dashboard: {str(e)}")
    
    # Common data for all users
    notices = Notice.objects.filter(
        Q(valid_until__gte=timezone.now()) | Q(valid_until__isnull=True)
    ).order_by('-priority', '-created_at')[:5]
    context['notices'] = notices
    
    return render(request, 'core/dashboard.html', context)

@login_required
def profile(request):
    if request.method == 'POST':
        user = request.user
        if hasattr(user, 'student'):
            profile = user.student
            profile.phone = request.POST.get('phone', profile.phone)
            profile.address = request.POST.get('address', profile.address)
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
            profile.save()
        elif hasattr(user, 'faculty'):
            profile = user.faculty
            profile.phone = request.POST.get('phone', profile.phone)
            if 'profile_picture' in request.FILES:
                profile.profile_picture = request.FILES['profile_picture']
            profile.save()
        
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    
    return render(request, 'registration/profile.html')

@login_required
def course_list(request):
    if hasattr(request.user, 'student'):
        courses = Course.objects.filter(
            Q(student=request.user.student) |
            Q(department=request.user.student.department)
        ).distinct()
    elif hasattr(request.user, 'faculty'):
        courses = Course.objects.filter(department=request.user.faculty.department)
    else:
        courses = Course.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        courses = courses.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query) |
            Q(department__name__icontains=search_query)
        )
    
    paginator = Paginator(courses, 10)  # Show 10 courses per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'core/course_list.html', context)

@login_required
def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    context = {
        'course': course,
        'enrollment_count': Enrollment.objects.filter(course=course).count(),
        'materials_count': CourseMaterial.objects.filter(course=course).count(),
        'assignments_count': Assignment.objects.filter(course=course).count(),
    }
    
    if hasattr(request.user, 'student'):
        enrollment = Enrollment.objects.filter(
            student=request.user.student,
            course=course
        ).first()
        context['enrollment'] = enrollment
        
    elif hasattr(request.user, 'faculty'):
        context['is_faculty'] = True
        context['enrollments'] = Enrollment.objects.filter(course=course)
    
    return render(request, 'core/course_detail.html', context)

@login_required
def student_list(request):
    if not (request.user.is_staff or hasattr(request.user, 'faculty')):
        messages.error(request, "You don't have permission to view this page.")
        return redirect('dashboard')
    
    if hasattr(request.user, 'faculty'):
        students = Student.objects.filter(department=request.user.faculty.department)
    else:
        students = Student.objects.all()
    
    search_query = request.GET.get('search', '')
    if search_query:
        students = students.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(student_id__icontains=search_query) |
            Q(department__name__icontains=search_query)
        )
    
    paginator = Paginator(students, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'core/student_list.html', context)

@login_required
def course_materials(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    materials = CourseMaterial.objects.filter(course=course).order_by('-upload_date')
    
    if request.method == 'POST' and hasattr(request.user, 'faculty'):
        title = request.POST.get('title')
        description = request.POST.get('description')
        file = request.FILES.get('file')
        
        if title and file:
            CourseMaterial.objects.create(
                course=course,
                title=title,
                description=description,
                file=file,
                uploaded_by=request.user.faculty
            )
            messages.success(request, 'Material uploaded successfully.')
            return redirect('course_materials', course_id=course_id)
    
    context = {
        'course': course,
        'materials': materials,
    }
    return render(request, 'core/course_materials.html', context)

@login_required
def course_assignments(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    assignments = Assignment.objects.filter(course=course).order_by('-due_date')
    
    if request.method == 'POST' and hasattr(request.user, 'faculty'):
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')
        total_marks = request.POST.get('total_marks')
        file = request.FILES.get('file')
        
        if all([title, description, due_date, total_marks]):
            Assignment.objects.create(
                course=course,
                title=title,
                description=description,
                due_date=due_date,
                total_marks=total_marks,
                file=file,
                created_by=request.user.faculty
            )
            messages.success(request, 'Assignment created successfully.')
            return redirect('course_assignments', course_id=course_id)
    
    context = {
        'course': course,
        'assignments': assignments,
    }
    return render(request, 'core/course_assignments.html', context)

@login_required
@require_POST
def submit_assignment(request, assignment_id):
    if not hasattr(request.user, 'student'):
        messages.error(request, "Only students can submit assignments.")
        return redirect('dashboard')
    
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if assignment.is_past_due:
        messages.error(request, "Assignment submission deadline has passed.")
        return redirect('assignment_detail', assignment_id=assignment_id)
    
    submission_file = request.FILES.get('submission_file')
    if submission_file:
        submission, created = AssignmentSubmission.objects.get_or_create(
            assignment=assignment,
            student=request.user.student,
            defaults={'submission_file': submission_file}
        )
        
        if not created:
            submission.submission_file = submission_file
            submission.submitted_at = timezone.now()
            submission.save()
        
        messages.success(request, 'Assignment submitted successfully.')
    else:
        messages.error(request, 'Please select a file to submit.')
    
    return redirect('assignment_detail', assignment_id=assignment_id)

@login_required
def exam_list(request):
    if hasattr(request.user, 'student'):
        exams = Exam.objects.filter(
            course__in=request.user.student.courses.all()
        ).order_by('date')
    elif hasattr(request.user, 'faculty'):
        exams = Exam.objects.filter(
            course__department=request.user.faculty.department
        ).order_by('date')
    else:
        exams = Exam.objects.all().order_by('date')
    
    # Filter for upcoming/past exams
    filter_type = request.GET.get('filter', 'upcoming')
    if filter_type == 'upcoming':
        exams = exams.filter(date__gte=timezone.now())
    elif filter_type == 'past':
        exams = exams.filter(date__lt=timezone.now())
    
    paginator = Paginator(exams, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'filter_type': filter_type,
    }
    return render(request, 'core/exam_list.html', context)

@login_required
def course_attendance(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if not (hasattr(request.user, 'faculty') or request.user.is_staff):
        messages.error(request, "You don't have permission to view this page.")
        return redirect('dashboard')
    
    students = Student.objects.filter(courses=course)
    attendance_date = request.GET.get('date', timezone.now().date().isoformat())
    
    try:
        viewing_date = datetime.strptime(attendance_date, '%Y-%m-%d').date()
    except ValueError:
        viewing_date = timezone.now().date()
    
    # Get attendance records for the selected date
    attendance_records = {
        a.student_id: a.is_present 
        for a in Attendance.objects.filter(course=course, date=viewing_date)
    }
    
    # Calculate attendance statistics
    attendance_stats = {}
    for student in students:
        total_classes = Attendance.objects.filter(student=student, course=course).count()
        present_classes = Attendance.objects.filter(
            student=student, 
            course=course, 
            is_present=True
        ).count()
        
        if total_classes > 0:
            attendance_percentage = (present_classes / total_classes) * 100
        else:
            attendance_percentage = 0
        
        attendance_stats[student.id] = {
            'total_classes': total_classes,
            'present_classes': present_classes,
            'attendance_percentage': round(attendance_percentage, 2)
        }
    
    context = {
        'course': course,
        'students': students,
        'attendance_date': viewing_date,
        'attendance_records': attendance_records,
        'attendance_stats': attendance_stats,
    }
    return render(request, 'core/course_attendance.html', context)

@login_required
@require_POST
def mark_attendance(request):
    if not hasattr(request.user, 'faculty'):
        return JsonResponse({'error': 'Only faculty can mark attendance'}, status=403)
    
    try:
        data = json.loads(request.body)
        course_id = data.get('course_id')
        student_id = data.get('student_id')
        date = data.get('date')
        is_present = data.get('is_present')
        
        course = get_object_or_404(Course, id=course_id)
        student = get_object_or_404(Student, id=student_id)
        
        attendance, created = Attendance.objects.update_or_create(
            student=student,
            course=course,
            date=date,
            defaults={
                'is_present': is_present,
                'marked_by': request.user.faculty
            }
        )
        
        return JsonResponse({
            'status': 'success',
            'message': 'Attendance marked successfully'
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def notice_list(request):
    if hasattr(request.user, 'student'):
        notices = Notice.objects.filter(
            Q(departments=request.user.student.department) | 
            Q(departments=None)
        ).filter(
            Q(valid_until__gte=timezone.now()) | 
            Q(valid_until__isnull=True)
        ).order_by('-priority', '-created_at')
    else:
        notices = Notice.objects.all().order_by('-created_at')
    
    if request.method == 'POST' and request.user.is_staff:
        title = request.POST.get('title')
        content = request.POST.get('content')
        priority = request.POST.get('priority', 'MED')
        valid_until = request.POST.get('valid_until')
        departments = request.POST.getlist('departments')
        
        if all([title, content]):
            notice = Notice.objects.create(
                title=title,
                content=content,
                priority=priority,
                valid_until=valid_until if valid_until else None,
                created_by=request.user
            )
            if departments:
                notice.departments.set(departments)
            messages.success(request, 'Notice created successfully.')
            return redirect('notice_list')
    
    context = {
        'notices': notices,
        'departments': Department.objects.all() if request.user.is_staff else None,
    }
    return render(request, 'core/notice_list.html', context)

@login_required
def student_detail(request, student_id):
    if not (request.user.is_staff or hasattr(request.user, 'faculty')):
        messages.error(request, "You don't have permission to view this page.")
        return redirect('dashboard')
    
    student = get_object_or_404(Student, id=student_id)
    enrollments = Enrollment.objects.filter(student=student)
    
    # Calculate attendance statistics for each course
    attendance_stats = {}
    for enrollment in enrollments:
        total_classes = Attendance.objects.filter(
            student=student,
            course=enrollment.course
        ).count()
        present_classes = Attendance.objects.filter(
            student=student,
            course=enrollment.course,
            is_present=True
        ).count()
        
        if total_classes > 0:
            attendance_percentage = (present_classes / total_classes) * 100
        else:
            attendance_percentage = 0
            
        attendance_stats[enrollment.course.id] = {
            'total_classes': total_classes,
            'present_classes': present_classes,
            'attendance_percentage': round(attendance_percentage, 2)
        }
    
    # Get assignment submissions
    submissions = AssignmentSubmission.objects.filter(student=student)
    
    # Get exam results
    exam_results = ExamResult.objects.filter(student=student)
    
    context = {
        'student': student,
        'enrollments': enrollments,
        'attendance_stats': attendance_stats,
        'submissions': submissions,
        'exam_results': exam_results,
    }
    return render(request, 'core/student_detail.html', context)

@login_required
def assignment_detail(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    
    if request.method == 'POST' and hasattr(request.user, 'faculty'):
        submission_id = request.POST.get('submission_id')
        marks = request.POST.get('marks')
        remarks = request.POST.get('remarks')
        
        if submission_id and marks:
            submission = get_object_or_404(AssignmentSubmission, id=submission_id)
            submission.marks_obtained = marks
            submission.remarks = remarks
            submission.save()
            messages.success(request, 'Marks updated successfully.')
            return redirect('assignment_detail', assignment_id=assignment_id)
    
    # Get all submissions if faculty, only student's submission if student
    if hasattr(request.user, 'faculty'):
        submissions = AssignmentSubmission.objects.filter(assignment=assignment)
        context = {
            'assignment': assignment,
            'submissions': submissions,
        }
    else:
        submission = AssignmentSubmission.objects.filter(
            assignment=assignment,
            student=request.user.student
        ).first()
        context = {
            'assignment': assignment,
            'submission': submission,
        }
    
    return render(request, 'core/assignment_detail.html', context)

@login_required
def exam_detail(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    if request.method == 'POST' and hasattr(request.user, 'faculty'):
        student_id = request.POST.get('student_id')
        marks = request.POST.get('marks')
        remarks = request.POST.get('remarks')
        
        if student_id and marks:
            student = get_object_or_404(Student, id=student_id)
            result, created = ExamResult.objects.update_or_create(
                exam=exam,
                student=student,
                defaults={
                    'marks_obtained': marks,
                    'remarks': remarks
                }
            )
            messages.success(request, 'Exam result updated successfully.')
            return redirect('exam_detail', exam_id=exam_id)
    
    # Get results
    if hasattr(request.user, 'faculty'):
        results = ExamResult.objects.filter(exam=exam)
        # Get students who haven't taken the exam
        enrolled_students = Student.objects.filter(courses=exam.course)
        students_with_results = ExamResult.objects.filter(exam=exam).values_list('student_id', flat=True)
        pending_students = enrolled_students.exclude(id__in=students_with_results)
        
        context = {
            'exam': exam,
            'results': results,
            'pending_students': pending_students,
        }
    else:
        result = ExamResult.objects.filter(
            exam=exam,
            student=request.user.student
        ).first()
        context = {
            'exam': exam,
            'result': result,
        }
    
    return render(request, 'core/exam_detail.html', context)

@login_required
def course_students(request, course_id):
    if not (hasattr(request.user, 'faculty') or request.user.is_staff):
        messages.error(request, "You don't have permission to view this page.")
        return redirect('dashboard')
    
    course = get_object_or_404(Course, id=course_id)
    enrollments = Enrollment.objects.filter(course=course)
    
    # Calculate class statistics
    total_classes = Attendance.objects.filter(course=course).values('date').distinct().count()
    attendance_stats = {}
    for enrollment in enrollments:
        present_classes = Attendance.objects.filter(
            student=enrollment.student,
            course=course,
            is_present=True
        ).count()
        
        if total_classes > 0:
            attendance_percentage = (present_classes / total_classes) * 100
        else:
            attendance_percentage = 0
            
        attendance_stats[enrollment.student.id] = {
            'total_classes': total_classes,
            'present_classes': present_classes,
            'attendance_percentage': round(attendance_percentage, 2)
        }
    
    context = {
        'course': course,
        'enrollments': enrollments,
        'attendance_stats': attendance_stats,
    }
    return render(request, 'core/course_students.html', context)

@login_required
def enroll_course(request, course_id):
    if not hasattr(request.user, 'student'):
        messages.error(request, "Only students can enroll in courses.")
        return redirect('course_list')
    
    course = get_object_or_404(Course, id=course_id)
    student = request.user.student
    
    # Check if already enrolled
    if Enrollment.objects.filter(student=student, course=course).exists():
        messages.warning(request, "You are already enrolled in this course.")
        return redirect('course_detail', course_id=course_id)
    
    # Create enrollment
    Enrollment.objects.create(student=student, course=course)
    messages.success(request, f"Successfully enrolled in {course.name}.")
    return redirect('course_detail', course_id=course_id)

@login_required
def drop_course(request, course_id):
    if not hasattr(request.user, 'student'):
        messages.error(request, "Only students can drop courses.")
        return redirect('course_list')
    
    course = get_object_or_404(Course, id=course_id)
    student = request.user.student
    
    # Check if enrolled
    enrollment = get_object_or_404(Enrollment, student=student, course=course)
    enrollment.delete()
    
    messages.success(request, f"Successfully dropped {course.name}.")
    return redirect('course_list')