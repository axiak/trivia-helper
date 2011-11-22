#!/bin/bash

if [[ $(id -u) -eq 0 ]]; then
    sudo -H -i -u axiak "$0"
    exit 0
fi

# Replace these three settings.
PROJDIR="/home/axiak/BigDocuments/trivia/triviaopt"
PIDFILE="$PROJDIR/mysite.pid"
SOCKET="/tmp/mysite.sock"

cd $PROJDIR

source bin/activate

coffee -c public_html/static/js/main.coffee

if [ -f $PIDFILE ]; then
    kill `cat -- $PIDFILE`
    rm -f -- $PIDFILE
fi

nohup /usr/bin/env - \
  PYTHONPATH="../python:.." \
  ./manage.py runfcgi socket=$SOCKET pidfile=$PIDFILE \
              maxchildren=3 errlog=$PROJDIR/error.log \
              outlog=$PROJDIR/out.log  &>/dev/null

chmod 777 "$SOCKET"
