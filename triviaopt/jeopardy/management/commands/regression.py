import csv
import os
import gc
import math
import random
import datetime
import itertools
import simplejson
import collections

from Bio import LogisticRegression

from django.core.management.base import BaseCommand, CommandError
from triviaopt.jeopardy.models import *

def show_progress(iteration, loglikelihood):
        print "Iteration:", iteration, "Log-likelihood function:", loglikelihood

class Command(BaseCommand):
    args = 'category.dat file'
    help = 'Regression'

    game_years = {}
    category_map = {}
    num_categories = 0


    def handle(self, *args, **options):
        self._load_categories(args[0])
        self._load_game_years()

        xs = []
        ys = []
        zeroes = [0] * self.num_categories

        output_file = open(args[1], 'w+')
        writer = csv.writer(output_file)

        headers = ['is_difficult', 'price', 'round', 'year'] + ['cat' + str(i + 1) for i in range(self.num_categories)]

        writer.writerow(headers)

        for question in Question.objects.values('price', 'category_id', 'answered_correctly', 'answered_incorrectly', 'round', 'game_id'):
            is_difficult = int(bool(question['answered_incorrectly']) or not bool(question['answered_correctly']))
            x = [is_difficult, float(question['price'] or 20000), float(question['round']), self.game_years[question['game_id']]] + zeroes
            x[4 + self.category_map[question['category_id']]] = 1.0
            #x = [float(question['price'] or 20000), float(question['round']), self.game_years[question['game_id']], self.category_map[question['category_id']]]
            writer.writerow(x)

        output_file.close()

        #model = LogisticRegression.train(xs, ys, update_fn=show_progress)
        #print model.beta

    def _load_categories(self, category_file):
        with open(category_file) as f:
            categories = self.categories = {}
            [self.categories.update({category: idx for category in line.decode('utf8').rstrip().split("\t")}) for idx, line in enumerate(f)]
        category_map = self.category_map = {}
        for category in Category.objects.all():
            category_map[category.pk] = categories[category.name]
            category.meta_category = categories[category.name]
            category.save()

        self.num_categories = len(set(category_map.values()))

    def _load_game_years(self):
        self.game_years = {game.id: game.date.year for game in Game.objects.all()}
