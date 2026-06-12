# 🧠 CareerNeuron-Pro: AI-Powered Smart Career Portal

**Live Deployed Application**: [https://careerneuron-pro.onrender.com](https://careerneuron-pro.onrender.com)

CareerNeuron-Pro is a state-of-the-art, Django-based AI-powered career portal. It seamlessly integrates modern web application architectures with advanced artificial intelligence pipelines, structured relational retrieval, live job feed scrapers, and resilient notification networks to automate resume analysis, optimize ATS scoring, generate personalized career advice, and simulate mock interviews.

---

## 📋 Table of Contents

1. [About CareerNeuron](#-about-careerneuron)
2. [Core Features](#-core-features)
3. [System Architecture](#%EF%B8%8F-system-architecture)
4. [Structured RAG & PostgreSQL Core (No Vector DB Needed)](#%EF%B8%8F-structured-rag--postgresql-core-no-vector-db-needed)
5. [Key Workflows](#-key-workflows)
6. [Database Schema](#-database-schema)
7. [Tech Stack](#-tech-stack)
8. [Installation & Setup](#-installation--setup)
9. [SMTP & Email API Troubleshooting (Render)](#-smtp--email-api-troubleshooting-render)
10. [Configuration Reference](#-configuration-reference)

---

## 💡 About CareerNeuron

**CareerNeuron** acts as a comprehensive, intelligent assistant for career optimization. Unlike basic job boards, CareerNeuron leverages LLMs and dynamic matching scores to build a contextual profile, generate matching recommendations, and prepare candidates:

* **Generative Parsing Pipeline**: Uploaded PDF resumes are processed through standard OCR extraction and an LLM parser (Groq `llama-3.3-70b-versatile` via LangChain) to instantly populate structured profiles, calculate an ATS score, and give dynamic critique tips.
* **Contextual Profile Customization**: Once parsed, users can refine their educational background, prior experiences, custom skills, and URLs on a dynamic dashboard.
* **Semantic & Match Scoring**: A matching algorithm analyses candidates' terms, profiles, and skills against live job descriptions, computing matching scores and producing explanations of compatibility.
* **AI Mock Interviews**: Conducts complete simulated interview rounds for specific roles and companies. The interviewer keeps track of state, evaluates user responses, increases difficulty, and grades the transcript.
* **Resilient Infrastructure**: Protected by PostgreSQL-resilience middleware (catching database errors to trigger auto-migrations), signed-cookie session backends to bypass database bottleneck outages, and outbound mail gateway failovers.

---

## ✨ Core Features

* **Multi-Step OTP Verification**: High-security user onboarding secured by OTP tokens dispatched via SMTP or secure HTTP APIs.
* **Automatic PDF Resumer Extraction**: Fully pulls user profiles, work durations, locations, and descriptions.
* **Conversational AI Career Advisor**: Tailored recommendations answering user-specific career path questions.
* **Custom Cover Letter Generator**: Writes highly tailored cover letters for any target job description.
* **Adaptive AI Mock Interviewer**: Interactive console with feedback and grading upon completion.
* **Smart Job Board Scraper**: Scraping logic for Remotive and Indeed coupled with Adzuna, Jooble, and SerpAPI search APIs.

---

## 🏗️ System Architecture

### High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph Client Layer
        A[User Browser]
    end

    subgraph Application Server [Render / Gunicorn / Django]
        B[Security & Static Middleware]
        C[Session & Auth Handler - Signed Cookies]
        D[portal.views: Controllers]
        E[Database & Relation Middleware]
    end

    subgraph AI & Matching Layer
        F[AIEngine: LangChain & Groq]
        G[Syntactic Scorer & Parser]
    end

    subgraph External Gateways
        H[Brevo / Resend HTTP API]
        I[Gmail SMTP Server]
        J[Web Scraper: BeautifulSoup4]
        K[Adzuna, Jooble, SerpAPI Keys]
    end

    subgraph Relational Database [Structured Storage]
        L[(PostgreSQL - Production)]
        M[(SQLite - Development)]
    end

    A -->|HTTP/HTTPS Request| B
    B --> C
    C --> D
    D --> E
    E -->|Auto-Migrations & Queries| L
    E -->|Auto-Migrations & Queries| M
    D -->|Match & Extraction| G
    D -->|Fast LLM Inference| F
    D -->|Outbound HTTPS Email| H
    D -->|Outbound SMTP Email| I
    D -->|Aggregated Job Feeds| J
    D -->|API Search Integrations| K
```

### Component Details
* **Security & Resilience**: Utilizes `DatabaseErrorCatchMiddleware` to detect and run pending migrations if a postgres database table is missing during runtime.
* **Signed Cookies Session Store**: Employs cookie-based signed sessions (`signed_cookies`) to eliminate session validation database calls, allowing the app to handle database traffic spikes smoothly.
* **Socket Timeout Guard**: Configured with global 10-second socket timeouts to safeguard Gunicorn server threads against hanging external network integrations.

---

## ⚙️ Structured RAG & PostgreSQL Core (No Vector DB Needed)

Unlike generic LLM applications that rely on chunking text files and computing similarity matrices in a vector database, CareerNeuron-Pro implements a **Structured Relational RAG (Retrieval-Augmented Generation)** architecture powered entirely by PostgreSQL (production) or SQLite (local development).

### 1. Why ChromaDB is Not Actively Used
Although configuration lines and package requirements for ChromaDB (`chromadb`) exist in the codebase for potential future scale, it is **not actively queried** at runtime. 
* **Compute Overhead**: Running vector engines inside free-tier cloud containers (like Render) introduces high memory usage and latency.
* **Lack of Precision**: Traditional vector searches split documents into arbitrary text chunks, which can lose vital context such as job durations, degree levels, or contact details. 
* **Database Efficiency**: Relational schemas guarantee precise retrieval without requiring dedicated semantic embedding lookup clusters.

### 2. How PostgreSQL Powers Structured RAG
Instead of unstructured vector chunks, the user’s resume data is parsed once into normalized relational tables inside PostgreSQL:

```
[Resume PDF] ──► [Groq Parser] ──► [PostgreSQL Schema]
                                         ├── portal_userprofile
                                         ├── portal_education
                                         └── portal_experience
```

When the user asks a career question or starts an interview, the backend performs the following steps:

1. **Retrieval**: Queries the database to retrieve the logged-in user's profile context (`profile.educations.all()`, `profile.experiences.all()`, `profile.skills`).
2. **Augmentation (Prompt Stuffing)**: Formats this relational data into an clean candidate context block using `build_career_profile_context()`:
   ```python
   # Example Context Generated
   Name: John Doe
   Skills: python, django, rest api
   Education:
   - B.Tech in Computer Science at University (2022 - 2026)
   Experience:
   - Backend Intern at TechCorp: Assisted with database modeling.
   ```
3. **Generation**: Merges the custom query (the user's advice request or interview reply) with the context block, submitting a fully augmented context package to Groq LLM.

### 3. Job Match Scorer (Syntactic Scoring)
In place of cosine distance similarity calculations, the portal matches scraped listings using a deterministic scoring algorithm in [portal/profile_utils.py](file:///c:/Users/siddh\OneDrive\Documents\Projects\Job Listing Scraper\portal\profile_utils.py):
* Pulls up to 20 unique key terms from the candidate profile.
* Scans the job title, description, and location of scraper results.
* Scores matches based on word frequency, key matching intersections, and string ratio metrics using `difflib.SequenceMatcher`.

---

## 🔄 Key Workflows

### 1. User Onboarding & Email OTP Verification

```mermaid
sequenceDiagram
    actor User as User Browser
    participant App as Django App
    participant DB as PostgreSQL
    participant Email as Brevo/Resend API (HTTP)

    User->>App: Submits Registration Form (POST /register/)
    App->>DB: Checks if email exists
    Note over App: Generates 6-digit OTP code & expires_at
    App->>DB: Stores OTPToken
    App->>Email: Sends OTP over HTTP/HTTPS (Port 443)
    Note over Email: Bypasses Render Port 587 blocks
    Email-->>App: Delivery Confirmation
    App-->>User: Redirects to /verify-otp/ with Success Alert
```

### 2. Resume Ingestion & Parsing Flow

```mermaid
sequenceDiagram
    actor User as User Browser
    participant App as Django App
    participant Parser as PyPDF2 Parser
    participant LLM as LangChain & Groq LLM
    participant DB as PostgreSQL

    User->>App: Uploads Resume (.pdf)
    App->>Parser: Extracts Raw PDF Text
    Parser-->>App: Returns Raw Text
    App->>LLM: Analyzes resume text and structure
    LLM-->>App: Returns structured JSON (Skills, ATS Score, Summary)
    App->>DB: Saves Profile, Educations, and Experiences records
    App-->>User: Renders fully-populated profile builder
```

---

## 📊 Database Schema

```
auth_user (Django Core)
 └── portal_userprofile (One-to-One Relation)
      ├── portal_education (Foreign Key)
      ├── portal_experience (Foreign Key)
      ├── portal_interview (Foreign Key)
      └── portal_otptoken (Email verification logs)

portal_job (Scraped job listings feed cache)
```

---

## 🛠️ Tech Stack

* **Backend**: Django 4.2+ (Python 3.11)
* **Application Servers**: Gunicorn + WhiteNoise
* **Database**: PostgreSQL (Production) / SQLite (Development)
* **AI Framework**: LangChain + Groq API (`llama-3.3-70b-versatile`)
* **Scraper**: BeautifulSoup4 + Requests + Adzuna, Jooble, SerpAPI keys
* **Mailing**: Brevo API & Resend API (HTTP Client) / Standard SMTP

---

## 📦 Installation & Setup

### Prerequisites
* Python 3.11+
* Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/siddheshasati/CareerNeuron-Pro.git
   cd CareerNeuron-Pro
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize environment configurations**
   ```bash
   cp .env.example .env
   # Edit .env and supply your GROQ_API_KEY
   ```

5. **Run Migrations & Launch Server**
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```
   Open `http://127.0.0.1:8000` to access the portal locally.

---

## 🚀 SMTP & Email API Troubleshooting (Render)

Render **completely blocks** outgoing TCP traffic on standard SMTP ports (`25`, `465`, `587`, `2525`) to prevent spam. Consequently, standard Django `send_mail` via SMTP will fail with `[Errno 101] Network is unreachable`.

To address this, CareerNeuron-Pro includes native HTTP API mail drivers. Outbound HTTP/HTTPS requests (ports `80`/`443`) are not blocked.

### Recommended Fix: Use Brevo (Sendinblue) HTTP API
Brevo allows you to verify a single sender address (like `youraddress@gmail.com`) and send emails to **any** recipient for free (up to 300/day) without domain ownership verification.

1. Create a free account at [brevo.com](https://www.brevo.com/).
2. Navigate to **SMTP & API** -> **API Keys** and generate a new key.
3. Add the following environment variables to your **Render Web Service (Environment tab)**:
   * `BREVO_API_KEY` = `your_brevo_api_key`
   * `BREVO_SENDER_EMAIL` = `your_signup_email@gmail.com`

*The system will automatically switch to the HTTP API, bypass the firewall blocks, and successfully send OTPs to your users.*

---

## ⚙️ Configuration Reference

### Key Environment Variables

| Variable | Description | Example / Default |
| :--- | :--- | :--- |
| `DJANGO_DEBUG` | Django debug toggle | `True` (dev) / `False` (prod) |
| `DATABASE_URL` | PostgreSQL connection string | `postgres://user:pass@host:port/db` |
| `GROQ_API_KEY` | Groq API Key | `gsk_...` |
| `BREVO_API_KEY` | Brevo SMTP API Key | `xkeysib-...` |
| `BREVO_SENDER_EMAIL` | Verified Sender Email | `name@gmail.com` |
| `RESEND_API_KEY` | Resend API Key | `re_...` |
| `ADZUNA_APP_ID` | Adzuna Scraper App ID | `adzuna_id` |
| `ADZUNA_API_KEY` | Adzuna Scraper Key | `adzuna_key` |
| `JOOBLE_API_KEY` | Jooble Scraper Key | `jooble_key` |
| `SERPAPI_KEY` | SerpAPI Scraper Key | `serp_key` |

---

**Built with ❤️ by the CareerNeuron Team**
