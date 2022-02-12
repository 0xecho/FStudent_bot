from peewee import *

from config import db

class User(Model):
    chat_id = IntegerField()
    username = CharField()
    password = CharField()
    full_notifications = BooleanField(default=True)

    class Meta:
        database = db

class Course(Model):
    name = CharField()
    eid = CharField()
    maxMark = FloatField(null=True)

    class Meta:
        database = db

class Assessment(Model):
    course = ForeignKeyField(Course, backref='assessments')
    name = CharField(null=True)
    maxMark = FloatField(null=True)

    class Meta:
        database = db

class Result(Model):
    user = ForeignKeyField(User, backref='results')
    assessment = ForeignKeyField(Assessment, backref='results')
    result = FloatField(null=True)

    class Meta:
        database = db

class UserCourse(Model):
    user = ForeignKeyField(User, backref='courses')
    course = ForeignKeyField(Course, backref='users')
    studentMark = FloatField(null=True)
    letterGrade = CharField(null=True)

    class Meta:
        database = db