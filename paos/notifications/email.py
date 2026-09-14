"""
Email notification service
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict, Any
from datetime import datetime
import asyncio
import os
from abc import ABC, abstractmethod


class EmailTemplate:
    """Email template with variable substitution"""
    
    def __init__(self, name: str, subject: str, body: str, html_body: Optional[str] = None):
        self.name = name
        self.subject = subject
        self.body = body
        self.html_body = html_body or self._convert_to_html(body)
    
    def render(self, variables: Dict[str, Any]) -> tuple[str, str]:
        """Render template with variables"""
        subject = self.subject
        body = self.body
        html_body = self.html_body
        
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            subject = subject.replace(placeholder, str(value))
            body = body.replace(placeholder, str(value))
            html_body = html_body.replace(placeholder, str(value))
        
        return subject, body, html_body
    
    @staticmethod
    def _convert_to_html(text: str) -> str:
        """Convert plain text to HTML"""
        html = f"<html><body><pre>{text}</pre></body></html>"
        return html


class EmailTemplateRegistry:
    """Registry of email templates"""
    
    def __init__(self):
        self.templates: Dict[str, EmailTemplate] = {}
        self._load_default_templates()
    
    def register(self, template: EmailTemplate):
        """Register a template"""
        self.templates[template.name] = template
    
    def get(self, name: str) -> Optional[EmailTemplate]:
        """Get a template"""
        return self.templates.get(name)
    
    def _load_default_templates(self):
        """Load default templates"""
        # Approval required template
        self.register(EmailTemplate(
            name="approval_required",
            subject="Action Required: Approval Needed for {{action_type}}",
            body="""Dear {{recipient}},

An approval is required for the following action:

Action Type: {{action_type}}
Task ID: {{task_id}}
Reason: {{reason}}

Please review and approve or reject this action by clicking the link below:
{{approval_link}}

This approval will expire at: {{expiration_time}}

Best regards,
PAOS Team""",
            html_body="""<html><body>
<h2>Action Required: Approval Needed</h2>
<p>An approval is required for the following action:</p>
<ul>
<li><strong>Action Type:</strong> {{action_type}}</li>
<li><strong>Task ID:</strong> {{task_id}}</li>
<li><strong>Reason:</strong> {{reason}}</li>
</ul>
<p><a href="{{approval_link}}">Click here to review and approve</a></p>
<p>This approval will expire at: {{expiration_time}}</p>
</body></html>"""
        ))
        
        # Task completed template
        self.register(EmailTemplate(
            name="task_completed",
            subject="Task Completed: {{task_name}}",
            body="""Dear {{recipient}},

Your task has been completed successfully!

Task: {{task_name}}
Task ID: {{task_id}}
Completed At: {{completion_time}}

Summary:
{{summary}}

Cost: {{cost}}

Best regards,
PAOS Team""",
            html_body="""<html><body>
<h2>Task Completed!</h2>
<p>Your task has been completed successfully!</p>
<ul>
<li><strong>Task:</strong> {{task_name}}</li>
<li><strong>Task ID:</strong> {{task_id}}</li>
<li><strong>Completed At:</strong> {{completion_time}}</li>
<li><strong>Cost:</strong> {{cost}}</li>
</ul>
<p><strong>Summary:</strong></p>
<p>{{summary}}</p>
</body></html>"""
        ))
        
        # Task failed template
        self.register(EmailTemplate(
            name="task_failed",
            subject="Task Failed: {{task_name}}",
            body="""Dear {{recipient}},

Your task has failed.

Task: {{task_name}}
Task ID: {{task_id}}
Failed At: {{failure_time}}

Error:
{{error_message}}

Please contact support if you need assistance.

Best regards,
PAOS Team""",
            html_body="""<html><body>
<h2>Task Failed</h2>
<p>Your task has encountered an error:</p>
<ul>
<li><strong>Task:</strong> {{task_name}}</li>
<li><strong>Task ID:</strong> {{task_id}}</li>
<li><strong>Failed At:</strong> {{failure_time}}</li>
</ul>
<p><strong>Error:</strong></p>
<pre>{{error_message}}</pre>
</body></html>"""
        ))
        
        # Budget alert template
        self.register(EmailTemplate(
            name="budget_alert",
            subject="Budget Alert: {{percentage}}% Used",
            body="""Dear {{recipient}},

