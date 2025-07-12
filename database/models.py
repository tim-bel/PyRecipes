class ShoppingListItem:
    CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS shopping_list (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        quantity TEXT,
        brand TEXT,
        instructions TEXT,
        category TEXT,
        purchased BOOLEAN NOT NULL CHECK (purchased IN (0, 1))
    );
    """

class Recipe:
    CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        ingredients TEXT NOT NULL,
        instructions TEXT NOT NULL,
        category TEXT,
        image_path TEXT
    );
    """

class MealPlanItem:
    CREATE_TABLE = """
    CREATE TABLE IF NOT EXISTS meal_plan (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        meal_type TEXT NOT NULL,
        recipe_id INTEGER,
        FOREIGN KEY (recipe_id) REFERENCES recipes (id)
    );
    """
