#!/usr/bin/python3
# from flask_socketio import SocketIO, send, emit
from flask import Flask, flash, request, jsonify, render_template, redirect, url_for, Response
from flask_bootstrap import Bootstrap

import logging
from logging.handlers import RotatingFileHandler
import uuid
import configparser
from queue import Queue
from threading import Thread
import threading

from database import operationsDB
from operations import task, threadPool, status, result

app = Flask(__name__)
bootstrap = Bootstrap(app)
currentTasks = {}

logLevel = {'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'ERROR': logging.ERROR,
            'WARN': logging.WARNING}

config = configparser.ConfigParser()
config.read('../etc/server.conf')

bufferSize = int(config['internal']['bufferSize'])
limitThread = int(config['internal']['limitThread'])
workerQueue = Queue(bufferSize)
pool = threadPool(limitThread=limitThread ,workerQueue=workerQueue, logger=app.logger)

def runTask(cmd):
    global currentTasks
    if workerQueue.full():
            return jsonify({'err': 'Server is overloading ...'}), 503
    
    taskId = str(uuid.uuid4().hex)
    dbDir = config['internal']['dbDir']
    worker = Thread(target=task().run,name='task-{0}'.format(threading.current_thread().getName()),
                    args=(currentTasks,taskId, cmd, app.logger, 'sqlite:///{0}'.format(dbDir)), daemon=True)
    workerQueue.put(worker)

    return jsonify({'id': '{}'.format(taskId)})

def loadTaskFromDB():
    global currentTasks
    dbDir = config['internal']['dbDir']
    if os.path.isfile(dbDir):
        db = operationsDB(db='sqlite:///{0}'.format(dbDir), logger=app.logger)
        code, items = db.read_task()
        if code:
            for it in items:    
                item = {'status': it.status,
                        'result': it.result,
                        'console': it.console,
                        'script': it.script,
                        'timestamp': it.timestamp}
                if it.status == status[0]:
                    item['result'] = result[1]
                    db.update_task(it.taskid, item)
                currentTasks[it.taskid] = item
        else:
            app.logger.error("Can't read tasks from database due to err {0}".format(items))

def getTaskFromCache(taskId):
    if taskId in currentTasks:
        return jsonify(currentTasks[taskId])
    else:
        return jsonify("{0} not found".format(taskId)), 404

def clearTask():
    global currentTasks
    dbDir = config['internal']['dbDir']
    db = operationsDB(db='sqlite:///{0}'.format(dbDir))
    currentTasks.clear()
    err, msg = db.delete_task_table()
    if not err:
        app.logger.error(">> clearTask: {0}".format(msg))

    return err


#####################################################################################################
##################################--------server--------###################################
#####################################################################################################

@app.route('/', methods=['GET'])
def index():
    if request.method == 'GET':
        return render_template('index.html', tasks=currentTasks)

@app.route('/clear-history', methods=['GET'])
def clear_history():
    if request.method == 'GET' and clearTask():
        app.logger.debug("History was cleaned!")
        return jsonify('OK')
    
    return jsonify('NOT OK')

@app.route('/status', methods=['GET'])
def status():
    if 'id' in request.headers:
        return getTaskFromCache(request.headers['id'])

    return jsonify(currentTasks)

@app.route('/test-commands', methods=['POST'])
def test_commands():
    if request.method == 'POST' and'cmd' in request.headers:
        return runTask(request.headers['cmd'])

    return jsonify({'err': 'Retry with correct headers and method'}), 403

@app.errorhandler(Exception)
def handle_error(e):
    app.logger.error(str(e))
    return jsonify(error=str(e)), 500

import signal, os
def graceful_killer(signal, frame):
    app.logger.info("====Stopping server====")
    os._exit(0)

def logInit():
    formatter = logging.Formatter(
        "[%(asctime)s] %(threadName)s %(levelname)s - %(message)s")

    handler = RotatingFileHandler(config['logger']['logAppFile'], maxBytes=10000000, backupCount=5)
    handler.setLevel(logLevel[config['logger']['logAppLevel']])
    handler.setFormatter(formatter)

    app.logger.setLevel(logging.DEBUG)
    app.logger.addHandler(handler)

    logger = logging.getLogger('werkzeug')
    werkzeugHandler = RotatingFileHandler(config['logger']['logwerkzeugFile'], maxBytes=10000000, backupCount=5)
    logger.setLevel(logLevel[config['logger']['logwerkzeugLevel']])
    logger.addHandler(werkzeugHandler)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, graceful_killer)
    signal.signal(signal.SIGTERM, graceful_killer)

    logInit()
    loadTaskFromDB()
    port = config['internal']['port']
    app.logger.info("====Starting server at port={0}====".format(port))
    pool.start()
    app.run(host='0.0.0.0', port=port)
    
