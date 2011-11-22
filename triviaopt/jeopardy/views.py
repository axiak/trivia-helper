import random
import functools
import simplejson

from django.core import serializers
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.models import User

from triviaopt.jeopardy.models import *

import django.contrib.auth.views
from django.views.generic.simple import direct_to_template

def with_session(wrapped):
    @functools.wraps(wrapped)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated():
            if request.is_ajax():
                return HttpResponse(simplejson.dumps({"error": "need authentication."}))
            else:
                return django.contrib.auth.views.login(request)

        session = request.session.get('activeSession')

        if request.GET.get('createSession') or not session:
            session = AnswerSession.objects.create(user=request.user)
            session.save()
            request.session['activeSession'] = session

        if request.GET.get('createSession'):
            return HttpResponseRedirect('/')

        kwargs['session'] = session

        return wrapped(request, *args, **kwargs)
    return _wrapped


@with_session
def index(request, session):
    return direct_to_template(request, 'index.html', extra_context = {'session': session})

@with_session
def next_question(request, session):
    breakdowns = session.get_breakdowns()
    user_questions = session.get_user_questions()
    meta = breakdowns.items()
    random.shuffle(meta)
    meta.sort(key=lambda x: x[1])
    category = meta[0][0]
    questions_list = session.get_category_questions(category, user_questions)
    question_id = questions_list[0]
    for question_id in questions_list:
        if question_id not in user_questions:
            break
    json_serializer = serializers.get_serializer("json")()

    questions = Question.objects.filter(id=question_id).select_related()

    json_info = simplejson.loads(json_serializer.serialize(questions,
                                                           ensure_ascii=False))

    json_info[0]['fields']['category'] = simplejson.loads(json_serializer.serialize([questions[0].category]))

    response = HttpResponse(simplejson.dumps(json_info),
                            mimetype="application/json")

    return response

@with_session
def answer_question(request, session):
    question_id = request.GET['question_id']
    answer = request.GET['answer']
    question = Question.objects.get(pk=question_id)
    correct = question.is_correct(answer)
    answer = Answer.objects.create(question=question,
                                   user=request.user,
                                   answer=answer,
                                   correct=correct,
                                   session=session)
    answer.save()
    breakdowns = session.get_breakdowns()
    user_questions = session.get_user_questions()
    breakdowns[question.category.meta_category] += 1
    user_questions.add(question.id)
    return HttpResponse(simplejson.dumps({'is_correct': correct,
                                          'correct_response': question.answer,
                                          'answer_id': answer.pk}),
                                         mimetype="application/json")

@with_session
def change_answer(request, session):
    answer = Answer.objects.get(id=request.GET.get('answer_id'))
    answer.correct = not answer.correct
    answer.save()
    return HttpResponse(simplejson.dumps({'is_correct': answer.correct,
                                          'answer_id': answer.pk}),
                        mimetype="application/json")
