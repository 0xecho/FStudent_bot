import requests

class EstudentAPI:
    def __init__(self, user_name, password):
        self.user_name = user_name
        self.password = password
        self.graphql_url = "http://10.240.1.89/api//graphql"
        self.auth_url = "http://10.240.1.89:80/api/auth/sign_in"
        self.default_headers = {
                "Accept": "application/json, text/plain, */*",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.105 Safari/537.36",
                "Origin": "http://10.240.1.89",
                "Referer": "http://10.240.1.89/",
                "Accept-Encoding": "gzip, deflate",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "close"
            }
        self.auth_headers = {}

    def update_auth_headers(self):
        auth_session = requests.session()
        resp = auth_session.post(self.auth_url, headers=self.default_headers, data={
                                 "user_name": self.user_name, "password": self.password})
        resp_headers = resp.headers
        # Check if response is valid, else raise exception
        self.auth_headers = self.default_headers.copy()
        self.auth_headers.update({
                    "Content-Type": "application/json",
                    "expiry": resp_headers["expiry"],
                    "access-token": resp_headers["access-token"],
                    "token-type": resp_headers["token-type"],
                    "uid": resp_headers["uid"],
                    "client": resp_headers["client"]
                })
    
    def is_auth_headers_valid(self):
        graph_ql_query = """ headerProfile { id } """
        graph_ql_obj = {"operationName": "headerProfile", "query": graph_ql_query, "variables": {}}
        resp = requests.post(self.graphql_url, headers=self.auth_headers, json=graph_ql_obj)
        return resp.status_code == 200
    
    def check_auth_headers(self):
        if not self.is_auth_headers_valid():
            self.update_auth_headers()
        if not self.is_auth_headers_valid():
            raise Exception("Invalid auth headers")
    
    def get_course_list(self):
        self.check_auth_headers()
        latest_semester_id = self.get_latest_semester()
        graph_ql_query = "{studentTranscript { academicYearSemester { id } courseEnrollments { id course { titleAndCode }}}}"
        graph_ql_obj = {"operationName": None, "variables": {}, "query": graph_ql_query}
        resp = requests.post(self.graphql_url, headers=self.auth_headers, json=graph_ql_obj)
        
        course_list = {}
        for year in resp.json()["data"]["studentTranscript"]:
            if year["academicYearSemester"]["id"] == latest_semester_id:
                for course in year["courseEnrollments"]:
                    course_list[course["course"]["titleAndCode"]] = course["id"]

        return course_list
    
    def get_course_results(self, course_id):
        self.check_auth_headers()
        graph_ql_query = """query assessmentResultForEnrollment($id: ID!) { assessmentResultForEnrollment(id: $id) { id sumOfMaximumMark sumOfResults course { courseTitle } studentGrade { letterGrade } assessmentResults { result assessment { assessmentName maximumMark assessmentType }}}}"""
        graph_ql_obj = {"operationName": "assessmentResultForEnrollment", "variables": {"id": str(course_id)}, "query": graph_ql_query}
        resp = requests.post(self.graphql_url, headers=self.auth_headers, json=graph_ql_obj)
        resp_data = resp.json()["data"]["assessmentResultForEnrollment"]
        course_result = {}
        course_result["total_marks"] = resp_data["sumOfMaximumMark"] if resp_data and "sumOfMaximumMark" in resp_data else 0
        course_result["student_marks"] = resp_data["sumOfResults"] if resp_data and "sumOfResults" in resp_data else 0
        course_result["grade"] = resp_data["studentGrade"]["letterGrade"] if resp_data and resp_data[
            "studentGrade"] and "letterGrade" in resp_data["studentGrade"] else "N/A"
        course_result["course_title"] = resp_data["course"]["courseTitle"] if resp_data and "courseTitle" in resp_data["course"] else "N/A"
        course_result["assessments"] = {} 
        for assessment in resp_data["assessmentResults"] if resp_data and "assessmentResults" in resp_data else []:
            course_result["assessments"][assessment["assessment"]["assessmentName"]] = {
                "result": assessment["result"],
                "maximum_mark": assessment["assessment"]["maximumMark"],
            }

        return course_result
    
    def get_latest_semester(self):
        self.check_auth_headers()
        graph_ql_query = """{\n  studentActiveSemester {\n    id\n    semesterName\n    __typename\n  }\n}\n"""
        graph_ql_obj = {"operationName": None, "variables": {}, "query": graph_ql_query}
        resp = requests.post(self.graphql_url, headers=self.auth_headers, json=graph_ql_obj)
        return resp.json()["data"]["studentActiveSemester"]["id"]
        

if __name__ == "__main__":
    # FOR TESTING
    echo = EstudentAPI("TEMP_USERNAME", "TEMP_PASSWORD")
    courses = echo.get_course_list()
    print(courses)
    print("---")
    for _, course_id in courses.items():
        print(echo.get_course_results(course_id))
