import csv
import os
import pdfplumber
import docx
import re
import nltk
from tabulate import tabulate
from typing import List, Tuple, Dict

# Download NLTK resources for tokenizing and processing
nltk.download('punkt')

# Define criteria for different faculty positions
POSITIONS = {
    "HOD": {
        "degree": "Ph.D. in Computer Science",
        "min_experience_years": 15,
        "required_skills": {"Leadership", "Departmental Oversight", "Research Excellence", "Budget Management"}
    },
    "Professor": {
        "degree": "Ph.D. in Computer Science",
        "min_experience_years": 10,
        "required_skills": {"Research", "Publications", "Ph.D. Supervision", "Curriculum Development", "Leadership"}
    },
    "Associate Professor": {
        "degree": "Ph.D. in Computer Science",
        "min_experience_years": 5,
        "required_skills": {"Research", "Publications", "Graduate Supervision", "Curriculum Contributions"}
    },
    "Assistant Professor": {
        "degree": "Bachelor's in Computer Science",
        "min_experience_years": 1,
        "required_skills": {"Teaching", "Publications", "Research Potential"}
    },
    "Lab Assistant": {
        "degree": "Bachelor's in Computer Science",
        "min_experience_years": 1,
        "required_skills": {"Lab Experience", "Equipment Handling", "Basic IT Skills", "Programming", "Networking"}
    }
}

def parse_resume(file_path: str) -> str:
    text = ""
    if file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    return text

def extract_name(resume_text: str) -> str:
    name_pattern = re.search(r'(?i)^Name:\s*(.+)', resume_text, re.MULTILINE)
    if name_pattern:
        return name_pattern.group(1).strip()
    lines = resume_text.splitlines()
    for line in lines[:5]:
        if re.match(r'^[A-Za-z\s]+$', line.strip()) and 1 < len(line.strip().split()) < 5:
            return line.strip()
    return "N/A"

def extract_email(resume_text: str) -> str:
    match = re.search(r'[\w\.-]+@[\w\.-]+', resume_text)
    return match.group(0) if match else "N/A"

def check_eligibility(resume_text: str, position: str) -> Tuple[bool, Dict[str, any]]:
    criteria = POSITIONS[position]
    skill_matches = {skill for skill in criteria["required_skills"] if skill.lower() in resume_text.lower()}
    skill_match_percentage = len(skill_matches) / len(criteria["required_skills"]) * 100
    experience_match = False
    if position != "Junior Assistant":
        experience_matches = re.findall(r'(\d+)\+?\s*years of experience', resume_text, re.IGNORECASE)
        experience_match = any(int(years) >= criteria["min_experience_years"] for years in experience_matches)
    degree_match = criteria["degree"].lower() in resume_text.lower()
    if position == "Junior Assistant":
        experience_match = True
    is_eligible = skill_match_percentage >= 70 and experience_match and degree_match
    return is_eligible, {
        "position": position,
        "matched_skills": skill_matches,
        "skill_match_percentage": skill_match_percentage,
        "experience_match": experience_match,
        "degree_match": degree_match
    }

def analyze_resumes(directory: str):
    shortlisted = []
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        if filename.lower().endswith(('.pdf', '.docx')):
            resume_text = parse_resume(file_path)
            name = extract_name(resume_text)
            email = extract_email(resume_text)
            for position in POSITIONS:
                is_eligible, result = check_eligibility(resume_text, position)
                if is_eligible:
                    shortlisted.append([
                        filename, 
                        name, 
                        email, 
                        position, 
                        f"{result['skill_match_percentage']:.1f}%", 
                        "Yes" if result["experience_match"] else "No", 
                        "Yes" if result["degree_match"] else "No"
                    ])
    # Sort by position order in POSITIONS
    shortlisted.sort(key=lambda x: list(POSITIONS.keys()).index(x[3]))
    return shortlisted

def save_to_csv(shortlisted_resumes, filename="shortlisted_resumes.csv"):
    headers = ["File", "Name", "Email", "Position", "Skill %", "Exp Match", "Deg Match"]
    total_applicants = len(shortlisted_resumes)
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(shortlisted_resumes)
        writer.writerow([])
        writer.writerow(["Total Shortlisted Applicants:", total_applicants])
    print(f"CSV file '{filename}' created successfully with {total_applicants} shortlisted applicants.")

# Directory where resumes are stored
resume_directory = r"C:\Users\chmad\OneDrive\Desktop\hloooooooooooooooo\Resumes"  # Update with your actual path

# Run the analysis
shortlisted_resumes = analyze_resumes(resume_directory)

# Print table
headers = ["File", "Name", "Email", "Position", "Skill %", "Exp Match", "Deg Match"]
print(tabulate(shortlisted_resumes, headers=headers, tablefmt="fancy_grid", numalign="center", stralign="center"))

# Display total number of shortlisted applicants
print(f"\nTotal Shortlisted Applicants: {len(shortlisted_resumes)}")

# Save shortlisted resumes to CSV
save_to_csv(shortlisted_resumes)
