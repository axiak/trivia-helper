import csv
import os
import gc
import math
import random
import datetime
import itertools
import simplejson
import collections

from django.core.management.base import BaseCommand, CommandError
from triviaopt.jeopardy.models import *


class Command(BaseCommand):
    args = ''
    help = 'Mean value calculation'

    def handle(self, *args, **options):
            value = collections.defaultdict(float)
            category_map = {row[0]: row[1] for row in Category.objects.values_list('id', 'meta_category')}
            for question in Question.objects.all():
                    value[category_map[question.category_id]] += question.value() * (question.price or 25000)
            for category in Category.objects.all():
                    category.mean_value = value[category.meta_category]
                    category.save()
