#!/bin/bash

# Replace these three settings.
PROJDIR="/home/axiak/BigDocuments/trivia/triviaopt"
PIDFILE="$PROJDIR/mysite.pid"
SOCKET="/tmp/mysite.sock"

cd $PROJDIR
if [ -f $PIDFILE ]; then
    kill `cat -- $PIDFILE`
    rm -f -- $PIDFILE
fi

exec /usr/bin/env - \
  PYTHONPATH="../python:.." \
  ./manage.py runfcgi socket=$SOCKET pidfile=$PIDFILE

chmod 777 "$SOCKET"
chmod 777 "$SOCKET"
