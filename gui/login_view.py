import json
import os
import tkinter as tk
from pathlib import Path
from tkinter import messagebox


DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "tai_khoan.json"


def doc_tai_khoan():
    """Đọc danh sách tài khoản; tạo file mẫu nếu chưa có."""
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

    if not DATA_FILE.exists() or DATA_FILE.stat().st_size == 0:
        accounts = [{
            "username": "admin",
            "password": "Admin123!",
            "role": "admin",
            "fullname": "Quản trị viên"
        }]
        ghi_tai_khoan(accounts)
        return accounts

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            accounts = json.load(f)
        if not isinstance(accounts, list):
            raise ValueError("Dữ liệu tài khoản phải là một danh sách.")
        return accounts
    except (json.JSONDecodeError, OSError, ValueError) as e:
        raise ValueError(f"File tài khoản không hợp lệ: {e}")


def ghi_tai_khoan(accounts):
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(accounts, f, ensure_ascii=False, indent=4)


class LoginView(tk.Toplevel):
    def __init__(self, parent, on_login_success):
        super().__init__(parent)
        self.on_login_success = on_login_success
        self.title("Đăng nhập - Quản lý kho quán ăn")
        self.geometry("420x350")
        self.resizable(False, False)
        self.transient(parent)
        self.protocol("WM_DELETE_WINDOW", self.close_app)

        self.create_widgets()
        self.entry_user.focus_set()
        self.bind("<Return>", lambda event: self.handle_login())

    def create_widgets(self):
        frame = tk.Frame(self, padx=24, pady=20)
        frame.pack(fill="both", expand=True)

        tk.Label(
            frame, text="HỆ THỐNG QUẢN LÝ KHO",
            font=("Arial", 14, "bold"), fg="#1976D2"
        ).grid(row=0, column=0, columnspan=2, pady=(5, 20))

        tk.Label(frame, text="Tài khoản:").grid(
            row=1, column=0, sticky="e", padx=6, pady=8
        )
        self.entry_user = tk.Entry(frame, width=24)
        self.entry_user.grid(row=1, column=1, padx=6, pady=8)

        tk.Label(frame, text="Mật khẩu:").grid(
            row=2, column=0, sticky="e", padx=6, pady=8
        )
        self.entry_pass = tk.Entry(frame, width=24, show="*")
        self.entry_pass.grid(row=2, column=1, padx=6, pady=8)

        tk.Button(
            frame, text="Đăng nhập", width=18,
            bg="#4CAF50", fg="white", command=self.handle_login
        ).grid(row=3, column=0, columnspan=2, pady=(15, 8))

        tk.Button(
            frame, text="Tạo tài khoản mới", bd=0, fg="#1976D2",
            command=self.open_register_window
        ).grid(row=4, column=0, pady=5)

        tk.Button(
            frame, text="Đổi mật khẩu", bd=0, fg="#1976D2",
            command=self.open_change_password
        ).grid(row=4, column=1, pady=5)

    def handle_login(self):
        user = self.entry_user.get().strip()
        pwd = self.entry_pass.get()

        if not user or not pwd:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập tài khoản và mật khẩu.", parent=self)
            return

        try:
            accounts = doc_tai_khoan()
        except ValueError as e:
            messagebox.showerror("Lỗi dữ liệu", str(e), parent=self)
            return

        logged_user = next(
            (acc for acc in accounts
             if acc.get("username") == user and acc.get("password") == pwd),
            None
        )

        if logged_user:
            # Truyền thông tin tài khoản cho main.py để xử lý giao diện/quyền.
            self.destroy()
            self.on_login_success(logged_user)
        else:
            messagebox.showerror("Đăng nhập thất bại", "Sai tài khoản hoặc mật khẩu.", parent=self)
            self.entry_pass.delete(0, tk.END)
            self.entry_pass.focus_set()

    def open_register_window(self):
        win = tk.Toplevel(self)
        win.title("Tạo tài khoản")
        win.geometry("360x260")
        win.resizable(False, False)
        win.transient(self)
        frame = tk.Frame(win, padx=18, pady=16)
        frame.pack(fill="both", expand=True)

        tk.Label(frame, text="Tên đăng nhập:").grid(row=0, column=0, sticky="e", pady=7)
        e_user = tk.Entry(frame, width=22)
        e_user.grid(row=0, column=1, pady=7)

        tk.Label(frame, text="Mật khẩu:").grid(row=1, column=0, sticky="e", pady=7)
        e_pass = tk.Entry(frame, width=22, show="*")
        e_pass.grid(row=1, column=1, pady=7)

        tk.Label(frame, text="Họ tên:").grid(row=2, column=0, sticky="e", pady=7)
        e_name = tk.Entry(frame, width=22)
        e_name.grid(row=2, column=1, pady=7)

        def save_register():
            username = e_user.get().strip()
            password = e_pass.get()
            fullname = e_name.get().strip()

            if not username or not password:
                messagebox.showwarning("Thiếu thông tin", "Tài khoản và mật khẩu không được để trống.", parent=win)
                return
            if len(username) < 3:
                messagebox.showwarning("Tài khoản không hợp lệ", "Tên đăng nhập cần có ít nhất 3 ký tự.", parent=win)
                return
            if len(password) < 4:
                messagebox.showwarning("Mật khẩu quá ngắn", "Mật khẩu cần có ít nhất 4 ký tự.", parent=win)
                return

            try:
                accounts = doc_tai_khoan()
                if any(a.get("username", "").casefold() == username.casefold() for a in accounts):
                    messagebox.showwarning("Trùng tài khoản", "Tên đăng nhập này đã được sử dụng.", parent=win)
                    return

                accounts.append({
                    "username": username,
                    "password": password,
                    "role": "user",
                    "fullname": fullname or username
                })
                ghi_tai_khoan(accounts)
                messagebox.showinfo("Thành công", "Tạo tài khoản thành công.", parent=win)
                win.destroy()
            except (OSError, ValueError) as e:
                messagebox.showerror("Lỗi", f"Không lưu được tài khoản: {e}", parent=win)

        tk.Button(
            frame, text="Đăng ký", width=16, bg="#4CAF50",
            fg="white", command=save_register
        ).grid(row=3, column=0, columnspan=2, pady=15)

    def open_change_password(self):
        win = tk.Toplevel(self)
        win.title("Đổi mật khẩu")
        win.geometry("370x250")
        win.resizable(False, False)
        win.transient(self)
        frame = tk.Frame(win, padx=18, pady=15)
        frame.pack(fill="both", expand=True)

        fields = []
        for row, label in enumerate(("Tên đăng nhập:", "Mật khẩu hiện tại:", "Mật khẩu mới:")):
            tk.Label(frame, text=label).grid(row=row, column=0, sticky="e", pady=8, padx=5)
            entry = tk.Entry(frame, width=23, show="*" if row else "")
            entry.grid(row=row, column=1, pady=8, padx=5)
            fields.append(entry)

        def save_password():
            username, old_pwd, new_pwd = (e.get().strip() for e in fields)
            if not username or not old_pwd or not new_pwd:
                messagebox.showwarning("Thiếu thông tin", "Vui lòng điền đầy đủ các ô.", parent=win)
                return
            if len(new_pwd) < 4:
                messagebox.showwarning("Mật khẩu quá ngắn", "Mật khẩu mới cần ít nhất 4 ký tự.", parent=win)
                return
            try:
                accounts = doc_tai_khoan()
                account = next(
                    (a for a in accounts if a.get("username") == username and a.get("password") == old_pwd),
                    None
                )
                if account is None:
                    messagebox.showerror("Không hợp lệ", "Tài khoản hoặc mật khẩu hiện tại không đúng.", parent=win)
                    return
                account["password"] = new_pwd
                ghi_tai_khoan(accounts)
                messagebox.showinfo("Thành công", "Đã đổi mật khẩu.", parent=win)
                win.destroy()
            except (OSError, ValueError) as e:
                messagebox.showerror("Lỗi", f"Không cập nhật được mật khẩu: {e}", parent=win)

        tk.Button(frame, text="Lưu mật khẩu mới", command=save_password).grid(
            row=3, column=0, columnspan=2, pady=12
        )

    def close_app(self):
        self.master.destroy()
