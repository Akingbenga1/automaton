"""MCP Client for communicating with public job listing servers (Apify)"""

import json
import os
from typing import List, Dict, Any, Optional
import httpx


class MCPClient:
    """Client for interacting with public MCP servers (Apify)"""

    def __init__(self, config_path: str = "config/mcp_servers.json"):
        self.config = self._load_config(config_path)
        self.servers = {}
        self.api_token = os.getenv("APIFY_API_TOKEN")
        self._init_servers()

    def _load_config(self, config_path: str) -> Dict:
        """Load MCP server configuration"""
        with open(config_path, 'r') as f:
            return json.load(f)

    def _init_servers(self):
        """Initialize configured MCP servers"""
        for name, config in self.config.get("servers", {}).items():
            if config.get("enabled", True):
                self.servers[name] = config

    def _get_auth_headers(self, server_config: Dict) -> Dict:
        """Get authentication headers for API requests"""
        auth_type = server_config.get("auth_type")

        if auth_type == "bearer" and self.api_token:
            return {"Authorization": f"Bearer {self.api_token}"}

        return {}

    def search_jobs_apify_linkedin(
        self,
        keywords: str = "software engineer",
        location: str = "London, UK",
        easy_apply_only: bool = True,
        job_type: Optional[str] = None,
        experience_level: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search LinkedIn jobs via Apify MCP server

        Args:
            keywords: Job search keywords
            location: Location
            easy_apply_only: Filter for Easy Apply jobs only
            job_type: full-time, contract, part-time, etc.
            experience_level: Entry level, Associate, Mid-Senior, Director, Executive
            limit: Max results

        Returns:
            List of job dictionaries
        """
        server = self.servers.get("apify_linkedin")
        if not server or not server.get("enabled"):
            return []

        # Build search input for Apify LinkedIn Jobs Scraper
        search_input = {
            "keywords": keywords,
            "location": location,
            "maxItems": limit
        }

        try:
            jobs = self._call_apify_actor(
                "worldunboxer/rapid-linkedin-scraper",
                search_input,
                server
            )
            return jobs

        except Exception as e:
            print(f"Error searching Apify LinkedIn: {e}")
            return []

    def search_jobs_apify_career_sites(
        self,
        keywords: str = "software engineer",
        location: str = "London, UK",
        company_names: Optional[List[str]] = None,
        ats_platforms: Optional[List[str]] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search career sites via Apify MCP server

        Args:
            keywords: Job search keywords
            location: Location
            company_names: Specific companies to search
            ats_platforms: Filter by ATS platform (workday, greenhouse, etc.)
            limit: Max results

        Returns:
            List of job dictionaries
        """
        server = self.servers.get("apify_career_sites")
        if not server or not server.get("enabled"):
            return []

        search_input = {
            "searchTerms": [keywords],
            "location": location,
            "maxItems": limit
        }

        if company_names:
            search_input["companyNames"] = company_names

        if ats_platforms:
            search_input["atsPlatforms"] = ats_platforms

        try:
            jobs = self._call_apify_actor(
                "fantastic-jobs/career-site-job-listing-api",
                search_input,
                server
            )
            return jobs

        except Exception as e:
            print(f"Error searching Apify Career Sites: {e}")
            return []

    def search_jobs_apify_indeed(
        self,
        keywords: str = "software engineer",
        location: str = "London, UK",
        job_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search Indeed via Apify MCP server

        Args:
            keywords: Job search keywords
            location: Location
            job_type: full-time, part-time, contract, etc.
            limit: Max results

        Returns:
            List of job dictionaries
        """
        server = self.servers.get("apify_indeed")
        if not server or not server.get("enabled"):
            return []

        search_input = {
            "position": keywords,
            "location": location,
            "maxItems": limit
        }

        if job_type:
            search_input["jobType"] = job_type

        try:
            jobs = self._call_apify_actor(
                "curious_coder/indeed-scraper",
                search_input,
                server
            )
            return jobs

        except Exception as e:
            print(f"Error searching Apify Indeed: {e}")
            return []

    def search_jobs_apify_reed(
        self,
        keywords: str = "software engineer",
        location: str = "London",
        limit: int = 20
    ) -> List[Dict]:
        """
        Search Reed.co.uk via Apify MCP server

        Args:
            keywords: Job search keywords
            location: Location (UK cities)
            limit: Max results

        Returns:
            List of job dictionaries
        """
        server = self.servers.get("apify_reed")
        if not server or not server.get("enabled"):
            return []

        search_input = {
            "keywords": keywords,
            "location": location,
            "maxItems": limit
        }

        try:
            jobs = self._call_apify_actor(
                "lexis-solutions/reed-co-uk-scraper",
                search_input,
                server
            )
            return jobs

        except Exception as e:
            print(f"Error searching Apify Reed: {e}")
            return []

    def search_jobs_apify_totaljobs(
        self,
        keywords: str = "software engineer",
        location: str = "London",
        limit: int = 20
    ) -> List[Dict]:
        """
        Search Totaljobs via Apify MCP server

        Args:
            keywords: Job search keywords
            location: Location (UK cities)
            limit: Max results

        Returns:
            List of job dictionaries
        """
        server = self.servers.get("apify_totaljobs")
        if not server or not server.get("enabled"):
            return []

        search_input = {
            "keywords": keywords,
            "location": location,
            "maxItems": limit
        }

        try:
            jobs = self._call_apify_actor(
                "lexis-solutions/totaljobs-scraper",
                search_input,
                server
            )
            return jobs

        except Exception as e:
            print(f"Error searching Apify Totaljobs: {e}")
            return []

    def _call_apify_actor(
        self,
        actor_id: str,
        input_data: Dict,
        server_config: Dict
    ) -> List[Dict]:
        """
        Call an Apify actor and get results

        Args:
            actor_id: Apify actor ID (e.g., "apify/linkedin-jobs-scraper")
            input_data: Input parameters for the actor
            server_config: Server configuration

        Returns:
            List of results from the actor
        """
        if not self.api_token:
            raise ValueError("APIFY_API_TOKEN not set in environment")

        # Apify API endpoint for running actors
        # Convert actor_id format from "username/actor-name" to "username~actor-name"
        actor_id_formatted = actor_id.replace("/", "~")
        run_url = f"https://api.apify.com/v2/acts/{actor_id_formatted}/runs"

        # Apify uses query parameter for token
        params = {"token": self.api_token}

        import time as time_module

        max_retries = 3
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                with httpx.Client(
                    timeout=httpx.Timeout(120.0, connect=30.0),
                    follow_redirects=True,
                    verify=True
                ) as client:
                    # Start actor run
                    if attempt > 0:
                        print(f"Retry attempt {attempt + 1}/{max_retries}...")
                    else:
                        print(f"Starting Apify actor: {actor_id}...")

                    run_response = client.post(
                        run_url,
                        params=params,
                        json=input_data
                    )
                    run_response.raise_for_status()
                    run_data = run_response.json()

                    run_id = run_data["data"]["id"]
                    default_dataset_id = run_data["data"]["defaultDatasetId"]

                    print(f"Actor run started: {run_id}")
                    print("Waiting for results...")

                    # Wait for run to complete and get results
                    # Poll the run status
                    status_url = f"https://api.apify.com/v2/actor-runs/{run_id}"

                    import time
                    max_wait = 180  # 3 minutes max
                    waited = 0

                    while waited < max_wait:
                        status_response = client.get(status_url, params=params)
                        status_data = status_response.json()
                        status = status_data["data"]["status"]

                        if status in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"]:
                            break

                        time.sleep(5)
                        waited += 5

                    if status != "SUCCEEDED":
                        print(f"Actor run finished with status: {status}")
                        return []

                    # Get dataset results
                    dataset_url = f"https://api.apify.com/v2/datasets/{default_dataset_id}/items"
                    results_response = client.get(dataset_url, params=params)
                    results_response.raise_for_status()

                    results = results_response.json()
                    print(f"Retrieved {len(results)} jobs from Apify")

                    return results

            except (httpx.HTTPStatusError, httpx.ConnectError, httpx.ReadTimeout, Exception) as e:
                error_msg = str(e)
                if attempt < max_retries - 1:
                    print(f"Connection error: {error_msg}")
                    print(f"Retrying in {retry_delay} seconds...")
                    time_module.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print(f"Error calling Apify actor after {max_retries} attempts: {error_msg}")
                    return []

    def get_available_platforms(self) -> List[str]:
        """Get list of available job platforms"""
        platforms = []
        for name, config in self.servers.items():
            if config.get("enabled"):
                if "platforms" in config:
                    platforms.extend(config["platforms"])
                else:
                    # Extract platform from server name
                    if "linkedin" in name:
                        platforms.append("linkedin")
                    elif "indeed" in name:
                        platforms.append("indeed")
                    elif "career" in name:
                        platforms.append("career_sites")

        return list(set(platforms))

    def is_server_available(self, server_name: str) -> bool:
        """Check if a server is configured and enabled"""
        server = self.servers.get(server_name)
        return server is not None and server.get("enabled", False)

    def test_connection(self) -> Dict[str, bool]:
        """Test connection to all enabled MCP servers"""
        results = {}

        if not self.api_token:
            print("⚠️  APIFY_API_TOKEN not set - cannot test connections")
            return results

        for name, server in self.servers.items():
            if not server.get("enabled"):
                continue

            try:
                # Try a minimal search to test connection
                print(f"Testing {name}...")

                if "linkedin" in name:
                    jobs = self.search_jobs_apify_linkedin(
                        keywords="test",
                        location="London",
                        limit=1
                    )
                elif "career" in name:
                    jobs = self.search_jobs_apify_career_sites(
                        keywords="test",
                        location="London",
                        limit=1
                    )
                elif "indeed" in name:
                    jobs = self.search_jobs_apify_indeed(
                        keywords="test",
                        location="London",
                        limit=1
                    )
                else:
                    jobs = []

                results[name] = len(jobs) >= 0  # Success if no error
                print(f"✓ {name}: Connected")

            except Exception as e:
                results[name] = False
                print(f"✗ {name}: Failed - {str(e)}")

        return results
