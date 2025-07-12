import requests
from bs4 import BeautifulSoup
import json

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

        name = json_data.get("name", "N/A")
        ingredients = json_data.get("recipeIngredient", [])
        instructions = [step["text"] for step in json_data.get("recipeInstructions", [])]

    except (AttributeError, json.JSONDecodeError):
        name = "N/A"
        ingredients = []
        instructions = []

    return {"name": name, "ingredients": ingredients, "instructions": instructions}
