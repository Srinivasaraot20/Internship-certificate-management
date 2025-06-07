import pandas as pd
import uuid
from datetime import datetime, date
from app import db
from models import Student, BatchUpload, CertificateStatus
import logging

logger = logging.getLogger(__name__)

class ExcelProcessor:
    """Handle Excel/CSV file processing and data validation"""

    def __init__(self):
        self.required_columns = [
            'student_name', 'roll_number', 'branch', 'college_name', 
            'email', 'internship_name', 'internship_start_date', 'internship_end_date'
        ]

        self.optional_columns = [
            'phone_number', 'duration_weeks', 'mentor_name', 'mentor_email',
            'internship_location', 'company_name', 'performance_rating',
            'skills_acquired', 'project_title', 'certificate_id', 'date_of_issue', 'remarks'
        ]

    def process_file(self, filepath, batch_id):
        """Process uploaded Excel file and create student records"""
        try:
            # Read Excel file
            df = pd.read_excel(filepath)

            # Clean column names
            df.columns = df.columns.str.lower().str.strip().str.replace(' ', '_')

            # Validate required columns
            missing_columns = [col for col in self.required_columns if col not in df.columns]
            if missing_columns:
                error_msg = f"Missing required columns: {', '.join(missing_columns)}"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'processed': 0,
                    'successful': 0,
                    'failed': 0
                }

            # Update batch upload record
            batch_upload = BatchUpload.query.get(batch_id)
            if not batch_upload:
                error_msg = "Batch upload record not found"
                logger.error(error_msg)
                return {
                    'success': False,
                    'error': error_msg,
                    'processed': 0,
                    'successful': 0,
                    'failed': 0
                }

            batch_upload.total_records = len(df)
            db.session.commit()

            processed = 0
            successful = 0
            failed = 0
            errors = []

            for index, row in df.iterrows():
                try:
                    # Check if student already exists
                    existing_student = Student.query.filter_by(
                        roll_number=str(row['roll_number']).strip()
                    ).first()

                    if existing_student:
                        errors.append(f"Row {index + 2}: Student with roll number {row['roll_number']} already exists")
                        failed += 1
                        continue

                    # Create student record
                    student_data = self._process_row(row, index + 1)
                    if student_data:
                        student = Student(**student_data)

                        db.session.add(student)
                        successful += 1
                    else:
                        failed += 1


                except Exception as e:
                    error_msg = f"Row {index + 2}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    failed += 1

                processed += 1

                # Update progress
                batch_upload.processed_records = processed
                batch_upload.successful_records = successful
                batch_upload.failed_records = failed

                if processed % 10 == 0:  # Commit every 10 records
                    try:
                        db.session.commit()
                    except Exception as e:
                        logger.error(f"Database commit error: {str(e)}")
                        db.session.rollback()

            # Final commit
            try:
                db.session.commit()

                # Update batch status
                batch_upload.status = 'completed' if failed == 0 else 'completed_with_errors'
                batch_upload.error_details = '\n'.join(errors) if errors else None
                db.session.commit()

                logger.info(f"Successfully processed {successful} out of {processed} records")

                return {
                    'success': True,
                    'processed': processed,
                    'successful': successful,
                    'failed': failed,
                    'errors': errors
                }

            except Exception as e:
                error_msg = f"Final database commit failed: {str(e)}"
                logger.error(error_msg)
                db.session.rollback()

                batch_upload.status = 'failed'
                batch_upload.error_details = error_msg
                db.session.commit()

                return {
                    'success': False,
                    'error': error_msg,
                    'processed': processed,
                    'successful': successful,
                    'failed': failed
                }

        except Exception as e:
            error_msg = f"Error processing Excel file: {str(e)}"
            logger.error(error_msg)

            # Update batch status to failed
            try:
                if 'batch_upload' in locals() and batch_upload:
                    batch_upload.status = 'failed'
                    batch_upload.error_details = error_msg
                    db.session.commit()
            except Exception as db_error:
                logger.error(f"Error updating batch status: {str(db_error)}")

            return {
                'success': False,
                'error': error_msg,
                'processed': 0,
                'successful': 0,
                'failed': 0
            }

    def _validate_columns(self, columns):
        """Validate that required columns are present"""
        columns = [col.lower().strip().replace(' ', '_') for col in columns]
        missing_columns = [col for col in self.required_columns if col not in columns]

        if missing_columns:
            return {
                'valid': False,
                'error': f"Missing required columns: {', '.join(missing_columns)}"
            }

        return {'valid': True}

    def _process_row(self, row, row_number):
        """Process a single row and return student data"""
        try:
            # Convert column names to lowercase and replace spaces with underscores
            row_dict = {}
            for key, value in row.items():
                clean_key = key.lower().strip().replace(' ', '_')
                row_dict[clean_key] = value

            # Validate required fields
            for col in self.required_columns:
                value = row_dict.get(col)
                if pd.isna(value) or str(value).strip() == '' or str(value).lower() in ['nan', 'none', 'null']:
                    raise ValueError(f"Missing required field: {col} (found: '{value}')")

            # Generate certificate ID if not provided
            certificate_id = row_dict.get('certificate_id')
            if pd.isna(certificate_id) or str(certificate_id).strip() == '':
                certificate_id = self._generate_certificate_id()

            # Parse dates
            start_date = self._parse_date(row_dict.get('internship_start_date'))
            end_date = self._parse_date(row_dict.get('internship_end_date'))

            if start_date and end_date and start_date > end_date:
                raise ValueError("Internship start date cannot be after end date")

            # Calculate duration if not provided
            duration_weeks = row_dict.get('duration_weeks')
            if pd.isna(duration_weeks) and start_date and end_date:
                duration_weeks = (end_date - start_date).days // 7

            # Parse issue date
            issue_date = row_dict.get('date_of_issue')
            if pd.isna(issue_date):
                issue_date = date.today()
            else:
                issue_date = self._parse_date(issue_date)

            # Validate email
            email = str(row_dict.get('email')).strip()
            if not self._validate_email(email):
                raise ValueError(f"Invalid email format: {email}")

            student_data = {
                'student_name': str(row_dict.get('student_name')).strip(),
                'roll_number': str(row_dict.get('roll_number')).strip(),
                'branch': str(row_dict.get('branch')).strip(),
                'college_name': str(row_dict.get('college_name')).strip(),
                'email': email,
                'phone_number': str(row_dict.get('phone_number', '')).strip() or None,
                'internship_name': str(row_dict.get('internship_name')).strip(),
                'internship_start_date': start_date,
                'internship_end_date': end_date,
                'duration_weeks': int(duration_weeks) if not pd.isna(duration_weeks) else None,
                'mentor_name': str(row_dict.get('mentor_name', '')).strip() or None,
                'mentor_email': str(row_dict.get('mentor_email', '')).strip() or None,
                'internship_location': str(row_dict.get('internship_location', '')).strip() or None,
                'company_name': str(row_dict.get('company_name', '')).strip() or None,
                'performance_rating': str(row_dict.get('performance_rating', '')).strip() or None,
                'skills_acquired': str(row_dict.get('skills_acquired', '')).strip() or None,
                'project_title': str(row_dict.get('project_title', '')).strip() or None,
                'certificate_id': certificate_id,
                'date_of_issue': issue_date,
                'remarks': str(row_dict.get('remarks', '')).strip() or None,
                'certificate_status': CertificateStatus.PENDING
            }

            return student_data

        except Exception as e:
            logger.error(f"Error processing row {row_number}: {str(e)}")
            raise ValueError(f"Row {row_number}: {str(e)}")

    def _generate_certificate_id(self):
        """Generate unique certificate ID"""
        while True:
            cert_id = f"CERT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
            existing = Student.query.filter_by(certificate_id=cert_id).first()
            if not existing:
                return cert_id

    def _parse_date(self, date_value):
        """Parse date from various formats"""
        if pd.isna(date_value):
            return None

        if isinstance(date_value, (date, datetime)):
            return date_value.date() if isinstance(date_value, datetime) else date_value

        date_str = str(date_value).strip()

        # Try various date formats
        date_formats = [
            '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y',
            '%Y/%m/%d', '%d.%m.%Y', '%m.%d.%Y', '%Y.%m.%d'
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        raise ValueError(f"Unable to parse date: {date_value}")

    def _validate_email(self, email):
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None