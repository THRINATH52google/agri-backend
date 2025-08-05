import requests
import base64
from typing import Dict, List
import io
from PIL import Image
import numpy as np


def detect_plant_disease(leaf_description: str = "", image_data: bytes = None) -> str:
    """
    Detect plant disease based on leaf description and/or image.
    This is a rule-based system that can be enhanced with ML models later.
    """

    # Common plant diseases and their symptoms
    diseases = {
        "leaf_blight": {
            "symptoms": ["brown spots", "yellow leaves", "blight", "spots on leaves", "leaf spots", "brown patches"],
            "description": "Leaf blight is a common fungal disease that causes brown or yellow spots on leaves.",
            "pesticides": [
                "Mancozeb 75% WP (2-3 g/liter water)",
                "Copper oxychloride 50% WP (3 g/liter water)",
                "Chlorothalonil 75% WP (2 g/liter water)"
            ],
            "application": "Spray every 7-10 days. Apply early morning or evening."
        },
        "powdery_mildew": {
            "symptoms": ["white powder", "powdery", "mildew", "white spots", "fungal growth", "white patches"],
            "description": "Powdery mildew appears as white powdery spots on leaves and stems.",
            "pesticides": [
                "Sulfur 80% WP (3 g/liter water)",
                "Dinocap 48% EC (2 ml/liter water)",
                "Hexaconazole 5% EC (2 ml/liter water)"
            ],
            "application": "Spray every 5-7 days. Avoid spraying in hot weather."
        },
        "rust": {
            "symptoms": ["rust", "orange spots", "red spots", "rusty spots", "orange powder", "reddish brown"],
            "description": "Rust disease causes orange or reddish-brown spots on leaves.",
            "pesticides": [
                "Mancozeb 75% WP (2-3 g/liter water)",
                "Propiconazole 25% EC (1 ml/liter water)",
                "Tebuconazole 25% EC (1 ml/liter water)"
            ],
            "application": "Spray every 10-14 days. Apply preventive sprays."
        },
        "bacterial_blight": {
            "symptoms": ["water soaked", "bacterial", "blight", "wilting", "dark spots", "black spots"],
            "description": "Bacterial blight causes water-soaked lesions and wilting.",
            "pesticides": [
                "Copper oxychloride 50% WP (3 g/liter water)",
                "Streptomycin sulfate (500 ppm)",
                "Kasugamycin 3% SL (2 g/liter water)"
            ],
            "application": "Spray every 5-7 days. Remove infected plant parts."
        },
        "aphids": {
            "symptoms": ["small insects", "aphids", "sticky leaves", "curled leaves", "honeydew", "tiny bugs"],
            "description": "Aphids are small insects that suck plant sap and cause leaf curling.",
            "pesticides": [
                "Imidacloprid 17.8% SL (0.5 ml/liter water)",
                "Acephate 75% SP (1 g/liter water)",
                "Dimethoate 30% EC (2 ml/liter water)"
            ],
            "application": "Spray every 7-10 days. Apply to both sides of leaves."
        },
        "thrips": {
            "symptoms": ["silver streaks", "thrips", "silver spots", "deformed leaves", "silver patches"],
            "description": "Thrips cause silver streaks and deformed leaves.",
            "pesticides": [
                "Spinosad 45% SC (0.5 ml/liter water)",
                "Fipronil 5% SC (1 ml/liter water)",
                "Acephate 75% SP (1 g/liter water)"
            ],
            "application": "Spray every 5-7 days. Apply in evening hours."
        }
    }

    # Analyze the description
    description_lower = leaf_description.lower() if leaf_description else ""

    # Image analysis
    image_analysis = ""
    detected_diseases_from_image = []

    if image_data:
        try:
            image = Image.open(io.BytesIO(image_data))
            image = image.convert('RGB')

            # Convert to numpy array for analysis
            img_array = np.array(image)

            # Basic color analysis
            red_channel = img_array[:, :, 0]
            green_channel = img_array[:, :, 1]
            blue_channel = img_array[:, :, 2]

            # Calculate average colors
            avg_red = np.mean(red_channel)
            avg_green = np.mean(green_channel)
            avg_blue = np.mean(blue_channel)

            # Simple color-based disease detection
            if avg_red > 150 and avg_green < 100 and avg_blue < 100:
                image_analysis = "Image analysis suggests reddish/brownish spots or patches, possibly indicating rust disease or leaf blight."
                detected_diseases_from_image = ["rust", "leaf_blight"]
            elif avg_red < 100 and avg_green < 100 and avg_blue > 150:
                image_analysis = "Image analysis suggests dark spots or patches, possibly indicating bacterial blight or fungal infection."
                detected_diseases_from_image = ["bacterial_blight"]
            elif avg_red > 200 and avg_green > 200 and avg_blue > 200:
                image_analysis = "Image analysis suggests white or light patches, possibly indicating powdery mildew."
                detected_diseases_from_image = ["powdery_mildew"]
            elif avg_green > 150 and avg_red < 100 and avg_blue < 100:
                image_analysis = "Image analysis suggests healthy green leaves with some variations."
                detected_diseases_from_image = []
            else:
                image_analysis = "Image analysis shows mixed colors, suggesting possible disease symptoms or natural leaf variations."
                detected_diseases_from_image = ["leaf_blight", "bacterial_blight"]  # Default to common issues

        except Exception as e:
            image_analysis = f"Image analysis failed: {str(e)}"

    # Find matching diseases based on description and image analysis
    detected_diseases = []

    # First, check diseases detected from image
    for disease_name in detected_diseases_from_image:
        if disease_name in diseases:
            detected_diseases.append((disease_name, diseases[disease_name]))

    # Then, check diseases based on text description
    combined_text = description_lower + " " + image_analysis.lower()

    for disease_name, disease_info in diseases.items():
        # Skip if already detected from image
        if any(d[0] == disease_name for d in detected_diseases):
            continue

        for symptom in disease_info["symptoms"]:
            if symptom in combined_text:
                detected_diseases.append((disease_name, disease_info))
                break

    # Remove duplicates while preserving order
    seen = set()
    unique_diseases = []
    for disease in detected_diseases:
        if disease[0] not in seen:
            seen.add(disease[0])
            unique_diseases.append(disease)

    detected_diseases = unique_diseases

    if not detected_diseases:
        response = "🔍 **Disease Detection Results:**\n\n"

        if image_data:
            response += f"📸 **Image Analysis:** {image_analysis}\n\n"

        response += "❌ **No specific disease detected.**\n\n"
        response += "💡 **Please provide more details about:**\n"
        response += "- Leaf color changes\n"
        response += "- Spots or marks on leaves\n"
        response += "- Any visible insects\n"
        response += "- Leaf texture changes\n"
        response += "- Plant wilting or drooping\n\n"
        response += "🌱 **General care tips:**\n"
        response += "- Ensure proper spacing between plants\n"
        response += "- Avoid overhead watering\n"
        response += "- Remove infected leaves\n"
        response += "- Maintain good air circulation"

        return response

    # Build response
    response = "🔬 **Disease Detection Results:**\n\n"

    if image_data:
        response += f"📸 **Image Analysis:** {image_analysis}\n\n"

    for disease_name, disease_info in detected_diseases:
        response += f" **Detected Disease:** {disease_name.replace('_', ' ').title()}\n"
        response += f" **Description:** {disease_info['description']}\n\n"

        response += "💊 **Recommended Pesticides:**\n"
        for i, pesticide in enumerate(disease_info['pesticides'], 1):
            response += f"{i}. {pesticide}\n"

        response += f"\n📋 **Application Method:** {disease_info['application']}\n\n"

    response += "⚠️ **Safety Precautions:**\n"
    response += "- Wear protective clothing and mask\n"
    response += "- Apply pesticides in calm weather\n"
    response += "- Keep children and pets away\n"
    response += "- Follow label instructions strictly\n"
    response += "- Store pesticides safely\n\n"

    response += "🌿 **Prevention Tips:**\n"
    response += "- Use disease-resistant varieties\n"
    response += "- Practice crop rotation\n"
    response += "- Maintain proper plant nutrition\n"
    response += "- Regular monitoring and early detection\n\n"

    response += "📞 **For expert advice:** Contact your local agricultural extension office"

    return response


def get_disease_detection_tool(description: str) -> str:
    """Tool wrapper for disease detection"""
    return detect_plant_disease(description)