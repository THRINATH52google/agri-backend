# tools/finance_info.py
import asyncio

import requests
from langchain.tools import tool

import os
import json # To potentially parse structured JSON if Grok supports it

# Configuration for Grok (assuming these are loaded from .env or config)
GROK_API_KEY = os.getenv("grok")
GROK_API_URL = "https://api.x.ai/v1/chat/completions" # Confirm with Grok API docs
GROK_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct" # Use the model suitable for detailed information

async def call_grok_api(prompt: str, temperature: float = 0.5, max_tokens: int = 1000) -> str:
    print("data",prompt)
    """Helper function to call the Grok API."""
    if not GROK_API_KEY:
        return "Error: Grok API key not configured."

    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": GROK_MODEL,
        "messages": [
            {"role": "system", "content": "You are a helpful AI assistant specializing in Indian agriculture, financial schemes, and government policies. Provide precise, actionable, and up-to-date information. If exact real-time data or application deadlines are not known, advise the user where to find them (e.g., official government portals, local agriculture offices, banks)."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(GROK_API_URL, headers=headers, json=data)
        response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
        grok_response = response.json()
        return grok_response["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Grok API: {e}. Please check your internet connection or API setup."
    except KeyError:
        return "Error: Could not parse Grok API response. Unexpected format."
    except Exception as e:
        return f"An unexpected error occurred while calling Grok: {e}"

async def get_finance_info(query: str, location: str = "India") -> str:
    """
    Leverages Grok to return precise financial help information based on the user's query and location.
    This includes loan schemes, subsidy options, credit access, and crop loss compensation.
    """
    prompt = (
        f"As an expert in Indian agricultural finance, please provide precise and actionable information "
        f"for a farmer in {location} regarding the following query: '{query}'.\n\n"
        "Specifically, cover relevant government schemes, eligibility criteria (if general), application process overview, "
        "and where to find official, up-to-date details or apply (e.g., official websites, specific departments, banks). "
        "Prioritize information about **Pradhan Mantri Fasal Bima Yojana (PMFBY)** for crop loss, "
        "**Kisan Credit Card (KCC)** for loans, and major central/state subsidies (e.g., Rythu Bandhu for Telangana if applicable). "
        "If specific deadlines or very detailed application forms are not known, explicitly state that the farmer should check "
        "the official scheme portal or local agriculture office/bank.\n"
        "Format the response clearly with headings or bullet points. Avoid vague answers."
    )
    return await call_grok_api(prompt)

@tool
def get_finance_info_tool(query: str, location: str = "India") -> str:
    """
    Tool to get financial scheme information for farmers.
    """
    async def inner():
        return await get_finance_info(query, location)

    try:
        return asyncio.run(inner())
    except Exception as e:
        return f"Error while retrieving finance info: {e}"