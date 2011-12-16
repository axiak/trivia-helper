import os
import math
import random
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

        num_cluster = 25 if not args else int(args[0])

        self.build_tfidf()

        result = self.cluster(num_cluster)
        self.update_categories(result)
        self.print_category_info(result)

    def update_categories(self, result):
        cats = {cat.name: cat for cat in Category.objects.all()}
        for i, category in enumerate(result):
            for real_cat_name in category:
                real_category = cats[real_cat_name]
                real_category.meta_category = i
                real_category.save()

    def cluster(self, num_cluster):
        category_tfidf = self.category_tfidf
        category_keys = list(category_tfidf)
        random.shuffle(category_keys)

        features = ndarray((len(category_tfidf), self.DIMENSION), 'float')

        for i, category in enumerate(category_keys):
            tfidf = category_tfidf[category]
            features[i] = array([tfidf.get(term, 0.0) for term in self.max_features])

        whiten(features)

        result = kmeans2(features, num_cluster, 200)

        categories = [[] for _ in range(num_cluster)]

        for i, category in enumerate(result[1]):
            categories[category].append(category_keys[i])

        return categories


    def build_tfidf(self):
        document_frequency = collections.Counter()

        document_frequency.update(itertools.chain.from_iterable(self.tokenize(name)
                                                                for name in Category.objects.values_list('name', flat=True)))

        document_frequency.update(itertools.chain.from_iterable(self.tokenize(text)
                                                                for text in Question.objects.values_list('answer', flat=True)))

        self.max_features = [feature[0] for feature in document_frequency.most_common(self.DIMENSION)]

        denominator = float(sum(document_frequency.values()))

        idf = self.idf = {term: math.log(denominator / frequency) for term, frequency in document_frequency.items()}

        max_idf = max(idf.values())

        category_bags = self.category_bags = {}
        for answer, category in Question.objects.values_list('answer', 'category__name'):
            if category not in category_bags:
                category_bags[category] = collections.Counter()
                category_bags[category].update(self.tokenize(category))
            category_bags[category].update(self.tokenize(answer))

        category_tfidf = self.category_tfidf = {}
        for category, bag in category_bags.items():
            denominator = sum(bag.values())
            category_tfidf[category] = {term: float(frequency) / denominator * idf.get(term, max_idf) for term, frequency in bag.items()}

    def print_category_info(self, results):
        idf = self.idf
        category_bags = self.category_bags

        max_idf = max(idf.values())

        for i, category_list in enumerate(results):
            main_bag = collections.Counter()
            for category in category_list:
                for term in category_bags[category]:
                    main_bag[term] += category_bags[category][term]

            denominator = sum(main_bag.values())
            tfidf = {term: float(frequency) / denominator * idf.get(term, max_idf) for term, frequency in main_bag.items()}
            terms = tfidf.items()
            terms.sort(key=lambda x: x[1], reverse=True)
            print "category %s: %s" % (i, '; '.join(term[0].encode('utf8') for term in terms[:50]))


    def stem(self, word):
        return self.stemmer.stem(word, 0, len(word) - 1)

    def tokenize(self, text):
        tokens = [self.stem(token.strip('"\'!.-:_')) for token in text.upper().replace('&AMP;', '&').split()
                  if token not in self.stop_words]
        tokens = filter(None, tokens)
        bigrams = [' '.join(tokens[i:i + 2]) for i in range(0, len(tokens) - 1)]
        return tokens # + bigrams

    def _load_stopwords(self):
        with open(os.path.join(os.path.dirname(__file__), 'english.stop')) as f:
            self.stop_words = set(self.stem(line.rstrip().upper()) for line in f)
        self.stop_words.add('&')
