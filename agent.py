# backend/agent.py
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.memory import ConversationBufferWindowMemory
from tools.weather import get_weather_forecast
from tools.crop_advisory import get_crop_advice
from tools.finance_info import get_finance_info_tool
from tools.policy_finder import get_policy_info_tool
from starlette.concurrency import run_in_threadpool
from langchain_groq import ChatGroq
from deep_translator import GoogleTranslator
from datetime import datetime
from typing import Dict, List, Tuple

from dotenv import load_dotenv

load_dotenv()

groq_key = ""

llm = ChatGroq(
    model="meta-llama/llama-4-scout-17b-16e-instruct",
    api_key=groq_key,
)

tools = [
    Tool(name="WeatherTool", func=get_weather_forecast,
         description="Get weather forecast by location. Use this when user asks about weather or when crop advice needs location-specific weather data."),
    Tool(name="CropAdvisoryTool", func=get_crop_advice,
         description="Get crop advice based on location, soil, weather conditions. Use this for questions about what crops to plant, harvest timing, or farming advice."),
    Tool(name="FinanceTool", func=get_finance_info_tool,
         description="Find finance information, loans, subsidies, and credit options for farmers. Use this for financial queries."),
    Tool(name="PolicyTool", func=get_policy_info_tool,
         description="Find relevant government schemes, policies, and agricultural programs. Use this for policy-related questions."),
]


def create_new_conversation() -> Dict:
    """Create a new conversation with memory"""
    memory = ConversationBufferWindowMemory(
        k=10,  # Keep last 10 exchanges
        return_messages=True,
        memory_key="chat_history"
    )

    return {
        "memory": memory,
        "created_at": datetime.now(),
        "last_activity": datetime.now(),
        "conversation_history": []
    }


def create_agent_with_memory(memory: ConversationBufferWindowMemory):
    """Create an agent with conversation memory"""
    return initialize_agent(
        tools,
        llm,
        agent=AgentType.CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        memory=memory,
        handle_parsing_errors=True,
        max_iterations=5,
        agent_kwargs={
            "system_message": """You are an expert agricultural advisor helping Indian farmers. Your role is to:

1. **Always be helpful and informative** - Provide detailed, practical advice
2. **Ask for missing information** - If a user asks about crops but doesn't provide location, ask them to specify their location
3. **Use appropriate tools** - Use weather tool for location-specific weather, crop advisory for farming advice, finance tool for money matters, policy tool for government schemes
4. **Provide context-aware responses** - Consider the conversation history and previous questions
5. **Be encouraging and supportive** - Farming is challenging, so be positive and motivating
6. **Give actionable advice** - Provide specific, implementable recommendations
7. **Mention relevant schemes** - Always inform about applicable government programs

Remember: If someone asks "what crop is suitable here" without specifying location, ask them to provide their location first, then use the weather and crop advisory tools to give specific recommendations."""
        }
    )


async def run_agent_with_memory(
        query: str,
        conversation_data: Dict,
        language: str = "en"
) -> Tuple[str, List[Dict]]:
    """
    Run agent with conversation memory
    Returns: (response, conversation_history)
    """
    try:
        # Update last activity
        conversation_data["last_activity"] = datetime.now()

        # Get memory from conversation
        memory = conversation_data["memory"]

        # Create agent with memory
        agent = create_agent_with_memory(memory)

        # Step 1: Translate the user's query to English if needed
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

        # Step 4: Update conversation history
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_message": query,
            "user_language": language,
            "agent_response": final_response,
            "english_query": translated_query,
            "english_response": english_response
        }

        conversation_data["conversation_history"].append(conversation_entry)

        return final_response, conversation_data["conversation_history"]

    except Exception as e:
        error_response = f"❌ Translation/Agent error: {str(e)}"
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_message": query,
            "user_language": language,
            "agent_response": error_response,
            "english_query": query,
            "english_response": error_response,
            "error": str(e)
        }

        conversation_data["conversation_history"].append(conversation_entry)
        return error_response, conversation_data["conversation_history"]


# Keep the old function for backward compatibility
async def run_agent(query: str, language: str = "en") -> str:
    """Legacy function for backward compatibility"""
    try:
        # Step 1: Translate the user's query to English
        if language != "en":
            translated_query = GoogleTranslator(source=language, target="en").translate(query)
        else:
            translated_query = query

        # Step 2: Run the agent with the translated English query
        agent = initialize_agent(
            tools,
            llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
        )
        english_response = await run_in_threadpool(agent.run, translated_query)

        # Step 3: Translate the agent's response back to the user's language
        if language != "en":
            final_response = GoogleTranslator(source="en", target=language).translate(english_response)
        else:
            final_response = english_response

        return final_response

    except Exception as e:
        return f"❌ Translation/Agent error: {str(e)}"

