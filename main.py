import tkinter as tk
import ttkbootstrap as ttk
from tkinter import messagebox

from gui.login_view import doc_tai_khoan
from gui.inventory_view import InventoryFrame
from gui.stats_view import StatsFrame


def main():
    root = ttk.Window(
        title="Đăng nhập - Quản lý kho quán ăn",
        themename="flatly",
        size=(420, 350)
    )
    root.resizable(False, False)

    def on_login_success(user_info):
        for widget in root.winfo_children():
            widget.destroy()

        fullname = user_info.get("fullname") or user_info.get("username", "Người dùng")
        role = user_info.get("role", "user")
        role_name = "Quản trị viên" if role == "admin" else "Nhân viên"

        root.geometry("1000x650")
        root.resizable(True, True)
        root.title(f"Quản lý kho quán ăn - {fullname}")

        header = ttk.Frame(root, padding=(16, 14, 16, 6))
        header.pack(fill="x")

        ttk.Label(
            header,
            text="QUẢN LÝ KHO NGUYÊN LIỆU QUÁN ĂN",
            font=("Arial", 17, "bold"),
            bootstyle="primary"
        ).pack(side="left")

        ttk.Label(
            header, text=f"{fullname} | {role_name}",
            font=("Arial", 9)
        ).pack(side="right", padx=5)

        notebook = ttk.Notebook(root, bootstyle="primary")
        notebook.pack(fill="both", expand=True, padx=15, pady=(8, 12))

        tab_inv = InventoryFrame(notebook)
        notebook.add(tab_inv, text="Quản lý tồn kho")

        tab_stats = StatsFrame(notebook)
        notebook.add(tab_stats, text="Thống kê")

        def close_window():
            if messagebox.askyesno("Thoát chương trình", "Bạn có muốn thoát ứng dụng không?", parent=root):
                root.destroy()

        root.protocol("WM_DELETE_WINDOW", close_window)

    login_frame = tk.Frame(root, padx=24, pady=20)
    login_frame.pack(fill="both", expand=True)

    tk.Label(
        login_frame, text="HỆ THỐNG QUẢN LÝ KHO",
        font=("Arial", 14, "bold"), fg="#1976D2"
    ).grid(row=0, column=0, columnspan=2, pady=(5, 20))

    tk.Label(login_frame, text="Tài khoản:").grid(
        row=1, column=0, sticky="e", padx=6, pady=8
    )
    entry_user = tk.Entry(login_frame, width=24)
    entry_user.grid(row=1, column=1, padx=6, pady=8)
    entry_user.focus_set()

    tk.Label(login_frame, text="Mật khẩu:").grid(
        row=2, column=0, sticky="e", padx=6, pady=8
    )
    entry_pass = tk.Entry(login_frame, width=24, show="*")
    entry_pass.grid(row=2, column=1, padx=6, pady=8)

    def handle_login():
        user = entry_user.get().strip()
        pwd = entry_pass.get()

        if not user or not pwd:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tài khoản và mật khẩu.", parent=root)
            return

        try:
            accounts = doc_tai_khoan()
        except ValueError as e:
            messagebox.showerror("Lỗi dữ liệu", str(e), parent=root)
            return

        logged_user = next(
            (acc for acc in accounts
             if acc.get("username") == user and acc.get("password") == pwd),
            None
        )

        if logged_user:
            on_login_success(logged_user)
        else:
            messagebox.showerror("Đăng nhập thất bại", "Sai tài khoản hoặc mật khẩu.", parent=root)
            entry_pass.delete(0, tk.END)
            entry_pass.focus_set()

    root.bind("<Return>", lambda event: handle_login())

    tk.Button(
        login_frame, text="Đăng nhập", width=18,
        bg="#4CAF50", fg="white", command=handle_login
    ).grid(row=3, column=0, columnspan=2, pady=(15, 8))

    root.protocol("WM_DELETE_WINDOW", root.destroy)
    root.mainloop()


if __name__ == "__main__":
    main()