# CareerNeuron-Pro: AI-Powered Career Portal

A Django-based web application that combines AI-powered resume analysis, job matching, and interview preparation to help users advance their careers.

---

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Key Workflows](#key-workflows)
3. [Features](#features)
4. [Tech Stack](#tech-stack)
5. [Installation & Setup](#installation--setup)
6. [Deployment](#deployment)
7. [Database Schema](#database-schema)
8. [Configuration](#configuration)
9. [Contributing](#contributing)

---

## 🏗️ System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT LAYER (Web Browser)                   │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/HTTPS
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                   DJANGO WEB SERVER (Gunicorn)                    │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────┐             │
│  │   URL Router         │  │   View Controllers   │             │
│  │  (career_neuron/urls)│  │  (portal/views.py)   │             │
│  └──────────────────────┘  └──────────────────────┘             │
│           ▲                           ▲                           │
│           └───────────┬───────────────┘                          │
│                       ▼                                           │
│  ┌────────────────────────────────────────┐                     │
│  │      Django ORM & Models               │                     │
│  │   (portal/models.py)                   │                     │
│  │   - UserProfile                        │                     │
│  │   - Education, Experience              │                     │
│  │   - Interview, Job Matches             │                     │
│  └────────────────────────────────────────┘                     │
│           ▲                       ▲                               │
└───────────┼───────────────────────┼───────────────────────────────┘
            │                       │
     Database Connection    Migrations (django.db)
            │                       │
     ┌──────▼───────┐       ┌──────▼───────────────┐
     │  PostgreSQL  │       │  SQLite (fallback)   │
     │  (Production)│       │  (Development)       │
     └──────────────┘       └──────────────────────┘
```

### Component Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                          CareerNeuron-Pro                          │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────┐         ┌──────────────────┐               │
│  │  AI Engine       │         │  User Portal     │               │
│  │ (portal/         │         │ (portal/views.py)│               │
│  │  ai_engine.py)   │         │                  │               │
│  │                  │         │  - Auth (Login,  │               │
│  │ ├─ Resume        │         │    Register)     │               │
│  │ │  Parsing       │         │  - Profile       │               │
│  │ │ (PyPDF2,       │         │    Management    │               │
│  │ │  LangChain)    │         │  - Dashboard     │               │
│  │ │                │         │  - Job Matching  │               │
│  │ ├─ Job Matching  │         │  - Interview     │               │
│  │ │ (LangChain +   │         │  - ATS Advisor   │               │
│  │ │  Groq LLM)     │         │                  │               │
│  │ │                │         └──────────────────┘               │
│  │ ├─ Interview     │                                            │
│  │ │  Simulation    │         ┌──────────────────┐               │
│  │ │                │         │  Web Scraper     │               │
│  │ └─ Career        │         │ (portal/         │               │
│  │    Advisor       │         │  scraper.py)     │               │
│  │    (ChatGPT)     │         │                  │               │
│  └──────────────────┘         │ ├─ Job listings  │               │
│           │                    │   aggregation   │               │
│           ▼                    │ └─ LinkedIn,    │               │
│  ┌──────────────────┐         │   Indeed parsing│               │
│  │  Vector Store    │         └──────────────────┘               │
│  │ (ChromaDB)       │                                            │
│  │                  │         ┌──────────────────┐               │
│  │ ├─ Resume        │         │  Utilities       │               │
│  │ │  embeddings    │         │ (portal/         │               │
│  │ │                │         │  profile_utils) │               │
│  │ └─ Job           │         │                  │               │
│  │    embeddings    │         │ - Email/OTP      │               │
│  └──────────────────┘         │ - File uploads   │               │
│                                └──────────────────┘               │
│                                                                    │
└──────────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

```
User Registration/Login
    │
    ▼
┌─────────────────────┐
│ Authenticate        │
│ (OTP Verification)  │
└────────┬────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Create/Update Profile       │
│ (Education, Experience)     │
└────────┬────────────────────┘
         │
         ▼
┌─────────────────────────────┐
│ Upload Resume               │
└────────┬────────────────────┘
         │
         ├────────────────────────────────┐
         │                                │
         ▼                                ▼
    ┌─────────────┐           ┌──────────────────┐
    │ PDF Parser  │           │ Extract Skills   │
    │ (PyPDF2)    │           │ & Experience     │
    └─────┬───────┘           └────────┬─────────┘
          │                             │
          ▼                             ▼
    ┌──────────────────────────────────────────┐
    │ AI Analysis (LangChain + Groq LLM)       │
    │ - Parse resume content                   │
    │ - Extract structured data                │
    └──────┬───────────────────────────────────┘
           │
           ▼
    ┌──────────────────────────────────────────┐
    │ Generate Embeddings (ChromaDB)           │
    │ - Store resume vectors                   │
    └──────┬───────────────────────────────────┘
           │
           ├──────────────────────────────┐
           │                              │
           ▼                              ▼
    ┌─────────────────┐      ┌──────────────────────┐
    │ Job Scraping    │      │ Job Matching Engine  │
    │ (BeautifulSoup) │      │ (LangChain + Groq)   │
    └────────┬────────┘      └──────────┬───────────┘
             │                          │
             │                          ▼
             │              ┌────────────────────────┐
             │              │ Similarity Scoring     │
             │              │ (Vector Search)        │
             │              └────────────┬───────────┘
             │                           │
             └─────────────┬─────────────┘
                           │
                           ▼
                ┌──────────────────────────┐
                │ Store Job Matches        │
                │ (Database)               │
                └────────┬─────────────────┘
                         │
                         ▼
                ┌──────────────────────────┐
                │ Display Recommendations  │
                │ on Dashboard             │
                └──────────────────────────┘
```

---

## 🔄 Key Workflows

### 1. **User Registration & Authentication Workflow**

```
Start: User visits platform
  │
  ▼
┌──────────────────────┐
│ Choose: Login/        │
│ Register              │
└─────────┬────────────┘
          │
     ┌────┴────┐
     │          │
     ▼          ▼
  Login    Register
     │          │
     │          ▼
     │    ┌─────────────────┐
     │    │ Enter Email &   │
     │    │ Password        │
     │    └────────┬────────┘
     │             │
     │             ▼
     │    ┌─────────────────┐
     │    │ Validate Email  │
     │    │ Format          │
     │    └────────┬────────┘
     │             │
     │             ▼
     │    ┌─────────────────┐
     │    │ Send OTP Email  │
     │    │ (via SMTP)      │
     │    └────────┬────────┘
     │             │
     │             ▼
     │    ┌─────────────────┐
     │    │ User enters OTP │
     │    │ from email      │
     │    └────────┬────────┘
     │             │
     │             ▼
     │    ┌─────────────────┐
     │    │ Verify OTP      │
     │    │ (6-digit code)  │
     │    └────────┬────────┘
     │             │
     └─────┬───────┘
           │
           ▼
    ┌────────────────────┐
    │ Create User Account│
    │ (auth_user table)  │
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────┐
    │ Create UserProfile │
    │ (Initial empty     │
    │  profile)          │
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────┐
    │ Log user in        │
    │ Set session token  │
    └────────┬───────────┘
             │
             ▼
    ┌────────────────────┐
    │ Redirect to        │
    │ Register Step 1    │
    │ (Education form)   │
    └────────────────────┘
```

### 2. **Resume Upload & AI Analysis Workflow**

```
Start: User uploads resume (PDF)
  │
  ▼
┌──────────────────────────────┐
│ Validate file                │
│ - Check format (PDF)         │
│ - Check file size (<10MB)    │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Save file to uploads/        │
│ resumes/ directory           │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Parse PDF (PyPDF2)           │
│ - Extract text content       │
│ - Clean formatting           │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Send to LLM (Groq via        │
│ LangChain)                   │
│ - Structured analysis        │
│ - Extract skills, exp.       │
│ - Calculate ATS score        │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Store results:               │
│ - resume_data (JSON)         │
│ - ats_score (0-100)          │
│ - UserProfile updated        │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Generate embeddings          │
│ (ChromaDB)                   │
│ - Convert resume to vectors  │
│ - Store in vector_store/     │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Trigger job matching         │
│ (background task)            │
└────────┬─────────────────────┘
         │
         ▼
    Result: User sees
    - Resume analysis score
    - ATS score
    - Job recommendations
```

### 3. **Job Matching & Recommendation Workflow**

```
Start: User dashboard loaded
  │
  ▼
┌──────────────────────────────┐
│ Fetch scraper jobs           │
│ (or use stored data)         │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ For each job:                │
│ - Generate job embedding     │
│ - Compare to resume vector   │
│ - Calculate similarity score │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ LangChain semantic search     │
│ - ChromaDB retrieves top K   │
│   matching jobs              │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Sort by match score          │
│ (0.0 - 1.0 similarity)       │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Store JobMatch records       │
│ - Link user to matched jobs  │
│ - Store score & reason       │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Display on dashboard         │
│ - Top 10 recommended jobs    │
│ - Match percentage           │
│ - Why you match              │
└──────────────────────────────┘
```

### 4. **Interview Preparation Workflow**

```
Start: User clicks "Interview Prep"
  │
  ▼
┌──────────────────────────────┐
│ Load interview questions     │
│ or generate from resume      │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Send to LLM (Groq):          │
│ "Generate 5 interview Q&As   │
│ based on this resume"        │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Create Interview record      │
│ - Store questions            │
│ - Store expected answers     │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Display in quiz format       │
│ - Question on screen         │
│ - User provides answer       │
│ - Show model answer          │
└────────┬─────────────────────┘
         │
         ▼
┌──────────────────────────────┐
│ Score responses (if enabled) │
│ - AI evaluates user answer   │
└────────┬─────────────────────┘
         │
         ▼
    Result: User prep for
    real interviews
```

---

## ✨ Features

### User Management
- **Registration & Authentication**: Email-based OTP verification
- **User Profiles**: Educational background, experience, skills
- **Resume Upload**: PDF parsing with AI analysis

### AI-Powered Features
- **Resume Analysis**: Extract skills, experience, ATS score
- **Job Matching**: Vector-based semantic search using ChromaDB
- **Career Advisor**: AI-powered career guidance (ChatGPT)
- **Interview Prep**: Generate and simulate interview questions

### Job Portal
- **Job Scraping**: Aggregate job listings (BeautifulSoup)
- **Smart Matching**: Recommend jobs based on resume similarity
- **Application Tracking**: Track job applications and status

### Admin Panel
- **User Management**: View and manage users
- **Job Management**: Manage job listings
- **System Monitoring**: Logs and diagnostics

---

## 🛠️ Tech Stack

### Backend
- **Django 4.2+**: Web framework
- **Python 3.11**: Runtime
- **PostgreSQL/SQLite**: Database (PostgreSQL recommended for production)
- **Gunicorn**: WSGI server

### AI & NLP
- **LangChain**: LLM orchestration framework
- **Groq API**: Fast LLM inference
- **ChromaDB**: Vector database for embeddings
- **PyPDF2**: PDF parsing
- **BeautifulSoup4**: Web scraping

### Frontend
- **Django Templates**: Server-side rendering
- **Bootstrap/CSS**: Responsive UI
- **JavaScript**: Client-side interactivity

### DevOps & Deployment
- **Render**: Cloud hosting platform
- **WhiteNoise**: Static file serving
- **dj-database-url**: Database configuration
- **psycopg2-binary**: PostgreSQL adapter

---

## 📦 Installation & Setup

### Prerequisites
- Python 3.11
- PostgreSQL 12+ (optional, uses SQLite for development)
- Git

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/siddheshasati/CareerNeuron-Pro.git
   cd CareerNeuron-Pro
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings:
   # DJANGO_SECRET_KEY = your-secret-key
   # GROQ_API_KEY = your-groq-api-key
   # EMAIL_HOST_USER = your-email@gmail.com
   # EMAIL_HOST_PASSWORD = your-app-password
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser (for admin panel)**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Application: http://localhost:8000/
   - Admin Panel: http://localhost:8000/admin/

---

## 🚀 Deployment

### Deploy to Render (Recommended - Free)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Deploy to Render"
   git push origin main
   ```

2. **Connect to Render**
   - Go to https://render.com/
   - Click "New +" → "Web Service"
   - Select your GitHub repository
   - Render auto-detects `render.yaml`

3. **Set environment variables** in Render dashboard:
   - `DJANGO_SECRET_KEY`: Generate with `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
   - `GROQ_API_KEY`: Your Groq API key
   - `EMAIL_HOST_USER`: Your Gmail address
   - `EMAIL_HOST_PASSWORD`: Your Gmail app password

4. **Deploy**
   - Click "Create Web Service"
   - Render provisions PostgreSQL automatically

See [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md) for detailed troubleshooting.

### Deploy to Railway, Heroku, or Others

Refer to deployment-specific branches or the Procfile for Heroku compatibility.

---

## 📊 Database Schema

### Core Tables

```
auth_user
├── id (PK)
├── username
├── email
├── password
└── is_active

portal_userprofile
├── id (PK)
├── user (FK to auth_user)
├── resume_data (JSON)
├── ats_score (0-100)
├── currently_pursuing
└── created_at

portal_education
├── id (PK)
├── user (FK to UserProfile)
├── school
├── degree
├── field
├── start_date
└── end_date

portal_experience
├── id (PK)
├── user (FK to UserProfile)
├── company
├── position
├── description
├── start_date
└── end_date

portal_jobmatch
├── id (PK)
├── user (FK to UserProfile)
├── job_title
├── company
├── match_score
└── reason

portal_interview
├── id (PK)
├── user (FK to UserProfile)
├── questions (JSON)
├── answers (JSON)
└── created_at

portal_otptoken
├── id (PK)
├── user (FK to auth_user)
├── token (6-digit)
├── created_at
└── expires_at
```

---

## ⚙️ Configuration

### Environment Variables

```
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DJANGO_DEBUG=False (production), True (development)
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database (auto-set on Render)
DATABASE_URL=postgresql://user:password@host:port/dbname

# AI & APIs
GROQ_API_KEY=your-groq-api-key
OPENAI_API_KEY=your-openai-api-key (optional for ChatGPT)

# Email (Gmail)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

# Render (auto-set)
RENDER_EXTERNAL_HOSTNAME=your-app.onrender.com
```

### Database Configuration

**Development**: SQLite (default, no setup needed)

**Production**: PostgreSQL (Render-managed or external)
- Automatically configured via `DATABASE_URL`
- Migrations run on every deployment

---

## 👥 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push to branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## 📝 License

This project is open-source. See LICENSE file for details.

---

## 🆘 Support & Troubleshooting

For issues or questions:
1. Check [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md) for deployment issues
2. Review Django logs: `python manage.py runserver` in development
3. Open an issue on GitHub: https://github.com/siddheshasati/CareerNeuron-Pro/issues

---

**Built with ❤️ by CareerNeuron Team**

- **Job search:** `portal/scraper.py` scrapes job listings and saves them in the `Job` model.
- **Storage:** Local SQLite database under `db/` and local media storage under `uploads/`.

### Architecture Diagram

```mermaid
flowchart TD
    A[User Browser] -->|HTTP/HTTPS| B[Django Views]
    B --> C[portal app]
    C --> D[SQLite Database]
    C --> E[File Storage uploads/]
    C --> F[LLM API via GROQ]
    C --> G[Web Templates]
    F --> H[Career Advice & Resume Analysis]
    C --> I[Job Scraping Engine]
    I --> D
```

## Key Workflows

### 1. User onboarding
1. User registers with email and password.
2. User verifies OTP and logs in.
3. User completes profile details and uploads a resume.

### 2. Resume parsing and profile enrichment
1. Uploaded resume is extracted and parsed.
2. AI engine analyzes resume text and returns structured profile data.
3. Parsed information is saved back to the user profile for editing.

### 3. AI career advisor
1. User submits a career question on the advisor page.
2. The AI engine uses profile context and resume data to return personalized guidance.

### 4. Job discovery
1. User enters a search query on the dashboard.
2. The scraper fetches job listings and persists them in the database.
3. Listings are displayed to the user in order.

### 5. Interview practice
1. User starts the interview module.
2. AI-driven interview questions are generated based on the user profile and target role.
3. The system tracks conversation history and provides realistic interview feedback.

## Deployment

This project is configured for deployment on free Python hosting platforms that support Django, including Render or Railway with PostgreSQL.

### Included deployment files
- `Procfile` — runs Gunicorn for production.
- `runtime.txt` — pins Python version.
- `render.yaml` — Render-native config with PostgreSQL database.
- `requirements.txt` — includes deployment dependencies like `gunicorn`, `whitenoise`, `dj-database-url`, and `psycopg2-binary`.
- `career_neuron/settings.py` — configured with WhiteNoise, security headers, and `DATABASE_URL` support.

### Deploy on Render (Recommended)

#### Step 1: Push to GitHub
```bash
git add .
git commit -m "Ready for production"
git push origin main
```

#### Step 2: Connect to Render
1. Go to [render.com](https://render.com/)
2. Connect your GitHub account
3. Select this repository
4. Render will auto-detect `render.yaml` and provision:
   - PostgreSQL database (free tier)
   - Django web service (free tier)

#### Step 3: Set required environment variables
- In Render Dashboard > Environment Variables:
  - `DJANGO_SECRET_KEY` — Generate one: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
  - Other variables are pre-configured in `render.yaml`

#### Step 4: Deploy
- Render will automatically:
  - Install dependencies
  - Collect static files
  - Run migrations
  - Start the web service

---

### Deploy on Railway

#### Step 1: Push to GitHub
```bash
git add .
git commit -m "Ready for production"
git push origin main
```

#### Step 2: Connect to Railway
1. Go to [railway.app](https://railway.app/)
2. Connect your GitHub account and create a new project
3. Add PostgreSQL database service
4. Add Python web service

#### Step 3: Set environment variables
In Railway Dashboard > Environment:
- `DJANGO_SECRET_KEY` (generate one as shown above)
- `DATABASE_URL` (Railway sets this automatically)
- `DJANGO_DEBUG` = `0`

#### Step 4: Configure start command
- Start Command: `python manage.py migrate && gunicorn career_neuron.wsgi:application --log-file -`

---

### Recommended deploy steps
1. Create a GitHub repository and push the source code.
2. Connect the repo to Render or Railway.
3. Set environment variables from `.env.example`.
4. Install dependencies and run `python manage.py collectstatic --noinput`.
5. Run migrations:
   - locally: `python manage.py migrate`
   - on Render: the included `render.yaml` uses `releaseCommand: python manage.py migrate`
   - on Railway: configure in start command
6. Start the web service using:
   - `gunicorn career_neuron.wsgi:application --log-file -`

## Local setup

1. Create and activate a Python virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and configure secrets.
4. Run migrations:
   ```bash
   python manage.py migrate
   ```
5. Create a superuser (optional):
   ```bash
   python manage.py createsuperuser
   ```
6. Start the app:
   ```bash
   python manage.py runserver
   ```

## Environment variables

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `RENDER_EXTERNAL_HOSTNAME` (optional, automatically used on Render)
- `DATABASE_URL` (optional, use for managed PostgreSQL on Render)
- `EMAIL_BACKEND`
- `EMAIL_HOST`
- `EMAIL_PORT`
- `EMAIL_USE_TLS`
- `EMAIL_USE_SSL`
- `EMAIL_HOST_USER`
- `EMAIL_HOST_PASSWORD`
- `DEFAULT_FROM_EMAIL`
- `GROQ_API_KEY`
- `OLLAMA_BASE_URL`
- `OLLAMA_MODEL`
- `LLM_TIMEOUT_SECONDS`

## Notes

- The project currently uses SQLite for local development.
- For production, set `DJANGO_DEBUG=0` and configure `DJANGO_ALLOWED_HOSTS`.
- If deploying on a free host, make sure to configure environment variables before launch.
