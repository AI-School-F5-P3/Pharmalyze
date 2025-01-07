# product_search/utils.py
from openai import OpenAI
from django.conf import settings
from typing import Tuple, List, Dict, Any
from pathlib import Path
import json

def process_query(query: str) -> Tuple[str, float]:
    """Determine query type and confidence score"""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    system_prompt = """You are a query classifier for a pharmacy product search system.
    Analyze the query and determine if it's:
    1. Product-related (searching for specific products or categories)
    2. Knowledge-related (asking for medical/technical information)
    
    Respond in JSON format:
    {
        "type": "product|knowledge",
        "confidence": 0.0-1.0,
        "reasoning": "brief explanation"
    }"""
    
    user_prompt = f"Query: {query}"
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        response_format={"type": "json_object"}
    )
    
    result = response.choices[0].message.content
    classification = json.loads(result)
    
    return classification["type"], classification["confidence"]

def scan_product_images():
    """Scan the product images directory and return categorized images"""
    base_path = Path(settings.MEDIA_ROOT) / 'images' / 'Dietetica' / 'Adelgazar'
    categories = [
        'celulitis', 'dieta', 'drenante', 'edulcorantes',
        'inhibidores_de_absorcion', 'laxantes', 'quemagrasas', 'saciante'
    ]
    
    product_images = {}
    for category in categories:
        category_path = base_path / category
        if category_path.exists():
            product_images[category] = [
                str(file.relative_to(settings.MEDIA_ROOT))
                for file in category_path.glob('*')
                if file.suffix.lower() in ['.jpg', '.jpeg', '.png']
            ]
    
    return product_images

def analyze_image(image_path: str) -> Dict[str, Any]:
    """Analyze product image using GPT-4 Vision"""
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    with open(image_path, 'rb') as image_file:
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this product image and extract: product name, main ingredients, intended use, and any notable visual elements."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64.b64encode(image_file.read()).decode()}"
                            }
                        }
                    ]
                }
            ]
        )
    
    return json.loads(response.choices[0].message.content)