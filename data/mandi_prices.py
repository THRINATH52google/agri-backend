# data/mandi_prices.py
from typing import Dict

def get_mandi_prices(crop: str) -> Dict:
    prices = {
        "wheat": {"min": 1800, "max": 2000},
        "rice": {"min": 1500, "max": 1800},
        "cotton": {"min": 5000, "max": 5500}
    }

    return prices.get(crop.lower(), {"min": 0, "max": 0})
