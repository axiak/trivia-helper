import math
import random
import datetime
import collections

try:
    from collections import Counter
except ImportError:
    from utils import Counter

from django.db import models
from django.contrib.auth.models import User

__all__ = ('Game', 'Category', 'Contestant', 'Question', 'Answer',
           'AnswerSession',)

class Game(models.Model):
    date = models.DateField(db_index=True)

    class Meta:
        ordering = ('-date',)

    def __unicode__(self):
        return u'<Game on %s>' % self.date


class Category(models.Model):
    name = models.CharField(max_length=1024)
    comments = models.TextField(null=True, blank=True)
    meta_category = models.IntegerField(null=True, blank=True)
    meta_category_name = models.CharField(max_length=1024)
    mean_value = models.FloatField(blank=True, null=True)

    def __unicode__(self):
        return u'<Category: %r>' % self.name

    class Meta:
        verbose_name_plural = 'Categories'

class Contestant(models.Model):
    name = models.CharField(max_length=1024)
    games = models.ManyToManyField(Game)

    def __unicode__(self):
        return u'<Contestant: %r>' % self.name


class Question(models.Model):

    ROUNDS = (
        (0, u'First'),
        (1, u'Second'),
        (2, u'Final'),
        )

    game = models.ForeignKey(Game, db_index=True)
    category = models.ForeignKey(Category, db_index=True)

    number = models.IntegerField()
    round = models.IntegerField(choices=ROUNDS)

    price = models.IntegerField(blank=True, null=True)

    clue = models.TextField()
    answer = models.TextField()

    is_daily_double = models.BooleanField(default=False)

    answered_incorrectly = models.IntegerField()
    answered_correctly = models.IntegerField()

    computed_value = models.FloatField(blank=True, null=True, db_index=True)

    random_weight = models.FloatField(blank=True, null=True, db_index=True)

    def is_correct(self, other_answer):
        return Question.normalize_single_answer(other_answer) in Question.normalize_answer(self.answer)

    @classmethod
    def normalize_answer(cls, answer):
        import re
        import itertools
        _or_re = re.compile(r'\bor\b')
        _paren_re = re.compile(r'\([^\)]+\)')
        answer = cls.normalize_single_answer(answer)
        result = set([answer])
        result.add(answer.replace("(", "").replace(")", "").strip())
        if '(' in answer and _or_re.search(answer):
            result.update(itertools.chain.from_iterable(
                    cls.normalize_answer(piece)
                    for piece in _or_re.split(answer)
                    if piece.strip()))
        if '(' in answer:
            result.add(_paren_re.sub('', answer).strip())
        return result

    @classmethod
    def normalize_single_answer(cls, answer):
        tokens = answer.strip().lower().split()
        for bad_word in ('the', 'an', 'a'):
            if bad_word in tokens:
                tokens.remove(bad_word)
        return ' '.join(tokens)

    class Meta:
        unique_together = ('game', 'number')
        ordering = ['-game__date', 'number']

    def value(self):
        if hasattr(self, '_value_cached'):
            return self._value_cached
        # logit
        _logit_coefficients = (-1.707015765, 0.000150362, 0.211078614,
                                0.0, 0.226851628, 0.0, 0.271769689,
                                0.232831474, 0.242451134, 0.293743018, 0.0,
                                0.42205324, 0.228055767, 0.390339103, 0.110244457,
                                0.240846623, 0.301152817, 0.165676702, 0.0,
                                0.25414831, 0.0, 0.236327479, 0.136417475, 0.0,
                                0.152464981, 0.138780691, 0.128021677, 0.205386742,
                                0.196025007, 0.181441473, 0.160830982, 0.0, 0.0
                                )
        price = self.price or 20000

        vector = [1.0, price, self.round] + [0.0] * 30

        meta_category = Question.category_cache.get(self.category_id)
        if meta_category is None:
            meta_category = Question.category_cache.setdefault(self.category_id, self.category.meta_category)
        vector[meta_category + 3] = 1.0

        z = sum(a * b for a, b in zip(vector, _logit_coefficients))
        result = 1 / (1.0 + math.exp(-z))
        self._value_cached = result
        return result

    def __unicode__(self):
        return u'<Question: {0}>'.format(self.value())

