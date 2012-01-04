from django.contrib import admin
from triviaopt.jeopardy import models
from ajax_select.admin import AjaxSelectAdmin
from ajax_select import make_ajax_form

for model in ('Game', 'Category', 'Contestant', 'Question',):
    admin.site.register(getattr(models, model))

class AnswerAdmin(AjaxSelectAdmin):
    form = make_ajax_form(models.Answer, {'question': 'question'})

admin.site.register(models.Answer, AnswerAdmin)
