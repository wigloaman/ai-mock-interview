import json

from django.conf import settings
from openai import OpenAI


class AIResponseError(Exception):
    pass


_client = None


def get_client():
    # Groq exposes an OpenAI-compatible API, so the official client works with a different base URL.
    # The client retries rate-limit (429) errors on its own, waiting as long as the API asks.
    global _client
    if _client is None:
        _client = OpenAI(api_key=settings.AI_API_KEY, base_url=settings.AI_BASE_URL,
                         max_retries=5, timeout=120)
    return _client


def chat_json(system_prompt, user_prompt=None, model=None, temperature=0.2, retries=3):
    """Send a chat request and return the reply parsed as a JSON object."""
    messages = [{"role": "system", "content": system_prompt}]
    if user_prompt:
        messages.append({"role": "user", "content": user_prompt})

    for attempt in range(retries):
        response = get_client().chat.completions.create(
            model=model or settings.AI_MODEL,
            messages=messages,
            temperature=temperature,
            response_format={"type": "json_object"},
        )
        try:
            return json.loads(response.choices[0].message.content)
        except (TypeError, json.JSONDecodeError):
            print(f"[WARN] AI returned invalid JSON, retrying ({attempt + 1}/{retries})...")
    raise AIResponseError("AI did not return valid JSON")


def interviewer_intro(interview):
    if interview.company:
        return f"You are an interviewer. You are hiring for the role of {interview.job_role} for {interview.company}. "
    return f"You are an interviewer. You are hiring for the role of {interview.job_role}. "


def question_generation_prompt(interview, number_of_questions):
    template = interviewer_intro(interview)

    template += "Generate questions to test if the candidate is a valid fit for the job role.\
 Generate questions in a sequence like a real interview happens starting with greeting\
 candidate, introduction and then casually going into domain knowledge starting with easy\
 questions and then slightly raising the difficulty level of the interview. "

    if interview.job_description:
        template += f"\n\nThe job description is: {interview.job_description}.\n\n"
        template += f"You need to assess both the candidate's domain knowledge, and their fit\
 for the job description. Include a mix of best interview questions asked to\
 {interview.job_role} and some questions specific to evaluating the candidate's knowledge on\
 the responsibilites, domains, sub-domains skills, tools and technologies mentioned in the job description. "

    if interview.subject:
        template += f"You need to access the candidate's skill on {interview.subject}. "

    if interview.topic:
        template += f"Furthermore, you should focus only on {interview.topic}. "

    if interview.tools:
        template += f"You should test candidate's knowledge on following tools: {interview.tools}. "

    if interview.difficulty_level:
        template += f"The difficulty level of questions should be {interview.difficulty_level}. "
    else:
        template += "Ensure questions cater to a range of difficulty levels, i.e, easy, medium and hard,\
 encompassing both straightforward and challenging aspects. "

    if interview.user_instructions:
        template += f"Further instructions are: {interview.user_instructions}."

    template += "Include a variety of questions on the concepts and tools required so both theoretical\
 and practical knowledge of the candidate can be checked. "

    template += "Also, include some good scenario-based and real-world industry questions. "

    template += "Ask the questions in a sequential manner,\
 where first generate questions related to a specific topic before moving on\
 to the next, allowing for a comprehensive evaluation of the candidate's expertise in each\
 topic and domain. "

    if interview.company:
        template += f"Use your prior information regarding the company {interview.company}, and their\
 past interview information to frame the questions. Also include a few questions specific to their\
 products and integrations. "

    template += "Ensure that you create a sufficient number of questions to evaluate\
 the candidate's comprehensive expertise in the field "

    if interview.job_description:
        template += "and to ascertain whether the candidate\
 possesses the necessary skills to meet all the responsibilities outlined in the job\
 description "

    template += "and do so in a way that allows for a reliable assessment, rather than relying\
 on chance or luck. "

    template += f"You can not generate more than {number_of_questions} questions.\
 You have to test the candidate's overall knowledge with {number_of_questions} questions, so frame the questions accordingly. "

    template += '\n\nRespond only with a JSON object of the form {"questions": ["question 1", "question 2", ...]}.'
    return template


