import math
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import ContactUsForm, FeedbackForm, UserProfileForm, UserInterviewForm
from interview import ai, models, review, voice

NUMBER_OF_QUESTIONS = {
    timedelta(minutes=30): 15,
    timedelta(minutes=60): 20,
    timedelta(minutes=90): 25,
    timedelta(minutes=120): 30,
}

# Per duration: (max follow-ups per answer, max follow-up depth, importance score a follow-up must beat)
CROSS_QUESTIONING = {
    timedelta(minutes=30): (1, 2, 8),
    timedelta(minutes=60): (2, 2, 9),
    timedelta(minutes=90): (2, 2, 8),
    timedelta(minutes=120): (2, 3, 7),
}


def index(request):
    context = {
    }
    return render(request, 'interview/index.html', context)


def contact(request):
    if request.method == 'POST':
        form = ContactUsForm(request.POST)
        if form.is_valid():
            form.save()
            context = {"complete": True}
        else:
            context = {"form": form,
                       "complete": False}
    else:
        form = ContactUsForm()
        if request.user.is_authenticated:
            form.fields['email'].initial = request.user.email
            form.fields['name'].initial = request.user.get_full_name()
        context = {"form": form,
                   "complete": False}
    return render(request, 'interview/contact.html', context)


def feedback(request):
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        if form.is_valid():
            form.save()
            context = {"complete": True}
        else:
            context = {"form": form,
                       "complete": False}
    else:
        form = FeedbackForm()
        if request.user.is_authenticated:
            form.fields['email'].initial = request.user.email
        context = {"form": form,
                   "complete": False}
    return render(request, 'interview/feedback.html', context)


@login_required
def view_profile(request):
    userprofile, _ = models.UserProfile.objects.get_or_create(user=request.user)
    interviews = models.UserInterview.objects.filter(user=request.user, is_complete=True).order_by('-created_at')
    context = {"user": request.user,
               "interviews": interviews,
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


def interview_form(request, data=None):
    form = UserInterviewForm(data)
    if not request.user.is_staff:
        del form.fields['auto_answer']  # Auto-answer is a testing tool for staff only
    return form


@login_required
def create_interview_session(request):
    if request.method == 'POST':
        form = interview_form(request, request.POST)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.user = request.user
            interview.save()
            request.session['interview_id'] = interview.id
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'errors': form.errors})

    context = {
        'form': interview_form(request),
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
        return redirect(result_url(interview))

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
        if interview.cross_question:
            add_cross_questions(interview, question)
    return JsonResponse({'success': True})


def add_cross_questions(interview, question):
    """Ask the AI for follow-ups to an answer and queue them right after it.

    Positions encode the nesting: follow-ups to question 3 get 3.1, 3.2, and a follow-up
    to 3.1 gets 3.11, so ordering by position keeps each thread together.
    """
    number_of_cross_questions, max_depth, importance_score = CROSS_QUESTIONING[interview.duration]
    pos = Decimal(str(question.pos)).normalize()
    depth = max(-pos.as_tuple().exponent, 0) + 1
    if depth > max_depth:
        return

    # The conversation so far for this main question, including earlier follow-ups
    main_pos = math.floor(question.pos)
    conversation = interview.userquestionanswer_set.filter(
        is_asked=True, pos__gte=main_pos, pos__lt=main_pos + 1).order_by('pos')
    cross_questions = ai.generate_cross_questions(interview, conversation, number_of_cross_questions, importance_score)

    step = Decimal(1).scaleb(-depth)
    for i, cross_question in enumerate(cross_questions, start=1):
        models.UserQuestionAnswer.objects.create(question=cross_question, user=interview.user,
                                                 session=interview, pos=float(pos + step * i))


@login_required
def get_answer_automatically(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=403)
    interview = get_current_interview(request)
    question = interview and interview.userquestionanswer_set.filter(id=request.session.get('question_id')).first()
    if question is None:
        return JsonResponse({'success': False, 'error': 'Invalid interview'})
    try:
        answer_text = ai.generate_answer(interview.job_role, question.question)
    except Exception as e:
        print(f"[ERROR] Error generating answer automatically: {e}")
        return JsonResponse({'success': False, 'error': 'Answer generation failed'})
    return JsonResponse({'success': True, 'answer': answer_text})


def result_url(interview):
    return reverse('interview:display_result') + f'?interview={interview.id}'


@login_required
def end_interview(request):
    # An unfinished interview from the profile is passed explicitly; otherwise use the current one
    interview_id = request.GET.get('interview')
    if interview_id:
        interview = models.UserInterview.objects.filter(id=interview_id, user=request.user).first()
    else:
        interview = get_current_interview(request)
    if interview is None:
        return render(request, 'interview/message/invalid_interview.html', {})
    review.complete_interview(interview)
    return redirect(result_url(interview))


@login_required
def display_result(request):
    interview = models.UserInterview.objects.filter(id=request.GET.get('interview'), user=request.user).first()
    if interview is None:
        return render(request, 'interview/message/invalid_interview.html', {})
    questions = interview.userquestionanswer_set.filter(is_asked=True).order_by('pos')
    context = {
        'interview': interview,
        'questions': questions,
        'num_questions': len(questions),
        'review_in_progress': review.is_in_progress(interview.id),
    }
    return render(request, 'interview/interview_result.html', context)


@login_required
def check_review_status(request):
    interview = models.UserInterview.objects.filter(id=request.GET.get('interview_id'), user=request.user).first()
    if interview is None:
        return JsonResponse({'error': 'Invalid interview'}, status=404)
    return JsonResponse({
        'review_generated': interview.review_generated,
        'error': interview.error_present and not review.is_in_progress(interview.id),
    })


@login_required
def speak_text(request):
    text = request.GET.get('text', '').strip()
    if not text:
        return JsonResponse({'error': 'Text is missing'}, status=400)
    try:
        audio = voice.synthesize_speech(text)
    except Exception as e:
        print(f"[ERROR] Error synthesizing speech: {e}")
        return JsonResponse({'error': 'Speech synthesis failed'}, status=502)
    return HttpResponse(audio, content_type='audio/mpeg')


@login_required
@require_POST
def transcribe_audio(request):
    audio_file = request.FILES.get('audio')
    if not audio_file:
        return JsonResponse({'success': False, 'error': 'Audio is missing'}, status=400)
    try:
        text = voice.transcribe_audio(audio_file)
    except Exception as e:
        print(f"[ERROR] Error transcribing audio: {e}")
        return JsonResponse({'success': False, 'error': 'Transcription failed'}, status=502)
    return JsonResponse({'success': True, 'text': text})


def privacy_policy(request):
    return render(request, 'interview/privacy_policy.html', {})


def terms_of_use(request):
    return render(request, 'interview/terms_of_use.html', {})
