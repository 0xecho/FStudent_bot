from time import sleep
import botogram
import requests

from api import EstudentAPI
from config import TELEGRAM_BOT_TOKEN, heartbeat_server, bot_id
from db import User, Course, Assessment, Result, UserCourse
from utils import get_notifiable_users_data, format_result, get_total_users_count

bot = botogram.create(TELEGRAM_BOT_TOKEN)

CONVERSATION = {
    
}

USERNAMES = {

}

PASSWORDS = {

}

@bot.process_message
def process(chat, message):
    if chat.id in CONVERSATION:
        ret = CONVERSATION[chat.id](chat, message)
    else:
        chat.send("I'm sorry, I don't understand you. Please use /help to see all available commands")

@bot.command("start")
def start(chat, message):
    chat.send("Hello, I'm a FStudent! I will notify you when new ውጤት is available estudent ላይ")
    chat.send("You can use /subscribe to subscribe to notifications\nYou can use /unsubscribe to unsubscribe from notifications")
    chat.send("NOTE: This bot will save your username and password in the database. IT MUST DO THAT TO WORK! I MADE THIS BOT FOR PERSONAL USE ONLY! USE IT AT YOUR OWN RISK! [THE CODE IS AVAILABLE ON GITHUB]")

@bot.command("subscribe")
def subscribe(chat, message):
    """Register your username and password to receive notifications on new results"""
    user_obj = User.select().where(User.chat_id == chat.id)
    if user_obj.count() == 0:
        chat.send("Please enter your id")
        CONVERSATION[chat.id] = accept_username
    else:
        chat.send("You are already subscribed")

@bot.command("unsubscribe")
def unsubscribe(chat, message):
    """Delete user data from database and unsubscribe from notifications"""
    user_obj = User.select().where(User.chat_id == chat.id)
    if user_obj.count() == 0:
        chat.send("You are not subscribed to notifications.")
    else:
        chat.send("Are you sure you want to unsubscribe?\nAll of your user data will be deleted when you do this. Type /unsubscribe_confirm to confirm")

@bot.command("unsubscribe_confirm", hidden=True)
def unsubscribe_confirm(chat, message):
    user_obj = User.select().where(User.chat_id == chat.id)
    if user_obj.count() == 0:
        chat.send("You are not subscribed to notifications.")
    else:
        user = user_obj[0]
        Result.delete().where(Result.user == user).execute()
        UserCourse.delete().where(UserCourse.user == user).execute()
        user.delete_instance()        
        chat.send("You are now unsubscribed from notifications")

@bot.command("settings")
def settings(chat, message):
    """Change user preferences"""
    user = User.select().where(User.chat_id == chat.id)
    if user.count() == 0:
        chat.send("Subscribe to notifications first")
    else:
        user = user[0]
        chat.send("You can change your settings here")
        chat.send("You can use /full_notifications to receive full results of new assessments")
        chat.send("You can use /short_notifications to receive the course name only")
        chat.send("You can use /unsubscribe to unsubscribe from notifications")

@bot.command("full_notifications")
def full_notifications(chat, message):
    """Subscribe to full notifications: Send full results of new assessments"""
    user = User.select().where(User.chat_id == chat.id)
    if user.count() == 0:
        chat.send("Subscribe to notifications first")
    else:
        user = user[0]
        user.full_notifications = True
        user.save()
        chat.send("You will now receive full results of new assessments")

@bot.command("short_notifications")
def short_notifications(chat, message):
    """Subscribe to short notifications: Send only course name when new results are available"""
    user = User.select().where(User.chat_id == chat.id)
    if user.count() == 0:
        chat.send("Subscribe to notifications first")
    else:
        user = user[0]
        user.full_notifications = False
        user.save()
        chat.send("You will now receive course name only")

def accept_username(chat, message):
    USERNAMES[chat.id] = message.text
    chat.send("Please enter your password")
    CONVERSATION[chat.id] = accept_password
    return True

def accept_password(chat, message):
    PASSWORDS[chat.id] = message.text
    CONVERSATION[chat.id] = None
    api = EstudentAPI(USERNAMES[chat.id], PASSWORDS[chat.id])
    try:
        api.check_auth_headers()
        onboard_user(USERNAMES[chat.id], PASSWORDS[chat.id], chat.id)
    except Exception as e:
        chat.send("Invalid username or password")
    return True

def onboard_user(username, password, chat_id):
    user = User.get_or_create(username=username, password=password, chat_id=chat_id)[0]
    api = EstudentAPI(username, password)
    course_lists = api.get_course_list()
    telegram_user = bot.chat(chat_id)
    for course_name, course_id  in course_lists.items():
        course_id = str(course_id)
        results = api.get_course_results(course_id)
        maxMark = results['total_marks']
        course = Course.get_or_create(name=course_name, eid=course_id, maxMark=maxMark)[0]
        UserCourse.get_or_create(user=user, course=course, studentMark=results['student_marks'], letterGrade=results['grade'])
        for assessment_name, marks in results['assessments'].items():
            assessment = Assessment.get_or_create(
                course=course, name=assessment_name, maxMark=marks['maximum_mark'])[0]
            Result.get_or_create(user=user, assessment=assessment, result=marks['result'])
        
        formatted_data = format_result(results)
        if user.full_notifications:
            telegram_user.send(formatted_data)
    telegram_user.send("You are now subscribed to notifications")
    telegram_user.send("You can use /settings to change your preferences, or use /help to see all available commands")

@bot.timer(60)
def notify_new_results():
    users = get_notifiable_users_data()
    for user, data in users.items():
        telegram_user = bot.chat(user.chat_id)
        for updated_course, updated_result in data.items():
            if user.full_notifications:
                formatted_data = format_result(updated_result)
                telegram_user.send(formatted_data)
            else:
                telegram_user.send(f"{updated_course.name} has new results!")
        sleep(1)

@bot.message_contains("")
def error_message(chat, message):
    chat.send("I'm sorry, I don't understand what you mean. Please use /help to see all available commands")

@bot.timer(60)
def send_heartbeat():
    total_users = get_total_users_count()
    requests.get(heartbeat_server +
                 f"/heartbeat?user_count={total_users}&bot_uuid={bot_id}")

if __name__ == "__main__":
    bot.run(workers=1)