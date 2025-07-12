import requests
from bs4 import BeautifulSoup
import json
import re
import html

def clean_text(text):
    """Cleans text by removing HTML tags, extra whitespace, and decoding HTML entities."""
    if not text:
        return ""
    # Decode HTML entities
    text = html.unescape(text)
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Replace multiple whitespace characters with a single space
    text = re.sub(r'\s+', ' ', text).strip()
    # Remove "Recipe - Food.com" from the end of the string
    text = text.replace(" Recipe - Food.com", "")
    return text

def scrape_recipe(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

    soup = BeautifulSoup(response.content, "html.parser")

    try:
        script_tag = soup.find("script", type="application/ld+json")
        json_data = json.loads(script_tag.string)

        name = clean_text(json_data.get("name", "N/A"))
        ingredients = [clean_text(ing) for ing in json_data.get("recipeIngredient", [])]
        instructions = [clean_text(step["text"]) for step in json_data.get("recipeInstructions", [])]

    except (AttributeError, json.JSONDecodeError):
        name = "N/A"
        ingredients = []
        instructions = []

    return {"name": name, "ingredients": ingredients, "instructions": instructions}
