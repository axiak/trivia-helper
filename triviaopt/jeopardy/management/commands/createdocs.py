import os
import csv
import math
import datetime
import itertools
import simplejson
import collections

from django.core.management.base import BaseCommand, CommandError
from triviaopt.jeopardy.models import *


class Command(BaseCommand):
    args = 'output csv'
    help = 'Output documents into csv.'

    def handle(self, *args, **options):
        output = open(args[0], 'w+')
        writer = csv.writer(output)
        writer.writerow(['category', 'text'])

        categories = {category.id: category.name for category in Category.objects.all()}

        current_category = None
        text = []
        for question in Question.objects.order_by('category__id'):
            category = categories[question.category_id]
            if category != current_category:
                if current_category is not None:
                    writer.writerow([current_category.encode('utf8'), u' '.join(text).encode('utf8') +
                                     ' ' + current_category.replace('&AMP;', '&').replace('&amp;', '&').encode('utf8')])
                current_category = category
                text = []

            text.append(question.clue.replace('\r\n', ' ').replace('\n', ' ').replace('&amp;', '&').replace('&AMP;', '&').strip())

        output.close()
