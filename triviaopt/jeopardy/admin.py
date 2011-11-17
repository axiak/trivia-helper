from django.contrib import admin
from triviaopt.jeopardy import models

for model in ('Game', 'Category', 'Contestant', 'Question', 'Answer',):
    admin.site.register(getattr(models, model))
