from typing import List, Dict
from app.services.ai_service import call_groq

def format_steps(steps: List[Dict]) -> str:
    result = []
    for step in steps:
        if step.get("type") == "click":
            result.append(f"User clicks {step.get('text','button')}")
        elif step.get("type") == "input":
            result.append(f"User enters {step.get('field','value')}")
    return "\n".join(result)


def generate_steps(actions: str) -> List[str]:
    prompt = f"""
You are a professional technical writer.

Convert the following actions into structured user manual steps.

Rules:
- Each step must have a clear title and explanation
- Explain what user should do
- Explain what happens after action
- Use professional tone
- Avoid robotic phrases like "click button"

Actions:
{actions}

Format:
Step 1: Title
Description: ...
"""
    output = call_groq(prompt)

    steps = []
    current = ""
            
    for line in output.split("\n"):
        line = line.strip()

    if line.lower().startswith("step"):
        if current:
            steps.append(current.strip())
        current = line
    else:
        current += " " + line

    if current:
        steps.append(current.strip())

    return steps