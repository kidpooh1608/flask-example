#!/usr/bin/python3
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy import Column, Date, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class task(Base):
    __tablename__ = 'taskId'
    id = Column(Integer, primary_key=True)
    taskid = Column(String(64), unique=True, index=True)
    status = Column(String())
    result = Column(String())
    console = Column(String())
    script = Column(String())
    timestamp = Column(String())

    def __init__(self, item):
        self.taskid = item['taskid']
        self.status = item['status']
        self.result = item['result']
        self.script = item['script']
        self.timestamp = item['timestamp']

class operationsDB():
    def __init__(self, db='sqlite:///db/history.db', logger=None):
        self.engine = create_engine(db, echo=False)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        self.logger = logger

    def delete_task_table(self):
        try:
            self.session.query(task).delete()
            self.session.commit()
            self.logger.debug("Task table was deleted")
            return True
        except Exception as e:
            self.logger.error("Can't delete task table {0}".format(str(e)))
            return False

    def add_task(self, taskid, item):
        try:
            item['taskid'] = taskid
            _item = task(item)
            self.session.add(_item)
            self.session.commit()
            self.logger.debug("Task {} was added".format(taskid))
            return True
        except Exception as e:
            self.session.rollback()
            self.logger.error("Can't add task {0} due to err {1}".format(taskid, str(e)))
            return False

    def update_task(self, taskid, item):
        try:
            _item = self.session.query(task).filter(task.taskid == taskid).all()
            _item[0].status = item['status']
            _item[0].result = item['result']
            _item[0].script = item['script']
            _item[0].console = item['console']
            self.session.commit()
            self.logger.debug("Task {} was updated".format(taskid))
            return True
        except Exception as e:
            self.session.rollback()
            self.logger.error("Can't update task {0} due to err {1}".format(taskid, str(e)))
            return False

    def read_task(self, taskid=''):
        if taskid:
            try:
                item = self.session.query(task).filter(task.taskid == taskid).all()
                return True, item
            except Exception as e:
                return False, str(e)
        else:
            try:
                item = self.session.query(task).all()
                return True, item
            except Exception as e:
                return False, str(e)