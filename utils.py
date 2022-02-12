import logging
from icecream import ic

from api import EstudentAPI
from db import *

def get_all_courses():
    logging.info('Getting all courses')
    courses = Course.select()
    logging.debug('Got all courses: %s' % courses)
    return courses

def get_course_first_user(course):
    logging.info('Getting first user of course %s' % course.name)
    user_course = UserCourse.select().where(UserCourse.course == course).order_by(UserCourse.id.desc()).get() or None
    user = user_course.user if user_course is not None else None
    logging.debug('Got first user of course %s: %s' % (course.name, user))
    return user

def get_all_course_users(course):
    logging.info('Getting all users of course %s' % course.name)
    user_courses = UserCourse.select().where(UserCourse.course == course)
    users = []
    for user_course in user_courses:
        users.append(user_course.user)
    logging.debug('Got all users of course %s: %s' % (course.name, users))
    return users

def get_latest_course_results(user, course):
    logging.info('Getting latest results of course %s for user %s' % (course.name, user.username))
    api = EstudentAPI(user.username, user.password)
    results = api.get_course_results(course.eid)
    logging.debug('Got latest results of course %s for user %s: %s' % (course.name, user.username, results))
    return results

def get_student_mark(user, course):
    logging.info('Getting student mark of course %s for user %s' % (course.name, user.username))
    user_course = UserCourse.select().where(UserCourse.user == user, UserCourse.course == course).get()
    student_mark = user_course.studentMark if user_course is not None else None
    logging.debug('Got student mark of course %s for user %s: %s' % (course.name, user.username, student_mark))
    return student_mark

def get_updated_courses():
    logging.info('Getting updated courses')
    updated_courses = []
    all_courses = get_all_courses()
    for course in all_courses:
        user = get_course_first_user(course)
        logging.debug('Getting latest results of course %s for user %s' % (course.name, user.username))
        if user is not None:
            results = get_latest_course_results(user, course)
            logging.info('Comparing stored results of course %s for user %s with latest results' % (course.name, user.username))
            logging.debug('Stored results: %s' % get_student_mark(user, course))
            logging.debug('Latest results: %s' % results["student_marks"])
            if results['student_marks'] != get_student_mark(user, course):
                logging.info('Course %s for user %s has been updated' % (course.name, user.username))
                updated_courses.append(course)
    return updated_courses

def get_notifiable_users_and_courses():
    logging.info('Getting notifiable users and courses')
    user_courses = {}
    updated_courses = get_updated_courses()
    for course in updated_courses:
        users = get_all_course_users(course)
        for user in users:
            if user not in user_courses:
                user_courses[user] = [ course ]
            else:
                user_courses[user].append(course)
    return user_courses

def get_user_latest_result(user, course):
    api = EstudentAPI(user.username, user.password)
    results = api.get_course_results(course.eid)
    return results

def get_notifiable_users_data():
    notifiable_users = get_notifiable_users_and_courses()
    notifiable_users_data = {}
    for user in notifiable_users:
        courses = notifiable_users[user]
        notifiable_users_data[user] = {}
        for course in courses:
            latest_course_result = get_user_latest_result(user, course)
            notifiable_users_data[user][course] = latest_course_result
            for assessment_name, marks in latest_course_result['assessments'].items():
                assessment_obj = Assessment.select().where(Assessment.name == assessment_name, Assessment.course == course).get()
                if not assessment_obj:
                    assessment_obj = Assessment(name=assessment_name, course=course)
                assessment_obj.maxMark = marks['maximum_mark']
                assessment_obj.save()
                result_obj = Result.select().where(Result.assessment == assessment_obj, Result.user == user).get()
                if not result_obj:
                    result_obj = Result(assessment=assessment_obj, user=user)
                result_obj.result = marks['result']
                result_obj.save()
            user_course_obj = UserCourse.select().where(UserCourse.user == user, UserCourse.course == course).get()
            if not user_course_obj:
                user_course_obj = UserCourse(user=user, course=course)
            user_course_obj.studentMark = latest_course_result['student_marks']
            user_course_obj.letterGrade = latest_course_result['grade']
            user_course_obj.save()

    return notifiable_users_data


def format_result(result):
    md_string = f"""
*Course:* {result['course_title']}
*Grade:* {result['grade']}
*Student Marks:* {result['student_marks']}/{result['total_marks']}
*Assessments:*
"""
    for assessment_name, marks in result['assessments'].items():
        md_string += f"""{assessment_name}: \t{marks['result']} / {marks['maximum_mark']}
"""
    md_string = md_string.replace("_", "\\_")
    return md_string
    