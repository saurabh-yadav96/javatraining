def build_prompt(context, query):
    return f"""
You are a senior product documentation expert.

Context:
{context}

Task:
{query}

Generate:
1. Feature Overview
2. Step-by-step user guide
3. Field descriptions
4. Validations
5. Error messages
6. Edge cases

Make it simple for non-technical users.
"""