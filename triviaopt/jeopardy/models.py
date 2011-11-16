from django.db import models

class Game(models.Model):
    date = models.DateField()

    def __unicode__(self):
        return u'<Game on %s>' % self.date


class Category(models.Model):
    name = models.CharField(max_length=1024)
    mean_value = models.FloatField(blank=True, null=True)

    def __unicode__(self):
        return u'<Category: %r>' % self.name

class Contestant(models.Model):
    name = models.CharField(max_length=1024)
    games = models.ManyToMany(Game)

    def __unicode__(self):
        return u'<Contestant: %r>' % self.name


class Question(models.Model):

    ROUNDS = (
        (0, u'First'),
        (1, u'Second'),
        (2, u'Final'),
        )

    game = models.ForeignKey(Game, indexes=True)
    category = models.ForeignKey(Category, indexes=True)

    number = models.IntegerField()
    round = models.IntegerField(choices=ROUNDS)

    price = models.IntegerField(blank=True, null=True)

    clue = models.TextField()
    answer = models.TextField()

    is_daily_double = models.BooleanField(default=False)

    answered_incorrectly = models.IntegerField()
    answered_correclty = models.IntegerField()

    class Meta:
        unique_together = ('game, number')

    def value(self):
        return price

    def __unicode__(self):
        return u'<Question: {0:f}>'.format(self.value())


class Answer(models.Model):
    date = models.DateTimeField(default=datetime.datetime.now)
    question = models.ForeignKey(Question)
    user = models.ForeignKey(User)
    answer = models.CharField(max_length=1024)
    correct = models.BooleanField()

    def __unicode__(self):
        return u'<Answer by {} on {} ({})>'.format(self.user,
                                                   self.date,
                                                   'correct' if self.correct else 'incorrect')

