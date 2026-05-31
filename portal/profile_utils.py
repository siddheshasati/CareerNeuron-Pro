import json
import re
from difflib import SequenceMatcher

import PyPDF2

from .models import Education, Experience


COMMON_SKILLS = [
    "python", "django", "flask", "fastapi", "java", "javascript", "typescript",
    "react", "node", "sql", "mysql", "postgresql", "mongodb", "html", "css",
    "machine learning", "deep learning", "nlp", "computer vision", "pandas",
    "numpy", "scikit-learn", "tensorflow", "pytorch", "aws", "azure", "git",
    "docker", "kubernetes", "rest api", "data analysis", "power bi", "excel",
]


def extract_resume_text(path):
    reader = PyPDF2.PdfReader(path)
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def split_full_name(name):
    parts = [part.strip() for part in re.split(r"\s+", name or "") if part.strip()]
    if not parts:
        return "", ""
    return parts[0], " ".join(parts[1:])


def find_first(pattern, text, flags=re.IGNORECASE):
    match = re.search(pattern, text, flags)
    return match.group(0).strip() if match else ""


def parse_resume_fallback(text):
    email = find_first(r"[\w.\-+]+@[\w.\-]+\.\w+", text)
    mobile = find_first(r"(?:\+?\d[\d\s().-]{8,}\d)", text)
    linkedin = find_first(r"https?://(?:www\.)?linkedin\.com/[^\s)]+", text)
    github = find_first(r"https?://(?:www\.)?github\.com/[^\s)]+", text)
    urls = re.findall(r"https?://[^\s)]+", text)
    portfolio = next((url for url in urls if url not in {linkedin, github}), "")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    name = ""
    for line in lines[:8]:
        if "@" not in line and not re.search(r"\d{4,}", line) and len(line.split()) <= 5:
            name = line
            break

    first_name, last_name = split_full_name(name)
    lowered = text.lower()
    skills = [skill for skill in COMMON_SKILLS if skill in lowered]

    return {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "mobile": mobile,
        "location": "",
        "linkedin_url": linkedin,
        "github_url": github,
        "portfolio_url": portfolio,
        "additional_urls": [],
        "skills": skills,
        "education": [],
        "experience": [],
        "projects": [],
        "ats_score": 0,
        "suggestions": [],
    }


def merge_resume_data(ai_data, fallback_data):
    data = fallback_data.copy()
    if isinstance(ai_data, dict):
        for key, value in ai_data.items():
            if value not in ("", None, [], {}):
                data[key] = value
    return data


def as_text(value):
    if isinstance(value, list):
        return ", ".join(str(item).strip() for item in value if str(item).strip())
    return str(value or "").strip()


def first_value(data, *keys):
    for key in keys:
        value = data.get(key)
        if value not in ("", None, [], {}):
            return value
    return ""


