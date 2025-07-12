import unittest
from scraper import scrape_recipe

class TestScraper(unittest.TestCase):
    def test_scrape_recipe(self):
        url = "https://www.food.com/recipe/frans-fruit-salad-32442"
        recipe_data = scrape_recipe(url)

        self.assertIsNotNone(recipe_data)
        self.assertEqual(recipe_data["name"], "Fran's Fruit Salad")
        self.assertIn("1 can fruit cocktail", recipe_data["ingredients"])
        self.assertIn("Drain fruit cocktail, mandarin orange,coconut gel,kaong set aside.", recipe_data["instructions"])

if __name__ == "__main__":
    unittest.main()
