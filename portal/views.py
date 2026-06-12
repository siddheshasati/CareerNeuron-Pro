from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from .models import UserProfile, Job, Education, Experience, OTPToken, Interview
import secrets
from django.utils import timezone
from datetime import timedelta
from .profile_utils import (
    extract_resume_text,
    merge_resume_data,
    parse_resume_fallback,
    save_parsed_resume,
    score_job_match,
)

def login_view(request):
    if request.user.is_authenticated:
        return redirect('portal:dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('portal:dashboard')
            else:
                messages.error(request, "Invalid credentials.")
        except Exception as e:
            messages.error(request, f"Error: {e}")

    return render(request, 'portal/login_register.html', {'is_login': True})

def logout_view(request):
    logout(request)
    return redirect('portal:login')

from .scraper import scrape_jobs

@login_required
def dashboard(request):
    query = request.GET.get('q', '')
    jobs = []
    if query:
        scraped_jobs = scrape_jobs(query)
        job_ids = []
        for j in scraped_jobs:
            job = Job.objects.filter(link=j['link']).first()
            if job:
                job.title = j['title']
                job.company = j['company']
                job.location = j.get('location', '')
                job.description = j.get('description', '')
                job.save()
            else:
                job = Job.objects.create(
                    title=j['title'],
                    company=j['company'],
                    location=j.get('location', ''),
                    link=j['link'],
                    description=j.get('description', ''),
                )
            job_ids.append(job.id)

        if job_ids:
            preserved_order = {job_id: index for index, job_id in enumerate(job_ids)}
            jobs = sorted(Job.objects.filter(id__in=job_ids), key=lambda job: preserved_order[job.id])
        else:
            jobs = Job.objects.none()
    else:
        jobs = Job.objects.exclude(link__icontains='example.com').order_by('-id')[:15]
    return render(request, 'portal/dashboard.html', {'jobs': jobs, 'query': query})


def save_profile_sections(request, profile):
    Education.objects.filter(profile=profile).delete()
    institutions = request.POST.getlist('edu_institution[]')
    degrees = request.POST.getlist('edu_degree[]')
    specializations = request.POST.getlist('edu_specialization[]')
    locations = request.POST.getlist('edu_location[]')
    starts = request.POST.getlist('edu_start_date[]')
    ends = request.POST.getlist('edu_end_date[]')
    pursuing_indexes = set(request.POST.getlist('edu_currently_pursuing[]'))

    for index, institution in enumerate(institutions):
        degree = degrees[index] if index < len(degrees) else ''
        if not institution and not degree:
            continue
        Education.objects.create(
            profile=profile,
            institution=institution or 'Not specified',
            degree=degree or 'Not specified',
            specialization=specializations[index] if index < len(specializations) else '',
            stream=specializations[index] if index < len(specializations) else '',
            location=locations[index] if index < len(locations) else '',
            city=locations[index] if index < len(locations) else '',
            start_date=starts[index] if index < len(starts) else '',
            end_date=ends[index] if index < len(ends) else '',
            currently_pursuing=str(index) in pursuing_indexes,
        )

    Experience.objects.filter(profile=profile).delete()
    organizations = request.POST.getlist('exp_organization[]')
    roles = request.POST.getlist('exp_role[]')
    exp_locations = request.POST.getlist('exp_location[]')
    ctcs = request.POST.getlist('exp_current_ctc[]')
    exp_starts = request.POST.getlist('exp_start_date[]')
    exp_ends = request.POST.getlist('exp_end_date[]')
    summaries = request.POST.getlist('exp_summary[]')

    for index, organization in enumerate(organizations):
        role = roles[index] if index < len(roles) else ''
        if not organization and not role:
            continue
        Experience.objects.create(
            profile=profile,
            company=organization or 'Not specified',
            organization=organization,
            role=role or 'Not specified',
            location=exp_locations[index] if index < len(exp_locations) else '',
            ctc=ctcs[index] if index < len(ctcs) else '',
            current_ctc=ctcs[index] if index < len(ctcs) else '',
            start_date=exp_starts[index] if index < len(exp_starts) else '',
            end_date=exp_ends[index] if index < len(exp_ends) else '',
            summary=summaries[index] if index < len(summaries) else '',
        )


@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    resume_parsed = None
    
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', request.user.first_name)
        request.user.last_name = request.POST.get('last_name', request.user.last_name)
        request.user.email = request.POST.get('email', request.user.email)
        request.user.username = request.user.email
        request.user.save()

        profile.full_name = f"{request.user.first_name} {request.user.last_name}".strip()
        profile.mobile = request.POST.get('mobile', profile.mobile)
        profile.gender = request.POST.get('gender', profile.gender)
        profile.disability = request.POST.get('disability', profile.disability)
        profile.city = request.POST.get('city', profile.city)
        profile.state = request.POST.get('state', profile.state)
        profile.country = request.POST.get('country', profile.country)
        profile.skills = request.POST.get('skills', profile.skills)
        profile.linkedin_url = request.POST.get('linkedin_url', profile.linkedin_url)
        profile.github_url = request.POST.get('github_url', profile.github_url)
        profile.portfolio_url = request.POST.get('portfolio_url', profile.portfolio_url)
        profile.additional_url_name = request.POST.get('additional_url_name', profile.additional_url_name)
        profile.additional_url = request.POST.get('additional_url', profile.additional_url)
        
        if 'resume' in request.FILES:
            profile.resume = request.FILES['resume']
            profile.save()
            
            try:
                text = extract_resume_text(profile.resume.path)
                engine = AIEngine()
                ai_data = engine.analyze_resume(text)
                parsed_data = merge_resume_data(ai_data, parse_resume_fallback(text))
                
                if parsed_data:
                    save_parsed_resume(
                        profile,
                        parsed_data,
                        registration_email=request.user.email,
                        registration_mobile=profile.mobile,
                    )
                    messages.success(request, "Resume uploaded, parsed, and saved to your editable profile.")
                else:
                    messages.warning(request, "Resume uploaded but AI analysis failed.")
            except Exception as e:
                print(f"Error processing resume: {e}")
                messages.error(request, "Failed to extract data from the resume.")
        else:
            profile.save()
            save_profile_sections(request, profile)
            messages.success(request, "Profile updated successfully.")
            
        return redirect('portal:profile')
        
    if profile.resume_data:
        import json
        try:
            resume_parsed = json.loads(profile.resume_data)
        except:
            pass
            
    return render(request, 'portal/profile_builder.html', {
        'profile': profile,
        'resume_parsed': resume_parsed,
        'educations': profile.educations.all(),
        'experiences': profile.experiences.all(),
    })

from .ai_engine import AIEngine

@login_required
def advisor_view(request):
    response = None
    formatted_response = None
    query = ''
    profile = getattr(request.user, 'profile', None)
    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        if query:
            engine = AIEngine()
            resume_data = profile.resume_data if profile else None
            profile_context = build_career_profile_context(request.user, profile)
            response = engine.get_career_advice(
                query,
                resume_data=resume_data,
                profile_context=profile_context,
            )

            if response:
                formatted_response = parse_markdown_response(response)

    return render(request, 'portal/advisor.html', {
        'ai_response': response,
        'formatted_response': formatted_response,
        'query': query,
        'profile': profile,
    })


def build_career_profile_context(user, profile):
    if not profile:
        return f"Name: {user.get_full_name() or user.email}\nEmail: {user.email}"

    education_lines = [
        f"- {edu.degree} {('in ' + edu.specialization) if edu.specialization else ''} at {edu.institution} ({edu.start_date or 'N/A'} - {edu.end_date or ('Present' if edu.currently_pursuing else 'N/A')})"
        for edu in profile.educations.all()[:4]
    ]
    experience_lines = [
        f"- {exp.role} at {exp.organization or exp.company}, {exp.location or 'Location not specified'}: {exp.summary or 'No summary'}"
        for exp in profile.experiences.all()[:4]
    ]

    return "\n".join([
        f"Name: {user.get_full_name() or profile.full_name or user.email}",
        f"Email: {user.email}",
        f"Mobile: {profile.mobile or 'Not provided'}",
        f"Skills: {profile.skills or 'Not provided'}",
        f"LinkedIn: {profile.linkedin_url or 'Not provided'}",
        "Education:",
        "\n".join(education_lines) or "- Not provided",
        "Experience:",
        "\n".join(experience_lines) or "- Not provided",
    ])


def parse_markdown_response(text):
    """Convert markdown headings into ordered sections for template display."""
    sections = []
    current_title = "Career Advice"
    current_content = []

    for line in text.split('\n'):
        if line.startswith('## '):
            if current_content:
                sections.append({
                    'title': current_title,
                    'content': '\n'.join(current_content).strip(),
                })
            current_title = line.replace('## ', '').strip()
            current_content = []
        else:
            current_content.append(line)

    if current_content:
        sections.append({
            'title': current_title,
            'content': '\n'.join(current_content).strip(),
        })

    return sections

@login_required
def interview_view(request):
    return render(request, 'portal/interview.html')

@login_required
def cover_letter_view(request):
    response = None
    if request.method == 'POST':
        job_desc = request.POST.get('job_desc')
        if job_desc:
            engine = AIEngine()
            profile = getattr(request.user, 'profile', None)
            profile_context = f"Name: {profile.full_name}\nRole: {profile.role}" if profile else "Unknown User"
            response = engine.generate_cover_letter(job_desc, profile_context)
    return render(request, 'portal/cover_letter.html', {'ai_response': response})

@login_required
def job_match_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    query = request.POST.get('query') or request.GET.get('q') or ''
    matched_jobs = []
    searched = False

    if request.method == 'POST' or request.GET.get('q'):
        searched = True
        if not query:
            skills = [skill.strip() for skill in (profile.skills or '').split(',') if skill.strip()]
            recent_role = profile.experiences.order_by('-id').first()
            query = recent_role.role if recent_role else ' '.join(skills[:3]) or 'software developer'

        scraped_jobs = scrape_jobs(query)
        for item in scraped_jobs:
            score, matched_terms = score_job_match(profile, item)
            if score >= 70:
                job = Job.objects.filter(link=item['link']).first()
                if job:
                    job.title = item['title']
                    job.company = item['company']
                    job.location = item.get('location', '')
                    job.description = item.get('description', '')
                    job.save()
                else:
                    job = Job.objects.create(
                        title=item['title'],
                        company=item['company'],
                        location=item.get('location', ''),
                        link=item['link'],
                        description=item.get('description', ''),
                    )
                matched_jobs.append({
                    'job': job,
                    'score': score,
                    'matched_terms': matched_terms,
                })

        matched_jobs.sort(key=lambda item: item['score'], reverse=True)

    return render(request, 'portal/job_match.html', {
        'profile': profile,
        'query': query,
        'matched_jobs': matched_jobs,
        'searched': searched,
        'has_match_data': bool(profile.skills or profile.experiences.exists()),
    })

@login_required
def smtp_test_view(request):
    if request.method == 'POST':
        test_email = request.POST.get('test_email')
        if test_email:
            try:
                send_mail(
                    'SMTP Test - Pro Job Portal',
                    'This is a test email to verify SMTP configuration is working.',
                    settings.DEFAULT_FROM_EMAIL,
                    [test_email],
                    fail_silently=False,
                )
                messages.success(request, f"Test email sent to {test_email} successfully!")
            except Exception as e:
                messages.error(request, f"SMTP Error: {e}")
        else:
            messages.error(request, "Please provide an email address.")
from django.http import JsonResponse
import json

@login_required
def interview_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            history = data.get('history', [])
            role = data.get('role', 'Software Engineer')
            company = data.get('company', 'Tech Company')
            job_description = data.get('job_description', '')

            profile = getattr(request.user, 'profile', None)
            resume_data = profile.resume_data if profile else "No resume data provided."

            engine = AIEngine()
            response = engine.conduct_interview(history, resume_data, role, company, job_description)

            if response and 'INTERVIEW_COMPLETE' in response:
                if profile:
                    interview = Interview.objects.create(
                        profile=profile,
                        role=role,
                        company=company,
                        question_count=len([msg for msg in history if msg['role'] == 'user']) - 1,
                        transcript=json.dumps(history),
                        ats_feedback=response.replace('INTERVIEW_COMPLETE', '').strip()
                    )

            return JsonResponse({'success': True, 'response': response})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


def register_step1_view(request):
    if request.user.is_authenticated:
        return redirect('portal:dashboard')

    if request.method == 'POST':
        from django.http import HttpResponse
        import traceback
        try:
            email = request.POST.get('email')

            if User.objects.filter(username=email).exists():
                messages.error(request, "Email already registered.")
                return redirect('portal:register')

            otp_code = str(secrets.randbelow(1000000)).zfill(6)
            expires_at = timezone.now() + timedelta(minutes=10)

            OTPToken.objects.filter(email=email).delete()
            OTPToken.objects.create(
                email=email,
                otp_code=otp_code,
                expires_at=expires_at
            )

            try:
                send_mail(
                    'Your OTP for Registration - Career Neuron',
                    f'Your One-Time Password is: {otp_code}\n\nThis OTP will expire in 10 minutes.\n\nDo not share this code with anyone.',
                    settings.DEFAULT_FROM_EMAIL,
                    [email],
                    fail_silently=False,
                )
                messages.success(request, f"OTP sent to {email}. Check your inbox.")
                request.session['registration_email'] = email
                return redirect('portal:verify_otp')
            except Exception as e:
                messages.error(request, f"Failed to send OTP: {str(e)}")
                return redirect('portal:register')
        except Exception as e:
            tb = traceback.format_exc()
            return HttpResponse(f"<h3>Internal Server Error Traceback</h3><pre>{tb}</pre>", status=500)

    return render(request, 'portal/register_step1.html')


def verify_otp_view(request):
    from django.http import HttpResponse
    import traceback
    try:
        email = request.session.get('registration_email')

        if not email:
            messages.error(request, "Please start registration from the beginning.")
            return redirect('portal:register')

        if request.method == 'POST':
            otp_code = request.POST.get('otp_code')

            try:
                otp_token = OTPToken.objects.get(email=email)

                if otp_token.otp_code == otp_code:
                    if not otp_token.is_valid():
                        messages.error(request, "OTP expired or too many attempts.")
                        OTPToken.objects.filter(email=email).delete()
                        del request.session['registration_email']
                        return redirect('portal:register')

                    otp_token.is_verified = True
                    otp_token.save()
                    request.session['otp_verified'] = True
                    messages.success(request, "Email verified successfully!")
                    return redirect('portal:register_step2')
                else:
                    otp_token.attempts += 1
                    otp_token.save()
                    remaining = 5 - otp_token.attempts
                    if remaining > 0:
                        messages.error(request, f"Invalid OTP. {remaining} attempts remaining.")
                    else:
                        messages.error(request, "Too many attempts. Please register again.")
                        OTPToken.objects.filter(email=email).delete()
                        del request.session['registration_email']
                        return redirect('portal:register')
            except OTPToken.DoesNotExist:
                messages.error(request, "OTP not found. Please register again.")
                return redirect('portal:register')

        return render(request, 'portal/verify_otp.html', {'email': email})
    except Exception as e:
        tb = traceback.format_exc()
        return HttpResponse(f"<h3>Internal Server Error Traceback (Verify OTP)</h3><pre>{tb}</pre>", status=500)


def register_step2_view(request):
    from django.http import HttpResponse
    import traceback
    try:
        email = request.session.get('registration_email')
        otp_verified = request.session.get('otp_verified')

        if not email or not otp_verified:
            messages.error(request, "Please complete email verification first.")
            return redirect('portal:register')

        if request.method == 'POST':
            mobile = request.POST.get('mobile')
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            gender = request.POST.get('gender', '')
            disability = request.POST.get('disability', '')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            role = request.POST.get('role', 'User')

            if password != password_confirm:
                messages.error(request, "Passwords do not match.")
                return redirect('portal:register_step2')

            if len(password) < 6:
                messages.error(request, "Password must be at least 6 characters.")
                return redirect('portal:register_step2')

            try:
                user = User.objects.create_user(
                    username=email,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )
                profile = UserProfile.objects.create(
                    user=user,
                    mobile=mobile,
                    role=role,
                    full_name=f"{first_name} {last_name}".strip(),
                    gender=gender,
                    disability=disability,
                )

                if 'resume' in request.FILES:
                    profile.resume = request.FILES['resume']
                    profile.save()

                    try:
                        text = extract_resume_text(profile.resume.path)
                        engine = AIEngine()
                        ai_data = engine.analyze_resume(text)
                        parsed_data = merge_resume_data(ai_data, parse_resume_fallback(text))

                        if parsed_data:
                            if first_name:
                                parsed_data['first_name'] = first_name
                            if last_name:
                                parsed_data['last_name'] = last_name
                            parsed_data['email'] = email
                            parsed_data['mobile'] = mobile
                            save_parsed_resume(profile, parsed_data, registration_email=email, registration_mobile=mobile)
                            messages.success(request, "Resume uploaded, parsed, and saved to your profile.")
                    except Exception as e:
                        print(f"Error processing resume: {e}")

                OTPToken.objects.filter(email=email).delete()
                if 'registration_email' in request.session:
                    del request.session['registration_email']
                if 'otp_verified' in request.session:
                    del request.session['otp_verified']

                messages.success(request, "Registration successful! Please login.")
                return redirect('portal:login')
            except Exception as e:
                messages.error(request, f"Registration failed: {str(e)}")
                return redirect('portal:register_step2')

        return render(request, 'portal/register_step2.html', {'email': email})
    except Exception as e:
        tb = traceback.format_exc()
        return HttpResponse(f"<h3>Internal Server Error Traceback (Register Step 2)</h3><pre>{tb}</pre>", status=500)


def test_db_view(request):
    from django.db import connection
    from django.http import HttpResponse
    import traceback
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            row = cursor.fetchone()
        return HttpResponse(f"<h3>Database Connection Successful!</h3>Query result: <code>{row}</code>")
    except Exception as e:
        tb = traceback.format_exc()
        return HttpResponse(f"<h3>Database Connection Failed!</h3><p>Error: {str(e)}</p><pre>{tb}</pre>", status=500)
