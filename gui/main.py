import tkinter as tk
from tkinter import messagebox, ttk
from services.kho_service import KhoService
from managers.data_manager import DataManager

class AppQuanLyKho:
    def __init__(self, root):
        self.root = root
        self.root.title("Phần Mềm Quản Lý Kho Quán Ăn")
        self.root.geometry("850x500")

        lbl_title = tk.Label(root, text="HỆ THỐNG QUẢN LÝ KHO QUÁN ĂN", font=("Arial", 16, "bold"), fg="blue")
        lbl_title.pack(pady=10)

        frame_kho = tk.LabelFrame(root, text="Nghiệp vụ Kho & Cảnh báo tồn kho thấp", font=("Arial", 11, "bold"))
        frame_kho.pack(fill="both", expand=True, padx=20, pady=10)

        btn_canh_bao = tk.Button(frame_kho, text="Kiểm tra Cảnh báo Tồn kho (<= 5)", font=("Arial", 10), bg="orange", command=self.hien_thi_canh_bao)
        btn_canh_bao.pack(pady=10)

        # Bảng hiển thị danh sách nguyên liệu
        self.tree = ttk.Treeview(frame_kho, columns=("MaNL", "TenNL", "DonVi", "TonKho", "GiaNhap"), show="headings")
        self.tree.heading("MaNL", text="Mã NL")
        self.tree.heading("TenNL", text="Tên Nguyên Liệu")
        self.tree.heading("DonVi", text="Đơn Vị")
        self.tree.heading("TonKho", text="Tồn Kho")
        self.tree.heading("GiaNhap", text="Giá Nhập")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        self.tai_du_lieu()

    def tai_du_lieu(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        ds_nl = DataManager.doc_json("data/nguyen_lieu.json")
        for nl in ds_nl:
            self.tree.insert("", "end", values=(nl["ma_nl"], nl["ten_nl"], nl["don_vi"], nl["so_luong_ton"], nl["gia_nhap"]))

    def hien_thi_canh_bao(self):
        canh_bao = KhoService.canh_bao_ton_kho(nguong_toi_thieu=5.0)
        if not canh_bao:
            messagebox.showinfo("Thông báo", "Tất cả nguyên liệu đều trên mức tồn kho tối thiểu!")
        else:
            msg = "Các nguyên liệu sắp hết hàng (<= 5):\n"
            for nl in canh_bao:
                msg += f"- {nl['ten_nl']} (Tồn hiện tại: {nl['so_luong_ton']} {nl['don_vi']})\n"
            messagebox.showwarning("Cảnh báo Tồn kho", msg)

if __name__ == "__main__":
    root = tk.Tk()
    app = AppQuanLyKho(root)
    root.mainloop()