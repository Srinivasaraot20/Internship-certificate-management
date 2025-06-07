import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class CertificateGenerator:
    """Generate PDF certificates with dynamic content using a background image"""
    
    def __init__(self):
        self.cert_width, self.cert_height = landscape(A4)
        self.margin = 0.5 * inch
        
        # Try to register custom fonts (fallback to default if not available)
        try:
            # Register fonts if available (e.g., pdfmetrics.registerFont(TTFont('Arial', 'Arial.ttf')))
            # For this example, we'll stick to Helvetica which is built-in.
            pass
        except Exception as e:
            logger.warning(f"Custom fonts not available, using default fonts: {e}")
    
    def generate_certificate(self, student, background_image_path, qr_code_path=None):
        """
        Generate certificate PDF for a student with a custom background image.
        
        Args:
            student: An object containing student details (e.g., student_name,
                     certificate_id, internship_name, internship_start_date,
                     internship_end_date, mentor_name, company_name, performance_rating).
            background_image_path (str): Path to the background image for the certificate.
            qr_code_path (str, optional): Path to the QR code image. Defaults to None.
        """
        try:
            # Create certificates directory if it doesn't exist
            cert_dir = 'certificates'
            os.makedirs(cert_dir, exist_ok=True)
            
            # Generate filename
            filename = f"certificate_{student.certificate_id}.pdf"
            filepath = os.path.join(cert_dir, filename)
            
            # Create PDF
            c = canvas.Canvas(filepath, pagesize=landscape(A4))
            
            # Draw background image first to fill the entire canvas
            self._draw_certificate_background(c, background_image_path)
            
            # Draw dynamic content on top of the background image
            self._draw_header_dynamic_content(c, student) # For Cert No and Date
            self._draw_student_info(c, student)
            self._draw_footer(c, student) # For signatures and organization details
            
            # Add QR code if provided
            if qr_code_path and os.path.exists(qr_code_path):
                self._add_qr_code(c, qr_code_path)
            
            # Save PDF
            c.save()
            
            logger.info(f"Certificate generated successfully: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating certificate for student {student.certificate_id}: {str(e)}")
            raise
    
    def _draw_certificate_background(self, c, image_path):
        """Draw the background image for the certificate, scaling it to fit the page."""
        try:
            # Ensure the image exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Background image not found at: {image_path}")

            # Draw the image to fill the entire canvas (A4 landscape: 842x595 points)
            # The image will be stretched/compressed to fit these dimensions.
            c.drawImage(image_path, 0, 0, width=self.cert_width, height=self.cert_height)
        except Exception as e:
            logger.error(f"Error drawing background image: {e}")
            # Fallback: if image fails to load or draw, draw a simple white background
            c.setFillColor(colors.white)
            c.rect(0, 0, self.cert_width, self.cert_height, fill=1, stroke=0)
            # Optionally, add a warning text on the fallback background
            c.setFillColor(colors.red)
            c.setFont("Helvetica-Bold", 20)
            c.drawString(self.cert_width / 2 - 150, self.cert_height / 2, "BACKGROUND IMAGE ERROR")

    def _draw_header_dynamic_content(self, c, student):
        """Draw dynamic content for the header (Cert No and Date) as per the image template."""
        # Cert No in top-left
        c.setFont("Helvetica", 12)
        c.setFillColor(colors.black)
        c.drawString(60, self.cert_height - 70, "Cert No :")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(60, self.cert_height - 85, f"{student.certificate_id}")

        # Date in top-right
        c.setFont("Helvetica", 12)
        c.drawString(self.cert_width - 180, self.cert_height - 70, "Date :")
        c.setFont("Helvetica-Bold", 10)
        c.drawString(self.cert_width - 120, self.cert_height - 85, f"{datetime.now().strftime('%d/%m/%Y')}")

    def _draw_student_info(self, c, student):
        """Draw student information section on the background image."""
        # Student name (large and prominent)
        # Positioned centrally, below "THIS CERTIFICATE IS PROUDLY PRESENTED TO" in the template.
        # Estimated Y-coordinate based on visual inspection of the template image.
        y_name = self.cert_height - 320 # This aligns with the image's name placement
        
        c.setFont("Helvetica-Bold", 32)
        c.setFillColor(colors.black)
        name_width = c.stringWidth(student.student_name, "Helvetica-Bold", 32)
        c.drawString((self.cert_width - name_width) / 2, y_name, student.student_name)
        
        # The background image already has a decorative line under the name,
        # so drawing an additional line here is not necessary.
        
        # Certification text that incorporates all dynamic student details.
        # This text appears as a paragraph below the student name.
        # Using ReportLab's Paragraph for better text flow and automatic wrapping.
        styles = getSampleStyleSheet()
        normal_style = styles['Normal']
        normal_style.fontName = "Helvetica"
        normal_style.fontSize = 14
        normal_style.leading = 18 # Line spacing between lines in the paragraph
        normal_style.alignment = 1 # TA_CENTER (center alignment for the paragraph)

        # Construct the full text with dynamic data.
        # The phrase "Power BI / Tableau" is retained from the original code as requested.
        full_cert_text = (
            f'We are happy to certify that he/she has completed his/her '
            f'"internship in <b>{student.internship_name}</b> using Power BI / Tableau" '
            f'from <b>{student.internship_start_date.strftime("%d/%m/%Y")}</b> to '
            f'<b>{student.internship_end_date.strftime("%d/%m/%Y")}</b>. '
            f'We appreciate his/her work and contributions.'
        )

        # Create a Paragraph object from the HTML-like text
        p = Paragraph(full_cert_text, normal_style)

        # Define the maximum width for the text block, considering page margins.
        text_block_width = self.cert_width - 2 * self.margin 
        # Calculate the actual height the paragraph will occupy when wrapped.
        text_height = p.wrapOn(c, text_block_width, self.cert_height)[1] 

        # Position the paragraph: it should start below the student name, centered.
        # y_name is the baseline of the student's name. We add a small buffer space (40 points)
        # and then subtract the calculated text_height to get the starting y-coordinate for the paragraph.
        # Adjust y_position to fit above the seal and signatures as in the image.
        text_x = self.margin
        text_y = y_name - 40 - text_height - 30 # Adjusted for better visual fit above seal

        # Draw the paragraph on the canvas
        p.drawOn(c, text_x, text_y)
    
    def _draw_footer(self, c, student):
        """Draw certificate footer matching CSC India template, including signatures and organization details."""
        # Y-position for the "Sincerely yours" line, based on visual alignment with the image template.
        y_signature_line = 180 
        
        c.setFont("Helvetica", 12)
        c.setFillColor(colors.black)
        
        # Left signature block - Y Sandesh
        left_x = 120
        c.drawString(left_x, y_signature_line, "Sincerely yours")
        
        # Signature line (drawn in a handwritten-like font and color)
        c.setFont("Helvetica-Oblique", 18)
        c.setFillColor(colors.Color(0.2, 0.4, 0.8))
        c.drawString(left_x - 10, y_signature_line - 30, "Y Sandesh") 
        
        # Draw a solid line under the signature
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.line(left_x - 20, y_signature_line - 40, left_x + 80, y_signature_line - 40)
        
        # Printed name and title below the signature line
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.black)
        c.drawString(left_x + 15, y_signature_line - 55, "Y Sandesh")
        c.setFont("Helvetica", 10)
        c.drawString(left_x + 5, y_signature_line - 70, "Associate Director")
        
        # Right signature block - G Indumathi
        right_x = self.cert_width - 220
        c.setFont("Helvetica", 12)
        c.setFillColor(colors.black)
        c.drawString(right_x, y_signature_line, "Sincerely yours")
        
        # Signature line (handwritten-like font and color)
        c.setFont("Helvetica-Oblique", 18)
        c.setFillColor(colors.Color(0.2, 0.4, 0.8))
        c.drawString(right_x - 10, y_signature_line - 30, "G Indumathi")
        
        # Draw a solid line under the signature
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.line(right_x - 20, y_signature_line - 40, right_x + 100, y_signature_line - 40)
        
        # Printed name and title below the signature line
        c.setFont("Helvetica-Bold", 12)
        c.setFillColor(colors.black)
        c.drawString(right_x + 20, y_signature_line - 55, "G Indumathi")
        c.setFont("Helvetica", 10)
        c.drawString(right_x + 5, y_signature_line - 70, "Head - Skill Development")
        
        # Central seal/stamp area (design based on the original code, visually aligned with image)
        center_x = self.cert_width / 2
        seal_radius = 35
        
        # Outer circle for the seal
        c.setFillColor(colors.Color(1.0, 0.8, 0.2))  # Golden color
        c.setStrokeColor(colors.Color(0.8, 0.6, 0.0))
        c.setLineWidth(3)
        c.circle(center_x, y_signature_line - 35, seal_radius, fill=1, stroke=1)
        
        # Inner circle for the seal
        c.setFillColor(colors.Color(1.0, 0.9, 0.3))
        c.circle(center_x, y_signature_line - 35, seal_radius - 8, fill=1, stroke=0)
        
        # Text inside the seal
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(colors.Color(0.4, 0.2, 0.0))
        c.drawString(center_x - 20, y_signature_line - 30, "OFFICIAL")
        c.drawString(center_x - 12, y_signature_line - 45, "SEAL")
        
        # Organization footer details at the very bottom of the certificate
        footer_y = 80
        c.setFont("Helvetica-Bold", 18)
        c.setFillColor(colors.Color(0.2, 0.7, 0.5))
        org_name = "Council for Skills and Competencies(CSC India)"
        org_width = c.stringWidth(org_name, "Helvetica-Bold", 18)
        c.drawString((self.cert_width - org_width) / 2, footer_y, org_name)
        
        # Draw a decorative line above the organization name
        c.setStrokeColor(colors.Color(0.2, 0.7, 0.5))
        c.setLineWidth(2)
        line_width = org_width + 40
        line_start = (self.cert_width - line_width) / 2
        c.line(line_start, footer_y + 10, line_start + line_width, footer_y + 10)
        
        # Address of the organization
        c.setFont("Helvetica-Bold", 14)
        c.setFillColor(colors.black)
        address = "Visakhapatnam, Andhra Pradesh 530022"
        addr_width = c.stringWidth(address, "Helvetica-Bold", 14)
        c.drawString((self.cert_width - addr_width) / 2, footer_y - 25, address)
        
        # Website of the organization
        c.setFont("Helvetica", 12)
        c.setFillColor(colors.Color(0.2, 0.4, 0.8))
        website = "www.cscindia.org.in"
        web_width = c.stringWidth(website, "Helvetica", 12)
        c.drawString((self.cert_width - web_width) / 2, footer_y - 45, website)
    
    def _add_qr_code(self, c, qr_code_path):
        """Add QR code to certificate with verification details at the top-right position as per the image template."""
        try:
            # Position QR code in top right corner as per image_7ab15a.png
            qr_size = 80 # Size of the QR code image
            x_position = self.cert_width - qr_size - 50 # 50 points from right edge
            y_position = self.cert_height - qr_size - 50 # 50 points from top edge

            # Draw a white background rectangle for the QR code with a border
            c.setFillColor(colors.white)
            c.setStrokeColor(colors.Color(0.3, 0.3, 0.3))
            c.setLineWidth(2)
            c.rect(x_position - 8, y_position - 8, qr_size + 16, qr_size + 16, fill=1, stroke=1)
            
            # Draw an inner border for the QR code area
            c.setStrokeColor(colors.Color(0.7, 0.7, 0.7))
            c.setLineWidth(1)
            c.rect(x_position - 4, y_position - 4, qr_size + 8, qr_size + 8, fill=0, stroke=1)
            
            # Draw the QR code image itself
            c.drawImage(qr_code_path, x_position, y_position, 
                        width=qr_size, height=qr_size)
            
            # Add verification text below the QR code
            c.setFont("Helvetica-Bold", 9)
            c.setFillColor(colors.black)
            verify_text = "Scan QR Code"
            text_width = c.stringWidth(verify_text, "Helvetica-Bold", 9)
            # Center the text below the QR code
            c.drawString(x_position + (qr_size - text_width) / 2, 
                         y_position - 20, verify_text)
            
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.Color(0.4, 0.4, 0.4))
            details_text = "for verification"
            details_width = c.stringWidth(details_text, "Helvetica", 8)
            # Center the details text below the main verification text
            c.drawString(x_position + (qr_size - details_width) / 2, 
                         y_position - 32, details_text)
            
            # Add a label above the QR code (e.g., "Digital Certificate")
            c.setFont("Helvetica", 7)
            c.setFillColor(colors.Color(0.5, 0.5, 0.5))
            label_text = "Digital Certificate"
            label_width = c.stringWidth(label_text, "Helvetica", 7)
            # Center the label above the QR code
            c.drawString(x_position + (qr_size - label_width) / 2, 
                         y_position + qr_size + 12, label_text)
            
        except Exception as e:
            logger.error(f"Error adding QR code to certificate: {str(e)}")

