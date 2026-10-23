import json
import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox
from tkcalendar import DateEntry


DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "nguyen_lieu.json"


class InventoryFrame(tk.Frame):
    """Màn hình xem nhanh danh sách nguyên liệu trong kho."""

    def __init__(self, parent):
        super().__init__(parent)
        self.items = []
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        top = tk.Frame(self)
        top.pack(fill="x", padx=12, pady=(12, 4))

        tk.Label(top, text="Ngày báo cáo:", font=("Arial", 10, "bold")).pack(side="left")
        self.cal = DateEntry(
            top, width=13, background="darkblue", foreground="white",
            borderwidth=2, date_pattern="dd/mm/yyyy"
        )
        self.cal.pack(side="left", padx=(8, 16))

        tk.Label(top, text="Tìm nguyên liệu:").pack(side="left")
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(top, textvariable=self.search_var, width=25)
        search_entry.pack(side="left", padx=8)
        search_entry.bind("<KeyRelease>", lambda event: self.show_data())

        ttk.Button(top, text="Làm mới", command=self.load_data).pack(side="left", padx=4)

        table_frame = tk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=12, pady=10)

        cols = ("ma", "ten", "dvt", "soluong", "dongia")
        self.tree = ttk.Treeview(table_frame, columns=cols, show="headings", height=14)

        headings = {
            "ma": ("Mã NL", 100),
            "ten": ("Tên nguyên liệu", 250),
            "dvt": ("Đơn vị tính", 120),
            "soluong": ("Tồn kho", 120),
            "dongia": ("Đơn giá", 140),
        }
        for col, (title, width) in headings.items():
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor="w" if col in ("ma", "ten", "dvt") else "e")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.status_label = tk.Label(self, text="", anchor="w", fg="#555555")
        self.status_label.pack(fill="x", padx=14, pady=(0, 8))

    def load_data(self):
        try:
            if not DATA_FILE.exists() or DATA_FILE.stat().st_size == 0:
                self.items = []
            else:  # Đã sửa lỗi thừa chữ A ở đây
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("Dữ liệu nguyên liệu phải là danh sách.")
                self.items = data
            self.show_data()
        except (OSError, json.JSONDecodeError, ValueError) as e:
            messagebox.showerror("Lỗi dữ liệu", f"Không đọc được danh sách nguyên liệu:\n{e}", parent=self)
            self.items = []
            self.show_data()

    def show_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        keyword = self.search_var.get().strip().casefold() if hasattr(self, "search_var") else ""
        shown = 0
        for item in self.items:
            code = str(item.get("ma_nl", ""))
            name = str(item.get("ten_nl", ""))
            if keyword and keyword not in code.casefold() and keyword not in name.casefold():
                continue

            quantity = item.get("so_luong", 0)
            price = item.get("don_gia", 0)
            self.tree.insert("", "end", values=(
                code, name, item.get("dvt", ""),
                self.format_number(quantity), self.format_number(price)
            ))
            shown += 1

        self.status_label.config(
            text=f"Ngày báo cáo: {self.cal.get()}  |  Hiển thị {shown}/{len(self.items)} nguyên liệu"
        )

    @staticmethod
    def format_number(value):
        try:
            number = float(value)
            if number.is_integer():
                return f"{int(number):,}".replace(",", ".")
            return f"{number:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (TypeError, ValueError):
            return str(value if value is not None else "")