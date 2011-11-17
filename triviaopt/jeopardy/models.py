import datetime

from django.db import models
from django.contrib.auth.models import User

__all__ = ('Game', 'Category', 'Contestant', 'Question', 'Answer',)

class Game(models.Model):
    date = models.DateField(db_index=True)

    class Meta:
        ordering = ('-date',)

    def __unicode__(self):
        return u'<Game on %s>' % self.date


class Category(models.Model):
    name = models.CharField(max_length=1024)
    comments = models.TextField(null=True, blank=True)
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

    class Meta:
        unique_together = ('game', 'number')
        ordering = ['-game__date', 'number']

    def value(self):
        return self.price

    def __unicode__(self):
        return u'<Question: {0}>'.format(self.value())


class Answer(models.Model):
    date = models.DateTimeField(default=datetime.datetime.now)
    question = models.ForeignKey(Question, related_name='user_answer')
    user = models.ForeignKey(User)
    answer = models.CharField(max_length=1024)
    correct = models.BooleanField()

    def __unicode__(self):
        return u'<Answer by {} on {} ({})>'.format(self.user,
                                                   self.date,
                                                   'correct' if self.correct else 'incorrect')

