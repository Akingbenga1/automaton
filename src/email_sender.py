"""Email sending functionality for job search results"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


class EmailSender:
    """Handles sending emails with attachments via SMTP"""

    def __init__(self):
        """Initialize email sender with SMTP configuration from environment"""
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.smtp_use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.from_email = os.getenv("EMAIL_FROM")
        self.to_email = os.getenv("EMAIL_TO")
        
        # Check if email is enabled
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"

    def is_configured(self) -> bool:
        """Check if email is properly configured"""
        if not self.enabled:
            return False
        
        required_vars = [
            self.smtp_host,
            self.smtp_username,
            self.smtp_password,
            self.from_email,
            self.to_email
        ]
        
        return all(required_vars)

    def send_results_email(self, results_file_path: str, job_count: int) -> bool:
        """
        Send results.md file as email attachment

        Args:
            results_file_path: Path to the results.md file
            job_count: Number of jobs found

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.is_configured():
            logger.info("Email not enabled or not fully configured. Skipping email send.")
            return False

        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = self.to_email
            msg['Subject'] = f"Job Search Results - {job_count} Jobs Found"

            # Email body
            body = f"""
Hello,

Your automated job search has completed.

Total Jobs Found: {job_count}

Please find the detailed results attached in the results.md file.

Best regards,
Job Search Automation System
            """
            msg.attach(MIMEText(body, 'plain'))

            # Attach results file
            if os.path.exists(results_file_path):
                with open(results_file_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())

                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {Path(results_file_path).name}'
                )
                msg.attach(part)
            else:
                logger.warning(f"Results file not found: {results_file_path}")
                return False

            # Send email via SMTP
            logger.info(f"Sending email to {self.to_email} via {self.smtp_host}:{self.smtp_port}")
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.smtp_use_tls:
                    server.starttls()
                
                server.login(self.smtp_username, self.smtp_password)
                text = msg.as_string()
                server.sendmail(self.from_email, self.to_email, text)

            logger.info(f"Email sent successfully to {self.to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {e}", exc_info=True)
            return False