# Define a dummy Student class to simulate student data for certificate generation
class Student:
    def __init__(self, student_name, certificate_id, roll_number, college_name,
                 internship_name, internship_start_date, internship_end_date,
                 duration_weeks=None, mentor_name=None, company_name=None,
                 performance_rating=None):
        self.student_name = student_name
        self.certificate_id = certificate_id
        self.roll_number = roll_number
        self.college_name = college_name
        self.internship_name = internship_name
        self.internship_start_date = internship_start_date
        self.internship_end_date = internship_end_date
        self.duration_weeks = duration_weeks
        self.mentor_name = mentor_name
        self.company_name = company_name
        self.performance_rating = performance_rating

# Example Usage (for demonstration purposes, runs when the script is executed directly)
if __name__ == "__main__":
    # Setup basic logging to see informational messages and errors
    logging.basicConfig(level=logging.INFO)

    # --- IMPORTANT: Replace with your actual dynamic student data ---
    # You will need to get this data from your application's input or database.
    # Example structure:
    # student_data = Student(
    #     student_name="ACTUAL STUDENT NAME",
    #     certificate_id="YOUR_CERT_ID_HERE",
    #     roll_number="YOUR_ROLL_NUMBER",
    #     college_name="YOUR COLLEGE NAME",
    #     internship_name="YOUR INTERNSHIP NAME",
    #     internship_start_date=datetime(YYYY, MM, DD), # e.g., datetime(2024, 1, 1)
    #     internship_end_date=datetime(YYYY, MM, DD),   # e.g., datetime(2024, 3, 31)
    #     duration_weeks=12, # Optional
    #     mentor_name="Your Mentor", # Optional
    #     company_name="Your Company", # Optional
    #     performance_rating="Good" # Optional
    # )
    # --- END OF DYNAMIC DATA SECTION ---

    # Example of how you would define a student object with real data:
    # (Uncomment and populate with your actual data when ready to use)
    student_data = Student(
        student_name="SRINIVASA RAO TALARI",
        certificate_id="72b5bfa8",
        roll_number="21B01A1234", # Example: Replace with actual roll number
        college_name="GVP College of Engineering", # Example: Replace with actual college name
        internship_name="AI Research Internship",
        internship_start_date=datetime(2024, 5, 1),
        internship_end_date=datetime(2024, 7, 1),
        duration_weeks=8, 
        mentor_name="Srinivas", # Example: Replace with actual mentor name
        company_name="CSC India", # Example: Replace with actual company name
        performance_rating="Excellent" 
    )


    # Define the path to your background image.
    # IMPORTANT: Update this path to the exact location of your image.
    # For example: r"C:\Users\ASUS\Downloads\InternshipCertifier\InternshipCertifier\attached_assets\_Internship Certificate.jpg"
    background_img = r"C:\Users\ASUS\Downloads\InternshipCertifier\InternshipCertifier\attached_assets\_Internship Certificate.jpg" 
    
    # Define the path to your QR code image.
    # If you have a specific QR code image, provide its path here.
    # Otherwise, you might need to generate one dynamically or provide a placeholder.
    qr_code_img = "qr_code_placeholder.png" 

    # --- IMPORTANT: Logic to generate QR code if it doesn't exist (optional) ---
    # This block will generate a dummy QR code if 'qrcode' library is installed
    # and 'qr_code_placeholder.png' does not exist.
    # If you have your own QR code generation logic or a pre-existing QR code image,
    # you can remove or modify this block.
    if not os.path.exists(qr_code_img):
        try:
            from qrcode import make
            # The QR code will link to a verification URL based on the certificate ID
            img = make(f"https://www.cscindia.org.in/verify/{student_data.certificate_id}")
            img.save(qr_code_img)
            logger.info(f"Dummy QR code generated at: {qr_code_img}")
        except ImportError:
            logger.warning("qrcode library not found. Cannot generate dummy QR code. Please install it (`pip install qrcode[pil]`) or provide a real QR code image.")
            qr_code_img = None # Set to None if QR code cannot be generated
        except Exception as e:
            logger.error(f"Error generating dummy QR code: {e}")
            qr_code_img = None
    # --- END OF QR CODE GENERATION LOGIC ---

    # Instantiate the CertificateGenerator and generate the PDF
    generator = CertificateGenerator()
    try:
        generated_pdf_path = generator.generate_certificate(
            student_data,
            background_image_path=background_img,
            qr_code_path=qr_code_img
        )
        print(f"Certificate saved to: {generated_pdf_path}")
    except Exception as e:
        print(f"Failed to generate certificate: {e}")
