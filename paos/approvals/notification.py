"""
Approval notifications
"""

from typing import List, Optional
from paos import models
from datetime import datetime
import asyncio


class ApprovalNotifier:
    """Sends notifications for approval requests"""
    
    def __init__(self):
        self.notification_queue: List[dict] = []
    
    async def notify_approval_required(
        self,
        approval: models.Approval,
        recipients: List[str],
        action_description: Optional[str] = None
    ):
        """Send approval required notification"""
        notification = {
            "type": "approval_required",
            "approval_id": approval.id,
            "task_id": approval.task_id,
            "action_type": approval.action_type,
            "reason": approval.required_reason,
            "recipients": recipients,
            "description": action_description,
            "timestamp": datetime.utcnow(),
            "status": "pending"
        }
        
        self.notification_queue.append(notification)
        
        # Send notifications (placeholder - would integrate with email/SMS)
        for recipient in recipients:
            await self._send_notification(
                recipient,
                f"Approval Required: {approval.action_type}",
                f"{approval.required_reason}\n\nApproval ID: {approval.id}"
            )
    
    async def notify_approval_decided(
        self,
        approval: models.Approval,
        recipients: List[str],
        approved: bool,
        comment: Optional[str] = None
    ):
        """Send approval decision notification"""
        decision = "APPROVED" if approved else "REJECTED"
        
        for recipient in recipients:
            await self._send_notification(
                recipient,
                f"Approval {decision}: {approval.action_type}",
                f"Status: {decision}\nComment: {comment or 'N/A'}\nApproval ID: {approval.id}"
            )
    
    async def notify_approval_expired(
        self,
        approval: models.Approval,
        recipients: List[str]
    ):
        """Send approval expired notification"""
        for recipient in recipients:
            await self._send_notification(
                recipient,
                f"Approval Expired: {approval.action_type}",
                f"The approval request for {approval.action_type} has expired.\n\nApproval ID: {approval.id}"
            )
    
    async def _send_notification(
        self,
        recipient: str,
        subject: str,
        body: str
    ):
        """Send individual notification (email/SMS/webhook)"""
        # Placeholder for actual notification sending
        # Would integrate with email service, SMS service, etc.
        print(f"NOTIFICATION: {recipient} - {subject}")
        print(f"Body: {body}")
        await asyncio.sleep(0.1)  # Simulate sending
    
    def get_pending_notifications(self) -> List[dict]:
        """Get pending notifications"""
        return [n for n in self.notification_queue if n["status"] == "pending"]
    
    def mark_sent(self, notification_id: int):
        """Mark notification as sent"""
        if 0 <= notification_id < len(self.notification_queue):
            self.notification_queue[notification_id]["status"] = "sent"


# Singleton instance
notifier = ApprovalNotifier()
