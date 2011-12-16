import sys
import csv
import os
import math
import random
import datetime
import itertools
import simplejson
import collections

from django.core.management.base import BaseCommand, CommandError
from triviaopt.jeopardy.models import *


class Command(BaseCommand):
    args = 'none'
    help = 'Pieces'

    def handle(self, *args, **options):
        reader = csv.reader(sys.stdin)
        for row in reader:
            Category.objects.filter(meta_category=row[2]).update(
                meta_category_name=row[1])

