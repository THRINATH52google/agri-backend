# tools/finance_info.py
import asyncio

import requests
from langchain.tools import tool

import os
import json  # To potentially parse structured JSON if Grok supports it

# Configuration for Grok (assuming these are loaded from .env or config)
GROK_API_KEY = os.getenv("GROQ_API_KEY")
GROK_API_URL = "https://api.x.ai/v1/chat/completions"  # Confirm with Grok API docs
GROK_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"  # Use the model suitable for detailed information


async def call_grok_api(prompt: str, temperature: float = 0.5, max_tokens: int = 1000) -> str:
    print("data", prompt)
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
            {"role": "system",
             "content": "You are a helpful AI assistant specializing in Indian agriculture, financial schemes, and government policies. Provide precise, actionable, and up-to-date information. If exact real-time data or application deadlines are not known, advise the user where to find them (e.g., official government portals, local agriculture offices, banks)."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        response = requests.post(GROK_API_URL, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
        grok_response = response.json()
        return grok_response["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"Error connecting to Grok API: {e}. Please check your internet connection or API setup."
    except KeyError:
        return "Error: Could not parse Grok API response. Unexpected format."
    except Exception as e:
        return f"An unexpected error occurred while calling Grok: {e}"


def get_finance_info(query: str) -> str:
    """Get finance information for farmers"""
    query_lower = query.lower()

    if "loan" in query_lower:
        return "💰 **Agricultural Loans Available:**\n\n" \
               "🏦 **Kisan Credit Card (KCC):**\n" \
               "- Up to ₹3 lakhs for crop production\n" \
               "- Interest rate: 7% (with interest subvention)\n" \
               "- Apply at: Any commercial bank or cooperative bank\n\n" \
               "🌾 **PM-KISAN:**\n" \
               "- ₹6,000 per year in 3 installments\n" \
               "- Direct benefit transfer\n" \
               "- Apply at: pmkisan.gov.in\n\n" \
               "️ **PM Fasal Bima Yojana:**\n" \
               "- Crop insurance at low premium\n" \
               "- Covers natural calamities\n" \
               "- Apply at: pmfby.gov.in\n\n" \
               " **For more details:** Contact your nearest bank or visit agricultural department office."

    elif "subsidy" in query_lower:
        return "🎯 **Agricultural Subsidies:**\n\n" \
               "🚜 **Farm Mechanization:**\n" \
               "- 50-80% subsidy on farm equipment\n" \
               "- Tractors, harvesters, seed drills\n\n" \
               " **Irrigation:**\n" \
               "- Drip irrigation: 55% subsidy\n" \
               "- Sprinkler systems: 50% subsidy\n\n" \
               " **Seeds and Fertilizers:**\n" \
               "- Quality seeds: 50% subsidy\n" \
               "- Organic farming: 25% subsidy\n\n" \
               "📋 **Apply at:** State agricultural department or Krishi Vigyan Kendra"

    else:
        return "💰 **Financial Support for Farmers:**\n\n" \
               "1. **Loans:** Kisan Credit Card, PM-KISAN\n" \
               "2. **Insurance:** PM Fasal Bima Yojana\n" \
               "3. **Subsidies:** Equipment, irrigation, seeds\n" \
               "4. **Grants:** State-specific schemes\n\n" \
               "💡 **Ask me specifically about:**\n" \
               "- Agricultural loans\n" \
               "- Subsidies\n" \
               "- Insurance schemes\n" \
               "- State-specific benefits"


def get_finance_info_tool(query: str) -> str:
    """Tool wrapper for finance info"""
    return get_finance_info(query)