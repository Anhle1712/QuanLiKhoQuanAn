import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
import requests


DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "nguyen_lieu.json"


class StatsFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.data = []
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        tk.Label(
            self, text="THỐNG KÊ TỒN KHO",
            font=("Arial", 13, "bold"), fg="#1976D2"
        ).pack(pady=(12, 5))

        self.summary_label = tk.Label(self, text="Đang tải dữ liệu...", font=("Arial", 10))
        self.summary_label.pack(pady=4)

        self.canvas = tk.Canvas(
            self, width=750, height=350, bg="white",
            highlightthickness=1, highlightbackground="#cccccc"
        )
        self.canvas.pack(fill="both", expand=True, padx=14, pady=10)
        self.canvas.bind("<Configure>", lambda event: self.draw_bar_chart())

        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=(0, 12))

        tk.Button(
            btn_frame, text="Cập nhật biểu đồ", bg="#4CAF50", fg="white",
            command=self.load_data
        ).pack(side="left", padx=5)
        tk.Button(
            btn_frame, text="Kiểm tra API mẫu", bg="#FF9800", fg="white",
            command=self.fetch_external_api
        ).pack(side="left", padx=5)

    def load_data(self):
        try:
            if not DATA_FILE.exists() or DATA_FILE.stat().st_size == 0:
                self.data = []
            else:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if not isinstance(data, list):
                    raise ValueError("Dữ liệu nguyên liệu phải là danh sách.")
                self.data = data
            self.update_summary()
            self.draw_bar_chart()
        except (OSError, json.JSONDecodeError, ValueError) as e:
            self.data = []
            self.update_summary()
            self.draw_bar_chart()
            messagebox.showerror("Lỗi dữ liệu", f"Không đọc được dữ liệu kho:\n{e}", parent=self)

    def update_summary(self):
        total_items = len(self.data)
        total_quantity = 0.0
        total_value = 0.0
        for item in self.data:
            qty = self.to_number(item.get("so_luong", 0))
            price = self.to_number(item.get("don_gia", 0))
            total_quantity += qty
            total_value += qty * price

        self.summary_label.config(
            text=(
                f"Số loại nguyên liệu: {total_items}    |    "
                f"Tổng số lượng: {self.format_number(total_quantity)}    |    "
                f"Giá trị tồn kho ước tính: {self.format_number(total_value)}"
            )
        )

    def draw_bar_chart(self):
        if not hasattr(self, "canvas"):
            return

        self.canvas.delete("all")
        width = max(self.canvas.winfo_width(), 400)
        height = max(self.canvas.winfo_height(), 250)
        margin_left, margin_right, margin_top, margin_bottom = 55, 20, 25, 65
        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom

        self.canvas.create_text(
            width / 2, 12, text="Số lượng tồn theo nguyên liệu",
            font=("Arial", 10, "bold"), anchor="n"
        )

        if not self.data:
            self.canvas.create_text(
                width / 2, height / 2,
                text="Chưa có dữ liệu nguyên liệu để vẽ biểu đồ",
                fill="#666666", font=("Arial", 11)
            )
            return

        values = [
            (str(item.get("ten_nl", "Chưa đặt tên")), max(0, self.to_number(item.get("so_luong", 0))))
            for item in self.data
        ]
        max_val = max((qty for _, qty in values), default=0) or 1

        # Giới hạn số cột để biểu đồ không bị chật khi dữ liệu nhiều.
        values = values[:20]
        count = len(values)
        slot_width = chart_width / max(count, 1)
        bar_width = max(8, min(42, slot_width * 0.58))

        x_axis = margin_top + chart_height
        self.canvas.create_line(margin_left, x_axis, width - margin_right, x_axis, fill="#555555")
        self.canvas.create_line(margin_left, margin_top, margin_left, x_axis, fill="#555555")

        for i, (name, qty) in enumerate(values):
            center_x = margin_left + slot_width * (i + 0.5)
            bar_height = (qty / max_val) * max(1, chart_height - 18)
            x0 = center_x - bar_width / 2
            y0 = x_axis - bar_height
            self.canvas.create_rectangle(
                x0, y0, center_x + bar_width / 2, x_axis,
                fill="#2196F3", outline="#0D47A1"
            )
            self.canvas.create_text(
                center_x, max(margin_top + 8, y0 - 9),
                text=self.format_number(qty), font=("Arial", 8, "bold")
            )
            short_name = name if len(name) <= 12 else name[:11] + "…"
            self.canvas.create_text(
                center_x, x_axis + 8, text=short_name,
                font=("Arial", 8), angle=25, anchor="n"
            )

        if len(self.data) > 20:
            self.canvas.create_text(
                width - margin_right, height - 8,
                text="Biểu đồ chỉ hiển thị 20 nguyên liệu đầu tiên.",
                fill="#666666", font=("Arial", 8), anchor="se"
            )

    def fetch_external_api(self):
        """Kiểm tra kết nối API minh họa; không ghi đè dữ liệu kho."""
        try:
            response = requests.get(
                "https://jsonplaceholder.typicode.com/todos/1", timeout=5
            )
            response.raise_for_status()
            result = response.json()
            title = result.get("title", "Không có nội dung")
            messagebox.showinfo(
                "API mẫu hoạt động",
                "Đã kết nối API minh họa thành công.\n\n"
                f"Dữ liệu nhận được: {title}\n\n"
                "Dữ liệu này chỉ dùng kiểm tra kết nối, không phải dữ liệu kho.",
                parent=self
            )
        except (requests.RequestException, ValueError) as e:
            messagebox.showerror(
                "Không kết nối được API",
                f"Bạn hãy kiểm tra mạng hoặc thử lại sau.\nChi tiết: {e}",
                parent=self
            )

    @staticmethod
    def to_number(value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def format_number(value):
        if float(value).is_integer():
            return f"{int(value):,}".replace(",", ".")
        return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
