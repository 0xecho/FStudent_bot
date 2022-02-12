import os
from peewee import *

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

db = SqliteDatabase('db.sqlite')
heartbeat_server = 'http://localhost:5000'
bot_id = '@fstudent_bot'