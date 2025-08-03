# data/gov_scheme_loader.py
import json
from typing import List, Dict

def load_government_schemes() -> List[Dict]:
    try:
        with open("backend/data/schemes.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return [{"name": "PM-KISAN", "benefit": "Income support to all landholding farmers"}]
