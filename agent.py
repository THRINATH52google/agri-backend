# backend/agent.py
from langchain.agents import initialize_agent, Tool,AgentType
from langchain_openai import ChatOpenAI
from tools.weather import get_weather_forecast
from tools.crop_advisory import get_crop_advice
from tools.finance_info import get_finance_info, get_finance_info_tool
from tools.policy_finder import get_policy, get_ploicy_info_tool
from starlette.concurrency import run_in_threadpool
from langchain_groq import ChatGroq
from deep_translator import GoogleTranslator


import os
from dotenv import load_dotenv
load_dotenv()

groq_key=""

# llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo", openai_api_key=OPENAI_API_KEY)
llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",  # blazing fast GPT-4-level model
    api_key=groq_key,
)

tools = [
    Tool(name="WeatherTool", func=get_weather_forecast, description="Get weather forecast by location"),
    Tool(name="CropAdvisoryTool", func=get_crop_advice, description="Get crop advice for conditions"),
    Tool(name="FinanceTool", func=get_finance_info_tool, description="Find finance or credit info"),
    Tool(name="PolicyTool", func=get_ploicy_info_tool, description="Find relevant government schemes"),
]

# agent = initialize_agent(tools, llm, agent="zero-shot-react-description", verbose=True)
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
)

async def run_agent(query: str, language: str = "en") -> str:
    try:
        # Step 1: Translate the user's query to English
        if language != "en":
            translated_query = GoogleTranslator(source=language, target="en").translate(query)
        else:
            translated_query = query

        # Step 2: Run the agent with the translated English query
        english_response = await run_in_threadpool(agent.run, translated_query)

        # Step 3: Translate the agent's response back to the user's language
        if language != "en":
            final_response = GoogleTranslator(source="en", target=language).translate(english_response)
        else:
            final_response = english_response

        return final_response

    except Exception as e:
        return f"❌ Translation/Agent error: {str(e)}"
