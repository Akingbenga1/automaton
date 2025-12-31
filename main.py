#!/usr/bin/env python3
"""
MCP-Based Automated Job Application System with Claude AI
Main entry point
"""

import os
import sys
import argparse
import yaml
import logging
import random
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich.panel import Panel

from src.mcp_client import MCPClient
from src.job_searcher import JobSearcher
from src.job_filter import JobFilter
from src.applicator import JobApplicator
from src.database import ApplicationDatabase
from src.claude_agent import ClaudeAgent
from src.email_sender import EmailSender


console = Console()


def setup_logging():
    """Configure logging to write to app.log file in root directory"""
    # Ensure log file is in root directory (current working directory)
    log_file = os.path.join(os.getcwd(), "app.log")
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create file handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    # Clear existing handlers to avoid duplicates
    root_logger.handlers = []
    root_logger.addHandler(file_handler)
    
    # Get logger for this module
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized. Log file: {log_file}")
    
    return logger


def apply_randomization(args: argparse.Namespace) -> argparse.Namespace:
    """
    Apply randomization to arguments based on randomization flags.
    Explicit argument values take precedence over randomization.
    
    Args:
        args: Parsed arguments namespace
        
    Returns:
        Modified arguments namespace with randomized values applied
    """
    logger = logging.getLogger(__name__)
    available_platforms = ["linkedin", "indeed", "career_sites", "reed", "totaljobs"]
    
    # Check which arguments were explicitly provided by checking sys.argv
    argv_str = ' '.join(sys.argv)
    
    # If --randomize is set, enable all randomization flags
    if args.randomize:
        logger.info("Randomize flag enabled - randomizing all configurable arguments")
        args.randomize_platforms = True
        args.randomize_max_results = True
        args.randomize_max_days = True
        args.randomize_easy_apply = True
    
    # Randomize platforms (only if not explicitly provided)
    if args.randomize_platforms:
        if '--platforms' not in argv_str:
            num_platforms = random.randint(1, min(3, len(available_platforms)))
            selected_platforms = random.sample(available_platforms, num_platforms)
            args.platforms = ",".join(selected_platforms)
            logger.info(f"Randomized platforms: {args.platforms}")
        else:
            logger.info(f"Platforms explicitly set, skipping randomization: {args.platforms}")
    
    # Randomize max-results (only if not explicitly provided)
    if args.randomize_max_results:
        if '--max-results' not in argv_str:
            args.max_results = random.randint(10, 100)
            logger.info(f"Randomized max-results: {args.max_results}")
        else:
            logger.info(f"Max-results explicitly set, skipping randomization: {args.max_results}")
    
    # Randomize max-days (only if not explicitly provided)
    if args.randomize_max_days:
        if '--max-days' not in argv_str:
            args.max_days = random.randint(1, 30)
            logger.info(f"Randomized max-days: {args.max_days}")
        else:
            logger.info(f"Max-days explicitly set, skipping randomization: {args.max_days}")
    
    # Randomize easy-apply-only (always randomize if flag is set, user can't easily override)
    if args.randomize_easy_apply:
        args.easy_apply_only = random.choice([True, False])
        logger.info(f"Randomized easy-apply-only: {args.easy_apply_only}")
    
    return args


def load_profile(config_path: str = "config/profile.yaml") -> dict:
    """Load user profile configuration"""
    logger = logging.getLogger(__name__)
    logger.info(f"Loading profile from: {config_path}")
    try:
        with open(config_path, 'r') as f:
            profile = yaml.safe_load(f)
        logger.info("Profile loaded successfully")
        return profile
    except Exception as e:
        logger.error(f"Failed to load profile: {e}")
        raise


def show_statistics(db: ApplicationDatabase):
    """Display application statistics"""
    stats = db.get_statistics()

    console.print("\n[bold cyan]Application Statistics[/bold cyan]")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Total Applications", str(stats["total"]))
    table.add_row("Average Match Score", f"{stats['average_match_score']:.2%}")

    console.print(table)

    # By platform
    if stats["by_platform"]:
        console.print("\n[bold]By Platform:[/bold]")
        for platform, count in stats["by_platform"].items():
            console.print(f"  {platform}: {count}")

    # By status
    if stats["by_status"]:
        console.print("\n[bold]By Status:[/bold]")
        for status, count in stats["by_status"].items():
            console.print(f"  {status}: {count}")


