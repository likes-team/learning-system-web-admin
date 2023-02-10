from flask_weasyprint import HTML, render_pdf
from flask import render_template
from prime_admin.services.student import StudentService
from prime_admin.services.batch import BatchService
from prime_admin.services.branch import BranchService
from prime_admin.helpers.query_filter import StudentQueryFilter
from prime_admin.utils.date import get_local_date_now, format_date
from prime_admin.utils.session import get_time_by_session



class AttendanceList:
    def __init__(self, students, query_filter: StudentQueryFilter):
        self.students = students
        self.query_filter = query_filter
        self.teacher = None
        self.batch_no = None
        self.branch = None
        self.schedule = None
        self.date = None
        self.time = None
        self.session = None


    @classmethod
    def fetch(cls, query_filter: StudentQueryFilter):
        service = StudentService.find_students(query_filter)
        students = service.get_data()
        return cls(students, query_filter)

    
    def set_teacher(self, teacher):
        self.teacher = teacher


    def _get_report_details(self):
        self.batch_no = BatchService.get_name_by_id(self.query_filter.get_filter()['batch_number'])
        self.branch = BranchService.get_name_by_id(self.query_filter.get_filter()['branch'])
        self.schedule = self.query_filter.get_filter()['schedule']
        self.date = format_date(get_local_date_now())
        self.session = self.query_filter.get_filter()['session']
        self.time = get_time_by_session(self.session)


    def generate_pdf(self):
        self._get_report_details()
        
        html = render_template(
            'lms/pdfs/attendance_list_pdf.html',
            teacher=self.teacher,
            batch_no=self.batch_no,
            schedule=self.schedule,
            branch=self.branch,
            date=self.date,
            time=self.time,
            session=self.session,
            students=self.students
        )
        return render_pdf(HTML(string=html))
