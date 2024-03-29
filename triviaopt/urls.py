from django.conf.urls.defaults import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

from ajax_select import urls as ajax_select_urls

admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'triviaopt.jeopardy.views.index', name='index'),
    url(r'^login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^next-question/$', 'triviaopt.jeopardy.views.next_question', name='next'),
    url(r'^answer-question/$', 'triviaopt.jeopardy.views.answer_question', name='answer'),
    url(r'^change-answer/$', 'triviaopt.jeopardy.views.change_answer', name='change_answer'),
    # url(r'^triviaopt/', include('triviaopt.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    url(r'^admin/lookups/', include(ajax_select_urls)),
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
