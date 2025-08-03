"""
Email interface for sending news summaries via email.
Supports SMTP configuration for various email providers.
"""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List

from .base_interface import BaseInterface


class EmailInterface(BaseInterface):
    """Email interface for message delivery."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Extract config values
        interface_config = config.get('config', {})
        self.smtp_server = interface_config.get('smtp_server', '')
        self.smtp_port = interface_config.get('smtp_port', 587)
        self.username = interface_config.get('username', '')
        self.password = interface_config.get('password', '')
        self.from_email = interface_config.get('from_email', '')
        self.to_emails = interface_config.get('to_emails', [])
        
        required_fields = ['smtp_server', 'username', 'password', 'from_email', 'to_emails']
        for field in required_fields:
            if not getattr(self, field):
                raise ValueError(f"Email {field} must be configured")
    
    def send(self, message: str, topic: str, config: Dict[str, Any] = None) -> bool:
        """Send message via email."""
        try:
            # Create email message
            msg = self._create_message(message, topic)
            
            self.logger.info(f"Sending email to {len(self.to_emails)} recipients")
            
            # Connect to SMTP server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                
                for to_email in self.to_emails:
                    msg['To'] = to_email
                    server.send_message(msg)
                    self.logger.debug(f"Email sent to {to_email}")
                    del msg['To']  # Remove for next iteration
            
            self.logger.info("All emails sent successfully")
            return True
            
        except smtplib.SMTPException as e:
            self.logger.error(f"SMTP error sending email: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending email: {e}")
            return False
    
    def _create_message(self, content: str, topic: str) -> MIMEMultipart:
        """Create email message with proper formatting."""
        msg = MIMEMultipart('alternative')
        
        # Email subject
        subject = f"News Summary - {topic.title()} - {self._get_date_string()}"
        msg['Subject'] = subject
        msg['From'] = self.from_email
        
        # Convert Markdown to plain text and HTML
        plain_text = self._markdown_to_text(content)
        html_content = self._markdown_to_html(content)
        
        # Create both plain text and HTML versions
        text_part = MIMEText(plain_text, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        return msg
    
    def _get_date_string(self) -> str:
        """Get formatted date string for email subject."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d")
    
    def _markdown_to_text(self, content: str) -> str:
        """Convert Markdown content to plain text."""
        # Simple Markdown to text conversion
        text = content.replace('**', '')  # Remove bold markers
        text = text.replace('*', '')     # Remove italic markers
        text = text.replace('📰', 'NEWS:')
        text = text.replace('🕐', 'TIME:')
        text = text.replace('📄', 'ARTICLES:')
        return text
    
    def _markdown_to_html(self, content: str) -> str:
        """Convert Markdown content to HTML."""
        html = content.replace('\n', '<br>\n')
        
        # Convert bold text
        import re
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # Convert links
        html = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', html)
        
        # Add basic HTML structure
        html_content = f"""
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .header {{ background-color: #f4f4f4; padding: 10px; border-radius: 5px; }}
                .content {{ margin: 20px 0; }}
                .sources {{ background-color: #f9f9f9; padding: 10px; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="content">
                {html}
            </div>
        </body>
        </html>
        """
        
        return html_content
    
    def test_connection(self) -> bool:
        """Test email SMTP connection."""
        try:
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.username, self.password)
                self.logger.info("Email SMTP connection successful")
                return True
                
        except Exception as e:
            self.logger.error(f"Error testing email connection: {e}")
            return False


# Main function for the module
def send(message: str, topic: str, config: Dict[str, Any]) -> bool:
    """Main entry point for the Email interface."""
    interface = EmailInterface(config)
    return interface.send(message, topic, config)
