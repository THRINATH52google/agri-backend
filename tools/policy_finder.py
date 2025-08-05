# tools/policy_finder.py
import os
import requests
from langchain.utilities import asyncio
from langchain_core.tools import tool

# Groq Configuration
GROK_API_KEY = ""  # Replace default for testing
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
            {"role": "system",
             "content": "You are an expert in Indian agricultural policies and government schemes. Answer in a helpful, direct, and updated manner. Be region-aware."},
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


def get_policy(query: str) -> str:
    """Get government policy information for farmers"""
    query_lower = query.lower()

    if "pm-kisan" in query_lower or "kisan" in query_lower:
        return "🌾 **PM-KISAN Scheme:**\n\n" \
               "💰 **Benefits:** ₹6,000 per year in 3 installments\n" \
               "👥 **Eligibility:** Small and marginal farmers\n" \
               "📋 **Documents Required:**\n" \
               "- Aadhaar card\n" \
               "- Land records\n" \
               "- Bank account details\n" \
               "🌐 **Apply at:** pmkisan.gov.in\n" \
               "📞 **Helpline:** 155261"

    elif "insurance" in query_lower or "fasal bima" in query_lower:
        return "️ **PM Fasal Bima Yojana:**\n\n" \
               "📊 **Coverage:** Natural calamities, pests, diseases\n" \
               " **Premium:** 1.5-5% of sum insured\n" \
               " **Crops Covered:** Food grains, oilseeds, commercial crops\n" \
               "📋 **Apply at:** pmfby.gov.in or nearest bank\n" \
               "📅 **Deadline:** Varies by crop and season"

    elif "organic" in query_lower:
        return "🌱 **Organic Farming Schemes:**\n\n" \
               "💰 **PMKSY:** 25% subsidy on organic inputs\n" \
               " **PKVY:** Paramparagat Krishi Vikas Yojana\n" \
               "📋 **Apply at:** State agricultural department\n" \
               "🌐 **More info:** organic.gov.in"

    else:
        return "🏛️ **Government Agricultural Schemes:**\n\n" \
               "1. **PM-KISAN:** Direct income support\n" \
               "2. **PM Fasal Bima Yojana:** Crop insurance\n" \
               "3. **PMKSY:** Irrigation and water management\n" \
               "4. **PKVY:** Organic farming promotion\n" \
               "5. **State-specific schemes:** Check your state's agricultural portal\n\n" \
               "💡 **Ask me about specific schemes:**\n" \
               "- PM-KISAN\n" \
               "- Crop insurance\n" \
               "- Organic farming\n" \
               "- Irrigation schemes"


def get_policy_info_tool(query: str) -> str:
    """Tool wrapper for policy info"""
    return get_policy(query)