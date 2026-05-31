import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup


BASE_DIR = Path(__file__).resolve().parent.parent
API_KEYS_FILE = BASE_DIR / "Note" / "api_keys.txt"

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }


def load_api_keys():
    keys = {
        "adzuna_app_id": os.getenv("ADZUNA_APP_ID", ""),
        "adzuna_api_key": os.getenv("ADZUNA_API_KEY", ""),
        "jooble_api_key": os.getenv("JOOBLE_API_KEY", ""),
        "serpapi_key": os.getenv("SERPAPI_KEY", ""),
    }

    if not API_KEYS_FILE.exists():
        return keys

    for line in API_KEYS_FILE.read_text(encoding="utf-8").splitlines():
        if ":" not in line:
            continue

        label, value = line.split(":", 1)
        label = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
        value = value.strip()

        if not value:
            continue
        if "adzuna" in label and "application" in label:
            keys["adzuna_app_id"] = value
        elif "adzuna" in label and "key" in label:
            keys["adzuna_api_key"] = value
        elif "jooble" in label and "key" in label:
            keys["jooble_api_key"] = value
        elif "serpapi" in label and "key" in label:
            keys["serpapi_key"] = value

    return keys


def normalize_job(title, company, location, link, description=""):
    if not title or not company or not link:
        return None

    return {
        "title": str(title).strip()[:200],
        "company": str(company).strip()[:200],
        "location": str(location or "Remote").strip()[:200],
        "link": str(link).strip()[:500],
        "description": str(description or "").strip(),
    }


def fetch_adzuna_jobs(query, location="Remote", limit=10):
    jobs = []
    keys = load_api_keys()

    if not keys["adzuna_app_id"] or not keys["adzuna_api_key"]:
        return jobs

    try:
        country = os.getenv("ADZUNA_COUNTRY", "in")
        url = f"https://api.adzuna.com/v1/api/jobs/{country}/search/1"
        params = {
            "app_id": keys["adzuna_app_id"],
            "app_key": keys["adzuna_api_key"],
            "what": query,
            "where": location,
            "results_per_page": limit,
            "sort_by": "date",
            "content-type": "application/json",
        }
        response = requests.get(url, params=params, timeout=12)
        response.raise_for_status()

        for item in response.json().get("results", []):
            company = item.get("company", {}).get("display_name", "Unknown Company")
            job_location = item.get("location", {}).get("display_name", location)
            job = normalize_job(
                item.get("title"),
                company,
                job_location,
                item.get("redirect_url"),
                item.get("description", ""),
            )
            if job:
                jobs.append(job)
    except Exception as e:
        print(f"Error fetching from Adzuna API: {e}")

    return jobs


def fetch_jooble_jobs(query, location="Remote", limit=10):
    jobs = []
    keys = load_api_keys()

    if not keys["jooble_api_key"]:
        return jobs

    try:
        url = f"https://jooble.org/api/{keys['jooble_api_key']}"
        payload = {
            "keywords": query,
            "location": location,
            "page": 1,
        }
        response = requests.post(url, json=payload, timeout=12)
        response.raise_for_status()

        for item in response.json().get("jobs", [])[:limit]:
            job = normalize_job(
                item.get("title"),
                item.get("company", "Unknown Company"),
                item.get("location", location),
                item.get("link"),
                item.get("snippet", ""),
            )
            if job:
                jobs.append(job)
    except Exception as e:
        print(f"Error fetching from Jooble API: {e}")

    return jobs


def fetch_serpapi_jobs(query, location="Remote", limit=10):
    jobs = []
    keys = load_api_keys()

    if not keys["serpapi_key"]:
        return jobs

    try:
        params = {
            "engine": "google_jobs",
            "q": f"{query} {location}".strip(),
            "hl": "en",
            "api_key": keys["serpapi_key"],
        }
        response = requests.get("https://serpapi.com/search.json", params=params, timeout=12)
        response.raise_for_status()

        for item in response.json().get("jobs_results", [])[:limit]:
            apply_options = item.get("apply_options") or []
            link = item.get("share_link")
            if apply_options:
                link = apply_options[0].get("link") or link

            job = normalize_job(
                item.get("title"),
                item.get("company_name", "Unknown Company"),
                item.get("location", location),
                link,
                item.get("description", ""),
            )
            if job:
                jobs.append(job)
    except Exception as e:
        print(f"Error fetching from SerpAPI: {e}")

    return jobs

def scrape_indeed(query, location=''):
    jobs = []
    try:
        url = f"https://www.indeed.com/jobs?q={query.replace(' ', '+')}&l={location.replace(' ', '+')}"
        response = requests.get(url, headers=get_headers(), timeout=10)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Indeed structure changes frequently, this is a best-effort approach
            job_cards = soup.find_all('div', class_=re.compile(r'job_seen_beacon|jobsearch-SerpJobCard'))
            
            for card in job_cards[:5]:
                title_elem = card.find('h2', class_=re.compile(r'jobTitle'))
                company_elem = card.find('span', class_='companyName') or card.find('span', {'data-testid': 'company-name'})
                location_elem = card.find('div', class_='companyLocation') or card.find('div', {'data-testid': 'text-location'})
                link_elem = card.find('a')

                if title_elem and link_elem:
                    title = title_elem.text.strip()
                    company = company_elem.text.strip() if company_elem else "Unknown Company"
                    loc = location_elem.text.strip() if location_elem else location
                    link = "https://www.indeed.com" + link_elem.get('href', '')
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': loc,
                        'link': link
                    })
    except Exception as e:
        print(f"Error scraping Indeed: {e}")
    
    return jobs

def scrape_remotive(query):
    # Public JSON API, very reliable
    jobs = []
    try:
        url = f"https://remotive.com/api/remote-jobs?search={query}&limit=10"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            for job in data.get('jobs', [])[:5]:
                jobs.append({
                    'title': job.get('title'),
                    'company': job.get('company_name'),
                    'location': job.get('candidate_required_location', 'Remote'),
                    'link': job.get('url')
                })
    except Exception as e:
        print(f"Error fetching from Remotive API: {e}")
    return jobs

def scrape_jobs(query, location='Remote'):
    all_jobs = []

    # API-backed live job sources. Keys can come from environment variables or Note/api_keys.txt.
    all_jobs.extend(fetch_adzuna_jobs(query, location))
    all_jobs.extend(fetch_jooble_jobs(query, location))
    all_jobs.extend(fetch_serpapi_jobs(query, location))

    # Public/HTML sources as extra live results.
    all_jobs.extend(scrape_remotive(query))
    all_jobs.extend(scrape_indeed(query, location))
    
    # Filter out duplicates by title and company
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        identifier = f"{job['title']}_{job['company']}_{job.get('link', '')}"
        if identifier not in seen:
            seen.add(identifier)
            unique_jobs.append(job)

    return unique_jobs
