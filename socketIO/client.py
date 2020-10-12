#!/usr/bin/python3
import socketio
import requests
from requests.exceptions import ConnectionError

sio = socketio.Client()
server = 'localhost'

def replyMsg():
    msg = str(input('REP: '))
    sio.emit('client_reply', msg, namespace='/test')

@sio.on('message', namespace='/test')
def on_message(data):
    print('MSG from {0}: \n{1}'.format(server, data))
    print('-'*40)
    replyMsg()

@sio.on('result', namespace='/test')
def result(data):
    print('Result =  {0}'.format(data))

@sio.event
def connect():
    print("I'm connected!")

@sio.event
def connect_error():
    print("The connection failed!")

@sio.event
def disconnect():
    print("I'm disconnected!")
    os._exit(0)


import signal, os
def graceful_killer(signal, frame):
    print('Goodbye!')
    sio.disconnect()
    os._exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, graceful_killer)
    signal.signal(signal.SIGTERM, graceful_killer)

    try:
        sio.connect('http://{0}:5000/test'.format(server))
        print('my sid is', sio.sid)
    except Exception as e:
        print('ERROR: can\'t connect to server due to {0}'.format(str(e)))

