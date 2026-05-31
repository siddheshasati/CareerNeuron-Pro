import os
import json
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from django.conf import settings

class AIEngine:
    def __init__(self):
        try:
            api_key = os.getenv('GROQ_API_KEY', getattr(settings, 'GROQ_API_KEY', ''))
            if not api_key:
                print("Warning: GROQ_API_KEY is not set.")
                self.llm = None
            else:
                self.llm = ChatGroq(
                    groq_api_key=api_key,
                    model_name="llama-3.3-70b-versatile",
                    temperature=0.7
                )
        except Exception as e:
            print(f"Warning: AI Engine initialization failed: {e}")
            self.llm = None

    def analyze_resume(self, resume_text):
        if not self.llm:
            return None
        prompt = PromptTemplate.from_template(
            "You are an expert ATS system and recruiter. Analyze the following resume text.\n"
            "Extract the following into a STRICT JSON object with these keys: "
            "'first_name', 'last_name', 'email', 'mobile', 'location', 'linkedin_url', 'github_url', "
            "'portfolio_url', 'additional_urls' (list of dicts with 'name' and 'url'), "
            "'skills' (list of strings), "
            "'education' (list of dicts with 'institution', 'degree', 'specialization', 'location', 'start_date', 'end_date', 'currently_pursuing'), "
            "'experience' (list of dicts with 'organization', 'role', 'location', 'current_ctc', 'start_date', 'end_date', 'summary'), "
            "'projects' (list of dicts with 'title', 'description'), "
            "'ats_score' (integer 0-100), and 'suggestions' (list of key points to improve the resume).\n\n"
            "Return ONLY valid JSON and nothing else.\n\n"
            "Resume Text: {resume_text}\n"
        )
        chain = prompt | self.llm
        response = chain.invoke({"resume_text": resume_text})
        content = response.content if hasattr(response, 'content') else str(response)
        
        # Clean up JSON if it contains markdown ticks
        if content.startswith("```json"):
            content = content.strip("```json").strip("```").strip()
        elif content.startswith("```"):
            content = content.strip("```").strip()
            
        try:
            return json.loads(content)
        except Exception as e:
            print(f"Failed to parse resume JSON: {e}\nContent was: {content}")
            return None

    def get_career_advice(self, query, resume_data=None, profile_context=None):
        if not self.llm:
            return (
                "## Direct Answer\n"
                "AI is currently unavailable because GROQ_API_KEY is not set.\n\n"
                "## Next Step\n"
                "Add GROQ_API_KEY in your .env file and restart the server to enable personalized career advice."
            )

        context_parts = []
        if profile_context:
            context_parts.append(str(profile_context))
        if resume_data:
            context_parts.append(f"Parsed resume knowledge base:\n{resume_data}")
        user_context = "\n\n".join(context_parts) or "No profile or resume knowledge base is available yet."

        prompt = PromptTemplate.from_template(
            "You are a practical career advisor for job seekers. Answer the user's exact career question first, "
            "then use their saved skills, education, experience, and parsed resume knowledge base to personalize the advice.\n\n"
            "Rules:\n"
            "- Stay focused on the question. Do not give generic advice unless it directly helps the question.\n"
            "- Reference the user's skills/resume only when relevant.\n"
            "- Give concrete actions the user can follow.\n"
            "- Return markdown with exactly these sections:\n"
            "## Direct Answer\n"
            "## Profile-Based Insight\n"
            "## Action Plan\n"
            "## Skills To Improve\n"
            "## Suggested Next Roles\n\n"
            "User profile and resume context:\n{user_context}\n\n"
            "User question:\n{query}"
        )
        chain = prompt | self.llm
        response = chain.invoke({"query": query, "user_context": user_context})
        return response.content if hasattr(response, 'content') else str(response)
        
    def generate_cover_letter(self, job_desc, user_profile_context):
        if not self.llm:
            return "AI is currently unavailable. Please ensure GROQ_API_KEY is set."
        prompt = PromptTemplate.from_template(
            "Write a highly professional and modern cover letter for the following job description based on the user's profile.\n\nJob Description: {job_desc}\n\nUser Profile: {user_profile_context}\n\nCover Letter:"
        )
        chain = prompt | self.llm
        response = chain.invoke({"job_desc": job_desc, "user_profile_context": user_profile_context})
        return response.content if hasattr(response, 'content') else str(response)

    def conduct_interview(self, history, resume_data, role, company, job_description=""):
        if not self.llm:
            return "AI is currently unavailable."

        history_text = ""
        for msg in history:
            history_text += f"{msg['role'].capitalize()}: {msg['content']}\n"

        resume_context = "No resume data provided."
        if resume_data and resume_data != "No resume data provided.":
            try:
                if isinstance(resume_data, str) and resume_data.startswith('{'):
                    import json
                    resume_json = json.loads(resume_data)
                    skills = resume_json.get('skills', [])
                    experience = resume_json.get('experience', [])
                    education = resume_json.get('education', [])
                    projects = resume_json.get('projects', [])
                    ats_score = resume_json.get('ats_score', 0)

                    resume_context = f"""
ATS Score: {ats_score}/100

Skills: {', '.join(skills[:10]) if skills else 'Not specified'}

Experience:
"""
                    for exp in experience[:3]:
                        resume_context += f"- {exp.get('role', 'Role')} at {exp.get('company', 'Company')} ({exp.get('duration', 'Duration')})\n"

                    resume_context += f"\nEducation:\n"
                    for edu in education[:2]:
                        resume_context += f"- {edu.get('degree', 'Degree')} in {edu.get('stream', 'Stream')} from {edu.get('institution', 'Institution')}\n"

                    if projects:
                        resume_context += f"\nKey Projects:\n"
                        for proj in projects[:2]:
                            resume_context += f"- {proj.get('title', 'Project')}: {proj.get('description', 'No description')}\n"
            except Exception as e:
                print(f"Error parsing resume data: {e}")
                resume_context = str(resume_data)[:500]

        job_context = job_description.strip() or "No job description was provided. Use the role, company, and candidate profile."

        system_prompt = f"""You are an expert technical and HR interviewer conducting a realistic interview for the role of {role} at {company}.

CANDIDATE PROFILE:
{resume_context}

TARGET JOB DESCRIPTION:
{job_context}

INTERVIEW GUIDELINES:
1. Review the conversation history and ask the NEXT single, focused interview question
2. Ask questions progressively: introduction -> experience/projects -> job-description-specific technical skills -> situational/behavioral
3. Reference the candidate's resume and the target job description when choosing questions
4. Be conversational and realistic - like a real interviewer would be
5. Keep responses concise (2-4 sentences). Ask ONE question per turn
6. Adjust difficulty based on their ATS score and answers - higher scores get harder technical questions
7. After 5-7 questions, conclude the interview with brief constructive feedback
8. End interview message with EXACTLY: INTERVIEW_COMPLETE

INTERVIEW PROGRESS:
Question count: {len([m for m in history if m['role'] == 'user']) - 1}

Conversation History:
{history_text}

NEXT INTERVIEWER RESPONSE:"""

        response = self.llm.invoke(system_prompt)
        return response.content if hasattr(response, 'content') else str(response)
