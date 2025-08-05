# tools/policy_finder.py
import os
import requests
from langchain.utilities import asyncio
from langchain_core.tools import tool

# Groq Configuration
GROK_API_KEY = os.getenv("grok")  # Replace default for testing
GROK_API_URL = "https://api.x.ai/v1/chat/completions"
GROK_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

async def call_grok_api(prompt: str, temperature: float = 0.5, max_tokens: int = 1000) -> str:
    """Helper to call Groq API."""
    if not GROK_API_KEY:
        return "Error: Groq API key not configured."

    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": GROK_MODEL,
        "messages": [
            {"role": "system", "content": "You are an expert in Indian agricultural policies and government schemes. Answer in a helpful, direct, and updated manner. Be region-aware."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(GROK_API_URL, headers=headers, json=data)
        response.raise_for_status()
        grok_response = response.json()
        return grok_response["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Grok API: {e}"
    except KeyError:
        return "Error: Grok API returned an unexpected response."
    except Exception as e:
        return f"Unexpected error: {e}"

async def get_policy(query: str, state: str = "India") -> str:
    """
    Uses Groq to provide precise agricultural policy and scheme information for a state or query.
    """
    prompt = (
        f"A farmer from {state} is asking: \"{query}\"\n"
        "Please provide:\n"
        "- Applicable government policies and schemes (central + state)\n"
        "- Benefits\n"
        "- Eligibility (if known)\n"
        "- Where to apply (websites, bank, or agriculture office)\n"
        "- Be specific. Mention yojanas like PMFBY, PM-KISAN, or state-specific like Rythu Bandhu.\n"
        "Use bullet points or headings. If deadlines or portals are unknown, guide the user to official websites or local offices."
    )
    return await call_grok_api(prompt)

@tool
def get_ploicy_info_tool(query: str, location: str = "India") -> str:
    """
    Tool to get financial scheme information for farmers.
    """
    async def inner():
        return await get_policy(query, location)

    try:
        return asyncio.run(inner())
    except Exception as e:
        return f"Error while retrieving finance info: {e}"