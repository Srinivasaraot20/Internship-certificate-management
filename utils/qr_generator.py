import qrcode
import os
import json
import logging
from datetime import datetime
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class QRGenerator:
    """Generate QR codes for certificate verification"""
    
    def __init__(self):
        self.qr_codes_dir = 'static/qr_codes'
        os.makedirs(self.qr_codes_dir, exist_ok=True)
        
        # Base URL for verification (will be updated with actual domain)
        self.base_url = "https://localhost:5000"
    
    def generate_verification_data(self, certificate_id, student=None):
        """Generate verification data for QR code with comprehensive student details"""
        verification_data = {
            'certificate_id': certificate_id,
            'verification_url': f"{self.base_url}/qr-data/{certificate_id}",
            'view_url': f"{self.base_url}/certificate/{certificate_id}",
            'generated_at': datetime.utcnow().isoformat(),
            'type': 'certificate_verification',
            'issuer': 'Council for Skills and Competencies (CSC India)',
            'location': 'Visakhapatnam, Andhra Pradesh 530022',
            'website': 'www.cscindia.org.in'
        }
        
        # Add comprehensive student details if provided
        if student:
            verification_data.update({
                # Personal Information
                'student_name': student.student_name,
                'roll_number': student.roll_number,
                'email': student.email,
                'phone': student.phone_number if student.phone_number else 'N/A',
                
                # Academic Information
                'college': student.college_name,
                'branch': student.branch,
                
                # Internship Details
                'internship_name': student.internship_name,
                'company_name': student.company_name,
                'start_date': student.internship_start_date.strftime('%d/%m/%Y'),
                'end_date': student.internship_end_date.strftime('%d/%m/%Y'),
                'duration_weeks': student.duration_weeks if student.duration_weeks else 'N/A',
                'mentor_name': student.mentor_name if student.mentor_name else 'N/A',
                'internship_location': student.internship_location if student.internship_location else 'N/A',
                'performance_rating': student.performance_rating if student.performance_rating else 'Excellent',
                
                # Additional Information
                'skills_acquired': student.skills_acquired if student.skills_acquired else 'N/A',
                'project_title': student.project_title if student.project_title else 'N/A',
                
                # Certificate Information
                'issue_date': student.date_of_issue.strftime('%d/%m/%Y') if hasattr(student, 'date_of_issue') and student.date_of_issue else datetime.now().strftime('%d/%m/%Y'),
                'certificate_status': student.certificate_status.value if student.certificate_status else 'verified'
            })
        
        return json.dumps(verification_data, indent=2)
    
    def create_qr_code(self, data, certificate_id, style='default'):
        """Create QR code image with the given data"""
        try:
            # Create QR code instance with higher error correction for detailed data
            qr = qrcode.QRCode(
                version=None,  # Auto-determine version based on data size
                error_correction=qrcode.constants.ERROR_CORRECT_M,  # Medium error correction for better reliability
                box_size=8,
                border=4,
            )
            
            # Add data to QR code
            qr.add_data(data)
            qr.make(fit=True)
            
            # Generate filename
            filename = f"qr_{certificate_id}.png"
            filepath = os.path.join(self.qr_codes_dir, filename)
            
            # Create QR code image with basic styling
            img = qr.make_image(
                fill_color="black",
                back_color="white"
            )
            
            # Save the image
            img.save(filepath)
            
            logger.info(f"QR code generated successfully: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating QR code for certificate {certificate_id}: {str(e)}")
            return None
    
    def create_verification_qr(self, certificate_id, student=None):
        """Create QR code specifically for certificate verification"""
        try:
            # Generate verification data with student details
            verification_data = self.generate_verification_data(certificate_id, student)
            
            # Create QR code
            qr_path = self.create_qr_code(verification_data, certificate_id)
            
            if qr_path:
                logger.info(f"Verification QR code created for certificate: {certificate_id}")
                return qr_path
            else:
                logger.error(f"Failed to create verification QR code for certificate: {certificate_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating verification QR code: {str(e)}")
            return None
    
    def create_batch_qr_codes(self, certificate_ids):
        """Generate QR codes for multiple certificates"""
        results = []
        
        for cert_id in certificate_ids:
            qr_path = self.create_verification_qr(cert_id)
            results.append({
                'certificate_id': cert_id,
                'qr_path': qr_path,
                'success': qr_path is not None
            })
        
        return results
    
    def verify_qr_data(self, qr_data):
        """Verify and parse QR code data"""
        try:
            # Parse JSON data
            data = json.loads(qr_data)
            
            # Validate required fields
            if 'certificate_id' not in data:
                return {'valid': False, 'error': 'Missing certificate ID'}
            
            if 'type' not in data or data['type'] != 'certificate_verification':
                return {'valid': False, 'error': 'Invalid QR code type'}
            
            return {
                'valid': True,
                'certificate_id': data['certificate_id'],
                'verification_url': data.get('verification_url', ''),
                'generated_at': data.get('generated_at', '')
            }
            
        except json.JSONDecodeError:
            return {'valid': False, 'error': 'Invalid QR code data format'}
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def get_qr_code_path(self, certificate_id):
        """Get the file path for a certificate's QR code"""
        filename = f"qr_{certificate_id}.png"
        return os.path.join(self.qr_codes_dir, filename)
    
    def cleanup_old_qr_codes(self, days_old=30):
        """Clean up QR code files older than specified days"""
        try:
            import time
            current_time = time.time()
            cutoff_time = current_time - (days_old * 24 * 60 * 60)
            
            cleaned_count = 0
            for filename in os.listdir(self.qr_codes_dir):
                if filename.startswith('qr_') and filename.endswith('.png'):
                    filepath = os.path.join(self.qr_codes_dir, filename)
                    if os.path.getmtime(filepath) < cutoff_time:
                        os.remove(filepath)
                        cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} old QR code files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up QR codes: {str(e)}")
            return 0