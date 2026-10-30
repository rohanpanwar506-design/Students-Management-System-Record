"""
Student Record Management System
BCA Python Project
Technology: Python Tkinter + SQLite
Works offline. No third-party packages are required.

Run:
    python student_record_management.py

The SQLite database (students.db) is created automatically beside this file.
"""

import csv
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "students.db"


class StudentRecordApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Student Record Management System")
        self.root.geometry("1050x650")
        self.root.minsize(850, 550)
        self.selected_id = None

        self.create_database()
        self.build_ui()
        self.load_students()

    def connect(self):
        return sqlite3.connect(DB_PATH)

    def create_database(self):
        with self.connect() as con:
            con.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    roll_no TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    course TEXT NOT NULL,
                    semester TEXT,
                    phone TEXT,
                    email TEXT
                )
            """)

    def build_ui(self):
        header = tk.Frame(self.root, bg="#17365D", padx=18, pady=14)
        header.pack(fill="x")
        tk.Label(
            header, text="STUDENT RECORD MANAGEMENT SYSTEM",
            font=("Arial", 18, "bold"), fg="white", bg="#17365D"
        ).pack(anchor="w")
        tk.Label(
            header, text="Offline desktop application | Python + Tkinter + SQLite",
            font=("Arial", 10), fg="#DCE6F1", bg="#17365D"
        ).pack(anchor="w", pady=(4, 0))

        body = tk.Frame(self.root, padx=16, pady=12)
        body.pack(fill="both", expand=True)

        form = ttk.LabelFrame(body, text="Student Details", padding=12)
        form.pack(fill="x")

        self.vars = {
            "roll_no": tk.StringVar(),
            "name": tk.StringVar(),
            "course": tk.StringVar(),
            "semester": tk.StringVar(),
            "phone": tk.StringVar(),
            "email": tk.StringVar(),
        }

        fields = [
            ("Roll Number *", "roll_no"),
            ("Student Name *", "name"),
            ("Course *", "course"),
            ("Semester", "semester"),
            ("Phone", "phone"),
            ("Email", "email"),
        ]

        for index, (label, key) in enumerate(fields):
            row, col = divmod(index, 3)
            cell = tk.Frame(form)
            cell.grid(row=row, column=col, sticky="ew", padx=8, pady=7)
            ttk.Label(cell, text=label).pack(anchor="w")
            ttk.Entry(cell, textvariable=self.vars[key], width=32).pack(fill="x", pady=(3, 0))
            form.columnconfigure(col, weight=1)

        buttons = tk.Frame(body)
        buttons.pack(fill="x", pady=10)

        ttk.Button(buttons, text="Add Student", command=self.add_student).pack(side="left", padx=4)
        ttk.Button(buttons, text="Update Selected", command=self.update_student).pack(side="left", padx=4)
        ttk.Button(buttons, text="Delete Selected", command=self.delete_student).pack(side="left", padx=4)
        ttk.Button(buttons, text="Clear Form", command=self.clear_form).pack(side="left", padx=4)
        ttk.Button(buttons, text="Export CSV", command=self.export_csv).pack(side="right", padx=4)

        search_frame = ttk.Frame(body)
        search_frame.pack(fill="x", pady=(2, 8))
        ttk.Label(search_frame, text="Search (roll number, name or course):").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=35)
        search_entry.pack(side="left", padx=8)
        search_entry.bind("<KeyRelease>", lambda _event: self.load_students())
        ttk.Button(search_frame, text="Show All", command=self.show_all).pack(side="left")

        table_frame = ttk.Frame(body)
        table_frame.pack(fill="both", expand=True)

        columns = ("id", "roll_no", "name", "course", "semester", "phone", "email")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=13)
        headings = {
            "id": "ID", "roll_no": "Roll Number", "name": "Student Name",
            "course": "Course", "semester": "Semester", "phone": "Phone", "email": "Email"
        }
        widths = {"id": 45, "roll_no": 105, "name": 180, "course": 130,
                  "semester": 85, "phone": 115, "email": 190}
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=widths[col], minwidth=45, anchor="center")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)
        self.tree.bind("<<TreeviewSelect>>", self.on_select)

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(body, textvariable=self.status_var, anchor="w").pack(fill="x", pady=(8, 0))

    def get_form_data(self):
        data = {key: var.get().strip() for key, var in self.vars.items()}
        if not data["roll_no"] or not data["name"] or not data["course"]:
            messagebox.showwarning("Missing information", "Roll Number, Student Name and Course are required.")
            return None
        if data["email"] and "@" not in data["email"]:
            messagebox.showwarning("Invalid email", "Please enter a valid email address.")
            return None
        return data

    def add_student(self):
        data = self.get_form_data()
        if data is None:
            return
        try:
            with self.connect() as con:
                con.execute("""
                    INSERT INTO students (roll_no, name, course, semester, phone, email)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, tuple(data.values()))
            self.load_students()
            self.clear_form()
            messagebox.showinfo("Success", "Student record added successfully.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate roll number", "This roll number already exists. Use a unique roll number.")

    def update_student(self):
        if self.selected_id is None:
            messagebox.showwarning("Select a record", "Please select a student from the table first.")
            return
        data = self.get_form_data()
        if data is None:
            return
        try:
            with self.connect() as con:
                con.execute("""
                    UPDATE students
                    SET roll_no=?, name=?, course=?, semester=?, phone=?, email=?
                    WHERE id=?
                """, (*data.values(), self.selected_id))
            self.load_students()
            self.clear_form()
            messagebox.showinfo("Success", "Student record updated successfully.")
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate roll number", "Another student already uses this roll number.")

    def delete_student(self):
        if self.selected_id is None:
            messagebox.showwarning("Select a record", "Please select a student from the table first.")
            return
        if not messagebox.askyesno("Confirm delete", "Are you sure you want to delete this student record?"):
            return
        with self.connect() as con:
            con.execute("DELETE FROM students WHERE id=?", (self.selected_id,))
        self.load_students()
        self.clear_form()
        self.status_var.set("Student record deleted.")

    def load_students(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        search = self.search_var.get().strip()
        with self.connect() as con:
            if search:
                rows = con.execute("""
                    SELECT id, roll_no, name, course, semester, phone, email
                    FROM students
                    WHERE roll_no LIKE ? OR name LIKE ? OR course LIKE ?
                    ORDER BY name
                """, (f"%{search}%", f"%{search}%", f"%{search}%")).fetchall()
            else:
                rows = con.execute("""
                    SELECT id, roll_no, name, course, semester, phone, email
                    FROM students ORDER BY name
                """).fetchall()
        for row in rows:
            self.tree.insert("", "end", values=row)
        self.status_var.set(f"Total records shown: {len(rows)}")

    def on_select(self, _event=None):
        selection = self.tree.selection()
        if not selection:
            return
        values = self.tree.item(selection[0], "values")
        self.selected_id = int(values[0])
        for key, value in zip(self.vars, values[1:]):
            self.vars[key].set(value)

    def clear_form(self):
        self.selected_id = None
        for var in self.vars.values():
            var.set("")
        for item in self.tree.selection():
            self.tree.selection_remove(item)

    def show_all(self):
        self.search_var.set("")
        self.load_students()

    def export_csv(self):
        path = filedialog.asksaveasfilename(
            title="Export student records",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not path:
            return
        with self.connect() as con:
            rows = con.execute("""
                SELECT roll_no, name, course, semester, phone, email
                FROM students ORDER BY name
            """).fetchall()
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(["Roll Number", "Student Name", "Course", "Semester", "Phone", "Email"])
                writer.writerows(rows)
            messagebox.showinfo("Export complete", f"Records exported successfully:\n{path}")
        except OSError as error:
            messagebox.showerror("Export failed", str(error))


if __name__ == "__main__":
    root = tk.Tk()
    app = StudentRecordApp(root)
    root.mainloop()
