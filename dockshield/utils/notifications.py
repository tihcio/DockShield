"""
Desktop notification management for DockShield (KDE integration)
"""

import subprocess
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages desktop notifications using KDE's notification system"""

    def __init__(self, enabled: bool = True, sound_enabled: bool = True):
        """
        Initialize notification manager

        Args:
            enabled: Enable notifications
            sound_enabled: Enable notification sounds
        """
        self.enabled = enabled
        self.sound_enabled = sound_enabled
        self.app_name = "DockShield"

    def send_notification(
        self,
        title: str,
        message: str,
        urgency: str = "normal",
        icon: Optional[str] = None,
        timeout: int = 5000,
    ) -> bool:
        """
        Send desktop notification

        Args:
            title: Notification title
            message: Notification message
            urgency: Urgency level (low, normal, critical)
            icon: Icon name or path (optional)
            timeout: Timeout in milliseconds

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            # Use kdialog for KDE notifications
            cmd = [
                "kdialog",
                "--title", self.app_name,
                "--passivepopup", f"{title}\n{message}",
                str(timeout // 1000)  # kdialog uses seconds
            ]

            # Alternative: use notify-send (works on most Linux desktops)
            # cmd = [
            #     "notify-send",
            #     "-a", self.app_name,
            #     "-u", urgency,
            #     "-t", str(timeout),
            # ]
            # if icon:
            #     cmd.extend(["-i", icon])
            # cmd.extend([title, message])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.debug(f"Notification sent: {title}")
                return True
            else:
                logger.warning(f"Failed to send notification: {result.stderr}")
                # Fallback to notify-send
                return self._send_notification_fallback(title, message, urgency, icon, timeout)

        except FileNotFoundError:
            # kdialog not found, try fallback
            return self._send_notification_fallback(title, message, urgency, icon, timeout)
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False

    def _send_notification_fallback(
        self,
        title: str,
        message: str,
        urgency: str,
        icon: Optional[str],
        timeout: int
    ) -> bool:
        """Fallback notification using notify-send"""
        try:
            cmd = [
                "notify-send",
                "-a", self.app_name,
                "-u", urgency,
                "-t", str(timeout),
            ]

            if icon:
                cmd.extend(["-i", icon])

            cmd.extend([title, message])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.debug(f"Fallback notification sent: {title}")
                return True
            else:
                logger.warning(f"Fallback notification failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"Error sending fallback notification: {e}")
            return False

    def notify_success(self, title: str, message: str) -> bool:
        """
        Send success notification

        Args:
            title: Notification title
            message: Notification message

        Returns:
            True if successful, False otherwise
        """
        return self.send_notification(
            title=title,
            message=message,
            urgency="normal",
            icon="dialog-ok-apply",
        )

    def notify_error(self, title: str, message: str) -> bool:
        """
        Send error notification

        Args:
            title: Notification title
            message: Notification message

        Returns:
            True if successful, False otherwise
        """
        return self.send_notification(
            title=title,
            message=message,
            urgency="critical",
            icon="dialog-error",
        )

    def notify_warning(self, title: str, message: str) -> bool:
        """
        Send warning notification

        Args:
            title: Notification title
            message: Notification message

        Returns:
            True if successful, False otherwise
        """
        return self.send_notification(
            title=title,
            message=message,
            urgency="normal",
            icon="dialog-warning",
        )

    def notify_info(self, title: str, message: str) -> bool:
        """
        Send info notification

        Args:
            title: Notification title
            message: Notification message

        Returns:
            True if successful, False otherwise
        """
        return self.send_notification(
            title=title,
            message=message,
            urgency="low",
            icon="dialog-information",
        )

    def notify_backup_started(self, container_name: str) -> bool:
        """Notify backup started"""
        return self.notify_info(
            title="Backup Started",
            message=f"Creating backup for container: {container_name}"
        )

    def notify_backup_completed(self, container_name: str, size: str) -> bool:
        """Notify backup completed"""
        return self.notify_success(
            title="Backup Completed",
            message=f"Backup created for {container_name} ({size})"
        )

    def notify_backup_failed(self, container_name: str, error: str) -> bool:
        """Notify backup failed"""
        return self.notify_error(
            title="Backup Failed",
            message=f"Failed to backup {container_name}: {error}"
        )

    def notify_restore_started(self, container_name: str) -> bool:
        """Notify restore started"""
        return self.notify_info(
            title="Restore Started",
            message=f"Restoring container: {container_name}"
        )

    def notify_restore_completed(self, container_name: str) -> bool:
        """Notify restore completed"""
        return self.notify_success(
            title="Restore Completed",
            message=f"Container {container_name} restored successfully"
        )

    def notify_restore_failed(self, container_name: str, error: str) -> bool:
        """Notify restore failed"""
        return self.notify_error(
            title="Restore Failed",
            message=f"Failed to restore {container_name}: {error}"
        )

    def play_sound(self, sound_name: str = "dialog-information") -> None:
        """
        Play notification sound

        Args:
            sound_name: Sound name from KDE sound theme
        """
        if not self.sound_enabled:
            return

        try:
            # Use KDE's sound player
            subprocess.run(
                ["knotify5", sound_name],
                capture_output=True,
                timeout=2
            )
        except Exception as e:
            logger.debug(f"Could not play sound: {e}")
