import os
from groq import Groq

client = Groq(api_key="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")

def call_groq(prompt: str) -> str:
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.5
    )
    return response.choices[0].message.content.strip()