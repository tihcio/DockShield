"""
Backup scheduler for DockShield
"""

import schedule
import time
import threading
from datetime import datetime
from typing import List, Dict, Any, Callable, Optional
import logging

logger = logging.getLogger(__name__)


class BackupScheduler:
    """Manages scheduled backup jobs"""

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize backup scheduler

        Args:
            config: Scheduler configuration
        """
        self.config = config
        self.enabled = config.get("enabled", False)
        self.jobs = config.get("jobs", [])
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.scheduled_jobs: List[schedule.Job] = []

    def setup_jobs(self, backup_callback: Callable) -> None:
        """
        Setup scheduled backup jobs

        Args:
            backup_callback: Callback function to execute backup
                            Should accept (job_config: Dict) as parameter
        """
        if not self.enabled:
            logger.info("Scheduler is disabled")
            return

        # Clear existing jobs
        schedule.clear()
        self.scheduled_jobs.clear()

        # Setup each job
        for job_config in self.jobs:
            if not job_config.get("enabled", True):
                continue

            job_name = job_config.get("name", "unnamed_job")
            job_schedule = job_config.get("schedule", "0 2 * * *")  # Default: 2 AM daily

            try:
                # Parse cron-style schedule (simplified)
                scheduled_job = self._schedule_job(job_schedule, backup_callback, job_config)

                if scheduled_job:
                    self.scheduled_jobs.append(scheduled_job)
                    logger.info(f"Scheduled job '{job_name}' with schedule: {job_schedule}")
                else:
                    logger.warning(f"Failed to schedule job '{job_name}'")

            except Exception as e:
                logger.error(f"Error setting up job '{job_name}': {e}")

        logger.info(f"Scheduler setup complete: {len(self.scheduled_jobs)} jobs configured")

    def _schedule_job(
        self,
        cron_schedule: str,
        callback: Callable,
        job_config: Dict[str, Any]
    ) -> Optional[schedule.Job]:
        """
        Schedule a job based on cron-style schedule

        Args:
            cron_schedule: Cron-style schedule string (minute hour day month weekday)
            callback: Callback function
            job_config: Job configuration

        Returns:
            Scheduled job or None
        """
        # Parse cron schedule: minute hour day month weekday
        parts = cron_schedule.split()
        if len(parts) != 5:
            logger.error(f"Invalid cron schedule format: {cron_schedule}")
            return None

        minute, hour, day, month, weekday = parts

        # Create wrapper function
        def job_wrapper():
            logger.info(f"Executing scheduled job: {job_config.get('name')}")
            try:
                callback(job_config)
            except Exception as e:
                logger.error(f"Error executing scheduled job: {e}")

        # Schedule based on pattern
        # Note: schedule library has limitations compared to full cron
        try:
            # Daily at specific time
            if weekday == "*" and day == "*" and month == "*":
                return schedule.every().day.at(f"{hour.zfill(2)}:{minute.zfill(2)}").do(job_wrapper)

            # Weekly on specific day
            elif weekday != "*" and day == "*" and month == "*":
                weekday_map = {
                    "0": "sunday",
                    "1": "monday",
                    "2": "tuesday",
                    "3": "wednesday",
                    "4": "thursday",
                    "5": "friday",
                    "6": "saturday",
                }
                day_name = weekday_map.get(weekday, "monday")
                job = getattr(schedule.every(), day_name)
                return job.at(f"{hour.zfill(2)}:{minute.zfill(2)}").do(job_wrapper)

            # Hourly
            elif minute != "*" and hour == "*":
                return schedule.every().hour.at(f":{minute.zfill(2)}").do(job_wrapper)

            # Every N hours
            elif hour == "*/6":  # Every 6 hours
                return schedule.every(6).hours.at(f":{minute.zfill(2)}").do(job_wrapper)

            else:
                logger.warning(f"Unsupported cron pattern: {cron_schedule}")
                logger.warning("Defaulting to daily at 2 AM")
                return schedule.every().day.at("02:00").do(job_wrapper)

        except Exception as e:
            logger.error(f"Error scheduling job: {e}")
            return None

    def start(self) -> None:
        """Start the scheduler in a background thread"""
        if self.running:
            logger.warning("Scheduler is already running")
            return

        if not self.enabled:
            logger.info("Scheduler is disabled, not starting")
            return

        if not self.scheduled_jobs:
            logger.warning("No jobs scheduled, not starting scheduler")
            return

        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Scheduler started")

    def _run_scheduler(self) -> None:
        """Run the scheduler loop"""
        logger.info("Scheduler thread started")

        while self.running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)

        logger.info("Scheduler thread stopped")

    def stop(self) -> None:
        """Stop the scheduler"""
        if not self.running:
            return

        logger.info("Stopping scheduler...")
        self.running = False

        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=5)

        schedule.clear()
        self.scheduled_jobs.clear()
        logger.info("Scheduler stopped")

    def get_next_run_times(self) -> List[Dict[str, Any]]:
        """
        Get next run times for all scheduled jobs

        Returns:
            List of dictionaries with job info and next run time
        """
        result = []

        for i, job in enumerate(self.scheduled_jobs):
            next_run = schedule.idle_seconds()
            if next_run is not None:
                job_info = {
                    "job_number": i,
                    "next_run": datetime.now().timestamp() + next_run,
                    "next_run_human": self._format_next_run(next_run),
                }

                # Try to get job name from config
                if i < len(self.jobs):
                    job_info["name"] = self.jobs[i].get("name", f"Job {i}")

                result.append(job_info)

        return result

    def _format_next_run(self, seconds: float) -> str:
        """Format next run time in human-readable format"""
        if seconds < 60:
            return f"in {int(seconds)} seconds"
        elif seconds < 3600:
            return f"in {int(seconds / 60)} minutes"
        elif seconds < 86400:
            return f"in {int(seconds / 3600)} hours"
        else:
            return f"in {int(seconds / 86400)} days"

    def add_job(self, job_config: Dict[str, Any], backup_callback: Callable) -> bool:
        """
        Add a new scheduled job

        Args:
            job_config: Job configuration
            backup_callback: Backup callback function

        Returns:
            True if successful, False otherwise
        """
        try:
            job_schedule = job_config.get("schedule", "0 2 * * *")
            scheduled_job = self._schedule_job(job_schedule, backup_callback, job_config)

            if scheduled_job:
                self.jobs.append(job_config)
                self.scheduled_jobs.append(scheduled_job)
                logger.info(f"Added job: {job_config.get('name')}")
                return True
            else:
                logger.error(f"Failed to add job: {job_config.get('name')}")
                return False

        except Exception as e:
            logger.error(f"Error adding job: {e}")
            return False

    def remove_job(self, job_name: str) -> bool:
        """
        Remove a scheduled job by name

        Args:
            job_name: Name of job to remove

        Returns:
            True if successful, False otherwise
        """
        try:
            for i, job_config in enumerate(self.jobs):
                if job_config.get("name") == job_name:
                    # Cancel scheduled job
                    if i < len(self.scheduled_jobs):
                        schedule.cancel_job(self.scheduled_jobs[i])
                        self.scheduled_jobs.pop(i)

                    # Remove from config
                    self.jobs.pop(i)
                    logger.info(f"Removed job: {job_name}")
                    return True

            logger.warning(f"Job not found: {job_name}")
            return False

        except Exception as e:
            logger.error(f"Error removing job: {e}")
            return False

    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self.running

    def get_job_count(self) -> int:
        """Get number of scheduled jobs"""
        return len(self.scheduled_jobs)
