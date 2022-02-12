from peewee import *
from db import *

def initialize_db():
    db.create_tables([User, Course, Assessment, Result, UserCourse])

if __name__ == '__main__':
    initialize_db()