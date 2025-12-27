"""Claude AI Agent for intelligent job analysis and decision making"""

import os
from typing import Dict, List, Optional
from anthropic import Anthropic
import json


class ClaudeAgent:
    """Claude Sonnet-powered AI agent for job application decisions"""

    def __init__(self, api_key: Optional[str] = None, model: str = "claude-sonnet-4-20250514"):
        """
        Initialize Claude AI agent

        Args:
            api_key: Anthropic API key (or from ANTHROPIC_API_KEY env var)
            model: Claude model to use (default: claude-sonnet-4)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment or parameters")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model

    def analyze_job_match(self, job: Dict, profile: Dict) -> Dict:
        """
        Use Claude to analyze how well a job matches the profile

        Args:
            job: Job dictionary
            profile: User profile dictionary

        Returns:
            Analysis with score, reasoning, and recommendation
        """
        prompt = self._build_job_analysis_prompt(job, profile)

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            # Parse Claude's response
            analysis_text = response.content[0].text
            analysis = self._parse_analysis_response(analysis_text)

            return analysis

        except Exception as e:
            print(f"Error calling Claude API: {e}")
            return {
                "score": 0.5,
                "reasoning": f"Error analyzing job: {str(e)}",
                "should_apply": False,
                "confidence": "low"
            }

    def _build_job_analysis_prompt(self, job: Dict, profile: Dict) -> str:
        """Build prompt for job analysis"""
        return f"""Analyze this job opportunity for a candidate and provide a detailed assessment.

**Candidate Profile:**
Name: {profile.get('personal', {}).get('name', 'Unknown')}
Location: {profile.get('personal', {}).get('location', 'Unknown')}
Current Title: {profile.get('professional', {}).get('current_title', 'Unknown')}
Years Experience: {profile.get('professional', {}).get('years_experience', 'Unknown')}
Has MBA: {profile.get('professional', {}).get('has_mba', False)}

Skills:
{self._format_skills(profile.get('skills', {}))}

Target Roles: {', '.join(profile.get('preferences', {}).get('target_roles', []))}
Preferred Locations: {', '.join(profile.get('preferences', {}).get('locations', []))}
Salary Range: £{profile.get('preferences', {}).get('salary', {}).get('min', 0):,} - £{profile.get('preferences', {}).get('salary', {}).get('max', 0):,}
Preferred Work Modes: {', '.join(profile.get('preferences', {}).get('work_modes', []))}

**Job Opportunity:**
Title: {job.get('title', 'Unknown')}
Company: {job.get('company', 'Unknown')}
Location: {job.get('location', 'Unknown')}
Work Mode: {job.get('work_mode', 'Unknown')}
Job Type: {job.get('job_type', 'Unknown')}
Salary: {self._format_salary(job)}
Platform: {job.get('platform', 'Unknown')}

Description:
{job.get('description', 'No description available')[:2000]}

**Task:**
Analyze this job match and provide your assessment in the following JSON format:

{{
  "match_score": <float 0.0 to 1.0>,
  "reasoning": "<detailed explanation of why this job is or isn't a good match>",
  "strengths": ["<strength 1>", "<strength 2>", ...],
  "concerns": ["<concern 1>", "<concern 2>", ...],
  "should_apply": <true/false>,
  "confidence": "<high/medium/low>",
  "key_skills_match": ["<skill 1>", "<skill 2>", ...],
  "missing_skills": ["<skill 1>", "<skill 2>", ...],
  "recommendations": "<specific advice for the application or why to skip>"
}}

Consider:
1. How well the role aligns with candidate's experience and skills
2. Career progression potential
3. Location and work mode preferences
4. Salary alignment
5. Company reputation and role responsibilities
6. Growth opportunities