Your budget threshold has been reached.

Budget Limit: {{budget_limit}}
Spent: {{spent}}
Remaining: {{remaining}}
Usage: {{percentage}}%

Please review your spending to avoid exceeding your budget.

Best regards,
PAOS Team""",
            html_body="""<html><body>
<h2>Budget Alert</h2>
<p>Your budget threshold has been reached:</p>
<ul>
<li><strong>Budget Limit:</strong> {{budget_limit}}</li>
<li><strong>Spent:</strong> {{spent}}</li>
<li><strong>Remaining:</strong> {{remaining}}</li>
<li><strong>Usage:</strong> {{percentage}}%</li>
</ul>
</body></html>"""
        ))


class EmailProvider(ABC):
    """Abstract email provider"""
    
    @abstractmethod
    async def send(self, to: str, subject: str, body: str, html_body: str) -> bool:
        """Send email"""
        pass


class SMTPEmailProvider(EmailProvider):
    """SMTP email provider"""
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_address: str
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_address = from_address
    
    async def send(self, to: str, subject: str, body: str, html_body: str) -> bool:
        """Send email via SMTP"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                self._send_smtp,
                to,
                subject,
                body,
                html_body
            )
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
    
    def _send_smtp(self, to: str, subject: str, body: str, html_body: str):
        """Send via SMTP (blocking)"""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.from_address
        msg["To"] = to
        
        msg.attach(MIMEText(body, "plain"))
        msg.attach(MIMEText(html_body, "html"))
        
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_user, self.smtp_password)
            server.send_message(msg)


class MockEmailProvider(EmailProvider):
    """Mock email provider for testing"""
    
    def __init__(self):
        self.sent_emails: List[Dict[str, str]] = []
    
    async def send(self, to: str, subject: str, body: str, html_body: str) -> bool:
        """Log email instead of sending"""
        self.sent_emails.append({
            "to": to,
            "subject": subject,
            "body": body,
            "html_body": html_body,
            "timestamp": datetime.utcnow().isoformat()
        })
        print(f"[MOCK EMAIL] To: {to}")
        print(f"[MOCK EMAIL] Subject: {subject}")
        return True
    
    def get_sent_emails(self) -> List[Dict[str, str]]:
        """Get sent emails for testing"""
        return self.sent_emails.copy()


class EmailService:
    """Email notification service"""
    
    def __init__(self, provider: EmailProvider):
        self.provider = provider
        self.template_registry = EmailTemplateRegistry()
        self.email_queue: asyncio.Queue = asyncio.Queue()
    
    async def send_template(
        self,
        template_name: str,
        to: str,
        variables: Dict[str, Any]
    ) -> bool:
        """Send email from template"""
        template = self.template_registry.get(template_name)
        if not template:
            print(f"Template '{template_name}' not found")
            return False
        
        subject, body, html_body = template.render(variables)
        return await self.provider.send(to, subject, body, html_body)
    
    async def send_direct(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """Send direct email"""
        html = html_body or EmailTemplate._convert_to_html(body)
        return await self.provider.send(to, subject, body, html)
    
    async def queue_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        delay: int = 0
    ):
        """Queue email for later sending"""
        await self.email_queue.put({
            "to": to,
            "subject": subject,
            "body": body,
            "html_body": html_body,
            "delay": delay,
            "queued_at": datetime.utcnow()
        })
    
    async def process_queue(self):
        """Process queued emails"""
        while True:
            try:
                email = await asyncio.wait_for(self.email_queue.get(), timeout=1.0)
                
                # Wait if delay is set
                if email["delay"] > 0:
                    await asyncio.sleep(email["delay"])
                
                await self.send_direct(
                    email["to"],
                    email["subject"],
                    email["body"],
                    email["html_body"]
                )
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error processing email queue: {e}")


# Singleton instances
template_registry = EmailTemplateRegistry()

# Use mock provider by default (change to SMTPEmailProvider in production)
email_provider = MockEmailProvider()
email_service = EmailService(email_provider)
