#!/usr/bin/python
import os
import sys
import pickle
import datetime
import simplejson
import collections
from ast import literal_eval

from BeautifulSoup import BeautifulSoup

try:
    with open(os.path.join(os.path.dirname(__file__), '_db.db')) as f:
        ORIGINAL = pickle.load(f)
except:
    ORIGINAL = set()


Question = collections.namedtuple('Question', [
        'game_date',
        'game_number',
        'question_number',
        'contestants',
        'round',
        'category',
        'category_comments',
        'price',
        'question',
        'answer',
        'daily_double',
        'answered_incorrectly',
        'answered_correctly',
        ])

def parse_game(str_input, game_id):
    root = BeautifulSoup(str_input)

    title = root.find('h1').text.strip()
    #sys.stderr.write("%s\n" % title)
    date_string = ' '.join(title.split()[-3:])

    game_date = datetime.datetime.strptime(date_string, '%B %d, %Y').strftime("%Y-%m-%d")
    game_number = game_id

    contestants = [node.find('a').text for node in root.findAll('p', {'class': 'contestants'})]

    categories = [node.text.replace('&amp;', '&') for node in root.findAll('td', {'class': 'category_name'})]
    category_comments = [node.text for node in root.findAll('td', {'class': 'category_comments'})]

    questions = []

    rounds = [node
           for node in root.findAll('table')
           if node.get('class') == 'round']

    for round_num, round_table in enumerate(rounds):
        for clue in round_table.findAll('td', {'class': 'clue'}):
            if not len(clue.text.strip()):
                continue
            clue_text = clue.find('td', {'class': 'clue_text'}).text

            clue_pieces = literal_eval(clue.find('div')['onmouseover'].replace('toggle(', '('))

            sub_root = BeautifulSoup(clue_pieces[2])

            clue_answer = sub_root.find('em', {'class': 'correct_response'}).text
            category_index = int(clue_pieces[0].split('_')[2]) - 1 + round_num * 6
            category = categories[category_index]
            category_comment = category_comments[category_index]

            price_text = clue.find('table', {'class': 'clue_header'}).findAll('td')[1].text
            daily_double = price_text.startswith('DD:')
            price = int(price_text.split()[-1].replace('$', '').replace(',', ''))

            num_right = 0
            num_wrong = 0
            for wrong_choice in sub_root.findAll('td', {'class': 'wrong'}):
                if not wrong_choice.text.upper().endswith('STUMPER'):
                    num_wrong += 1

            for right_choice in (sub_root.findAll('td', {'class': 'right'}) or []):
                num_right += 1

            question = Question(game_date, game_number, len(questions), contestants,
                                round_num, category, category_comment,
                                price,
                                clue_text, clue_answer,
                                daily_double, num_wrong, num_right)
            questions.append(question)


    final_round = root.find('table', {'class': 'final_round'})

    if not questions or not final_round:
        return []

    #sys.stderr.write("%s\n" % final_round)

    clue_text = final_round.find('td', {'class': 'clue_text'}).text
    clue_pieces = literal_eval(final_round.find('div')['onmouseover'].replace('toggle(', '('))
    sub_root = BeautifulSoup(clue_pieces[2])

    clue_answer = sub_root.find('em', {'class': 'correct_response'}).text
    num_right = 0
    num_wrong = 0
    for wrong_choice in sub_root.findAll('td', {'class': 'wrong'}):
        if not wrong_choice.text.upper().endswith('STUMPER'):
            num_wrong += 1

    for right_choice in (sub_root.find('td', {'class': 'right'}) or ()):
        num_right += 1

    questions.append(Question(game_date, game_number, len(questions), contestants,
                              2, categories[-1], category_comments[-1], 0,
                              clue_text, clue_answer, False, num_wrong, num_right))
    return questions


def all_games():
    for root, dirs, files in os.walk(os.path.dirname(__file__) or '.'):
        for file_name in files:
            if file_name.startswith('showgame.php?game_id'):
                yield os.path.join(root, file_name)


def parse_all_files():
    number_of_games = sum(1 for _ in all_games())

    for i, game_file in enumerate(all_games()):
        sys.stderr.write("%s\n" % game_file)
        if not game_file.rsplit('=', 1)[1].strip():
            continue
        game_id = int(game_file.rsplit('=', 1)[1])
        if game_id in ORIGINAL:
            continue
        with open(game_file) as game_file_obj:
            for question in parse_game(game_file_obj.read(), game_id):
                print simplejson.dumps(question)
        sys.stderr.write("%0.2f%%\n" % (float(i) / number_of_games * 100))
        ORIGINAL.add(game_id)
        with open(os.path.join(os.path.dirname(__file__), '_db.db'), 'w+') as f:
            pickle.dump(ORIGINAL, f)
    print number_of_games

def main():
    #parse_game(open('./www.j-archive.com/showgame.php?game_id=1292').read())
    parse_all_files()

if __name__ == '__main__':
    main()
