from typing import Dict

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
    Expected input: "soil_type=loamy, rainfall=250, temperature=28"
    """
    try:
        parts = dict(
            part.strip().split("=")
            for part in input_str.split(",")
        )
        soil = parts["soil_type"]
        rain = float(parts["rainfall"])
        temp = float(parts["temperature"])
        result = get_crop_advice_logic(soil, rain, temp)
        return f"Recommended Crop: {result['recommended_crop']}\nReason: {result['reason']}"
    except Exception as e:
        return f"❌ Error parsing input: {e}"
