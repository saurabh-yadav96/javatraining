def enhance_steps(steps):

    prompt = f"""
You are a professional technical writer.

Rewrite steps into detailed user manual steps.

Rules:
- Each step must include title + explanation
- Format strictly like:

Step 1: Title
Explanation: ...

Step 2: Title
Explanation: ...

Steps:
{steps}
"""

    output = call_groq(prompt)

    enhanced = []
    current_step = ""

    for line in output.split("\n"):
        line = line.strip()

        if line.lower().startswith("step"):
            if current_step:
                enhanced.append(current_step.strip())
            current_step = line

        elif line.lower().startswith("explanation"):
            current_step += "<br/>" + line

        else:
            current_step += " " + line

    if current_step:
        enhanced.append(current_step.strip())

    return enhanced
    
def generate_notes(steps):
    prompt = f"""
Generate helpful notes for users.

Include:
- Common mistakes
- Tips
- Warnings

Steps:
{steps}
"""
    return call_groq(prompt)
from app.services.ai_service import call_groq

def generate_sections(frs: str):
    if not frs:
        return {
            "title": "Application Process",
            "introduction": "",
            "purpose": "",
            "prerequisites": ""
        }

    prompt = f"""
You are a professional technical writer.

Generate user manual sections.

FRS:
{frs}

Output:
Title: (max 6 words)
Introduction: (3-4 lines)
Purpose: (2-3 lines)
Prerequisites: (bullet points)
"""

    output = call_groq(prompt)

    data = {
        "title": "",
        "introduction": "",
        "purpose": "",
        "prerequisites": ""
    }

    for line in output.split("\n"):
        if line.lower().startswith("title"):
            data["title"] = line.split(":",1)[-1].strip()
        elif line.lower().startswith("introduction"):
            data["introduction"] = line.split(":",1)[-1].strip()
        elif line.lower().startswith("purpose"):
            data["purpose"] = line.split(":",1)[-1].strip()
        elif line.lower().startswith("prerequisites"):
            data["prerequisites"] = line.split(":",1)[-1].strip()

    return data