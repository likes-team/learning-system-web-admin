from flask_weasyprint import HTML, render_pdf
from flask import render_template
from prime_admin.services.student import StudentService



class AttendanceList:
    def __init__(self, teacher=None, batch_no=None, schedule=None, session=None):
        self.teacher = teacher
        self.batch_no = batch_no
        self.schedule = schedule
        self.session = session
        
        self._get_attendance_list()


    def _get_attendance_list(self):
        service = StudentService(batch_no=self.batch_no, schedule=self.schedule, session=self.session)
        self.data = service.fetch_students()


    def print(self):
        html = render_template(
            'lms/pdfs/attendance_list_pdf.html',
            teacher=self.teacher,
            batch_no=self.batch_no,
            schedule=self.schedule,
            session=self.session,
            students=self.data
        )
        return render_pdf(HTML(string=html))
