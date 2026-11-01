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
