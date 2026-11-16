import tkinter as tk
from tkinter import ttk,messagebox,filedialog
try:
    from tkcalendar import DateEntry
except ImportError:
    # Offline fallback: DateEntry supplied by tkcalendar when installed.
    from datetime import date
    class DateEntry(ttk.Entry):
        def __init__(self,parent,date_pattern=None,**kwargs):
            super().__init__(parent,**kwargs)
            self.insert(0,date.today().strftime('%d/%m/%Y'))
from services.kho_service import KhoService

class InventoryFrame(ttk.Frame):
    """Custom inventory widget extending ttk.Frame; retains original screen's Treeview/DateEntry."""
    def __init__(self,parent,service=None,user=None):
        super().__init__(parent,padding=12)
        self.service=service or KhoService();self.user=user or {'role':'admin'}
        self.values={}
        form=ttk.LabelFrame(self,text='Thông tin nguyên liệu',padding=8);form.pack(fill='x')
        columns=[('ma_nl','Mã NL'),('ten_nl','Tên nguyên liệu'),('don_vi','Đơn vị'),('gia_nhap','Giá nhập'),('so_luong_ton','Tồn đầu kỳ'),('nguong_toi_thieu','Ngưỡng tối thiểu'),('han_su_dung','Hạn YYYY-MM-DD')]
        for i,(key,label) in enumerate(columns):
            c=i%4;r=(i//4)*2
            ttk.Label(form,text=label).grid(row=r,column=c,sticky='w',padx=4)
            entry=ttk.Entry(form,width=19);entry.grid(row=r+1,column=c,sticky='ew',padx=4,pady=(0,6))
            self.values[key]=entry
        self.values['so_luong_ton'].insert(0,'0');self.values['nguong_toi_thieu'].insert(0,'5')
        ttk.Label(form,text='Ngày xem:').grid(row=4,column=0)
        self.calendar=DateEntry(form,date_pattern='dd/mm/yyyy',width=13)
        self.calendar.grid(row=5,column=0,sticky='w')
        controls=ttk.Frame(self);controls.pack(fill='x',pady=8)
        ttk.Label(controls,text='Tìm mã/tên:').pack(side='left')
        self.search=tk.StringVar();ttk.Entry(controls,textvariable=self.search,width=26).pack(side='left',padx=5)
        self.search.trace_add('write',lambda *_:self.show_data())
        ttk.Button(controls,text='Lưu nguyên liệu',command=self.save).pack(side='left',padx=4)
        ttk.Button(controls,text='Xóa',command=self.delete).pack(side='left',padx=4)
        ttk.Button(controls,text='Xuất CSV',command=self.export).pack(side='left',padx=4)
        ttk.Button(controls,text='Làm mới',command=self.load_data).pack(side='left',padx=4)
        self.tree=ttk.Treeview(self,columns=('ma','ten','dvt','qty','price','expiry'),show='headings',height=13)
        for key,title,width in [('ma','Mã NL',110),('ten','Tên nguyên liệu',220),('dvt','Đơn vị',105),('qty','Tồn kho',110),('price','Đơn giá',140),('expiry','Hạn sử dụng',130)]:
            self.tree.heading(key,text=title);self.tree.column(key,width=width)
        self.tree.pack(fill='both',expand=True)
        self.tree.bind('<<TreeviewSelect>>',self.choose)
        self.status=ttk.Label(self,text='');self.status.pack(anchor='w',pady=6)
        self.load_data()
    def load_data(self):
        try:self.items=self.service.list('nguyen_lieu');self.show_data()
        except (ValueError,OSError) as e:messagebox.showerror('Lỗi dữ liệu',str(e),parent=self)
    def show_data(self):
        if not hasattr(self,'items'):return
        self.tree.delete(*self.tree.get_children())
        term=self.search.get().casefold().strip()
        displayed=0
        for item in self.items:
            if term not in (item['ma_nl']+' '+item['ten_nl']).casefold():continue
            self.tree.insert('','end',iid=item['ma_nl'],values=(item['ma_nl'],item['ten_nl'],item['don_vi'],item['so_luong_ton'],item['gia_nhap'],item.get('han_su_dung','')))
            displayed+=1
        self.status.config(text=f'Hiển thị {displayed}/{len(self.items)} nguyên liệu. Tồn kho chỉ thay đổi qua nghiệp vụ nhập/xuất sau khi tạo.')
    def choose(self,event=None):
        selected=self.tree.selection()
        if not selected:return
        item=next((x for x in self.items if x['ma_nl']==selected[0]),None)
        if item:
            for k,e in self.values.items():e.delete(0,'end');e.insert(0,str(item.get(k,'')))
    def save(self):
        if self.user['role']!='admin':messagebox.showwarning('Quyền hạn','Chỉ quản trị viên được sửa nguyên liệu',parent=self);return
        try:self.service.upsert('nguyen_lieu',{k:e.get().strip() for k,e in self.values.items()});self.load_data()
        except (ValueError,OSError) as e:messagebox.showerror('Lỗi',str(e),parent=self)
    def delete(self):
        if self.user['role']!='admin':messagebox.showwarning('Quyền hạn','Chỉ quản trị viên được xóa nguyên liệu',parent=self);return
        selected=self.tree.selection()
        if not selected:return
        if messagebox.askyesno('Xác nhận','Xóa nguyên liệu?',parent=self):
            try:self.service.delete('nguyen_lieu',selected[0]);self.load_data()
            except ValueError as e:messagebox.showerror('Lỗi',str(e),parent=self)
    def export(self):
        path=filedialog.asksaveasfilename(parent=self,defaultextension='.csv',filetypes=[('CSV','*.csv')])
        if path:
            try:self.service.export_csv('nguyen_lieu',path);messagebox.showinfo('Xuất CSV','Đã xuất dữ liệu',parent=self)
            except (ValueError,OSError) as e:messagebox.showerror('Lỗi',str(e),parent=self)
