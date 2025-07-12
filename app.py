import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkcalendar import Calendar
from database import initialize_database, create_connection
import csv
from ttkthemes import ThemedTk
from scraper import scrape_recipe

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
        # View selection buttons
        self.view_frame = ttk.Frame(self.meal_planner_frame)
        self.view_frame.pack(pady=5)
        self.month_view_button = ttk.Button(self.view_frame, text="Month View", command=self.show_month_view)
        self.month_view_button.pack(side="left", padx=5)
        self.week_view_button = ttk.Button(self.view_frame, text="Week View", command=self.show_week_view)
        self.week_view_button.pack(side="left", padx=5)

        # Calendar view
        self.calendar = Calendar(self.meal_planner_frame, selectmode='day')
        self.calendar.pack(pady=10, padx=10, fill="both", expand=True)
        self.calendar.bind("<<CalendarSelected>>", self.display_meals_for_day)

        # Meal display area
        self.meal_display_frame = ttk.LabelFrame(self.meal_planner_frame, text="Meals for Selected Date")
        self.meal_display_frame.pack(pady=10, padx=10, fill="x")

        self.meal_slots = ["Breakfast", "Lunch", "Snack", "Dinner"]
        self.meal_labels = {}
        for i, slot in enumerate(self.meal_slots):
            ttk.Label(self.meal_display_frame, text=f"{slot}:").grid(row=i, column=0, sticky="w", padx=5, pady=2)
            self.meal_labels[slot] = ttk.Label(self.meal_display_frame, text="No meal planned")
            self.meal_labels[slot].grid(row=i, column=1, sticky="w", padx=5, pady=2)

        # Add meal button
        self.add_meal_to_plan_button = ttk.Button(self.meal_planner_frame, text="Add/Edit Meal", command=self.add_or_edit_meal_in_plan)
        self.add_meal_to_plan_button.pack(pady=5)

        self.add_ingredients_from_plan_button = ttk.Button(self.meal_planner_frame, text="Add Ingredients to Shopping List", command=self.add_ingredients_from_plan)
        self.add_ingredients_from_plan_button.pack(pady=5)

    def show_month_view(self):
        # The calendar is already in month view by default
        pass

    def show_week_view(self):
        # This is a bit more complex and might require a custom widget.
        # For now, we'll just stick to the month view.
        messagebox.showinfo("Info", "Weekly view is not yet implemented.")

    def display_meals_for_day(self, event=None):
        selected_date = self.calendar.get_date()
        cursor = self.conn.cursor()
        for slot in self.meal_slots:
            self.meal_labels[slot].config(text="No meal planned")

        cursor.execute("""
            SELECT meal_plan.meal_type, recipes.name
            FROM meal_plan
            JOIN recipes ON meal_plan.recipe_id = recipes.id
            WHERE meal_plan.date = ?
        """, (selected_date,))

        rows = cursor.fetchall()
        for row in rows:
            meal_type, recipe_name = row
            if meal_type in self.meal_labels:
                self.meal_labels[meal_type].config(text=recipe_name)

    def add_or_edit_meal_in_plan(self):
        selected_date = self.calendar.get_date()

        edit_window = tk.Toplevel(self)
        edit_window.title(f"Plan Meals for {selected_date}")

        ttk.Label(edit_window, text="Date:").grid(row=0, column=0)
        ttk.Label(edit_window, text=selected_date).grid(row=0, column=1)

        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM recipes")
        recipes = [row[0] for row in cursor.fetchall()]

        self.meal_comboboxes = {}
        for i, slot in enumerate(self.meal_slots):
            ttk.Label(edit_window, text=f"{slot}:").grid(row=i+1, column=0)
            combo = ttk.Combobox(edit_window, values=recipes)
            combo.grid(row=i+1, column=1)
            self.meal_comboboxes[slot] = combo

            # Pre-fill with existing meal plan
            cursor.execute("SELECT recipes.name FROM meal_plan JOIN recipes ON meal_plan.recipe_id = recipes.id WHERE meal_plan.date=? AND meal_plan.meal_type=?", (selected_date, slot))
            result = cursor.fetchone()
            if result:
                combo.set(result[0])

        def save_meal_plan():
            cursor = self.conn.cursor()
            for slot, combo in self.meal_comboboxes.items():
                recipe_name = combo.get()
                if recipe_name:
                    cursor.execute("SELECT id FROM recipes WHERE name=?", (recipe_name,))
                    recipe_id_result = cursor.fetchone()
                    if recipe_id_result:
                        recipe_id = recipe_id_result[0]
                        # Check if a meal already exists for this slot and date
                        cursor.execute("SELECT id FROM meal_plan WHERE date=? AND meal_type=?", (selected_date, slot))
                        existing_meal = cursor.fetchone()
                        if existing_meal:
                            cursor.execute("UPDATE meal_plan SET recipe_id=? WHERE id=?", (recipe_id, existing_meal[0]))
                        else:
                            cursor.execute("INSERT INTO meal_plan (date, meal_type, recipe_id) VALUES (?, ?, ?)", (selected_date, slot, recipe_id))
                else:
                    # If the combobox is empty, delete the meal from the plan
                    cursor.execute("DELETE FROM meal_plan WHERE date=? AND meal_type=?", (selected_date, slot))

            self.conn.commit()
            self.display_meals_for_day()
            edit_window.destroy()

        ttk.Button(edit_window, text="Save", command=save_meal_plan).grid(row=len(self.meal_slots)+1, column=0, columnspan=2)

    def add_ingredients_from_plan(self):
        # For simplicity, this will add ingredients from all meals in the current month view
        # A more advanced implementation would consider the selected week or month

        # Get the currently displayed month and year
        cal_date = self.calendar.get_date()
        if isinstance(cal_date, str):
            from datetime import datetime
            cal_date = datetime.strptime(cal_date, self.calendar.date_pattern)

        month = cal_date.month
        year = cal_date.year

        cursor = self.conn.cursor()
        # The date in the database is stored as a string, so we need to be careful with the LIKE query
        date_pattern = f"{year}-{month:02d}-%"
        cursor.execute("""
            SELECT r.ingredients
            FROM meal_plan mp
            JOIN recipes r ON mp.recipe_id = r.id
            WHERE mp.date LIKE ?
        """, (date_pattern,))

        all_ingredients = []
        for row in cursor.fetchall():
            ingredients_str = row[0]
            all_ingredients.extend([ing.strip() for ing in ingredients_str.split(",")])

        if not all_ingredients:
            messagebox.showinfo("Info", "No meals planned for the current view.")
            return

        for ingredient in all_ingredients:
            cursor.execute("INSERT INTO shopping_list (name, purchased) VALUES (?, ?)", (ingredient, 0))

        self.conn.commit()
        self.load_shopping_list()
        messagebox.showinfo("Success", "Ingredients from the current month's meals have been added to the shopping list.")

    def create_menu(self):
        self.menu_bar = tk.Menu(self)
        self.config(menu=self.menu_bar)

        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Backup to CSV", command=self.backup_to_csv)
        self.file_menu.add_command(label="Export All Recipes to CSV", command=self.export_all_recipes_to_csv)
        self.file_menu.add_command(label="Print...", command=self.print_dialog)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.quit)

    def print_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("Print")

        ttk.Label(dialog, text="What would you like to print?").pack(pady=10)

        ttk.Button(dialog, text="Shopping List", command=self.print_shopping_list).pack(pady=5)
        ttk.Button(dialog, text="Current Recipe", command=self.print_current_recipe).pack(pady=5)
        ttk.Button(dialog, text="Meal Planner (Month)", command=self.print_meal_planner_month).pack(pady=5)

    def print_shopping_list(self):
        content = "Shopping List\n\n"
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, quantity, brand, category FROM shopping_list WHERE purchased = 0")
        items = cursor.fetchall()
        for item in items:
            content += f"- {item[0]} ({item[1] if item[1] else 'N/A'}) - Brand: {item[2] if item[2] else 'N/A'}, Category: {item[3] if item[3] else 'N/A'}\n"

        self.save_and_print(content, "shopping_list")

    def print_current_recipe(self):
        selected_item = self.recipe_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select a recipe to print.")
            return

        recipe_id = self.recipe_tree.item(selected_item, "values")[0]
        cursor = self.conn.cursor()
        cursor.execute("SELECT name, ingredients, instructions FROM recipes WHERE id=?", (recipe_id,))
        recipe = cursor.fetchone()

        content = f"Recipe: {recipe[0]}\n\n"
        content += "Ingredients:\n"
        for ingredient in recipe[1].split(','):
            content += f"- {ingredient.strip()}\n"

        content += "\nInstructions:\n"
        content += recipe[2]

        self.save_and_print(content, f"recipe_{recipe[0].replace(' ', '_')}")

    def print_meal_planner_month(self):
        cal_date = self.calendar.get_date()
        if isinstance(cal_date, str):
            from datetime import datetime
            cal_date = datetime.strptime(cal_date, self.calendar.date_pattern)
        month = cal_date.month
        year = cal_date.year

        content = f"Meal Plan for {cal_date.strftime('%B %Y')}\n\n"

        date_pattern = f"{year}-{month:02d}-%"
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT mp.date, mp.meal_type, r.name
            FROM meal_plan mp
            JOIN recipes r ON mp.recipe_id = r.id
            WHERE mp.date LIKE ?
            ORDER BY mp.date, mp.meal_type
        """, (date_pattern,))

        meal_plan = cursor.fetchall()

        current_date = ""
        for date, meal_type, recipe_name in meal_plan:
            if date != current_date:
                content += f"\n--- {date} ---\n"
                current_date = date
            content += f"{meal_type}: {recipe_name}\n"

        self.save_and_print(content, f"meal_plan_{year}_{month:02d}")

    def save_and_print(self, content, filename_prefix):
        file_path = filedialog.asksaveasfilename(
            initialfile=f"{filename_prefix}.txt",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if not file_path:
            return

        try:
            with open(file_path, "w") as f:
                f.write(content)
            messagebox.showinfo("Success", f"Content saved to {file_path}")
            # Here you would typically open the file with the default application
            # For simplicity, we'll just show a message.
            # For a real application, you might use:
            # import os
            # os.startfile(file_path, 'print') # On Windows
            # or subprocess.run(['lpr', file_path]) on Linux
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {e}")

    def export_recipe_to_csv(self):
        selected_item = self.recipe_tree.focus()
        if not selected_item:
            messagebox.showerror("Error", "Please select a recipe to export.")
            return

        recipe_id = self.recipe_tree.item(selected_item, "values")[0]
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM recipes WHERE id=?", (recipe_id,))
        recipe = cursor.fetchone()

        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([i[0] for i in cursor.description])
            writer.writerow(recipe)

        messagebox.showinfo("Export Successful", f"Recipe exported to {file_path}")

    def export_all_recipes_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM recipes")
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([i[0] for i in cursor.description])
            writer.writerows(cursor)

        messagebox.showinfo("Export Successful", f"All recipes exported to {file_path}")

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

        # Treeview to display recipes
        self.recipe_tree = ttk.Treeview(self.recipes_frame, columns=("ID", "Name", "Category"), show="headings")
        self.recipe_tree.pack(fill="both", expand=True, padx=10, pady=5)

        self.recipe_tree.heading("ID", text="ID")
        self.recipe_tree.heading("Name", text="Name")
        self.recipe_tree.heading("Category", text="Category")
        self.recipe_tree.column("ID", width=30)
        self.recipe_tree.bind("<Double-1>", self.view_recipe_event)

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

        self.export_recipe_button = ttk.Button(self.recipe_management_frame, text="Export Recipe to CSV", command=self.export_recipe_to_csv)
        self.export_recipe_button.pack(side="left", padx=5)

    def add_ingredient_to_shopping_list(self, ingredient_name):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO shopping_list (name, purchased) VALUES (?, ?)", (ingredient_name, 0))
        self.conn.commit()
        self.load_shopping_list()
        messagebox.showinfo("Success", f"'{ingredient_name}' added to shopping list.")

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

    def view_recipe_event(self, event):
        self.view_recipe()

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
        ingredients_frame = ttk.Frame(view_window)
        ingredients_frame.grid(row=2, column=1, sticky="w")
        for ingredient in recipe[1].split(','):
            ingredient = ingredient.strip()
            link = ttk.Label(ingredients_frame, text=ingredient, foreground="blue", cursor="hand2")
            link.pack(anchor="w")
            link.bind("<Button-1>", lambda e, ing=ingredient: self.add_ingredient_to_shopping_list(ing))

        ttk.Label(view_window, text="Instructions:").grid(row=3, column=0, sticky="w")
        instructions_text = tk.Text(view_window, height=10, width=40)
        instructions_text.grid(row=3, column=1, sticky="nsew")
        instructions_text.insert("1.0", recipe[2])
        instructions_text.config(state="disabled")

        add_to_list_button = ttk.Button(view_window, text="Add Ingredients to Shopping List",
                                        command=lambda: self.add_ingredients_to_shopping_list_from_view(recipe_id))
        add_to_list_button.grid(row=4, column=0, columnspan=2, pady=5)

        view_window.grid_columnconfigure(1, weight=1)
        view_window.grid_rowconfigure(3, weight=1)

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

    def add_ingredients_to_shopping_list_from_view(self, recipe_id):
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

    def load_meal_plan(self):
        self.display_meals_for_day()

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
        self.delete_all_button = ttk.Button(self.list_management_frame, text="Delete All", command=self.delete_all_shopping_list_items)
        self.delete_all_button.pack(side="left", padx=5)

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

    def delete_all_shopping_list_items(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to delete all items from the shopping list?"):
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM shopping_list")
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
