# Job Search Tool

A Python-based job search tool that aggregates job listings from multiple platforms (LinkedIn, Indeed, etc.) using Apify scrapers.

## Overview

✅ **Searches for jobs** across multiple UK & global platforms:
   - **LinkedIn** - Global platform with UK Easy Apply jobs
   - **Reed.co.uk** - Major UK job site
   - **Totaljobs** - UK's largest hiring platform (280k+ jobs, 20M monthly visits)
   - **Indeed** - Global platform with UK support
   - **Career Sites** - 125k+ companies across 37 ATS platforms

✅ **Displays job listings** in an easy-to-read table format
✅ **Filters for Easy Apply jobs** (LinkedIn)
✅ **Saves results** to a markdown file (`results.md`) with clickable links
✅ **Customizable search** based on your profile preferences

## What This Tool Does NOT Do

❌ **Does NOT automatically submit applications**
❌ **Does NOT interact with job platforms on your behalf**
❌ **Does NOT require your login credentials**

**You must apply to jobs manually** by clicking the job links and applying through each platform.

## Requirements

- Python 3.8+
- Apify API Token (free tier available at https://apify.com)
- Required Python packages (see `requirements.txt`)

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and add your Apify API token:
   ```
   APIFY_API_TOKEN=your_token_here
   ```
4. Update `config/profile.yaml` with your job search preferences

## Configuration

### Environment Variables (.env)

```env
# Apify API Token (get from https://apify.com)
APIFY_API_TOKEN=your_token_here
```

### Profile Configuration (config/profile.yaml)

```yaml
personal:
  name: "Your Name"
  email: "your.email@example.com"
  phone: "+44 XXXX XXXXXX"
  location: "London, UK"

preferences:
  job_titles:
    - "Senior Software Engineer"
    - "Tech Lead"
    - "Engineering Manager"

  locations:
    - "London, UK"
    - "Remote"

  salary_min: 70000
  job_types:
    - "full-time"
    - "contract"

  work_modes:
    - "remote"
    - "hybrid"

skills:
  - "Python"
  - "JavaScript"
  - "AWS"
  - "Docker"
  - "React"

cv_path: "cv/Gbenga Akinbami Base Tech CV.pdf"
```

## Usage

### Basic Search

```bash
python main.py
```

This will search for jobs based on your profile preferences and display up to 50 results.

### Command Line Options

```bash
# Search specific platforms
python main.py --platforms linkedin

# Show more results
python main.py --max-results 100

# Use custom profile config
python main.py --config path/to/profile.yaml
```

### Available Arguments

- `--platforms`: Comma-separated list of platforms (linkedin, indeed, career_sites)
- `--easy-apply-only`: Filter for Easy Apply jobs only (default: True)
- `--max-results`: Maximum number of jobs to display (default: 50)
- `--config`: Path to profile config file (default: config/profile.yaml)

## Output

The tool provides two outputs:

1. **Console Table**: Displays first 20 jobs in your terminal with clickable links
2. **results.md**: Markdown file with all found jobs (up to max-results)

Each job listing includes:
- Job title
- Company name
- Location
- Date posted
- Platform (LinkedIn, Indeed, etc.)
- Easy Apply status
- Direct link to job posting

## How to Apply to Jobs

1. Run the search tool
2. Review the jobs in the console or open `results.md`
3. Click on job links that interest you
4. Apply manually through the job platform

## Limitations

- Search results depend on Apify scraper availability and rate limits
- Free Apify tier has monthly credit limits
- Some scrapers may require paid Apify subscriptions
- Job data freshness depends on the Apify actors

## Troubleshooting

### SSL/Connection Errors

If you get SSL or connection errors:
- Check your internet connection
- Try disabling VPN if using one
- Verify your firewall isn't blocking Python
- The tool will automatically retry up to 3 times

### No Jobs Found

If no jobs are found:
- Adjust your profile.yaml preferences (try broader search terms)
- Check that your Apify API token is valid
- Verify the Apify actors are still available and enabled

## License

MIT License - See LICENSE file for details

## Disclaimer

This tool is for personal job search use only. Users are responsible for:
- Complying with platform terms of service
- Respecting rate limits
- Using scraped data responsibly
- Applying to jobs manually through official channels

This tool does not guarantee job search success or the accuracy of job listings.
