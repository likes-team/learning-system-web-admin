import os
import glob
import io
from datetime import datetime
from shutil import copyfile
from flask import current_app
from reportlab.pdfgen import canvas
from PyPDF2 import PdfFileWriter, PdfFileReader



class Certificate:
    def __init__(self, cert_type, inch=72.0):
        """Get source dir base on cert_type

        Args:
            cert_type (str): Certification type. Possible value is: 
            no_partner_no_underline, partner_underline, partner_no_underline, no_partner_underline

        Raises:
            ValueError: InceptionError: cert_type is not a valid value
        """
        if cert_type == 'no_partner_no_underline':
            src_dir = current_app.config['PDF_FOLDER'] + 'cert_no_partner_no_underline.pdf'
        elif cert_type == 'partner_underline':
            src_dir = current_app.config['PDF_FOLDER'] + 'cert_partner_underline.pdf'
        elif cert_type == 'partner_no_underline':
            src_dir = current_app.config['PDF_FOLDER'] + 'cert_partner_no_underline.pdf'
        elif cert_type == 'no_partner_underline':
            src_dir = current_app.config['PDF_FOLDER'] + 'cert_no_partner_underline.pdf'
        else:
            raise ValueError("InceptionError: cert_type is not a valid value")
        self.src_dir = src_dir
        self.cert_type = cert_type
        self.inch = inch
        self._get_dst_dir()
        self._delete_old_files()
        self._copy_file()


    def _get_dst_dir(self):
        self.file_name = "generated/" +"cert_" + str(datetime.timestamp(datetime.utcnow())) + '.pdf'
        self.dst_dir = os.path.join(current_app.config['PDF_FOLDER'], self.file_name)


    def _delete_old_files(self):
        old_files = glob.glob(current_app.config['PDF_FOLDER'] + 'generated/*.pdf')
        for file in old_files:
            os.remove(file)


    def _copy_file(self):
        copyfile(self.src_dir, self.dst_dir)


    def create(self):
        """Create pdf canvas with Reportlab
        """
        self.packet = io.BytesIO()
        self.pdf: canvas.Canvas = canvas.Canvas(self.packet, pagesize=(14.76*self.inch, 11.33*self.inch))


    def set_full_name(self, name, font_size):
        self.pdf.setFont('Black Chancery', font_size)
        self.pdf.drawCentredString(320, 270, name)
        
    
    def set_date(self, day, month, year, font_size=18):
        self.pdf.setFont('Black Chancery', font_size)
        if self.cert_type in ['partner_underline', 'partner_no_underline']:
            day_x, day_y = 150, 182
            month_x, month_y = 247, 182
            year_x, year_y = 312, 182
        elif self.cert_type == "no_partner_underline":
            day_x, day_y = 150, 182
            month_x, month_y = 245, 182
            year_x, year_y = 312, 182
        else:
            day_x, day_y = 160, 182
            month_x, month_y = 255, 182
            year_x, year_y = 322, 182
        self.pdf.drawCentredString(day_x, day_y, day)
        self.pdf.drawCentredString(month_x, month_y, month)
        self.pdf.drawCentredString(year_x, year_y, year)
        
    
    def set_address(self, address, font_size):
        self.pdf.setFont('Black Chancery', font_size)
        if self.cert_type in ['partner_underline', 'partner_no_underline']:
            self.pdf.drawString(360, 182, address)
        else:
            self.pdf.drawString(370, 182, address)
    
    
    def set_teacher(self, name, font_size):
        self.pdf.setFont('ArialTh', font_size)
        if self.cert_type in ['partner_underline', 'partner_no_underline']:
            self.pdf.drawCentredString(140, 105, name)
        else:
            self.pdf.drawCentredString(225, 75, name)


    def set_manager(self, name, font_size):
        if self.cert_type in ['partner_underline', 'partner_no_underline']:
            self.pdf.setFont('ArialTh', font_size)
            self.pdf.drawCentredString(507, 105, name)
    
    
    def set_certificate_no(self, no, font_size=15):
        self.pdf.setFont('Black Chancery', font_size)
        self.pdf.drawString(682, 498, no)


    def save(self):
        self.pdf.showPage()
        self.pdf.save()
        # Move to the beginning of the StringIO buffer
        self.packet.seek(0)
        new_pdf = PdfFileReader(self.packet)
        # Read your existing PDF
        existing_pdf = PdfFileReader(open(self.src_dir, "rb"))
        output = PdfFileWriter()
        # Add the "watermark" (which is the new pdf) on the existing page
        page = existing_pdf.getPage(0)
        page.mergePage(new_pdf.getPage(0))
        output.addPage(page)
        # Finally, write "output" to a real file
        output_stream = open(self.dst_dir, "wb")
        output.write(output_stream)
        output_stream.close()
        
    
    def get_file_name(self):
        return self.file_name

        
