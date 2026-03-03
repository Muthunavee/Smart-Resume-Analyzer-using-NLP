from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import os
import spacy
from PyPDF2 import PdfReader
import docx2txt
import json
import requests
import re

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# Admin credentials
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

UPLOAD_FOLDER = 'upload'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

nlp = spacy.load("en_core_web_sm")

RESUME_DB_PATH = 'resumes.json'

# ========== Helper functions for database ==========
def load_resumes():
    if not os.path.exists(RESUME_DB_PATH):
        return []
    with open(RESUME_DB_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_resume_entry(entry):
    data = load_resumes()
    data.append(entry)
    with open(RESUME_DB_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

# ========== Skills, courses, soft skills ==========
COURSE_RECOMMENDATIONS = {
    
    'python': ['Python for Everybody - Coursera', 'Automate the Boring Stuff - Udemy'],
    'machine learning': ['ML Crash Course - Google', 'Machine Learning A-Z - Udemy'],
    'deep learning': ['Deep Learning Specialization - Coursera', 'Intro to Deep Learning - MIT OpenCourseWare'],
    'tensorflow': ['Intro to TensorFlow - Udacity', 'TensorFlow Developer Certificate - Coursera'],
    'pytorch': ['Deep Learning with PyTorch - Udacity', 'PyTorch for Deep Learning - Coursera'],
    'data analysis': ['Data Analyst Nanodegree - Udacity', 'Data Analysis with Python - Coursera'],
    'sql': ['Intro to SQL - Khan Academy', 'SQL for Data Science - Coursera'],
    'statistics': ['Intro to Statistics - Stanford Online', 'Statistics with Python - Coursera'],
    'excel': ['Excel Skills for Business - Coursera', 'Master Excel - Udemy'],
    'web development': ['The Web Developer Bootcamp - Udemy', 'Responsive Web Design - freeCodeCamp'],
    'html': ['HTML Crash Course - freeCodeCamp', 'Build Responsive Websites - Coursera'],
    'css': ['CSS Fundamentals - Codecademy', 'CSS and Flexbox - freeCodeCamp'],
    'javascript': ['JavaScript Essentials - Udemy', 'JavaScript Algorithms and Data Structures - freeCodeCamp'],
    'react': ['React - The Complete Guide - Udemy', 'Front-End Development with React - Coursera'],
    'node.js': ['The Complete Node.js Developer Course - Udemy', 'Server-side Development with Node.js - Coursera'],
    'docker': ['Docker for Beginners - Udemy', 'Containerization with Docker - Coursera'],
    'kubernetes': ['Learn Kubernetes - Udemy', 'Architecting with Kubernetes - Coursera'],
    'aws': ['AWS Certified Cloud Practitioner - Coursera', 'AWS Essentials - Linux Academy'],
    'azure': ['AZ-900 Azure Fundamentals - Microsoft Learn', 'Azure Essentials - Pluralsight'],
    'linux': ['Linux Command Line Basics - Coursera', 'Linux for Beginners - Udemy'],
    'terraform': ['Terraform on Azure - Pluralsight', 'Learn Terraform - HashiCorp Learn'],
    'ci/cd': ['CI/CD Pipelines with Jenkins - Coursera', 'DevOps CI/CD with GitHub Actions - Udemy'],
    'jenkins': ['Jenkins Beginner Tutorial - YouTube (Automation Step by Step)', 'Jenkins CI/CD Pipeline - Udemy'],
    'git': ['Git & GitHub Crash Course - Udemy', 'Version Control with Git - Coursera'],
    'figma': ['Figma UI/UX Design - Skillshare', 'Learn Figma - freeCodeCamp'],
    'adobe xd': ['Adobe XD for Beginners - Udemy', 'UI/UX Design with Adobe XD - Coursera'],
    'sketch': ['Sketch for Beginners - Udemy', 'Design with Sketch - Skillshare'],
    'wireframing': ['Wireframing for UX - LinkedIn Learning', 'Wireframe & Prototype with Figma - Coursera'],
    'prototyping': ['UX Design: From Wireframes to Prototypes - Coursera', 'Prototyping with Adobe XD - Udemy'],
    'user research': ['User Research Fundamentals - LinkedIn Learning', 'UX Research at Scale - Coursera'],
    'user interface': ['UI Design Essentials - Udemy', 'Visual Elements of UI Design - Coursera'],
    'user experience': ['User Experience Design - Coursera', 'UX & Web Design Master Course - Udemy'],
    'network security': ['Network Security & Database Vulnerabilities - Coursera', 'Cybersecurity Foundations - LinkedIn Learning'],
    'firewalls': ['Firewall Essentials - Udemy', 'Network Security Basics - Cybrary'],
    'encryption': ['Cryptography I - Coursera', 'Encryption & Cryptography - Udemy'],
    'penetration testing': ['Learn Ethical Hacking - Udemy', 'Penetration Testing & Ethical Hacking - Cybrary'],
    'ethical hacking': ['The Complete Ethical Hacking Course - Udemy', 'Ethical Hacking Essentials - EC-Council'],
    'risk management': ['Risk Management in Cybersecurity - Coursera', 'IT Risk Management - LinkedIn Learning'],
    'siem': ['SIEM Tools & Techniques - Udemy', 'Security Information and Event Management - Cybrary'],
    'java': ['Java Programming Masterclass - Udemy', 'Java Programming and Software Engineering - Coursera'],
    'swift': ['iOS App Development with Swift - Coursera', 'Swift 5 Programming for Beginners - Udemy'],
    'react native': ['React Native - The Practical Guide - Udemy', 'Multiplatform Mobile App Development - Coursera'],
    'kotlin': ['Kotlin for Android - Udacity', 'The Complete Kotlin Developer Course - Udemy'],
    'android': ['Android App Development - Udacity', 'Android Basics with Kotlin - Google'],
    'ios': ['iOS App Development - Stanford', 'iOS & Swift - The Complete iOS App Development Bootcamp - Udemy'],
    'xcode': ['Xcode Tutorial for Beginners - YouTube', 'iOS App Development with Swift and Xcode - Udemy'],
    'flutter': ['Flutter & Dart - The Complete Guide - Udemy', 'Build Native Mobile Apps with Flutter - Coursera'],
    'objective-c': ['Objective-C for Beginners - Udemy', 'Learn Objective-C - RayWenderlich.com'],
    'google cloud': ['Google Cloud Fundamentals - Coursera', 'GCP Essentials - Qwiklabs'],
    'networking': ['Computer Networking - Coursera', 'Networking Fundamentals - Cisco Networking Academy'],
    'nlp': ['Natural Language Processing - Coursera (DeepLearning.AI)', 'Applied NLP - Udemy'],
    'ai': ['AI For Everyone - Coursera', 'Artificial Intelligence A-Z - Udemy'],
    'neural networks': ['Neural Networks and Deep Learning - Coursera', 'Build Neural Networks - Udacity'],
    'data science': ['IBM Data Science Professional Certificate - Coursera', 'Data Science Bootcamp - Udemy'],
    'business intelligence': ['Business Intelligence Concepts - Coursera', 'BI Basics - Udemy'],
    'power bi': ['Power BI A-Z - Udemy', 'Getting Started with Power BI - LinkedIn Learning'],
    'tableau': ['Data Visualization with Tableau - Coursera', 'Tableau 2023 A-Z - Udemy'],
    'project management': ['Project Management Principles - Coursera', 'PMP Exam Prep - Udemy'],
    'agile': ['Agile with Atlassian Jira - Coursera', 'Agile Project Management - Udemy'],
    'scrum': ['Scrum Certification Prep - Udemy', 'Intro to Scrum - LinkedIn Learning'],
    'product strategy': ['Digital Product Management - Coursera', 'Product Strategy - Northwestern | edX'],
    'market research': ['Market Research - University of California | Coursera', 'Marketing Analytics & Research - Udemy'],
    'roadmap': ['Product Roadmaps - LinkedIn Learning', 'Creating a Product Roadmap - Udemy'],
    'stakeholder management': ['Stakeholder Management Techniques - Udemy', 'Managing Stakeholders - Coursera'],
    'business analysis': ['Business Analysis Fundamentals - Udemy', 'Business Analysis & Process Management - Coursera'],
    'ux design': ['UX Design Professional Certificate - Google | Coursera', 'UX & UI Design Master Course - Udemy'],
    'manual testing': ['Manual Testing for Beginners - Udemy', 'Software Testing Fundamentals - Coursera'],
    'automation testing': ['Test Automation with Selenium - Coursera', 'Automation Testing - Udemy'],
    'selenium': ['Selenium WebDriver with Java - Udemy', 'Test Automation with Selenium - Coursera'],
    'test cases': ['Writing Effective Test Cases - Udemy', 'Software Testing Essentials - Coursera'],
    'bug tracking': ['JIRA for Bug Tracking - Udemy', 'Bug Tracking Tools Overview - LinkedIn Learning'],
    'jira': ['JIRA Fundamentals - Coursera', 'Mastering JIRA - Udemy'],
    'test plans': ['Creating Test Plans - LinkedIn Learning', 'Software QA Test Plans - Udemy'],
    'solidity': ['Ethereum and Solidity - Coursera', 'Solidity Smart Contracts - Udemy'],
    'ethereum': ['Ethereum Development - Udemy', 'Blockchain with Ethereum - Coursera'],
    'smart contracts': ['Smart Contract Development - Coursera', 'Ethereum Smart Contracts - Udemy'],
    'blockchain': ['Blockchain Basics - Coursera', 'Blockchain A-Z - Udemy'],
    'cryptocurrency': ['Bitcoin and Cryptocurrency Technologies - Coursera', 'Cryptocurrency Investment Course - Udemy'],
    'javascript': ['JavaScript Essentials - Udemy', 'JavaScript Algorithms and Data Structures - freeCodeCamp'],
    'dapp development': ['DApp Development on Ethereum - Udemy', 'Blockchain DApp Development - Coursera'],
    'hyperledger': ['Hyperledger Basics - edX', 'Blockchain with Hyperledger - Coursera']
}

    


SOFT_SKILLS = ['communication', 'teamwork', 'leadership', 'adaptability', 'problem solving']

ROLE_SKILLS = {
    'data analyst': ['python', 'data analysis', 'sql', 'statistics', 'excel'],
    'machine learning engineer': ['python', 'machine learning', 'deep learning', 'tensorflow', 'pytorch', 'statistics'],
    'web developer': ['html', 'css', 'javascript', 'react', 'node.js', 'web development'],
    'data scientist': ['python', 'machine learning', 'statistics', 'data visualization', 'sql', 'deep learning'],
    'devops engineer': ['docker', 'kubernetes', 'aws', 'azure', 'linux', 'terraform', 'ci/cd', 'jenkins', 'git', 'python'],
    'ui/ux designer': ['figma', 'adobe xd', 'sketch', 'html', 'css', 'wireframing', 'prototyping', 'user research', 'user interface', 'user experience'],
    'cybersecurity analyst': ['network security', 'firewalls', 'encryption', 'penetration testing', 'ethical hacking', 'linux', 'aws', 'risk management', 'siem'],
    'mobile app developer': ['java', 'swift', 'react native', 'kotlin', 'android', 'ios', 'xcode', 'flutter', 'objective-c'],
    'cloud engineer': ['aws', 'azure', 'google cloud', 'docker', 'kubernetes', 'terraform', 'linux', 'python', 'networking'],
    'ai engineer': ['python', 'tensorflow', 'pytorch', 'machine learning', 'deep learning', 'nlp', 'ai', 'neural networks', 'data science'],
    'business analyst': ['sql', 'excel', 'business intelligence', 'data analysis', 'power bi', 'tableau', 'project management', 'agile', 'scrum'],
    'product manager': ['product strategy', 'agile', 'market research', 'roadmap', 'stakeholder management', 'project management', 'business analysis', 'ux design'],
    'qa tester': ['manual testing', 'automation testing', 'selenium', 'test cases', 'bug tracking', 'jira', 'ci/cd', 'python', 'test plans'],
    'blockchain developer': ['solidity', 'ethereum', 'smart contracts', 'blockchain', 'cryptocurrency', 'javascript', 'python', 'dapp development', 'hyperledger'],
    'frontend developer': ['html', 'css', 'javascript', 'react', 'vue.js', 'responsive design', 'typescript'],
    'backend developer': ['node.js', 'express.js', 'python', 'django', 'flask', 'sql', 'rest api'],
    'full stack developer': ['html', 'css', 'javascript', 'react', 'node.js', 'mongodb', 'sql', 'git'],
    'data engineer': ['python', 'sql', 'spark', 'hadoop', 'etl', 'airflow', 'data warehousing'],
    'devops specialist': ['jenkins', 'docker', 'kubernetes', 'ci/cd', 'aws', 'linux', 'ansible'],
    'database administrator': ['sql', 'oracle', 'mysql', 'postgresql', 'database tuning', 'backup and recovery'],
    'software engineer': ['java', 'python', 'c++', 'data structures', 'algorithms', 'git', 'oop'],
    'systems analyst': ['systems analysis', 'uml', 'sql', 'requirements gathering', 'project documentation'],
    'ai researcher': ['python', 'machine learning', 'deep learning', 'reinforcement learning', 'research methods'],
    'game developer': ['unity', 'c#', 'game physics', '3d modeling', 'animation', 'game design', 'unreal engine'],
    'robotics engineer': ['c++', 'python', 'ros', 'robot kinematics', 'control systems', 'embedded systems'],
    'network engineer': ['networking', 'cisco', 'routing and switching', 'firewalls', 'tcp/ip', 'network protocols'],
    'digital marketer': ['seo', 'sem', 'google analytics', 'content marketing', 'social media', 'email marketing'],
    'content writer': ['content writing', 'seo', 'copywriting', 'grammar', 'research', 'wordpress'],
    'hr specialist': ['recruitment', 'hr analytics', 'onboarding', 'compliance', 'performance management'],
    'financial analyst': ['excel', 'financial modeling', 'valuation', 'accounting', 'power bi', 'sql'],
    'cloud architect': ['cloud architecture', 'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform'],
    'blockchain architect': ['blockchain', 'solidity', 'smart contracts', 'ethereum', 'hyperledger', 'ipfs'],
    'cybersecurity engineer': ['network security', 'penetration testing', 'siem', 'encryption', 'incident response'],
    'ai product manager': ['product strategy', 'ai', 'data analysis', 'user stories', 'agile', 'model evaluation']
}



    


# ========== Routes ==========
@app.route('/')
def index():
    return render_template('index.html')  # Shows User/Admin choice

@app.route('/user')
def user_side():
    return render_template('user.html')  # Resume upload + chatbot

@app.route('/demo')
def resume_demo():
    return render_template('demo_resume.html')


@app.route('/admin')
def admin_login_page():
    return render_template('adminlogin.html')


@app.route('/adminlogin', methods=['POST'])
def admin_login():
    username = request.form.get('username')
    password = request.form.get('password')

    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        session['username'] = username
        session['role'] = 'admin'
        return redirect(url_for('admin_dashboard'))
    else:
        error = "Invalid credentials. Please try again."
        return render_template('adminlogin.html', error=error)


@app.route('/admin_dashboard')
def admin_dashboard():
    if 'role' in session and session['role'] == 'admin':
        resumes = load_resumes()

        # Sort by score descending
        sorted_resumes = sorted(resumes, key=lambda r: r.get('score', 0), reverse=True)

        # Optional: remove exact duplicates based on filename + score
        unique = []
        seen = set()
        for r in sorted_resumes:
            identifier = (r.get('filename'), r.get('score'))
            if identifier not in seen:
                seen.add(identifier)
                unique.append(r)

        return render_template('admin.html', resumes=unique)
    else:
        return redirect(url_for('admin_login_page'))



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin_login_page'))


# ========== Resume Analysis ==========
def extract_text(file_path):
    if file_path.endswith('.pdf'):
        reader = PdfReader(file_path)
        return "\n".join(page.extract_text() or '' for page in reader.pages)
    elif file_path.endswith('.docx'):
        return docx2txt.process(file_path)
    elif file_path.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    return "Unsupported file type."

def analyze_resume(text):
    doc = nlp(text.lower())
    tokens = set(token.text for token in doc if not token.is_stop and token.is_alpha)
    skills = [token for token in tokens if token in COURSE_RECOMMENDATIONS]
    soft_skills = [token for token in tokens if token in SOFT_SKILLS]
    return skills, soft_skills

def grammar_check(text):
    url = "https://api.languagetool.org/v2/check"
    data = {
        "text": text,
        "language": "en-US"
    }
    try:
        response = requests.post(url, data=data)
        results = response.json()
    except Exception as e:
        print("Grammar API failed:", e)
        return [{"context": "N/A", "message": "Grammar API unavailable", "suggestion": "Try again later"}]

    corrections = []
    for match in results.get("matches", []):
        context_text = match.get("context", {}).get("text", "")
        message = match.get("message", "No message")
        replacements = match.get("replacements", [])
        suggestion = replacements[0]["value"] if replacements else "No suggestion"
        corrections.append({
            "context": context_text,
            "message": message,
            "suggestion": suggestion
        })

    return corrections


def suggest_objective_rewrite(objective_text):
    suggestions = []

    if len(objective_text.split()) < 10:
        suggestions.append("Your objective is too short. Consider expanding it with more details about your goals.")

    if "hardworking" in objective_text.lower():
        suggestions.append("Try replacing vague words like 'hardworking' with specific achievements or aspirations.")

    # Example of a professional objective
    example = ("Example: 'Motivated computer science graduate with hands-on experience in software development, "
               "seeking to leverage strong problem-solving skills in a dynamic tech environment.'")

    return suggestions + [example]


def get_nlp_suggestions(text, target_role=None):
    """
    Generate professional resume improvement suggestions using NLP.
    Parameters:
        text (str): The resume text content.
        target_role (str, optional): The desired job title for alignment scoring.
    Returns:
        suggestions (list): List of actionable suggestion strings.
    """

    suggestions = []
    doc = nlp(text)

    # Normalize lowercase text for simple keyword checks
    lower_text = text.lower()

    # Check for presence of essential resume sections
    if 'objective' not in lower_text:
        suggestions.append("Include an 'Objective' section at the top to briefly outline your career goals and what you bring to the role.")
    if 'experience' not in lower_text:
        suggestions.append("An 'Experience' section is crucial—use it to describe your job history, responsibilities, and accomplishments.")
    if 'skills' not in lower_text:
        suggestions.append("Highlight your technical and soft abilities in a dedicated 'Skills' section to improve scanability.")

    # Check for missing educational background keywords
    if 'education' not in lower_text:
        suggestions.append("Add an 'Education' section to list your academic qualifications, degrees, and institutions attended.")

    # Check for presence of company or organization names (ORG entities)
    orgs = [ent.text for ent in doc.ents if ent.label_ == "ORG"]
    if not orgs:
        suggestions.append("Mentioning past employers, universities, or project partners (organization names) adds credibility and context.")

    # Look for strong action verbs in resume content
    action_verbs = {'lead', 'manage', 'develop', 'create', 'implement', 'design', 'build', 'coordinate'}
    verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
    if not any(v in verbs for v in action_verbs):
        suggestions.append("Use strong action verbs such as 'developed', 'led', 'implemented', or 'coordinated' to emphasize achievements.")

    # Check sentence length for readability and clarity
    long_sentences = [sent for sent in doc.sents if len(sent.text.split()) > 30]
    if long_sentences:
        suggestions.append("Some sentences are too long. Break them into shorter, concise bullet points to improve readability.")

    # Check if any quantifiable metrics are included (numbers, %s, etc.)
    if not any(char.isdigit() for char in text):
        suggestions.append("Include quantifiable results (e.g., 'Increased user engagement by 30%') to demonstrate measurable impact.")

    # Check if resume includes soft skills
    soft_skills = ['communication', 'teamwork', 'problem-solving', 'adaptability', 'leadership']
    if not any(skill in lower_text for skill in soft_skills):
        suggestions.append("Consider adding relevant soft skills like 'teamwork' or 'problem-solving' to showcase well-rounded capabilities.")

    # Check alignment of content with target job role (if provided)
    if target_role:
        role_doc = nlp(target_role.lower())
        sim_score = doc.similarity(role_doc)
        if sim_score < 0.7:
            suggestions.append(f"The content of your resume has limited alignment with the role '{target_role}'. Include more domain-relevant keywords and experiences to improve relevance.")

    # Bonus: Check if contact section is present
    if not any(x in lower_text for x in ['email', '@', 'phone', 'contact']):
        suggestions.append("Ensure your contact information (email, phone number) is clearly visible for recruiters to reach out.")

    return suggestions


def get_score(skills):
    return min(100, len(skills) * 10)

@app.route('/upload', methods=['POST'])
def upload():
    if 'resume' not in request.files:
        return 'No file part'

    file = request.files['resume']
    job_role = request.form.get('job_role', '').strip().lower()

    if file.filename == '':
        return 'No selected file'

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    text = extract_text(file_path)
    skills, soft_skills = analyze_resume(text)
    score = get_score(skills)

    required_skills = ROLE_SKILLS.get(job_role, [])
    gaps = [skill for skill in required_skills if skill not in skills]
    recommendations = {skill: COURSE_RECOMMENDATIONS[skill] for skill in gaps if skill in COURSE_RECOMMENDATIONS}
    nlp_suggestions = get_nlp_suggestions(text, target_role=job_role)

    # Full resume grammar check
    grammar_corrections = grammar_check(text)

    # Extract objective text if available, for objective suggestions only
    objective_match = re.search(r'(objective[:\-\s]*)(.*?)(education|experience|skills|projects|$)', text, re.IGNORECASE | re.DOTALL)
    objective_text = objective_match.group(2).strip() if objective_match else ""
    objective_suggestions = suggest_objective_rewrite(objective_text) if objective_text else []

    resume_entry = {
        "filename": file.filename,
        "text": text,
        "score": score,
        "skills": skills,
        "soft_skills": soft_skills
    }
    save_resume_entry(resume_entry)

    return render_template('result.html', score=score, skills=skills, gaps=gaps,
                           soft_skills=soft_skills, recommendations=recommendations,
                           nlp_suggestions=nlp_suggestions,
                           grammar_corrections=grammar_corrections,
                           objective_suggestions=objective_suggestions)


# ========== Chatbot Endpoint ==========
import openai

# Set your Groq API key
openai.api_key = "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"  # Replace with your actual key
openai.api_base = "https://api.groq.com/openai/v1"

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json.get('message', '')

    try:
        response = openai.ChatCompletion.create(
            model = "llama3-70b-8192"  # Replace this in your API call
,  # Groq currently supports models like Mixtral, Gemma, LLaMA
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant that helps users with resume tips, career advice, and course recommendations."},
                {"role": "user", "content": user_input}
            ]
        )
        bot_reply = response['choices'][0]['message']['content']
        return jsonify({'response': bot_reply})

    except Exception as e:
        return jsonify({'response': f"Error communicating with AI model: {str(e)}"})


# ========== Run ==========
if __name__ == '__main__':
    app.run(debug=True)
