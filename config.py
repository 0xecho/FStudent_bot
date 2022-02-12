import os
from peewee import *

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

db = SqliteDatabase('db.sqlite')
heartbeat_server = os.environ.get("HEARTBEAT_SERVER")
bot_id = os.environ.get("BOT_ID")