def save_parsed_resume(profile, data, registration_email="", registration_mobile=""):
    user = profile.user
    first_name = as_text(first_value(data, "first_name"))
    last_name = as_text(first_value(data, "last_name"))
    email = registration_email or user.email or as_text(first_value(data, "email"))
    mobile = registration_mobile or profile.mobile or as_text(first_value(data, "mobile", "phone"))

    if first_name:
        user.first_name = first_name[:150]
    if last_name:
        user.last_name = last_name[:150]
    if email:
        user.email = email
        user.username = email
    user.save()

    full_name = " ".join(part for part in [user.first_name, user.last_name] if part).strip()
    profile.full_name = full_name or profile.full_name
    profile.mobile = mobile or profile.mobile
    profile.skills = as_text(data.get("skills")) or profile.skills
    profile.city = as_text(first_value(data, "city", "location"))[:100] or profile.city
    profile.linkedin_url = as_text(data.get("linkedin_url"))[:500] or profile.linkedin_url
    profile.github_url = as_text(data.get("github_url"))[:500] or profile.github_url
    profile.portfolio_url = as_text(data.get("portfolio_url"))[:500] or profile.portfolio_url

    additional_urls = data.get("additional_urls") or []
    if additional_urls and isinstance(additional_urls, list):
        first_url = additional_urls[0]
        if isinstance(first_url, dict):
            profile.additional_url_name = as_text(first_url.get("name"))[:100] or profile.additional_url_name
            profile.additional_url = as_text(first_url.get("url"))[:500] or profile.additional_url

    profile.ats_score = data.get("ats_score") or profile.ats_score
    profile.resume_data = json.dumps(data)
    profile.save()

    Education.objects.filter(profile=profile).delete()
    for item in data.get("education", []) or []:
        if not isinstance(item, dict):
            continue
        institution = as_text(first_value(item, "institution", "institute", "institute_name"))[:200]
        degree = as_text(item.get("degree"))[:100]
        if not institution and not degree:
            continue
        Education.objects.create(
            profile=profile,
            institution=institution or "Not specified",
            degree=degree or "Not specified",
            specialization=as_text(first_value(item, "specialization", "stream"))[:150],
            stream=as_text(first_value(item, "stream", "specialization"))[:100],
            location=as_text(first_value(item, "location", "city"))[:200],
            city=as_text(first_value(item, "city", "location"))[:100],
            start_date=as_text(first_value(item, "start_date", "from"))[:20],
            end_date=as_text(first_value(item, "end_date", "to"))[:20],
            currently_pursuing=bool(item.get("currently_pursuing")),
        )

    Experience.objects.filter(profile=profile).delete()
    for item in data.get("experience", []) or []:
        if not isinstance(item, dict):
            continue
        organization = as_text(first_value(item, "organization", "company", "company_name"))[:200]
        role = as_text(first_value(item, "role", "title", "designation"))[:100]
        if not organization and not role:
            continue
        Experience.objects.create(
            profile=profile,
            company=organization or "Not specified",
            organization=organization,
            role=role or "Not specified",
            location=as_text(item.get("location"))[:100],
            ctc=as_text(first_value(item, "ctc", "current_ctc"))[:50],
            current_ctc=as_text(first_value(item, "current_ctc", "ctc"))[:50],
            start_date=as_text(first_value(item, "start_date", "from"))[:20],
            end_date=as_text(first_value(item, "end_date", "to", "duration"))[:20],
            summary=as_text(first_value(item, "summary", "description")),
        )


def profile_match_terms(profile):
    terms = []
    if profile.skills:
        terms.extend([item.strip() for item in profile.skills.split(",") if item.strip()])
    terms.extend(exp.role for exp in profile.experiences.all() if exp.role)
    for exp in profile.experiences.all():
        if exp.summary:
            terms.extend(skill for skill in COMMON_SKILLS if skill in exp.summary.lower())
    terms.extend(edu.degree for edu in profile.educations.all() if edu.degree)
    terms.extend(edu.specialization for edu in profile.educations.all() if edu.specialization)
    unique_terms = []
    seen = set()
    for term in terms:
        cleaned = str(term).strip()
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            unique_terms.append(cleaned)
    return unique_terms[:20]


def score_job_match(profile, job):
    terms = profile_match_terms(profile)
    if not terms:
        return 0, []

    job_text = " ".join([
        job.get("title", ""),
        job.get("company", ""),
        job.get("location", ""),
        job.get("description", ""),
    ]).lower()

    matched = []
    weighted_hits = 0
    important_hits = 0
    for term in terms:
        cleaned = term.lower().strip()
        if not cleaned:
            continue
        weight = 2 if len(cleaned.split()) > 1 else 1
        if cleaned in job_text:
            matched.append(term)
            weighted_hits += weight
            important_hits += 1
        elif SequenceMatcher(None, cleaned, job_text[: max(len(cleaned) * 4, 80)]).ratio() > 0.55:
            matched.append(term)
            weighted_hits += 1

    title_text = job.get("title", "").lower()
    role_boost = 20 if any(term.lower() in title_text for term in terms) else 0
    coverage_score = int((important_hits / max(min(len(terms), 8), 1)) * 80)
    score = min(100, max(coverage_score + role_boost, int(weighted_hits * 12)))
    return score, matched[:8]
