"""Job search logic using public MCP servers (Apify)"""

from typing import List, Dict, Optional
from src.mcp_client import MCPClient
import hashlib


class JobSearcher:
    """Searches for jobs across multiple platforms using Apify MCP servers"""

    def __init__(self, mcp_client: MCPClient, profile: Dict):
        self.mcp = mcp_client
        self.profile = profile

    def search_all_platforms(
        self,
        platforms: Optional[List[str]] = None,
        limit_per_platform: int = 20,
        easy_apply_only: bool = True
    ) -> List[Dict]:
        """
        Search for jobs across all configured platforms

        Args:
            platforms: List of platform names (None = all available)
            limit_per_platform: Max results per platform
            easy_apply_only: Filter for Easy Apply jobs (LinkedIn)

        Returns:
            List of normalized job dictionaries
        """
        if platforms is None:
            platforms = self.mcp.get_available_platforms()

        all_jobs = []

        # Search LinkedIn via Apify
        if "linkedin" in platforms and self.mcp.is_server_available("apify_linkedin"):
            linkedin_jobs = self._search_apify_linkedin(limit_per_platform, easy_apply_only)
            all_jobs.extend(linkedin_jobs)

        # Search Career Sites via Apify
        if "career_sites" in platforms and self.mcp.is_server_available("apify_career_sites"):
            career_jobs = self._search_apify_career_sites(limit_per_platform)
            all_jobs.extend(career_jobs)

        # Search Indeed via Apify
        if "indeed" in platforms and self.mcp.is_server_available("apify_indeed"):
            indeed_jobs = self._search_apify_indeed(limit_per_platform)
            all_jobs.extend(indeed_jobs)

        # Search Reed.co.uk via Apify
        if "reed" in platforms and self.mcp.is_server_available("apify_reed"):
            reed_jobs = self._search_apify_reed(limit_per_platform)
            all_jobs.extend(reed_jobs)

        # Search Totaljobs via Apify
        if "totaljobs" in platforms and self.mcp.is_server_available("apify_totaljobs"):
            totaljobs_jobs = self._search_apify_totaljobs(limit_per_platform)
            all_jobs.extend(totaljobs_jobs)

        # Deduplicate jobs
        all_jobs = self._deduplicate_jobs(all_jobs)

        return all_jobs

    def _search_apify_linkedin(self, limit: int, easy_apply_only: bool) -> List[Dict]:
        """Search LinkedIn via Apify MCP server"""
        prefs = self.profile.get("preferences", {})

        # Build search query from target roles
        target_roles = prefs.get("target_roles", [])
        keywords = target_roles[0] if target_roles else "software engineer"

        # Get location
        locations = prefs.get("locations", ["London, UK"])
        location = locations[0] if locations else "London, UK"

        # Get job types
        job_types = prefs.get("job_types", [])
        job_type = job_types[0] if job_types else "full-time"

        # Search via Apify
        jobs = self.mcp.search_jobs_apify_linkedin(
            keywords=keywords,
            location=location,
            easy_apply_only=easy_apply_only,
            job_type=job_type,
            limit=limit
        )

        # Normalize format
        return [self._normalize_job(job, "linkedin") for job in jobs]

    def _search_apify_career_sites(self, limit: int) -> List[Dict]:
        """Search career sites via Apify MCP server"""
        prefs = self.profile.get("preferences", {})

        # Build search query
        target_roles = prefs.get("target_roles", [])
        keywords = target_roles[0] if target_roles else "software engineer"

        # Get location
        locations = prefs.get("locations", ["London, UK"])
        location = locations[0] if locations else "London, UK"

        # Search via Apify
        jobs = self.mcp.search_jobs_apify_career_sites(
            keywords=keywords,
            location=location,
            limit=limit
        )

        # Normalize format
        return [self._normalize_job(job, "career_site") for job in jobs]

    def _search_apify_indeed(self, limit: int) -> List[Dict]:
        """Search Indeed via Apify MCP server"""
        prefs = self.profile.get("preferences", {})

        # Build search query
        target_roles = prefs.get("target_roles", [])
        keywords = target_roles[0] if target_roles else "software engineer"

        # Get location
        locations = prefs.get("locations", ["London, UK"])
        location = locations[0] if locations else "London, UK"

        # Get job type
        job_types = prefs.get("job_types", [])
        job_type = job_types[0] if job_types else None

        # Search via Apify
        jobs = self.mcp.search_jobs_apify_indeed(
            keywords=keywords,
            location=location,
            job_type=job_type,
            limit=limit
        )

        # Normalize format
        return [self._normalize_job(job, "indeed") for job in jobs]

    def _search_apify_reed(self, limit: int) -> List[Dict]:
        """Search Reed.co.uk via Apify MCP server"""
        prefs = self.profile.get("preferences", {})

        # Build search query
        target_roles = prefs.get("target_roles", [])
        keywords = target_roles[0] if target_roles else "software engineer"

        # Get location (Reed is UK-only, use UK cities)
        locations = prefs.get("locations", ["London"])
        # Strip ", UK" suffix if present for better Reed search
        location = locations[0].replace(", UK", "").replace(", United Kingdom", "")

        # Search via Apify
        jobs = self.mcp.search_jobs_apify_reed(
            keywords=keywords,
            location=location,
            limit=limit
        )

        # Normalize format
        return [self._normalize_job(job, "reed") for job in jobs]

    def _search_apify_totaljobs(self, limit: int) -> List[Dict]:
        """Search Totaljobs via Apify MCP server"""
        prefs = self.profile.get("preferences", {})

        # Build search query
        target_roles = prefs.get("target_roles", [])
        keywords = target_roles[0] if target_roles else "software engineer"

        # Get location (Totaljobs is UK-only)
        locations = prefs.get("locations", ["London"])
        # Strip ", UK" suffix if present
        location = locations[0].replace(", UK", "").replace(", United Kingdom", "")

        # Search via Apify
        jobs = self.mcp.search_jobs_apify_totaljobs(
            keywords=keywords,
            location=location,
            limit=limit
        )

        # Normalize format
        return [self._normalize_job(job, "totaljobs") for job in jobs]

    def _normalize_job(self, job: Dict, platform: str) -> Dict:
        """
        Normalize job data to a standard format

        Different MCP servers return different formats, so we normalize
        to a consistent structure
        """
        # Generate unique job ID
        job_id = self._generate_job_id(job, platform)

        # Extract salary
        salary_min, salary_max = self._extract_salary(job)

        # Extract location (handle arrays from career sites)
        location = job.get("location") or job.get("jobLocation")
        if not location and job.get("locations_derived"):
            # Career sites returns array of locations
            locations_derived = job.get("locations_derived", [])
            location = locations_derived[0] if locations_derived else "Unknown"
        if not location:
            location = "Unknown"

        # Extract posted date
        posted_date = (job.get("posted_date") or job.get("date_posted") or
                      job.get("postedDate") or job.get("time_posted") or
                      job.get("datePosted") or job.get("publishedAt"))

        # Extract employment type (handle arrays)
        job_type = job.get("jobType") or job.get("type")
        if not job_type and job.get("employment_type"):
            emp_type = job.get("employment_type")
            job_type = emp_type[0] if isinstance(emp_type, list) else emp_type

        # Normalize job data
        normalized = {
            "job_id": job_id,
            "platform": platform,
            "title": job.get("title") or job.get("job_title") or job.get("position") or job.get("jobTitle") or "Unknown",
            "company": (job.get("company") or job.get("company_name") or
                       job.get("companyName") or job.get("organization") or
                       job.get("employer") or "Unknown"),
            "location": location,
            "url": job.get("url") or job.get("job_url") or job.get("jobUrl") or job.get("link") or "",
            "description": (job.get("description") or job.get("job_description") or
                          job.get("description_text") or job.get("jobDescription") or ""),
            "salary_min": salary_min,
            "salary_max": salary_max,
            "job_type": job_type,
            "work_mode": self._extract_work_mode(job),
            "posted_date": posted_date,
            "easy_apply": job.get("easyApply") or job.get("easy_apply") or job.get("isEasyApply") or False,
            "raw_data": job  # Keep original for reference
        }

        return normalized

    def _generate_job_id(self, job: Dict, platform: str) -> str:
        """Generate unique job ID"""
        # Use platform's ID if available
        if "job_id" in job:
            return f"{platform}_{job['job_id']}"
        elif "id" in job:
            return f"{platform}_{job['id']}"
        elif "jobId" in job:
            return f"{platform}_{job['jobId']}"

        # Otherwise hash the URL or key fields
        url = job.get("url") or job.get("jobUrl") or job.get("link") or ""
        if url:
            return hashlib.md5(url.encode()).hexdigest()

        # Fallback to hashing title + company
        title = job.get("title") or job.get("position") or job.get("jobTitle") or ""
        company = job.get("company") or job.get("companyName") or ""
        text = f"{platform}_{company}_{title}"
        return hashlib.md5(text.encode()).hexdigest()

    def _extract_salary(self, job: Dict) -> tuple:
        """Extract salary min and max from job data"""
        salary_min = job.get("salaryMin") or job.get("salary_min") or job.get("minSalary")
        salary_max = job.get("salaryMax") or job.get("salary_max") or job.get("maxSalary")

        # Try to parse salary text if not structured
        if not salary_min and not salary_max:
            salary_text = job.get("salary") or job.get("salary_range") or job.get("salaryRange") or ""
            if salary_text:
                salary_min, salary_max = self._parse_salary_text(salary_text)

        return salary_min, salary_max

    def _parse_salary_text(self, text: str) -> tuple:
        """Parse salary from text like '£50,000 - £70,000' or '$80k-$100k'"""
        import re

        # Remove currency symbols and commas
        text = text.replace("£", "").replace("$", "").replace(",", "")

        # Look for patterns like "50000-70000" or "50k-70k"
        pattern = r'(\d+\.?\d*)\s*[kK]?\s*[-to]\s*(\d+\.?\d*)\s*[kK]?'
        match = re.search(pattern, text)

        if match:
            min_val = float(match.group(1))
            max_val = float(match.group(2))

            # Convert k notation
            if 'k' in text.lower():
                min_val *= 1000
                max_val *= 1000

            return int(min_val), int(max_val)

        # Try single value
        pattern = r'(\d+\.?\d*)\s*[kK]?'
        match = re.search(pattern, text)
        if match:
            val = float(match.group(1))
            if 'k' in text.lower():
                val *= 1000
            return int(val), int(val)

        return None, None

    def _extract_work_mode(self, job: Dict) -> Optional[str]:
        """Extract work mode (remote/hybrid/onsite)"""
        # Check explicit field
        work_mode = job.get("workMode") or job.get("remoteType") or job.get("workplace_type")
        if work_mode:
            return work_mode.lower()

        # Check description
        description = (job.get("description") or "").lower()
        location = (job.get("location") or "").lower()
        text = description + " " + location

        if "remote" in text:
            return "remote"
        elif "hybrid" in text:
            return "hybrid"
        else:
            return "onsite"

    def _deduplicate_jobs(self, jobs: List[Dict]) -> List[Dict]:
        """Remove duplicate jobs based on job_id"""
        seen = set()
        unique_jobs = []

        for job in jobs:
            job_id = job["job_id"]
            if job_id not in seen:
                seen.add(job_id)
                unique_jobs.append(job)

        return unique_jobs
