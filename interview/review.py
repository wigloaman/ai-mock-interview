import threading

from django.db import connection

from interview import ai, models

# Interviews whose review is being generated right now, so a reload doesn't start a second run
_in_progress = set()
_lock = threading.Lock()


def complete_interview(interview):
    """Mark the interview complete and generate its review in the background."""
    if not interview.is_complete:
        interview.is_complete = True
        interview.save()
    if interview.review_generated:
        return
    with _lock:
        if interview.id in _in_progress:
            return
        _in_progress.add(interview.id)
    threading.Thread(target=generate_reviews, args=[interview.id], daemon=True).start()


def is_in_progress(interview_id):
    return interview_id in _in_progress


def generate_reviews(interview_id):
    interview = models.UserInterview.objects.get(id=interview_id)
    questions = list(interview.userquestionanswer_set.filter(is_asked=True, answer__isnull=False).order_by('pos'))
    try:
        ai.generate_review(interview, questions)
        ai.generate_answer_review(interview, questions)
        interview.error_present = False
        interview.error_message = None
    except Exception as e:
        print(f"[ERROR] Error generating review for interview id {interview.id}: {e}")
        interview.error_present = True
        interview.error_message = f"Review generation failed: {e}"
    finally:
        interview.review_generated = not interview.error_present
        interview.save()
        with _lock:
            _in_progress.discard(interview_id)
        connection.close()  # This thread opened its own database connection
