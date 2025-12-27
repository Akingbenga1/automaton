"""Job application logic"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from src.database import ApplicationDatabase
import time


class JobApplicator:
    """Handles job applications with rate limiting"""

    def __init__(self, database: ApplicationDatabase, profile: Dict, dry_run: bool = False):
        self.db = database
        self.profile = profile
        self.dry_run = dry_run
        self.rate_limits = profile.get("application", {}).get("rate_limits", {})

    def can_apply_to_platform(self, platform: str) -> bool:
        """Check if we can apply to another job on this platform"""
        limit = self.rate_limits.get(platform, self.rate_limits.get("default", 1))

        # Get applications in the last hour
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        count = self.db.get_platform_count(platform, since=one_hour_ago)

        return count < limit

    def apply_to_job(self, job: Dict, manual_approval: bool = False) -> Dict:
        """
        Apply to a job

        Args:
            job: Job dictionary
            manual_approval: If True, ask for confirmation before applying

        Returns:
            Dictionary with application result
        """
        result = {
            "success": False,
            "job_id": job["job_id"],
            "job_title": job["title"],
            "company": job["company"],
            "platform": job["platform"],
            "message": ""
        }

        # Check if already applied
        if self.db.has_applied(job["job_id"]):
            result["message"] = "Already applied to this job"
            return result

        # Check rate limits
        if not self.can_apply_to_platform(job["platform"]):
            result["message"] = f"Rate limit reached for {job['platform']}"
            return result

        # Manual approval
        if manual_approval:
            if not self._get_user_approval(job):
                result["message"] = "User declined to apply"
                return result

        # Dry run mode
        if self.dry_run:
            result["success"] = True
            result["message"] = "DRY RUN - Would have applied"
            self._log_application(job, "dry_run")
            return result

        # Actually apply
        try:
            application_result = self._submit_application(job)

            if application_result["success"]:
                # Record in database
                self.db.add_application(job)
                result["success"] = True
                result["message"] = "Application submitted successfully"
                result["confirmation"] = application_result.get("confirmation_number")
            else:
                result["message"] = f"Application failed: {application_result.get('error')}"

        except Exception as e:
            result["message"] = f"Error applying: {str(e)}"

        return result

    def _get_user_approval(self, job: Dict) -> bool:
        """Ask user for approval to apply"""
        print("\n" + "="*80)
        print(f"Job: {job['title']}")
        print(f"Company: {job['company']}")
        print(f"Location: {job['location']}")
        print(f"Platform: {job['platform']}")
        print(f"Match Score: {job.get('match_score', 0):.2%}")
        print(f"URL: {job['url']}")

        if job.get("salary_min") or job.get("salary_max"):
            salary = []
            if job.get("salary_min"):
                salary.append(f"£{job['salary_min']:,}")
            if job.get("salary_max"):
                salary.append(f"£{job['salary_max']:,}")
            print(f"Salary: {' - '.join(salary)}")

        print("\nDescription (first 500 chars):")
        print(job.get("description", "")[:500])
        print("="*80)

        response = input("\nApply to this job? (y/n): ").strip().lower()
        return response == 'y'

    def _submit_application(self, job: Dict) -> Dict:
        """
        Submit application to the platform

        This is a placeholder for actual application logic.
        In a real implementation, this would:
        1. For LinkedIn: Use Playwright to click "Easy Apply" and fill forms
        2. For Indeed: Use their API or browser automation
        3. For other platforms: Platform-specific logic

        Returns:
            Dict with success status and optional confirmation number
        """
        platform = job["platform"]

        # Simulate application delay
        time.sleep(2)

        if platform == "linkedin":
            return self._apply_linkedin(job)
        elif platform == "indeed":
            return self._apply_indeed(job)
        else:
            return self._apply_generic(job)

    def _apply_linkedin(self, job: Dict) -> Dict:
        """
        Apply via LinkedIn Easy Apply

        PLACEHOLDER: In production, this would use Playwright to:
        1. Navigate to job URL
        2. Click "Easy Apply" button
        3. Fill out multi-step form using profile data
        4. Submit application
        5. Capture confirmation
        """
        # TODO: Implement LinkedIn Easy Apply automation
        # For now, return mock success
        return {
            "success": True,
            "confirmation_number": f"LI-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "method": "easy_apply"
        }

    def _apply_indeed(self, job: Dict) -> Dict:
        """
        Apply via Indeed

        PLACEHOLDER: In production, this would:
        1. Use Indeed API if available
        2. Or use browser automation for Indeed Easy Apply
        """
        # TODO: Implement Indeed application
        return {
            "success": True,
            "confirmation_number": f"IND-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "method": "indeed_apply"
        }

    def _apply_generic(self, job: Dict) -> Dict:
        """
        Generic application for other platforms

        PLACEHOLDER: In production, implement platform-specific logic
        """
        # TODO: Implement generic application
        return {
            "success": True,
            "confirmation_number": f"GEN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "method": "generic"
        }

    def _log_application(self, job: Dict, status: str):
        """Log application for dry run mode"""
        print(f"\n[DRY RUN] Would apply to:")
        print(f"  {job['title']} at {job['company']}")
        print(f"  Platform: {job['platform']}")
        print(f"  Match: {job.get('match_score', 0):.2%}")

    def apply_to_jobs_batch(
        self,
        jobs: List[Dict],
        max_applications: int = 5,
        manual_approval: bool = False
    ) -> List[Dict]:
        """
        Apply to multiple jobs with rate limiting

        Args:
            jobs: List of jobs to apply to
            max_applications: Maximum number of applications to submit
            manual_approval: Ask for approval for each job

        Returns:
            List of application results
        """
        results = []
        applications_submitted = 0

        for job in jobs:
            if applications_submitted >= max_applications:
                break

            result = self.apply_to_job(job, manual_approval)
            results.append(result)

            if result["success"] and not self.dry_run:
                applications_submitted += 1

                # Rate limiting delay
                time.sleep(5)  # Wait 5 seconds between applications

        return results
