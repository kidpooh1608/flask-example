#!/usr/bin/python3
import subprocess, json, time
import threading
from threading import Thread, Lock
from queue import Queue
import os, time
from database import operationsDB
from datetime import datetime

def run_command(command):
        process = subprocess.Popen(command.split(), stdout=subprocess.PIPE, universal_newlines=True)
        out = ''
        while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                        break
                if output:
                        tmp = output.strip()
                        # print(tmp)
                        out += tmp + '\n'
        returnCode = process.poll()
        return returnCode, out


class threadPool(Thread):
    def __init__(self, limitThread=100, workerQueue=Queue(100), logger=None):
        super().__init__(name="threadPool")
        self.workerQueue = workerQueue
        self.limitThread = limitThread
        self.logger = logger

    def run(self):
        self.logger.debug("Started thread pool at id = {0}".format(threading.currentThread().ident))
        while True:
            if threading.active_count() > self.limitThread:
                self.logger.debug("Thread number reached to limit = {0}".format(self.limitThread))
            else:
                worker = self.workerQueue.get()
                worker.start()

currentTasksLock = Lock()
status = ["INPROGRESS", "DONE"]
result = ["OK", "FAILED"]

class task():
    def __init__(self):
          pass

    def run(self, currentTasks, taskId, cmd, logger, dbDir):
        logger.debug("Running {0} in thread {1}".format(taskId, threading.get_ident()))
        try:
            db = operationsDB(db=dbDir, logger=logger)
            with currentTasksLock:
                currentTasks[taskId] = {'status': status[0], 'result': 'NA', 'console': '', 'script': cmd, 'timestamp': str(datetime.now())}
                db.add_task(taskid=taskId, item=currentTasks[taskId])

            code, con = run_command(cmd)
            with currentTasksLock:
                currentTasks[taskId]["console"] = con
                currentTasks[taskId]["result"] = result[1 if code !=0 else 0]
                currentTasks[taskId]["status"] = status[1]
                db.update_task(taskid=taskId, item=currentTasks[taskId])
        except Exception as e:
            logger.error("in thread {0}: \n {1}".format(threading.currentThread().getName(), str(e)))
        