from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .forms import UserProfileForm, UserInterviewForm
from interview import ai, models

NUMBER_OF_QUESTIONS = {
    timedelta(minutes=30): 15,
    timedelta(minutes=60): 20,
    timedelta(minutes=90): 25,
    timedelta(minutes=120): 30,
}


def index(request):
    context = {
    }
    return render(request, 'interview/index.html', context)


@login_required
def view_profile(request):
    userprofile, _ = models.UserProfile.objects.get_or_create(user=request.user)
    context = {"user": request.user,
               "userprofile": userprofile
               }
    return render(request, 'interview/view_profile.html', context)


@login_required
def update_profile(request):
    userprofile, _ = models.UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=userprofile)
        if form.is_valid():
            form.save()
            return redirect("interview:view_profile")
    else:
        form = UserProfileForm(instance=userprofile)
    return render(request, 'interview/edit_profile.html', {'form': form})


def get_current_interview(request):
    """Return the interview stored in the session, if it belongs to the logged-in user."""
    return models.UserInterview.objects.filter(id=request.session.get('interview_id'),
                                               user=request.user).first()


@login_required
def create_interview_session(request):
    if request.method == 'POST':
        form = UserInterviewForm(request.POST)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.user = request.user
            interview.save()
            request.session['interview_id'] = interview.id
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'errors': form.errors})

    context = {
        'form': UserInterviewForm(),
        'interview': None
    }
    interview = models.UserInterview.objects.filter(user=request.user).last()
    if interview and not interview.is_complete and not interview.error_present:
        context['interview'] = interview
        request.session['interview_id'] = interview.id
    return render(request, 'interview/create_interview_session.html', context)


@login_required
def start_interview(request):
    interview = get_current_interview(request)
    if interview is None:
        return redirect('interview:create_interview_session')
    if interview.is_complete:
        return redirect('interview:view_profile')

    # Generate questions the first time the interview is opened
    if not interview.userquestionanswer_set.exists():
        questions = ai.generate_questions(interview, NUMBER_OF_QUESTIONS[interview.duration])
        if questions is None:
            interview.error_present = True
            interview.error_message = "Question generation failed"
            interview.save()
            return render(request, 'interview/message/interview_schedule_error.html', {})
        for pos, question in enumerate(questions, start=1):
            models.UserQuestionAnswer.objects.create(question=question, user=interview.user,
                                                     session=interview, pos=pos)

    context = {'user_initial': interview.user.first_name[:1] or interview.user.email[:1]}
    return render(request, 'interview/interview_interface.html', context)


@login_required
def get_question(request):
    interview = get_current_interview(request)
    if interview is None:
        return JsonResponse({'success': False, 'error': 'Invalid interview'})
    question = interview.userquestionanswer_set.filter(is_asked=False).order_by('pos').first()
    if not question:
        return JsonResponse({'success': True, 'redirect': '/end-interview/'})
    request.session['question_id'] = question.id
    return JsonResponse({
        'success': True,
        'question': question.question,
        'auto_answer': interview.auto_answer
    })


@login_required
@require_POST
def save_answer(request):
    interview = get_current_interview(request)
    if interview is None:
        return JsonResponse({'success': False, 'error': 'Invalid interview'})
    if interview.is_complete:
        return JsonResponse({'success': False, 'error': 'Interview Already Complete'})

    answer_text = request.POST.get('answer')
    if not answer_text:
        return JsonResponse({'success': False, 'error': 'Answer is missing'})

    question = interview.userquestionanswer_set.filter(id=request.session.get('question_id')).first()
    if question and question.answer is None:
        question.answer = answer_text
        question.is_asked = True
        question.save()
    return JsonResponse({'success': True})


@login_required
def end_interview(request):
    interview = get_current_interview(request)
    if interview and not interview.is_complete:
        interview.is_complete = True
        interview.save()
    return redirect('interview:view_profile')
