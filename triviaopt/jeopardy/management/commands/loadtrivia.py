import datetime
import simplejson

from django.core.management.base import BaseCommand, CommandError
from triviaopt.jeopardy.models import *

class Command(BaseCommand):
    args = 'inputfile'
    help = 'Loads data from jeopardy database.'

    known_questions = set()
    games = set()
    contestants_map = {}
    categories_map = {}

    def handle(self, *args, **options):
        self._load_data()

        with open(args[0]) as input_file:
            for line in input_file:
                row = simplejson.loads(line.rstrip().decode('utf8'))
                self.insert_row(row)

    def _load_data(self):
        self.known_questions = set(Question.objects.values_list('game_id', 'number'))
        self.games = set(Game.objects.values_list('id', flat=True))

        self.contestants_map = {x.name: x for x in Contestant.objects.all()}
        self.categories_map  = {x[1]: x[0] for x in Category.objects.values_list('id', 'name')}


    def insert_row(self, row):
        question_key = (row['game_number'], row['question_number'])

        if question_key in self.known_questions:
            return

        if row['game_number'] not in self.games:
            self.create_game(row)

        category_id = self.categories_map.get(row['category'])
        if category_id is None:
            category = Category.objects.create(name=row['category'],
                                               comments=(row['category_comments'] or None))
            category_id = category.id
            self.categories_map[category.name] = category_id

        try:
            Question.objects.create(
                game_id = row['game_number'],
                category_id = category_id,
                number = row['question_number'],
                round = row['round'],
                price = None if row['round'] == 2 else row['price'],
                clue = row['question'],
                answer = row['answer'],
                is_daily_double = row['daily_double'],
                answered_incorrectly = row['answered_incorrectly'],
                answered_correctly = row['answered_correctly'],
                )
        except:
            print row
            raise

        self.known_questions.add(question_key)

    def create_game(self, row):
        date = datetime.datetime.strptime(row['game_date'], "%Y-%m-%d")
        game = Game.objects.create(date=date,
                                   id=row['game_number'])
        self.games.add(row['game_number'])
        for name in row['contestants']:
            obj = self.contestants_map.get(name)
            if obj is None:
                obj = Contestant.objects.create(name=name)
                self.contestants_map[name] = obj
            #print "Adding {} to {}".format(name, row['game_date'])
            obj.games.add(game)
