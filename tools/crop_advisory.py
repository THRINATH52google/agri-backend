from typing import Dict
import requests
from datetime import datetime


# Original function
def get_crop_advice_logic(soil_type: str, rainfall: float, temperature: float) -> Dict:
    if soil_type.lower() in ['loamy', 'sandy'] and 20 <= temperature <= 30:
        if rainfall >= 300:
            crop = "Rice"
        else:
            crop = "Millets"
    elif soil_type.lower() in ['clay', 'black']:
        crop = "Cotton"
    else:
        crop = "Pulses"

    return {
        "recommended_crop": crop,
        "reason": f"Based on soil ({soil_type}), rainfall ({rainfall}mm), and temperature ({temperature}°C)"
    }


# LangChain-compatible wrapper
def get_crop_advice(input_str: str) -> str:
    """
    Get crop advice based on location and conditions.
    Can handle queries like:
    - "what crop is suitable here to harvest"
    - "crop advice for Mumbai"
    - "soil_type=loamy, rainfall=250, temperature=28"
    """
    input_lower = input_str.lower().strip()

    # Check if it's a general question without specific data
    if any(keyword in input_lower for keyword in ["what crop", "suitable crop", "harvest", "plant"]):
        if "here" in input_lower or "location" not in input_lower:
            return "🌱 To provide crop advice, I need to know your location (city, village, or district). Please tell me where you are located so I can check the weather and soil conditions for that area."

    # Check if location is provided
    if any(keyword in input_lower for keyword in
           ["mumbai", "delhi", "bangalore", "chennai", "kolkata", "pune", "hyderabad", "ahmedabad"]):
        # For now, provide general advice based on common conditions
        return f"🌾 Based on typical conditions in {input_str}, here are some crop recommendations:\n\n" \
               f"**Kharif Season (June-October):**\n" \
               f"- Rice, Maize, Cotton, Sugarcane\n\n" \
               f"**Rabi Season (November-March):**\n" \
               f"- Wheat, Barley, Mustard, Peas\n\n" \
               f"**Summer Season (March-June):**\n" \
               f"- Vegetables, Pulses, Oilseeds\n\n" \
               f"💡 For more specific advice, please provide:\n" \
               f"- Current soil type\n" \
               f"- Expected rainfall\n" \
               f"- Temperature range\n" \
               f"- Season you want to plant in"

    # Handle structured input (soil_type=loamy, rainfall=250, temperature=28)
    if "=" in input_str:
        try:
            parts = dict(
                part.strip().split("=")
                for part in input_str.split(",")
            )
            soil = parts.get("soil_type", "unknown")
            rain = float(parts.get("rainfall", 0))
            temp = float(parts.get("temperature", 25))

            # Enhanced crop recommendation logic
            if soil.lower() in ['loamy', 'sandy'] and 20 <= temp <= 30:
                if rain >= 300:
                    crop = "Rice"
                    reason = "High rainfall and moderate temperature are ideal for rice cultivation"
                else:
                    crop = "Millets"
                    reason = "Moderate rainfall and temperature suitable for drought-resistant millets"
            elif soil.lower() in ['clay', 'black']:
                crop = "Cotton"
                reason = "Clay soil retains moisture well, suitable for cotton"
            elif temp > 30:
                crop = "Pulses and Oilseeds"
                reason = "High temperature conditions favor pulses and oilseeds"
            else:
                crop = "Mixed Cropping (Pulses + Cereals)"
                reason = "Versatile conditions allow for mixed cropping"

            return f"🌾 **Recommended Crop:** {crop}\n\n" \
                   f"📊 **Analysis:**\n" \
                   f"- Soil Type: {soil}\n" \
                   f"- Rainfall: {rain}mm\n" \
                   f"- Temperature: {temp}°C\n\n" \
                   f"💡 **Reason:** {reason}\n\n" \
                   f"🔍 **Additional Tips:**\n" \
                   f"- Check local market prices before finalizing\n" \
                   f"- Consider crop rotation for soil health\n" \
                   f"- Consult local agricultural extension office"

        except Exception as e:
            return f"❌ Error processing crop advice: {str(e)}\n\nPlease provide information in format: soil_type=type, rainfall=amount, temperature=value"

    # Default response for unclear queries
    return "🌱 I'd be happy to help with crop advice! Please provide:\n\n" \
           "1. **Location** (city, village, or district)\n" \
           "2. **Season** you want to plant in\n" \
           "3. **Soil type** (if known)\n" \
           "4. **Water availability**\n\n" \
           "Or ask me about weather for your location first!"
