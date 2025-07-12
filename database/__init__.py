from .models import ShoppingListItem, Recipe, MealPlanItem
from .database import create_connection, create_table

def initialize_database():
    conn = create_connection("pantrypal.db")
    if conn is not None:
        create_table(conn, ShoppingListItem.CREATE_TABLE)
        create_table(conn, Recipe.CREATE_TABLE)
        create_table(conn, MealPlanItem.CREATE_TABLE)
        conn.close()
    else:
        print("Error! cannot create the database connection.")
