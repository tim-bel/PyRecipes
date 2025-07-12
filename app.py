import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from database import initialize_database, create_connection
import csv
from ttkthemes import ThemedTk
from scraper import scrape_recipe
main

class PantryPal(ThemedTk):
    def __init__(self):
        super().__init__(theme="arc")
        self.title("PantryPal")
        self.geometry("800x600")

        initialize_database()
        self.conn = create_connection("pantrypal.db")

        self.create_menu()

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(pady=10, padx=10, expand=True, fill="both")

        self.shopping_list_frame = ttk.Frame(self.notebook)
        self.recipes_frame = ttk.Frame(self.notebook)
        self.meal_planner_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.shopping_list_frame, text="Shopping List")
        self.notebook.add(self.recipes_frame, text="Recipes")
        self.notebook.add(self.meal_planner_frame, text="Meal Planner")

        self.create_shopping_list_widgets()
        self.create_recipe_widgets()
        self.create_meal_planner_widgets()
        self.load_shopping_list()
        self.load_recipes()
        self.load_meal_plan()

    def create_meal_planner_widgets(self):
        # Calendar view for meal planning
        self.calendar_frame = ttk.Frame(self.meal_planner_frame)
        self.calendar_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # For simplicity, we'll use a Treeview to represent the calendar
        self.meal_plan_tree = ttk.Treeview(self.calendar_frame, columns=("Date", "Meal Type", "Recipe"), show="headings")
        self.meal_plan_tree.pack(fill="both", expand=True)

        self.meal_plan_tree.heading("Date", text="Date")
        self.meal_plan_tree.heading("Meal Type", text="Meal Type")
        self.meal_plan_tree.heading("Recipe", text="Recipe")

        # Form to add a meal to the plan
        self.add_meal_frame = ttk.LabelFrame(self.meal_planner_frame, text="Add Meal to Plan", padding=(10, 5))
        self.add_meal_frame.pack(fill="x", expand="yes", padx=10, pady=5)

        ttk.Label(self.add_meal_frame, text="Date (YYYY-MM-DD):").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.meal_date_entry = ttk.Entry(self.add_meal_frame)
        self.meal_date_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(self.add_meal_frame, text="Meal Type:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.meal_type_entry = ttk.Entry(self.add_meal_frame)
        self.meal_type_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        ttk.Label(self.add_meal_frame, text="Recipe:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.recipe_combobox = ttk.Combobox(self.add_meal_frame, state="readonly")
        self.recipe_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.add_to_plan_button = ttk.Button(self.add_meal_frame, text="Add to Plan", command=self.add_to_meal_plan)
        self.add_to_plan_button.grid(row=3, column=1, padx=5, pady=5, sticky="e")

    def create_menu(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Backup to CSV", command=self.backup_to_csv)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.quit)

    def backup_to_csv(self):
        backup_dir = filedialog.askdirectory()
        if not backup_dir:
            return

        # Backup shopping list
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM shopping_list")
        with open(f"{backup_dir}/shopping_list_backup.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([i[0] for i in cursor.description])
            writer.writerows(cursor)

        # Backup recipes
        cursor.execute("SELECT * FROM recipes")
        with open(f"{backup_dir}/recipes_backup.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([i[0] for i in cursor.description])
            writer.writerows(cursor)

        # Backup meal plan
        cursor.execute("SELECT * FROM meal_plan")
        with open(f"{backup_dir}/meal_plan_backup.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([i[0] for i in cursor.description])
            writer.writerows(cursor)

        messagebox.showinfo("Backup Successful", f"Backup completed successfully in {backup_dir}")

    def create_recipe_widgets(self):
        # Entry form for adding new recipes
        self.recipe_entry_frame = ttk.LabelFrame(self.recipes_frame, text="Add Recipe", padding=(10, 5))
        self.recipe_entry_frame.pack(fill="x", expand="yes", padx=10, pady=5)

        self.recipe_name_label = ttk.Label(self.recipe_entry_frame, text="Name:")
        self.recipe_name_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.recipe_name_entry = ttk.Entry(self.recipe_entry_frame)
        self.recipe_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.ingredients_label = ttk.Label(self.recipe_entry_frame, text="Ingredients (comma-separated):")
        self.ingredients_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.ingredients_entry = ttk.Entry(self.recipe_entry_frame)
        self.ingredients_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.instructions_label_recipes = ttk.Label(self.recipe_entry_frame, text="Instructions:")
        self.instructions_label_recipes.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.instructions_entry_recipes = tk.Text(self.recipe_entry_frame, height=5, width=40)
        self.instructions_entry_recipes.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.recipe_category_label = ttk.Label(self.recipe_entry_frame, text="Category:")
        self.recipe_category_label.grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.recipe_category_entry = ttk.Entry(self.recipe_entry_frame)
        self.recipe_category_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        self.add_recipe_button = ttk.Button(self.recipe_entry_frame, text="Add Recipe", command=self.add_recipe)
        self.add_recipe_button.grid(row=4, column=1, padx=5, pady=5, sticky="e")

        self.scrape_recipe_button = ttk.Button(self.recipe_entry_frame, text="Scrape Recipe", command=self.scrape_and_fill_recipe)
        self.scrape_recipe_button.grid(row=4, column=0, padx=5, pady=5, sticky="w")

main
        # Treeview to display recipes
        self.recipe_tree = ttk.Treeview(self.recipes_frame, columns=("ID", "Name", "Category"), show="headings")
        self.recipe_tree.pack(fill="both", expand=True, padx=10, pady=5)

        self.recipe_tree.heading("ID", text="ID")
        self.recipe_tree.heading("Name", text="Name")
        self.recipe_tree.heading("Category", text="Category")
        self.recipe_tree.column("ID", width=30)

        # Buttons for managing recipes
        self.recipe_management_frame = ttk.Frame(self.recipes_frame)
        self.recipe_management_frame.pack(fill="x", expand="yes", padx=10, pady=5)

        self.view_recipe_button = ttk.Button(self.recipe_management_frame, text="View Recipe", command=self.view_recipe)
        self.view_recipe_button.pack(side="left", padx=5)
        self.edit_recipe_button = ttk.Button(self.recipe_management_frame, text="Edit Recipe", command=self.edit_recipe)
        self.edit_recipe_button.pack(side="left", padx=5)
        self.delete_recipe_button = ttk.Button(self.recipe_management_frame, text="Delete Recipe", command=self.delete_recipe)
        self.delete_recipe_button.pack(side="left", padx=5)
        self.add_to_shopping_list_button = ttk.Button(self.recipe_management_frame, text="Add to Shopping List", command=self.add_ingredients_to_shopping_list)
        self.add_to_shopping_list_button.pack(side="left", padx=5)

    def add_recipe(self):
        name = self.recipe_name_entry.get()
        ingredients = self.ingredients_entry.get()
        instructions = self.instructions_entry_recipes.get("1.0", "end-1c")
        category = self.recipe_category_entry.get()

        if not name or not ingredients or not instructions:
            messagebox.showerror("Error", "All recipe fields must be filled.")
            return

        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO recipes (name, ingredients, instructions, category) VALUES (?, ?, ?, ?)",
                       (name, ingredients, instructions, category))
        self.conn.commit()
        self.load_recipes()
        self.clear_recipe_entries()

    def load_recipes(self):
        for i in self.recipe_tree.get_children():
            self.recipe_tree.delete(i)

        cursor = self.conn.cursor()
        cursor.execute("SELECT id, name, category FROM recipes")
        rows = cursor.fetchall()
        for row in rows:
            self.recipe_tree.insert("", "end", values=row)

    def view_recipe(self):
        selected_item = self.recipe_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select a recipe to view.")
            return

        recipe_id = self.recipe_tree.item(selected_item, "values")[0]
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, ingredients, instructions, category FROM recipes WHERE id=?", (recipe_id,))
        recipe = cursor.fetchone()

        view_window = tk.Toplevel(self)
        view_window.title(f"View Recipe: {recipe[0]}")

        ttk.Label(view_window, text="Name:").grid(row=0, column=0, sticky="w")
        ttk.Label(view_window, text=recipe[0]).grid(row=0, column=1, sticky="w")

        ttk.Label(view_window, text="Category:").grid(row=1, column=0, sticky="w")
        ttk.Label(view_window, text=recipe[3]).grid(row=1, column=1, sticky="w")

        ttk.Label(view_window, text="Ingredients:").grid(row=2, column=0, sticky="w")
        ingredients_text = tk.Text(view_window, height=5, width=40)
        ingredients_text.grid(row=2, column=1, sticky="w")
        ingredients_text.insert("1.0", recipe[1])
        ingredients_text.config(state="disabled")

        ttk.Label(view_window, text="Instructions:").grid(row=3, column=0, sticky="w")
        instructions_text = tk.Text(view_window, height=10, width=40)
        instructions_text.grid(row=3, column=1, sticky="w")
        instructions_text.insert("1.0", recipe[2])
        instructions_text.config(state="disabled")

    def edit_recipe(self):
        selected_item = self.recipe_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select a recipe to edit.")
            return

        recipe_id = self.recipe_tree.item(selected_item, "values")[0]
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, ingredients, instructions, category FROM recipes WHERE id=?", (recipe_id,))
        recipe = cursor.fetchone()

        edit_window = tk.Toplevel(self)
        edit_window.title(f"Edit Recipe: {recipe[0]}")

        ttk.Label(edit_window, text="Name:").grid(row=0, column=0)
        name_entry = ttk.Entry(edit_window)
        name_entry.grid(row=0, column=1)
        name_entry.insert(0, recipe[0])

        ttk.Label(edit_window, text="Ingredients:").grid(row=1, column=0)
        ingredients_entry = ttk.Entry(edit_window)
        ingredients_entry.grid(row=1, column=1)
        ingredients_entry.insert(0, recipe[1])

        ttk.Label(edit_window, text="Instructions:").grid(row=2, column=0)
        instructions_entry = tk.Text(edit_window, height=5, width=40)
        instructions_entry.grid(row=2, column=1)
        instructions_entry.insert("1.0", recipe[2])

        ttk.Label(edit_window, text="Category:").grid(row=3, column=0)
        category_entry = ttk.Entry(edit_window)
        category_entry.grid(row=3, column=1)
        category_entry.insert(0, recipe[3])

        def update_recipe():
            new_name = name_entry.get()
            new_ingredients = ingredients_entry.get()
            new_instructions = instructions_entry.get("1.0", "end-1c")
            new_category = category_entry.get()

            if not new_name or not new_ingredients or not new_instructions:
                messagebox.showerror("Error", "All recipe fields must be filled.")
                return

            cursor = self.conn.cursor()
            cursor.execute("UPDATE recipes SET name=?, ingredients=?, instructions=?, category=? WHERE id=?",
                           (new_name, new_ingredients, new_instructions, new_category, recipe_id))
            self.conn.commit()
            self.load_recipes()
            edit_window.destroy()

        ttk.Button(edit_window, text="Update", command=update_recipe).grid(row=4, column=0, columnspan=2)

    def delete_recipe(self):
        selected_item = self.recipe_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select a recipe to delete.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this recipe?"):
            recipe_id = self.recipe_tree.item(selected_item, "values")[0]
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM recipes WHERE id=?", (recipe_id,))
            self.conn.commit()
            self.load_recipes()

    def add_ingredients_to_shopping_list(self):
        selected_item = self.recipe_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select a recipe.")
            return

        recipe_id = self.recipe_tree.item(selected_item, "values")[0]
        cursor = self.conn.cursor()
        cursor.execute("SELECT ingredients FROM recipes WHERE id=?", (recipe_id,))
        ingredients_str = cursor.fetchone()[0]
        ingredients = [ing.strip() for ing in ingredients_str.split(",")]

        for ingredient in ingredients:
            cursor.execute("INSERT INTO shopping_list (name, purchased) VALUES (?, ?)", (ingredient, 0))

        self.conn.commit()
        self.load_shopping_list()
        messagebox.showinfo("Success", "Ingredients added to shopping list.")

    def clear_recipe_entries(self):
        self.recipe_name_entry.delete(0, "end")
        self.ingredients_entry.delete(0, "end")
        self.instructions_entry_recipes.delete("1.0", "end")
        self.recipe_category_entry.delete(0, "end")


    def scrape_and_fill_recipe(self):
        url = simpledialog.askstring("Scrape Recipe", "Enter the URL of the recipe:")
        if not url:
            return

        recipe_data = scrape_recipe(url)
        if recipe_data:
            self.clear_recipe_entries()
            self.recipe_name_entry.insert(0, recipe_data["name"])
            self.ingredients_entry.insert(0, ", ".join(recipe_data["ingredients"]))
            self.instructions_entry_recipes.insert("1.0", "\n".join(recipe_data["instructions"]))
        else:
            messagebox.showerror("Error", "Failed to scrape the recipe. Please check the URL and try again.")

main
    def load_meal_plan(self):
        for i in self.meal_plan_tree.get_children():
            self.meal_plan_tree.delete(i)

        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT meal_plan.date, meal_plan.meal_type, recipes.name
            FROM meal_plan
            JOIN recipes ON meal_plan.recipe_id = recipes.id
            ORDER BY meal_plan.date
        """)
        rows = cursor.fetchall()
        for row in rows:
            self.meal_plan_tree.insert("", "end", values=row)

        self.populate_recipe_combobox()

    def add_to_meal_plan(self):
        date = self.meal_date_entry.get()
        meal_type = self.meal_type_entry.get()
        recipe_name = self.recipe_combobox.get()

        if not date or not meal_type or not recipe_name:
            messagebox.showerror("Error", "All meal plan fields must be filled.")
            return

        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM recipes WHERE name=?", (recipe_name,))
        recipe_id = cursor.fetchone()[0]

        cursor.execute("INSERT INTO meal_plan (date, meal_type, recipe_id) VALUES (?, ?, ?)",
                       (date, meal_type, recipe_id))
        self.conn.commit()
        self.load_meal_plan()

    def populate_recipe_combobox(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM recipes")
        recipes = [row[0] for row in cursor.fetchall()]
        self.recipe_combobox['values'] = recipes

    def create_shopping_list_widgets(self):
        # Entry form for adding new items
        self.item_entry_frame = ttk.LabelFrame(self.shopping_list_frame, text="Add Item", padding=(10, 5))
        self.item_entry_frame.pack(fill="x", expand="yes", padx=10, pady=5)

        self.item_name_label = ttk.Label(self.item_entry_frame, text="Name:")
        self.item_name_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.item_name_entry = ttk.Entry(self.item_entry_frame)
        self.item_name_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        self.quantity_label = ttk.Label(self.item_entry_frame, text="Quantity:")
        self.quantity_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.quantity_entry = ttk.Entry(self.item_entry_frame)
        self.quantity_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        self.brand_label = ttk.Label(self.item_entry_frame, text="Brand:")
        self.brand_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.brand_entry = ttk.Entry(self.item_entry_frame)
        self.brand_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        self.instructions_label = ttk.Label(self.item_entry_frame, text="Instructions:")
        self.instructions_label.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.instructions_entry = ttk.Entry(self.item_entry_frame)
        self.instructions_entry.grid(row=1, column=3, padx=5, pady=5, sticky="ew")

        self.category_label = ttk.Label(self.item_entry_frame, text="Category:")
        self.category_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.category_entry = ttk.Entry(self.item_entry_frame)
        self.category_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        self.add_item_button = ttk.Button(self.item_entry_frame, text="Add Item", command=self.add_shopping_list_item)
        self.add_item_button.grid(row=2, column=3, padx=5, pady=5, sticky="e")

        # Treeview to display the shopping list
        self.shopping_list_tree = ttk.Treeview(self.shopping_list_frame, columns=("ID", "Name", "Quantity", "Brand", "Instructions", "Category", "Purchased"), show="headings")
        self.shopping_list_tree.pack(fill="both", expand=True, padx=10, pady=5)

        self.shopping_list_tree.heading("ID", text="ID")
        self.shopping_list_tree.heading("Name", text="Name")
        self.shopping_list_tree.heading("Quantity", text="Quantity")
        self.shopping_list_tree.heading("Brand", text="Brand")
        self.shopping_list_tree.heading("Instructions", text="Instructions")
        self.shopping_list_tree.heading("Category", text="Category")
        self.shopping_list_tree.heading("Purchased", text="Purchased")

        self.shopping_list_tree.column("ID", width=30)

        # Buttons for managing the list
        self.list_management_frame = ttk.Frame(self.shopping_list_frame)
        self.list_management_frame.pack(fill="x", expand="yes", padx=10, pady=5)

        self.mark_purchased_button = ttk.Button(self.list_management_frame, text="Mark as Purchased", command=self.mark_item_as_purchased)
        self.mark_purchased_button.pack(side="left", padx=5)
        self.edit_item_button = ttk.Button(self.list_management_frame, text="Edit Item", command=self.edit_shopping_list_item)
        self.edit_item_button.pack(side="left", padx=5)
        self.delete_item_button = ttk.Button(self.list_management_frame, text="Delete Item", command=self.delete_shopping_list_item)
        self.delete_item_button.pack(side="left", padx=5)

    def load_shopping_list(self):
        for i in self.shopping_list_tree.get_children():
            self.shopping_list_tree.delete(i)

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM shopping_list")
        rows = cursor.fetchall()
        for row in rows:
            self.shopping_list_tree.insert("", "end", values=row)

    def add_shopping_list_item(self):
        name = self.item_name_entry.get()
        quantity = self.quantity_entry.get()
        brand = self.brand_entry.get()
        instructions = self.instructions_entry.get()
        category = self.category_entry.get()

        if not name:
            messagebox.showerror("Error", "Item name cannot be empty.")
            return

        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO shopping_list (name, quantity, brand, instructions, category, purchased) VALUES (?, ?, ?, ?, ?, ?)",
                       (name, quantity, brand, instructions, category, 0))
        self.conn.commit()
        self.load_shopping_list()
        self.clear_shopping_list_entries()

    def edit_shopping_list_item(self):
        selected_item = self.shopping_list_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select an item to edit.")
            return

        item_values = self.shopping_list_tree.item(selected_item, "values")
        item_id = item_values[0]

        # Create a new window for editing
        edit_window = tk.Toplevel(self)
        edit_window.title("Edit Item")

        ttk.Label(edit_window, text="Name:").grid(row=0, column=0)
        name_entry = ttk.Entry(edit_window)
        name_entry.grid(row=0, column=1)
        name_entry.insert(0, item_values[1])

        ttk.Label(edit_window, text="Quantity:").grid(row=1, column=0)
        quantity_entry = ttk.Entry(edit_window)
        quantity_entry.grid(row=1, column=1)
        quantity_entry.insert(0, item_values[2])

        ttk.Label(edit_window, text="Brand:").grid(row=2, column=0)
        brand_entry = ttk.Entry(edit_window)
        brand_entry.grid(row=2, column=1)
        brand_entry.insert(0, item_values[3])

        ttk.Label(edit_window, text="Instructions:").grid(row=3, column=0)
        instructions_entry = ttk.Entry(edit_window)
        instructions_entry.grid(row=3, column=1)
        instructions_entry.insert(0, item_values[4])

        ttk.Label(edit_window, text="Category:").grid(row=4, column=0)
        category_entry = ttk.Entry(edit_window)
        category_entry.grid(row=4, column=1)
        category_entry.insert(0, item_values[5])

        def update_item():
            new_name = name_entry.get()
            new_quantity = quantity_entry.get()
            new_brand = brand_entry.get()
            new_instructions = instructions_entry.get()
            new_category = category_entry.get()

            if not new_name:
                messagebox.showerror("Error", "Item name cannot be empty.")
                return

            cursor = self.conn.cursor()
            cursor.execute("UPDATE shopping_list SET name=?, quantity=?, brand=?, instructions=?, category=? WHERE id=?",
                           (new_name, new_quantity, new_brand, new_instructions, new_category, item_id))
            self.conn.commit()
            self.load_shopping_list()
            edit_window.destroy()

        ttk.Button(edit_window, text="Update", command=update_item).grid(row=5, column=0, columnspan=2)

    def delete_shopping_list_item(self):
        selected_item = self.shopping_list_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select an item to delete.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this item?"):
            item_id = self.shopping_list_tree.item(selected_item, "values")[0]
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM shopping_list WHERE id=?", (item_id,))
            self.conn.commit()
            self.load_shopping_list()

    def mark_item_as_purchased(self):
        selected_item = self.shopping_list_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select an item to mark as purchased.")
            return

        item_id = self.shopping_list_tree.item(selected_item, "values")[0]
        cursor = self.conn.cursor()
        cursor.execute("UPDATE shopping_list SET purchased=1 WHERE id=?", (item_id,))
        self.conn.commit()
        self.load_shopping_list()

    def clear_shopping_list_entries(self):
        self.item_name_entry.delete(0, "end")
        self.quantity_entry.delete(0, "end")
        self.brand_entry.delete(0, "end")
        self.instructions_entry.delete(0, "end")
        self.category_entry.delete(0, "end")

if __name__ == "__main__":
    app = PantryPal()
    app.mainloop()
