"""
Notifications package initialization
"""

from paos.notifications.email import (
    EmailTemplate,
    EmailTemplateRegistry,
    EmailProvider,
    SMTPEmailProvider,
    MockEmailProvider,
    EmailService,
    email_service,
    template_registry
)
from paos.notifications.dispatcher import (
    NotificationType,
    NotificationPreferences,
    NotificationDispatcher,
    notification_dispatcher
)

__all__ = [
    "EmailTemplate",
    "EmailTemplateRegistry",
    "EmailProvider",
    "SMTPEmailProvider",
    "MockEmailProvider",
    "EmailService",
    "email_service",
    "template_registry",
    "NotificationType",
    "NotificationPreferences",
    "NotificationDispatcher",
    "notification_dispatcher",
]
