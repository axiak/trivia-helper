import os
import math
import datetime
import itertools
import simplejson
import collections

from numpy import ndarray, array
from scipy.cluster.vq import vq, kmeans2, whiten

from django.core.management.base import BaseCommand, CommandError
from triviaopt.jeopardy.models import *

from . import porter

class Command(BaseCommand):
    args = 'number of clusters'
    help = 'Clusters categories into a number of super-categories'
    stemmer = porter.PorterStemmer()
    stop_words = set()
    category_tfidf = {}
    max_features = []
    DIMENSION = 1000

    def handle(self, *args, **options):
        self._load_stopwords()

        num_cluster = 30 if not args else int(args[0])

        self.build_tfidf()

        result = self.cluster(num_cluster)
        print '\n'.join('\t'.join(x.encode('utf8') for x in cat) for cat in result)

    def cluster(self, num_cluster):
        category_tfidf = self.category_tfidf

        features = ndarray((len(category_tfidf), self.DIMENSION), 'float')

        for i, category in enumerate(sorted(category_tfidf)):
            tfidf = category_tfidf[category]
            features[i] = array([tfidf.get(term, 0.0) for term in self.max_features])

        whiten(features)

        result = kmeans2(features, num_cluster, 400)

        categories = [[] for _ in range(num_cluster)]
        sorted_cats = sorted(category_tfidf)

        for i, category in enumerate(result[1]):
            categories[category].append(sorted_cats[i])

        return categories


    def build_tfidf(self):
        document_frequency = collections.Counter()

        document_frequency.update(itertools.chain.from_iterable(self.tokenize(name)
                                                                for name in Category.objects.values_list('name', flat=True)))

        document_frequency.update(itertools.chain.from_iterable(self.tokenize(text)
                                                                for text in Question.objects.values_list('clue', flat=True)))

        self.max_features = [feature[0] for feature in document_frequency.most_common(self.DIMENSION)]

        denominator = float(sum(document_frequency.values()))

        idf = {term: math.log(denominator / frequency) for term, frequency in document_frequency.items()}

        max_idf = max(idf.values())

        category_bags = {}
        for clue, category in Question.objects.values_list('clue', 'category__name'):
            if category not in category_bags:
                category_bags[category] = collections.Counter()
                category_bags[category].update(self.tokenize(category))
            category_bags[category].update(self.tokenize(clue))

        category_tfidf = self.category_tfidf = {}
        for category, bag in category_bags.items():
            denominator = sum(bag.values())
            category_tfidf[category] = {term: float(frequency) / denominator * idf.get(term, max_idf) for term, frequency in bag.items()}


    def stem(self, word):
        return self.stemmer.stem(word, 0, len(word) - 1)

    def tokenize(self, text):
        tokens = [self.stem(token.strip('"\'!.-:_')) for token in text.upper().replace('&AMP;', '&').split()
                  if token not in self.stop_words]
        tokens = filter(None, tokens)
        bigrams = [' '.join(tokens[i:i + 2]) for i in range(0, len(tokens) - 1)]
        return tokens + bigrams

    def _load_stopwords(self):
        with open(os.path.join(os.path.dirname(__file__), 'english.stop')) as f:
            self.stop_words = set(self.stem(line.rstrip().upper()) for line in f)