def generate_questions(interview, number_of_questions):
    """Return a list of interview questions, or None if generation failed."""
    print("Generating questions...")
    try:
        data = chat_json(question_generation_prompt(interview, number_of_questions), temperature=0.6)
    except Exception as e:
        print(f"[ERROR] Error generating questions: {e}")
        return None

    questions = [q.strip() for q in data.get("questions", []) if isinstance(q, str) and q.strip()]
    return questions[:number_of_questions] or None


def to_score(value):
    """Clamp an AI-provided score to an integer from 0 to 10."""
    try:
        return max(0, min(10, int(round(float(value)))))
    except (TypeError, ValueError):
        return 0


def to_text(value):
    """Flatten an AI-provided value (sometimes a list) into display text."""
    if isinstance(value, list):
        return "\n".join(f"- {item}" for item in value)
    return str(value or "").strip()


def interview_review_prompt(interview):
    template = interviewer_intro(interview)
    template += "You are given all the questions asked during the interview and candidate's answer to it.\
 Your task is to do a detailed analysis of the candidate on the basis of it. Generate a detailed\
 review of the candidate including where they were good and where they were bad. Also, generate score of the candidate ranging\
 from 0 to 10 where higher the score means better the candidate. Also generate, strong and weak\
 points/domains/fields of the candidate in a detailed and formatted manner.\
 You also need to generate all improvements including\
 minute details that can to be done to make the candidate a better fit. Also tell if you will select\
 the candidate or not with the detailed reason of why if selected and why not if not selected.\
 The output will be provided to the candidate, so use direct speech as you are\
 advising the candidate. So, use 'you' to refer to the candidate.\n"
    template += '\nRespond only with a JSON object with these keys: "score" (integer 0-10), "review" (string),\
 "strong_points" (string), "weak_points" (string), "improvements" (string), "is_selected" (boolean),\
 "reason_selection" (string).'
    return template


def answer_review_prompt(interview):
    template = interviewer_intro(interview)
    template += "You are given a question and the candidate's answer.\
 Your task is to do a detailed analysis of the answer. You need to generate\
 score of the answer in a range of 0 to 10 denoting how good the candidate's answer is, where\
 higher score denotes better answer. You also need to generate a detailed review of the answer\
 highlighting overall quality of the answer including where it was good and where it was bad.\
 You also need to generate all improvements\
 including minute details that need to be done to make candidate's answer better.\
 Also generate a perfect answer of the question.\
 Note that the output will be provided to the candidate, so use direct speech as you are\
 advising the candidate. So, use 'you' to refer to the candidate.\n"
    template += '\nRespond only with a JSON object with these keys: "score" (integer 0-10), "review" (string),\
 "improvements" (string), "perfect_answer" (string).'
    return template


def generate_review(interview, questions):
    """Fill in the overall review of a completed interview."""
    question_answer = "".join(f"Question: {q.question}\nCandidate's Answer: {q.answer}\n\n" for q in questions)
    data = chat_json(interview_review_prompt(interview), question_answer or "The candidate did not answer any question.")
    interview.score = to_score(data.get("score"))
    interview.review = to_text(data.get("review"))
    interview.strong_points = to_text(data.get("strong_points"))
    interview.weak_points = to_text(data.get("weak_points"))
    interview.improvements = to_text(data.get("improvements"))
    interview.is_selected = bool(data.get("is_selected"))
    interview.reason_selection = to_text(data.get("reason_selection"))
    interview.save()


def generate_answer_review(interview, questions):
    """Review each answer separately; a failed answer review does not stop the others."""
    prompt = answer_review_prompt(interview)
    for question in questions:
        try:
            data = chat_json(prompt, f"Question: {question.question}\nCandidate's Answer: {question.answer}",
                             model=settings.AI_FAST_MODEL)
        except Exception as e:
            print(f"[ERROR] Error generating answer review for question id {question.id}: {e}")
            continue
        question.score = to_score(data.get("score"))
        question.review = to_text(data.get("review"))
        question.improvements = to_text(data.get("improvements"))
        question.perfect_answer = to_text(data.get("perfect_answer"))
        question.save()
