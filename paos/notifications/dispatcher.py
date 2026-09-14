"""
Notification dispatcher
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from paos.notifications.email import email_service
from paos import models


class NotificationType(str, Enum):
    """Types of notifications"""
    APPROVAL_REQUIRED = "approval_required"
    APPROVAL_APPROVED = "approval_approved"
    APPROVAL_REJECTED = "approval_rejected"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    BUDGET_ALERT = "budget_alert"
    STATUS_UPDATE = "status_update"


class NotificationPreferences:
    """User notification preferences"""
    
    def __init__(self, user_email: str):
        self.user_email = user_email
        self.preferences = {
            NotificationType.APPROVAL_REQUIRED: True,
            NotificationType.APPROVAL_APPROVED: True,
            NotificationType.APPROVAL_REJECTED: True,
            NotificationType.TASK_COMPLETED: True,
            NotificationType.TASK_FAILED: True,
            NotificationType.BUDGET_ALERT: True,
            NotificationType.STATUS_UPDATE: False,
        }
        self.quiet_hours_start = 22  # 10 PM
        self.quiet_hours_end = 8    # 8 AM
    
    def is_enabled(self, notification_type: NotificationType) -> bool:
        """Check if notification type is enabled"""
        return self.preferences.get(notification_type, True)
    
    def is_quiet_hours(self) -> bool:
        """Check if currently in quiet hours"""
        current_hour = datetime.utcnow().hour
        if self.quiet_hours_start > self.quiet_hours_end:
            # Range spans midnight
            return current_hour >= self.quiet_hours_start or current_hour < self.quiet_hours_end
        else:
            return self.quiet_hours_start <= current_hour < self.quiet_hours_end
    
    def should_notify(self, notification_type: NotificationType) -> bool:
        """Determine if notification should be sent"""
        if not self.is_enabled(notification_type):
            return False
        
        # Always send critical notifications even during quiet hours
        critical = [
            NotificationType.APPROVAL_REQUIRED,
            NotificationType.TASK_FAILED,
            NotificationType.BUDGET_ALERT
        ]
        
        if notification_type in critical:
            return True
        
        return not self.is_quiet_hours()


class NotificationDispatcher:
    """Dispatches notifications to users"""
    
    def __init__(self):
        self.preferences: Dict[str, NotificationPreferences] = {}
        self.notification_history: List[Dict[str, Any]] = []
    
    def register_user(self, user_email: str) -> NotificationPreferences:
        """Register user for notifications"""
        if user_email not in self.preferences:
            self.preferences[user_email] = NotificationPreferences(user_email)
        return self.preferences[user_email]
    
    def get_preferences(self, user_email: str) -> Optional[NotificationPreferences]:
        """Get user preferences"""
        return self.preferences.get(user_email)
    
    async def notify_approval_required(
        self,
        approval: models.Approval,
        user_email: str,
        approval_url: str
    ) -> bool:
        """Notify about approval requirement"""
        prefs = self.register_user(user_email)
        
        if not prefs.should_notify(NotificationType.APPROVAL_REQUIRED):
            return False
        
        return await email_service.send_template(
            "approval_required",
            user_email,
            {
                "recipient": user_email.split("@")[0],
                "action_type": approval.action_type,
                "task_id": approval.task_id,
                "reason": approval.required_reason,
                "approval_link": approval_url,
                "expiration_time": (approval.created_at + models.timedelta(hours=24)).isoformat()
            }
        )
    
    async def notify_task_completed(
        self,
        task: models.Task,
        user_email: str,
        summary: str,
        cost: str
    ) -> bool:
        """Notify about task completion"""
        prefs = self.register_user(user_email)
        
        if not prefs.should_notify(NotificationType.TASK_COMPLETED):
            return False
        
        return await email_service.send_template(
            "task_completed",
            user_email,
            {
                "recipient": user_email.split("@")[0],
                "task_name": task.name,
                "task_id": str(task.id),
                "completion_time": datetime.utcnow().isoformat(),
                "summary": summary,
                "cost": cost
            }
        )
    
    async def notify_task_failed(
        self,
        task: models.Task,
        user_email: str,
        error_message: str
    ) -> bool:
        """Notify about task failure"""
        prefs = self.register_user(user_email)
        
        if not prefs.should_notify(NotificationType.TASK_FAILED):
            return False
        
        return await email_service.send_template(
            "task_failed",
            user_email,
            {
                "recipient": user_email.split("@")[0],
                "task_name": task.name,
                "task_id": str(task.id),
                "failure_time": datetime.utcnow().isoformat(),
                "error_message": error_message
            }
        )
    
    async def notify_budget_alert(
        self,
        user_email: str,
        budget_limit: str,
        spent: str,
        remaining: str,
        percentage: float
    ) -> bool:
        """Notify about budget alert"""
        prefs = self.register_user(user_email)
        
        if not prefs.should_notify(NotificationType.BUDGET_ALERT):
            return False
        
        return await email_service.send_template(
            "budget_alert",
            user_email,
            {
                "recipient": user_email.split("@")[0],
                "budget_limit": budget_limit,
                "spent": spent,
                "remaining": remaining,
                "percentage": f"{percentage:.1f}"
            }
        )
    
    def get_notification_history(
        self,
        user_email: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get notification history"""
        history = self.notification_history
        
        if user_email:
            history = [h for h in history if h["user_email"] == user_email]
        
        return history[-limit:]


# Singleton instance
notification_dispatcher = NotificationDispatcher()
