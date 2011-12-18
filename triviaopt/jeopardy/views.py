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
    json_serializer = serializers.get_serializer("json")()

    questions = session.get_next_questions()

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
    is_correct, correct_answer, answer_pk = session.answer_question(request.user, question_id, answer)

    return HttpResponse(simplejson.dumps({'is_correct': is_correct,
                                          'correct_response': correct_answer,
                                          'answer_id': answer_pk}),
                                         mimetype="application/json")

@with_session
def change_answer(request, session):
    answer = Answer.objects.get(id=request.GET.get('answer_id'))
    answer.correct = not answer.correct
    answer.save()
    return HttpResponse(simplejson.dumps({'is_correct': answer.correct,
                                          'answer_id': answer.pk}),
                        mimetype="application/json")