Provide ONLY the JSON response, no other text."""

    def _format_skills(self, skills: Dict) -> str:
        """Format skills dictionary for prompt"""
        if isinstance(skills, list):
            return ', '.join(skills)

        formatted = []
        for category, skill_list in skills.items():
            formatted.append(f"{category.title()}: {', '.join(skill_list)}")
        return '\n'.join(formatted)

    def _format_salary(self, job: Dict) -> str:
        """Format salary information"""
        salary_min = job.get('salary_min')
        salary_max = job.get('salary_max')

        if salary_min and salary_max:
            return f"£{salary_min:,} - £{salary_max:,}"
        elif salary_min:
            return f"£{salary_min:,}+"
        elif salary_max:
            return f"Up to £{salary_max:,}"
        else:
            return "Not specified"

    def _parse_analysis_response(self, response_text: str) -> Dict:
        """Parse Claude's JSON response"""
        try:
            # Extract JSON from response (handle markdown code blocks)
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                json_text = response_text[start:end].strip()
            else:
                json_text = response_text.strip()

            analysis = json.loads(json_text)
            return analysis

        except json.JSONDecodeError:
            # Fallback if JSON parsing fails
            return {
                "match_score": 0.5,
                "reasoning": response_text[:500],
                "should_apply": False,
                "confidence": "low",
                "strengths": [],
                "concerns": ["Could not parse Claude's response"],
                "key_skills_match": [],
                "missing_skills": [],
                "recommendations": "Manual review needed"
            }

    def generate_cover_letter(self, job: Dict, profile: Dict, analysis: Dict) -> str:
        """
        Generate a tailored cover letter using Claude

        Args:
            job: Job dictionary
            profile: User profile
            analysis: Job match analysis from analyze_job_match

        Returns:
            Cover letter text
        """
        prompt = f"""Generate a compelling cover letter for this job application.

**Candidate:**
{profile.get('personal', {}).get('name', 'Candidate')}
{profile.get('professional', {}).get('current_title', '')}
{profile.get('professional', {}).get('years_experience', '')} years of experience

**Job:**
{job.get('title', '')} at {job.get('company', '')}

**Key Skills Match:**
{', '.join(analysis.get('key_skills_match', []))}

**Job Description:**
{job.get('description', '')[:1500]}

**Requirements:**
1. Professional and engaging tone
2. Highlight relevant experience and skills
3. Show enthusiasm for the role
4. Keep it concise (3-4 paragraphs)
5. Focus on value the candidate brings
6. Reference specific aspects of the job description

Generate ONLY the cover letter text, no additional commentary."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text.strip()

        except Exception as e:
            return f"Error generating cover letter: {str(e)}"

    def should_apply_batch(self, jobs: List[Dict], profile: Dict) -> List[Dict]:
        """
        Analyze multiple jobs in batch using Claude

        Args:
            jobs: List of job dictionaries
            profile: User profile

        Returns:
            List of jobs with Claude's analysis added
        """
        analyzed_jobs = []

        for job in jobs:
            analysis = self.analyze_job_match(job, profile)

            # Add Claude's analysis to the job
            job['claude_analysis'] = analysis
            job['claude_score'] = analysis.get('match_score', 0.5)
            job['claude_recommendation'] = analysis.get('should_apply', False)

            analyzed_jobs.append(job)

        # Sort by Claude's score
        analyzed_jobs.sort(key=lambda j: j.get('claude_score', 0), reverse=True)

        return analyzed_jobs

    def explain_rejection(self, job: Dict, profile: Dict) -> str:
        """
        Generate explanation for why a job was rejected

        Args:
            job: Job dictionary
            profile: User profile

        Returns:
            Explanation text
        """
        prompt = f"""Briefly explain why this job is NOT a good match for the candidate.

**Job:** {job.get('title', '')} at {job.get('company', '')}
**Candidate:** {profile.get('professional', {}).get('current_title', '')} with {profile.get('professional', {}).get('years_experience', '')} years experience

Provide a 1-2 sentence explanation focusing on the main mismatch."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            return response.content[0].text.strip()

        except Exception as e:
            return f"Analysis unavailable: {str(e)}"

    def improve_resume_for_job(self, job: Dict, profile: Dict) -> Dict:
        """
        Suggest resume improvements for a specific job

        Args:
            job: Job dictionary
            profile: User profile

        Returns:
            Dictionary with improvement suggestions
        """
        prompt = f"""Analyze how to tailor the candidate's resume for this specific job.

**Job:** {job.get('title', '')} at {job.get('company', '')}
**Job Description:** {job.get('description', '')[:1500]}

**Candidate Skills:** {self._format_skills(profile.get('skills', {}))}

Provide suggestions in JSON format:
{{
  "keywords_to_add": ["<keyword 1>", "<keyword 2>", ...],
  "skills_to_emphasize": ["<skill 1>", "<skill 2>", ...],
  "experience_to_highlight": ["<experience 1>", "<experience 2>", ...],
  "suggested_summary": "<brief professional summary tailored to this role>"
}}

Provide ONLY the JSON response."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text
            return self._parse_analysis_response(response_text)

        except Exception as e:
            return {
                "keywords_to_add": [],
                "skills_to_emphasize": [],
                "experience_to_highlight": [],
                "suggested_summary": f"Error: {str(e)}"
            }
