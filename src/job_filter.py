"""Job filtering and matching logic"""

from typing import Dict, List
from datetime import datetime, timedelta
import re


class JobFilter:
    """Filters and scores jobs based on profile preferences"""

    def __init__(self, profile: Dict):
        self.profile = profile
        self.min_match_score = profile.get("filtering", {}).get("min_match_score", 0.65)
        self.exclude_keywords = profile.get("filtering", {}).get("exclude_keywords", [])
        self.prefer_keywords = profile.get("filtering", {}).get("prefer_keywords", [])
        self.max_days_old = profile.get("filtering", {}).get("max_days_old", 7)

    def calculate_match_score(self, job: Dict) -> float:
        """
        Calculate how well a job matches the profile (0.0 to 1.0)

        Scoring factors:
        - Title match: 30%
        - Skills match: 30%
        - Location match: 15%
        - Salary match: 15%
        - Preferred keywords: 10%
        """
        score = 0.0

        # Title match (30 points)
        score += self._score_title(job) * 0.30

        # Skills match (30 points)
        score += self._score_skills(job) * 0.30

        # Location match (15 points)
        score += self._score_location(job) * 0.15

        # Salary match (15 points)
        score += self._score_salary(job) * 0.15

        # Preferred keywords bonus (10 points)
        score += self._score_preferences(job) * 0.10

        return min(1.0, max(0.0, score))

    def _score_title(self, job: Dict) -> float:
        """Score job title match"""
        title = job.get("title", "").lower()
        target_roles = self.profile.get("preferences", {}).get("target_roles", [])
        keywords = self.profile.get("preferences", {}).get("job_titles_keywords", [])

        # Check if any target role is in the title
        for role in target_roles:
            if role.lower() in title:
                return 1.0

        # Check for keyword matches
        matches = sum(1 for kw in keywords if kw.lower() in title)
        if matches > 0:
            return min(1.0, matches * 0.3)

        return 0.0

    def _score_skills(self, job: Dict) -> float:
        """Score skills match"""
        description = (job.get("description", "") + " " + job.get("title", "")).lower()
        all_skills = []

        # Collect all skills from profile
        skills_data = self.profile.get("skills", {})
        if isinstance(skills_data, dict):
            for skill_type in ["technical", "business", "leadership"]:
                all_skills.extend(skills_data.get(skill_type, []))
        elif isinstance(skills_data, list):
            all_skills = skills_data

        if not all_skills:
            return 0.5  # Neutral score if no skills defined

        # Count skill matches
        matches = sum(1 for skill in all_skills if skill.lower() in description)
        score = matches / len(all_skills)

        return min(1.0, score)

    def _score_location(self, job: Dict) -> float:
        """Score location match"""
        job_location = job.get("location", "").lower()
        preferred_locations = self.profile.get("preferences", {}).get("locations", [])

        if not preferred_locations:
            return 1.0  # No preference means all locations OK

        # Check for exact or partial matches
        for pref_loc in preferred_locations:
            if pref_loc.lower() in job_location or job_location in pref_loc.lower():
                return 1.0

        # Check for remote/hybrid
        if "remote" in job_location or "hybrid" in job_location:
            work_modes = self.profile.get("preferences", {}).get("work_modes", [])
            if "remote" in work_modes or "hybrid" in work_modes:
                return 1.0

        return 0.0

    def _score_salary(self, job: Dict) -> float:
        """Score salary match"""
        salary_prefs = self.profile.get("preferences", {}).get("salary", {})
        min_expected = salary_prefs.get("min", 0)
        max_expected = salary_prefs.get("max", float('inf'))

        job_salary_min = job.get("salary_min")
        job_salary_max = job.get("salary_max")

        # If no salary info in job, give neutral score
        if not job_salary_min and not job_salary_max:
            return 0.5

        # If job max is below our minimum, low score
        if job_salary_max and job_salary_max < min_expected:
            return 0.0

        # If job min is above our maximum, still might be OK
        if job_salary_min and job_salary_min > max_expected:
            return 0.7  # Might be worth it

        # If in range, perfect score
        if job_salary_min and job_salary_min >= min_expected:
            return 1.0

        return 0.5

    def _score_preferences(self, job: Dict) -> float:
        """Score preferred keywords"""
        text = (job.get("title", "") + " " + job.get("description", "")).lower()

        matches = sum(1 for kw in self.prefer_keywords if kw.lower() in text)

        if not self.prefer_keywords:
            return 0.0

        return min(1.0, matches / len(self.prefer_keywords))

    def should_exclude(self, job: Dict) -> bool:
        """Check if job should be excluded"""
        text = (job.get("title", "") + " " + job.get("description", "")).lower()

        # Check exclude keywords
        for keyword in self.exclude_keywords:
            if keyword.lower() in text:
                return True

        # Check if too old
        if "posted_date" in job:
            try:
                posted_date = self._parse_date(job["posted_date"])
                if posted_date:
                    days_old = (datetime.now() - posted_date).days
                    if days_old > self.max_days_old:
                        return True
            except:
                pass

        return False

    def _parse_date(self, date_str: str) -> datetime:
        """Parse various date formats"""
        # Try ISO format
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except:
            pass

        # Try common formats
        formats = [
            "%Y-%m-%d",
            "%Y-%m-%dT%H:%M:%S",
            "%d/%m/%Y",
            "%m/%d/%Y"
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except:
                continue

        return None

    def should_apply(self, job: Dict) -> bool:
        """Decide if we should apply to this job"""
        # First check exclusions
        if self.should_exclude(job):
            return False

        # Calculate match score
        score = self.calculate_match_score(job)
        job["match_score"] = score  # Store for later

        # Check if score meets threshold
        return score >= self.min_match_score

    def filter_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """
        Filter and score a list of jobs

        Returns:
            List of jobs that pass filters, sorted by match score
        """
        filtered = []

        for job in jobs:
            if self.should_apply(job):
                filtered.append(job)

        # Sort by match score (highest first)
        filtered.sort(key=lambda j: j.get("match_score", 0), reverse=True)

        return filtered
