#!/usr/bin/python3
from flask_socketio import SocketIO, send, emit
from flask import Flask, flash, request, jsonify, render_template, redirect, url_for

app = Flask(__name__)
sio = SocketIO(app, async_mode=None)
clientconnected = ''

@app.route('/msg', methods=['GET'])
def send_message():
    print(request.headers['msg'])
    print(request.headers['sid'])

    sio.emit('message', request.headers['msg'], namespace='/test', room=request.headers['sid'])
    return jsonify('OK')

@sio.on('connect', namespace='/test')
def connect():
    global clientconnected
    print('connected')
    print(request.sid)
    clientconnected = request.sid

@sio.on('client_reply', namespace='/test')
def client_reply(msg):
    print("Reply from client: {}".format(msg))
    sio.emit('message', "ACK", namespace='/test', room=clientconnected)
    print("Done")

import signal, os
def graceful_killer(signal, frame):
    print('Goodbye!')
    # sio.stop()
    os._exit(0)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, graceful_killer)
    signal.signal(signal.SIGTERM, graceful_killer)
    sio.run(app, host='0.0.0.0', port=5000)
    