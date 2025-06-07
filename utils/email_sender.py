from flask_mail import Message
from app import mail, app
import os
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib

logger = logging.getLogger(__name__)

class EmailSender:
    """Handle email delivery for certificates"""
    
    def __init__(self):
        self.sender_email = app.config['MAIL_DEFAULT_SENDER']
        self.sender_name = "Certificate System"
    
    def send_certificate_email(self, student, certificate_path):
        """Send certificate email to student"""
        try:
            # Create email subject
            subject = f"Internship Certificate - {student.internship_name}"
            
            # Create email body
            body = self._create_email_body(student)
            
            # Create message
            msg = Message(
                subject=subject,
                sender=(self.sender_name, self.sender_email),
                recipients=[student.email]
            )
            
            msg.html = body
            
            # Attach certificate if file exists
            if certificate_path and os.path.exists(certificate_path):
                with app.open_resource(certificate_path) as fp:
                    msg.attach(
                        filename=f"certificate_{student.certificate_id}.pdf",
                        content_type="application/pdf",
                        data=fp.read()
                    )
            
            # Send email
            mail.send(msg)
            
            logger.info(f"Certificate email sent successfully to {student.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending certificate email to {student.email}: {str(e)}")
            return False
    
    def _create_email_body(self, student):
        """Create personalized email body"""
        body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Internship Certificate</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px 20px;
                    text-align: center;
                    border-radius: 10px 10px 0 0;
                }}
                .content {{
                    background: #f8f9fa;
                    padding: 30px 20px;
                    border-radius: 0 0 10px 10px;
                }}
                .highlight {{
                    background: #e3f2fd;
                    padding: 15px;
                    border-left: 4px solid #2196f3;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    color: #666;
                    font-size: 12px;
                }}
                .btn {{
                    display: inline-block;
                    background: #2196f3;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎓 Congratulations!</h1>
                <p>Your Internship Certificate is Ready</p>
            </div>
            
            <div class="content">
                <p>Dear <strong>{student.student_name}</strong>,</p>
                
                <p>Congratulations on successfully completing your internship program! We are pleased to inform you that your certificate has been generated and is attached to this email.</p>
                
                <div class="highlight">
                    <h3>Internship Details:</h3>
                    <ul>
                        <li><strong>Program:</strong> {student.internship_name}</li>
                        <li><strong>Duration:</strong> {student.internship_start_date.strftime('%B %d, %Y')} to {student.internship_end_date.strftime('%B %d, %Y')}</li>
                        <li><strong>Certificate ID:</strong> {student.certificate_id}</li>
                        <li><strong>College:</strong> {student.college_name}</li>
                        <li><strong>Branch:</strong> {student.branch}</li>
        """
        
        if student.mentor_name:
            body += f"                        <li><strong>Mentor:</strong> {student.mentor_name}</li>\n"
        
        if student.company_name:
            body += f"                        <li><strong>Company:</strong> {student.company_name}</li>\n"
        
        if student.performance_rating:
            body += f"                        <li><strong>Performance Rating:</strong> {student.performance_rating}</li>\n"
        
        body += f"""
                    </ul>
                </div>
                
                <p>Your certificate is attached as a PDF file. You can also verify your certificate online using the certificate ID: <strong>{student.certificate_id}</strong></p>
                
                <p style="text-align: center;">
                    <a href="https://your-domain.com/certificate/{student.certificate_id}" class="btn">Verify Certificate Online</a>
                </p>
                
                <p><strong>Important Notes:</strong></p>
                <ul>
                    <li>Keep this certificate safe as it serves as proof of your successful completion</li>
                    <li>The QR code on the certificate can be scanned for instant verification</li>
                    <li>This is an official document - do not share or modify it</li>
                </ul>
                
                <p>We wish you all the best in your future endeavors and career!</p>
                
                <p>Best regards,<br>
                <strong>Certificate Management System</strong></p>
            </div>
            
            <div class="footer">
                <p>This is an automated email. Please do not reply to this message.</p>
                <p>If you have any questions, please contact our support team.</p>
            </div>
        </body>
        </html>
        """
        
        return body
    
    def send_bulk_notification(self, recipients, subject, message):
        """Send bulk notification emails"""
        try:
            successful_sends = 0
            failed_sends = 0
            
            for recipient in recipients:
                try:
                    msg = Message(
                        subject=subject,
                        sender=(self.sender_name, self.sender_email),
                        recipients=[recipient]
                    )
                    msg.html = message
                    mail.send(msg)
                    successful_sends += 1
                    
                except Exception as e:
                    logger.error(f"Error sending notification to {recipient}: {str(e)}")
                    failed_sends += 1
            
            return {
                'successful': successful_sends,
                'failed': failed_sends,
                'total': len(recipients)
            }
            
        except Exception as e:
            logger.error(f"Error in bulk email sending: {str(e)}")
            return {'successful': 0, 'failed': len(recipients), 'total': len(recipients)}
    
    def test_email_configuration(self):
        """Test email configuration"""
        try:
            msg = Message(
                subject="Email Configuration Test",
                sender=(self.sender_name, self.sender_email),
                recipients=[self.sender_email]
            )
            msg.body = "This is a test email to verify email configuration."
            mail.send(msg)
            return True
            
        except Exception as e:
            logger.error(f"Email configuration test failed: {str(e)}")
            return False
