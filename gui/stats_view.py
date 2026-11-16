import tkinter as tk
from tkinter import ttk,messagebox
from services.kho_service import KhoService

class StatsFrame(ttk.Frame):
    def __init__(self,parent,service=None):
        super().__init__(parent,padding=12);self.service=service or KhoService()
        self.summary=ttk.Label(self,text='',font=('Arial',12,'bold'));self.summary.pack(anchor='w',pady=8)
        self.warning=ttk.Treeview(self,columns=('ma','ten','qty','expiry','reason'),show='headings',height=6)
        for key,title in [('ma','Mã NL'),('ten','Tên'),('qty','Tồn'),('expiry','Hạn dùng'),('reason','Cảnh báo')]:self.warning.heading(key,text=title);self.warning.column(key,width=150)
        ttk.Label(self,text='CẢNH BÁO NGUYÊN LIỆU',font=('Arial',11,'bold')).pack(anchor='w')
        self.warning.pack(fill='x',pady=7)
        self.canvas=tk.Canvas(self,bg='white',height=230,highlightbackground='#cbd5e1',highlightthickness=1)
        self.canvas.pack(fill='both',expand=True,pady=10)
        self.canvas.bind('<Configure>',lambda e:self.draw())
        actions=ttk.Frame(self);actions.pack(fill='x')
        ttk.Button(actions,text='Làm mới thống kê',command=self.load_data).pack(side='left',padx=4)
        ttk.Button(actions,text='Lấy danh mục món ăn từ API (lưu JSON riêng)',command=self.fetch_api).pack(side='left',padx=4)
        self.load_data()
    def load_data(self):
        try:
            st=self.service.stats();self.items=self.service.list('nguyen_lieu')
            self.summary.config(text=f"{st['so_loai']} loại nguyên liệu  •  Giá trị kho: {st['gia_tri_ton']:,.0f} VNĐ  •  Nhập: {st['so_phieu_nhap']} phiếu  •  Xuất: {st['so_phieu_xuat']} phiếu")
            self.warning.delete(*self.warning.get_children())
            for n in self.service.warnings():self.warning.insert('','end',values=(n['ma_nl'],n['ten_nl'],n['so_luong_ton'],n.get('han_su_dung',''),n['canh_bao']))
            self.draw()
        except (ValueError,OSError) as e:messagebox.showerror('Lỗi thống kê',str(e),parent=self)
    def draw(self):
        if not hasattr(self,'items'):return
        self.canvas.delete('all')
        width=max(self.canvas.winfo_width(),560);height=max(self.canvas.winfo_height(),200)
        items=self.items[:12]
        if not items:self.canvas.create_text(width/2,height/2,text='Chưa có dữ liệu');return
        maxqty=max(max(float(i['so_luong_ton']) for i in items),1)
        spacing=(width-80)/len(items)
        for index,item in enumerate(items):
            x=45+(index+.5)*spacing;bottom=height-40
            bh=(height-80)*float(item['so_luong_ton'])/maxqty
            self.canvas.create_rectangle(x-16,bottom-bh,x+16,bottom,fill='#239a93',outline='')
            self.canvas.create_text(x,bottom-bh-12,text=f"{item['so_luong_ton']:g}",font=('Arial',9))
            self.canvas.create_text(x,bottom+14,text=item['ma_nl'],font=('Arial',9))
        self.canvas.create_text(width/2,12,text='BIỂU ĐỒ TỒN KHO (theo mã nguyên liệu)',font=('Arial',10,'bold'))
    def fetch_api(self):
        try:rows=self.service.fetch_api();messagebox.showinfo('API thành công',f'Đã lưu {len(rows)} món tham khảo trong data/api_mon_an.json',parent=self)
        except ValueError as e:messagebox.showerror('Lỗi API',str(e),parent=self)