def show_recent_applications(db: ApplicationDatabase, limit: int = 20):
    """Display recent applications"""
    apps = db.get_recent_applications(limit)

    if not apps:
        console.print("\n[yellow]No applications found[/yellow]")
        return

    console.print(f"\n[bold cyan]Recent Applications (last {len(apps)})[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Date", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Company", style="yellow")
    table.add_column("Platform", style="blue")
    table.add_column("Match", style="magenta")

    for app in apps:
        date = app["applied_at"][:10]  # Just the date part
        match = f"{app['match_score']:.1%}" if app['match_score'] else "N/A"

        table.add_row(
            date,
            app["title"][:40],
            app["company"][:30],
            app["platform"],
            match
        )

    console.print(table)


def show_claude_analysis(job: Dict, analysis: Dict):
    """Display Claude's detailed analysis for a job"""
    console.print("\n" + "="*80)
    console.print(Panel(
        f"[bold]{job['title']}[/bold] at [bold]{job['company']}[/bold]",
        style="cyan"
    ))

    console.print(f"\n[bold]Claude Match Score:[/bold] [{'green' if analysis['match_score'] > 0.7 else 'yellow'}]{analysis['match_score']:.1%}[/]")
    console.print(f"[bold]Recommendation:[/bold] {'✓ APPLY' if analysis['should_apply'] else '✗ SKIP'}")
    console.print(f"[bold]Confidence:[/bold] {analysis['confidence'].upper()}")

    console.print(f"\n[bold]Reasoning:[/bold]")
    console.print(analysis['reasoning'])

    if analysis.get('strengths'):
        console.print(f"\n[bold green]Strengths:[/bold green]")
        for strength in analysis['strengths']:
            console.print(f"  ✓ {strength}")

    if analysis.get('concerns'):
        console.print(f"\n[bold yellow]Concerns:[/bold yellow]")
        for concern in analysis['concerns']:
            console.print(f"  ⚠ {concern}")

    if analysis.get('key_skills_match'):
        console.print(f"\n[bold]Matching Skills:[/bold] {', '.join(analysis['key_skills_match'][:5])}")

    if analysis.get('missing_skills'):
        console.print(f"[bold]Missing Skills:[/bold] {', '.join(analysis['missing_skills'][:5])}")

    console.print("="*80 + "\n")


def main():
    """Main application entry point"""
    # Setup logging first
    logger = setup_logging()
    logger.info("="*80)
    logger.info("Job Search Application Started")
    logger.info(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    parser = argparse.ArgumentParser(
        description="Job Search Tool - Search and display jobs from LinkedIn, Indeed, and other platforms"
    )

    parser.add_argument(
        "--platforms",
        type=str,
        help="Comma-separated list of platforms (linkedin,indeed,career_sites)"
    )

    parser.add_argument(
        "--easy-apply-only",
        action="store_true",
        default=True,
        help="Filter for Easy Apply jobs only (default: True for LinkedIn)"
    )

    parser.add_argument(
        "--max-results",
        type=int,
        default=50,
        help="Maximum number of jobs to display (default: 50)"
    )

    parser.add_argument(
        "--max-days",
        type=int,
        default=14,
        help="Maximum days since job was posted (default: 14 days)"
    )

    parser.add_argument(
        "--config",
        type=str,
        default="config/profile.yaml",
        help="Path to profile config file"
    )

    # Randomization arguments
    parser.add_argument(
        "--randomize",
        action="store_true",
        help="Randomize all configurable arguments (platforms, max-results, max-days, easy-apply)"
    )

    parser.add_argument(
        "--randomize-platforms",
        action="store_true",
        help="Randomly select platforms from available options"
    )

    parser.add_argument(
        "--randomize-max-results",
        action="store_true",
        help="Randomly select max-results between 10 and 100"
    )

    parser.add_argument(
        "--randomize-max-days",
        action="store_true",
        help="Randomly select max-days between 1 and 30"
    )

    parser.add_argument(
        "--randomize-easy-apply",
        action="store_true",
        help="Randomly set easy-apply-only to True or False"
    )

    args = parser.parse_args()
    
    # Apply randomization logic (must be done before using args)
    args = apply_randomization(args)
    
    logger.info(f"Command line arguments: platforms={args.platforms}, max_results={args.max_results}, max_days={args.max_days}, easy_apply_only={args.easy_apply_only}")

    # Load environment variables
    logger.info("Loading environment variables")
    load_dotenv()

    # Load profile
    console.print("[bold cyan]Loading profile...[/bold cyan]")
    profile = load_profile(args.config)

    # Initialize components
    console.print("[bold cyan]Initializing MCP clients...[/bold cyan]")
    logger.info("Initializing MCP client")
    mcp_client = MCPClient()

    logger.info("Initializing JobSearcher")
    searcher = JobSearcher(mcp_client, profile)

    # Determine platforms
    platforms = None
    if args.platforms:
        platforms = [p.strip() for p in args.platforms.split(",")]
        logger.info(f"Platforms specified: {', '.join(platforms)}")
    else:
        logger.info("No platforms specified, will search all available platforms")

    # Search for jobs
    console.print(f"\n[bold green]Searching for jobs via Apify MCP servers...[/bold green]")
    if platforms:
        console.print(f"Platforms: {', '.join(platforms)}")

    if args.easy_apply_only:
        console.print("[cyan]Filtering for Easy Apply jobs (LinkedIn)[/cyan]")
        logger.info("Easy Apply filter enabled")

    console.print(f"[cyan]Filtering for jobs posted within last {args.max_days} days[/cyan]")
    logger.info(f"Starting job search with limit_per_platform={args.max_results}, max_days={args.max_days}")

    jobs = searcher.search_all_platforms(
        platforms=platforms,
        limit_per_platform=args.max_results,
        easy_apply_only=args.easy_apply_only
    )

    logger.info(f"Job search completed. Found {len(jobs)} jobs total")
    console.print(f"Found [bold]{len(jobs)}[/bold] jobs")

    if not jobs:
        logger.warning("No jobs found. Try different search criteria.")
        console.print("[yellow]No jobs found. Try different search criteria.[/yellow]")
        return

    # Filter by date - only show jobs posted within max_days
    from datetime import timedelta

    def is_job_recent(job, max_days):
        """Check if job was posted within max_days"""
        posted_date = job.get("posted_date")
        if not posted_date:
            # If no date, include it (better to show than hide)
            return True

        try:
            # Try to parse various date formats
            # Format 1: ISO format (2025-10-27T00:21:00)
            if isinstance(posted_date, str):
                if 'T' in posted_date:
                    job_date = datetime.fromisoformat(posted_date.replace('Z', '+00:00'))
                # Format 2: Relative format ("1 month ago", "2 days ago")
                elif "ago" in posted_date.lower():
                    # Extract number from string like "1 month ago"
                    import re
                    match = re.search(r'(\d+)\s*(day|week|month|year|hour)', posted_date.lower())
                    if match:
                        num = int(match.group(1))
                        unit = match.group(2)

                        if unit == 'day' or unit == 'days':
                            days_ago = num
                        elif unit == 'week' or unit == 'weeks':
                            days_ago = num * 7
                        elif unit == 'month' or unit == 'months':
                            days_ago = num * 30
                        elif unit == 'year' or unit == 'years':
                            days_ago = num * 365
                        elif unit == 'hour' or unit == 'hours':
                            days_ago = 0  # Same day
                        else:
                            return True

                        return days_ago <= max_days
                    return True
                else:
                    # Try parsing as date string
                    job_date = datetime.strptime(posted_date, "%Y-%m-%d")
            elif isinstance(posted_date, datetime):
                job_date = posted_date
            else:
                return True

            # Calculate days difference
            days_diff = (datetime.now() - job_date).days
            return days_diff <= max_days

        except Exception as e:
            # If parsing fails, include the job
            return True

    logger.info(f"Filtering jobs by date (max_days={args.max_days})")
    filtered_jobs = [job for job in jobs if is_job_recent(job, args.max_days)]

    jobs_filtered_by_date = len(jobs) - len(filtered_jobs)
    logger.info(f"Date filtering complete: {len(filtered_jobs)} jobs remaining after filtering out {jobs_filtered_by_date} older jobs")
    if jobs_filtered_by_date > 0:
        console.print(f"[yellow]Filtered out {jobs_filtered_by_date} jobs older than {args.max_days} days[/yellow]")

    # Show all jobs
    console.print(f"\n[bold cyan]Available Jobs ({len(filtered_jobs)} total):[/bold cyan]\n")

    table = Table(show_header=True, header_style="bold magenta", box=None)
    table.add_column("#", style="white", width=4)
    table.add_column("Title", style="green", no_wrap=False, max_width=40)
    table.add_column("Company", style="yellow", no_wrap=False, max_width=25)
    table.add_column("Location", style="blue", no_wrap=False, max_width=25)
    table.add_column("Posted", style="white", max_width=15)
    table.add_column("Platform", style="magenta", max_width=10)
    table.add_column("Easy Apply", style="white", max_width=10)
    table.add_column("Link", style="cyan", no_wrap=False)

    # Prepare markdown content
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    markdown_lines = [
        f"# Job Search Results",
        f"",
        f"**Run Date:** {current_time}",
        f"**Total Jobs Found:** {len(filtered_jobs)}",
        f"",
        f"---",
        f"",
        f"## Instructions",
        f"",
        f"This tool searches for jobs and displays them for you. To apply to these jobs:",
        f"1. Click on the job link to open it in your browser",
        f"2. Review the full job description",
        f"3. Apply directly through the platform (LinkedIn, Indeed, etc.)",
        f"",
        f"**Note:** This tool does NOT automatically submit applications. All applications must be done manually through the respective platforms.",
        f"",
        f"---",
        f"",
        f"| # | Title | Company | Location | Posted | Platform | Easy Apply | Link |",
        f"|---|-------|---------|----------|--------|----------|------------|------|"
    ]

    for idx, job in enumerate(filtered_jobs[:args.max_results], 1):  # Show jobs up to max_results
        easy_apply = "Yes" if job.get('easy_apply') else "No"
        job_url = job.get("url", "N/A")
        posted_date = job.get("posted_date", "N/A")

        # Create clickable link using Rich markup
        clickable_link = f"[link={job_url}]{job_url}[/link]" if job_url != "N/A" else "N/A"

        if idx <= 20:  # Only show first 20 in console table
            table.add_row(
                str(idx),
                job["title"],
                job["company"],
                job["location"],
                posted_date,
                job["platform"],
                easy_apply,
                clickable_link
            )

        # Add all jobs to markdown
        markdown_lines.append(
            f"| {idx} | {job['title']} | {job['company']} | {job['location']} | {posted_date} | {job['platform']} | {easy_apply} | {job_url} |"
        )

    console.print(table)

    # Calculate how many jobs will be saved
    jobs_to_save = min(len(filtered_jobs), args.max_results)

    if len(filtered_jobs) > 20:
        console.print(f"\n[yellow]Showing first 20 of {jobs_to_save} jobs in console. See results.md for complete list.[/yellow]")

    # Save results to markdown file
    markdown_content = "\n".join(markdown_lines)
    results_file = "results.md"

    logger.info(f"Saving results to {results_file} ({jobs_to_save} jobs)")
    try:
        with open(results_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)
        logger.info(f"Successfully saved {jobs_to_save} jobs to {results_file}")
        console.print(f"\n[green]Results saved to {results_file}[/green]")
        console.print(f"[cyan]Saved {jobs_to_save} jobs to {results_file}. Click links to apply manually.[/cyan]")
    except Exception as e:
        logger.error(f"Failed to save results to {results_file}: {e}")
        console.print(f"[yellow]Warning: Could not save results to {results_file}: {e}[/yellow]")

    # Send email with results
    logger.info("Attempting to send email with results")
    try:
        email_sender = EmailSender()
        email_sent = email_sender.send_results_email(results_file, len(filtered_jobs))
        if email_sent:
            logger.info("Email sent successfully")
            console.print(f"[green]Results emailed to configured address[/green]")
        else:
            logger.info("Email not sent (disabled or not configured)")
    except Exception as e:
        logger.error(f"Error during email sending: {e}")
        # Don't fail the whole process if email fails
        console.print(f"[yellow]Warning: Could not send email: {e}[/yellow]")

    logger.info(f"Job search process completed successfully. Total jobs found: {len(filtered_jobs)}")
    console.print(f"\n[bold yellow]IMPORTANT: This tool only searches and displays jobs.[/bold yellow]")
    console.print(f"[bold yellow]To apply, click the job links above and apply manually through each platform.[/bold yellow]\n")

    console.print(f"\n[bold cyan]Job search complete![/bold cyan]")
    console.print(f"[green]Found {len(filtered_jobs)} jobs matching your criteria.[/green]")
    console.print(f"[cyan]Review the jobs above and click links to apply manually.[/cyan]")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger = logging.getLogger(__name__)
        logger.warning("Application interrupted by user (KeyboardInterrupt)")
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Application failed with error: {e}", exc_info=True)
        console.print(f"\n[bold red]Error: {e}[/bold red]")
        if "--verbose" in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)
