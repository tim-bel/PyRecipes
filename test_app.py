import unittest
from unittest.mock import patch, MagicMock
import tkinter as tk
from app import PantryPal

class TestApp(unittest.TestCase):
    @patch('app.PantryPal.create_meal_planner_widgets')
    @patch('app.PantryPal.create_recipe_widgets')
    @patch('app.PantryPal.create_shopping_list_widgets')
    @patch('app.PantryPal.create_menu')
    @patch('tkinter.ttk.Notebook')
    @patch('app.create_connection')
    @patch('app.initialize_database')
    @patch('ttkthemes.ThemedTk')
    def setUp(self, mock_themed_tk, mock_initialize_database, mock_create_connection, mock_notebook, mock_create_menu, mock_create_shopping_list_widgets, mock_create_recipe_widgets, mock_create_meal_planner_widgets):
        # Mock the __init__ method of PantryPal to avoid running tkinter code
        with patch.object(PantryPal, '__init__', lambda x: None):
            self.app = PantryPal()
            self.app.conn = mock_create_connection.return_value
            self.app.notebook = mock_notebook.return_value

    @patch('tkinter.Toplevel')
    def test_view_recipe_grid_configure(self, mock_toplevel):
        # Create a mock for the view_window
        mock_view_window = MagicMock()
        mock_toplevel.return_value = mock_view_window

        # Mock the database cursor and fetchone to return a dummy recipe
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ('Test Recipe', 'Ingredient 1, Ingredient 2', 'Step 1. Step 2.', 'Test Category')

        # We need to mock the connection and cursor attributes on the app instance
        self.app.conn = MagicMock()
        self.app.conn.cursor.return_value = mock_cursor

        # Mock the recipe_tree to have a selected item
        self.app.recipe_tree = MagicMock()
        self.app.recipe_tree.focus.return_value = 'some_item'
        self.app.recipe_tree.item.return_value = [1] # Mocking the return value of item selection

        # Call the view_recipe method
        self.app.view_recipe()

        # Assert that grid_columnconfigure and grid_rowconfigure were called with the correct arguments
        mock_view_window.grid_columnconfigure.assert_called_with(1, weight=1)
        mock_view_window.grid_rowconfigure.assert_called_with(3, weight=1)

if __name__ == '__main__':
    unittest.main()