Question.category_cache = {}

class AnswerSession(models.Model):
    date = models.DateTimeField(default=datetime.datetime.now, db_index=True)
    last_touch_date = models.DateTimeField(default=datetime.datetime.now)
    user = models.ForeignKey(User, db_index=True)

    _breakdowns = None
    _user_questions = None
    _category_scores = None
    _category_questions = None

    def __unicode__(self):
        return u'Session started on {0}'.format(self.date)

    @property
    def age(self):
        answers = list(Answer.objects.filter(session=self).order_by('-date')[:1])
        if not answers:
            last_date = self.date
            if self.last_touch_date:
                last_date = max(last_date, self.last_touch_date)
        else:
            last_date = answers[0].date
        td = datetime.datetime.now() - last_date
        # in python 2.7...
        #return td.total_seconds()
        return (td.microseconds + (td.seconds + td.days * 24.0 * 3600) * 10**6) / 10**6

    def get_breakdowns(self):
        CATS = (10, 8, 9, 2,)
        if self._breakdowns:
            return self._breakdowns
        self._breakdowns = Counter(Answer.objects.filter(session=self, question__category__meta_category__in = CATS).values_list('question__category__meta_category', flat=True))
        for i in set(Category.objects.filter(meta_category__in=CATS).values_list('meta_category', flat=True)):
            if i not in self._breakdowns:
                self._breakdowns[i] = 0
        return self._breakdowns

    def get_user_questions(self):
        if self._user_questions:
            return self._user_questions
        self._user_questions = set(Answer.objects.filter(user=self.user).values_list('question_id', flat=True))
        return self._user_questions

    def get_category_scores(self):
        if self._category_scores:
            return self._category_scores
        self._category_scores = collections.defaultdict(float)
        for key, value in Category.objects.values_list('meta_category', 'mean_value', flat=True):
            self._category_scores[key] += value
        return self._category_scores

    def get_category_questions(self, meta_category, seen_questions=()):
        if self._category_questions:
            return self._category_questions
        questions = list(Question.objects.filter(category__meta_category=meta_category
                                                 ).exclude(id__in=seen_questions
                                                 ).order_by('random_weight').values_list('id', flat=True)[:1])
        return questions

    def get_next_questions(self):
        breakdowns = self.get_breakdowns()
        user_questions = self.get_user_questions()
        meta = breakdowns.items()
        random.shuffle(meta)
        meta.sort(key=lambda x: x[1])
        category = meta[0][0]
        questions_list = self.get_category_questions(category, user_questions)
        question_id = questions_list[0]
        for question_id in questions_list:
            if question_id not in user_questions:
                break
        return Question.objects.filter(id=question_id).select_related()


    def answer_question(self, user, question_id, answer):
        question = Question.objects.get(pk=question_id)
        correct = question.is_correct(answer)
        answer = Answer.objects.create(question=question,
                                       user=user,
                                       answer=answer,
                                       correct=correct,
                                       session=self)
        answer.save()
        breakdowns = self.get_breakdowns()
        user_questions = self.get_user_questions()
        breakdowns[question.category.meta_category] += 1
        user_questions.add(question.id)
        return correct, question.answer, answer.pk

        #cats = self.get_breakdowns().keys()
        #self._category_questions = {}
        #for cat in cats:
        #for question in Question.objects.all():
        #    question.computed_value = question.value()
        #    question.save()
        #questions = list(Question.objects.filter(category__meta_category = meta_category))
        #random.shuffle(questions)
        #questions.sort(key=lambda q: q.value(), reverse=True)
        #return map(lambda x: x.id, questions)
        #self._category_questions[cat] = map(lambda q: q.pk, questions)
        #return self._category_questions

class Answer(models.Model):
    date = models.DateTimeField(default=datetime.datetime.now)
    question = models.ForeignKey(Question, related_name='user_answer')
    user = models.ForeignKey(User)
    answer = models.CharField(max_length=1024)
    correct = models.BooleanField()
    session = models.ForeignKey(AnswerSession, blank=True, null=True)

    def __unicode__(self):
        return u'<Answer by {0} on {1} ({2})>'.format(self.user,
                                                   self.date,
                                                   'correct' if self.correct else 'incorrect')

