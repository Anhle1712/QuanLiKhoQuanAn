"""Desktop entrypoint for the group's existing Tkinter/ttkbootstrap project."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date
from pathlib import Path
from gui.inventory_view import InventoryFrame
from gui.stats_view import StatsFrame
from services.kho_service import KhoService
from services.auth_service import AuthService
from managers.data_manager import DataManager

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Đăng nhập • Kho nguyên liệu quán ăn')
        self.geometry('440x340')
        self.auth=AuthService()
        self.configure(bg='#f2f5f9')
        ttk.Label(self,text='QUẢN LÝ KHO QUÁN ĂN',font=('Arial',17,'bold')).pack(pady=(32,22))
        form=ttk.Frame(self,padding=12)
        form.pack()
        ttk.Label(form,text='Tên đăng nhập').grid(row=0,column=0,sticky='w',pady=8)
        self.username=ttk.Entry(form,width=26)
        self.username.grid(row=0,column=1,padx=12,pady=8)
        ttk.Label(form,text='Mật khẩu').grid(row=1,column=0,sticky='w',pady=8)
        self.password=ttk.Entry(form,width=26,show='•')
        self.password.grid(row=1,column=1,padx=12,pady=8)
        ttk.Button(self,text='Đăng nhập',command=self.login).pack(pady=10)
        ttk.Button(self,text='Đăng ký tài khoản',command=self.register).pack()
        self.bind('<Return>',lambda e:self.login())
        self.username.focus_set()

    def register(self):
        popup=tk.Toplevel(self)
        popup.title('Tạo tài khoản')
        popup.geometry('390x270')
        frame=ttk.Frame(popup,padding=16);frame.pack(fill='both')
        entries={}
        for i,(key,title,hidden) in enumerate([('username','Tên tài khoản',False),('password','Mật khẩu (≥8 ký tự)',True),('fullname','Họ tên',False)]):
            ttk.Label(frame,text=title).grid(row=i,column=0,sticky='w',pady=8)
            entry=ttk.Entry(frame,width=23,show='•' if hidden else '')
            entry.grid(row=i,column=1,padx=9,pady=8);entries[key]=entry
        def save():
            try:
                self.auth.register(**{k:e.get().strip() for k,e in entries.items()})
                messagebox.showinfo('Thành công','Tạo tài khoản thành công.',parent=popup)
                popup.destroy()
            except (ValueError,OSError) as e:messagebox.showerror('Lỗi',str(e),parent=popup)
        ttk.Button(frame,text='Tạo tài khoản',command=save).grid(row=3,columnspan=2,pady=16)

    def login(self):
        try: user=self.auth.login(self.username.get().strip(),self.password.get())
        except (ValueError,OSError) as e:
            messagebox.showerror('Đăng nhập thất bại',str(e),parent=self)
            return
        self.withdraw()
        window=MainWindow(self,user)
        self.wait_window(window)
        self.destroy()

class MainWindow(tk.Toplevel):
    def __init__(self,parent,user):
        super().__init__(parent)
        self.user=user
        self.service=KhoService()
        self.auth=AuthService()
        self.title('Quản lý kho nguyên liệu quán ăn • '+user['fullname'])
        self.geometry('1150x735')
        self.minsize(960,580)
        self.protocol('WM_DELETE_WINDOW',self.close)
        top=ttk.Frame(self,padding=12);top.pack(fill='x')
        ttk.Label(top,text='HỆ THỐNG QUẢN LÝ KHO',font=('Arial',16,'bold')).pack(side='left')
        ttk.Label(top,text=user['fullname']+'  •  '+('Quản trị viên' if user['role']=='admin' else 'Nhân viên')).pack(side='right')
        nav=ttk.Frame(self,padding=(12,0));nav.pack(fill='x')
        ttk.Button(nav,text='Sao lưu JSON',command=self.backup).pack(side='left',padx=3)
        ttk.Button(nav,text='Đổi mật khẩu',command=self.change_password).pack(side='left',padx=3)
        ttk.Button(nav,text='Làm mới tất cả',command=self.refresh_all).pack(side='left',padx=3)
        self.tabs=ttk.Notebook(self);self.tabs.pack(fill='both',expand=True,padx=12,pady=12)
        self.inventory=InventoryFrame(self.tabs,self.service,user)
        self.tabs.add(self.inventory,text='Nguyên liệu')
        self.suppliers=CrudFrame(self.tabs,self.service,'nha_cung_cap',user)
        self.tabs.add(self.suppliers,text='Nhà cung cấp')
        self.movements=TransactionFrame(self.tabs,self.service,user)
        self.tabs.add(self.movements,text='Nhập / xuất kho')
        self.recipes=RecipeFrame(self.tabs,self.service,user)
        self.tabs.add(self.recipes,text='Món ăn / định mức')
        self.stats=StatsFrame(self.tabs,self.service)
        self.tabs.add(self.stats,text='Thống kê / cảnh báo')
        self.tabs.bind('<<NotebookTabChanged>>',lambda e:self.refresh_current())

    def refresh_current(self):
        current=self.tabs.nametowidget(self.tabs.select())
        if hasattr(current,'load_data'):current.load_data()
    def refresh_all(self):
        for tab in (self.inventory,self.suppliers,self.movements,self.recipes,self.stats):
            tab.load_data()
    def backup(self):
        try:messagebox.showinfo('Đã sao lưu',DataManager.backup_data(),parent=self)
        except OSError as e:messagebox.showerror('Lỗi sao lưu',str(e),parent=self)
    def change_password(self):
        popup=tk.Toplevel(self);popup.title('Đổi mật khẩu');popup.geometry('380x200')
        e1=ttk.Entry(popup,show='•');e2=ttk.Entry(popup,show='•')
        ttk.Label(popup,text='Mật khẩu hiện tại').pack(pady=5);e1.pack()
        ttk.Label(popup,text='Mật khẩu mới (≥8 ký tự)').pack(pady=5);e2.pack()
        def save():
            try:self.auth.change_password(self.user['username'],e1.get(),e2.get());popup.destroy();messagebox.showinfo('Thành công','Đã đổi mật khẩu',parent=self)
            except ValueError as err:messagebox.showerror('Lỗi',str(err),parent=popup)
        ttk.Button(popup,text='Lưu',command=save).pack(pady=9)
    def close(self):
        if messagebox.askyesno('Xác nhận','Thoát chương trình?',parent=self):self.destroy()

class CrudFrame(ttk.Frame):
    def __init__(self,parent,service,entity,user):
        super().__init__(parent,padding=12)
        self.service,self.entity,self.user=service,entity,user
        self.fields=[('ma_ncc','Mã NCC'),('ten_ncc','Tên nhà cung cấp'),('sdt','Số điện thoại'),('dia_chi','Địa chỉ')]
        self.values={}
        toolbar=ttk.Frame(self);toolbar.pack(fill='x',pady=7)
        for k,title in self.fields:
            ttk.Label(toolbar,text=title).pack(side='left',padx=(7,2))
            ent=ttk.Entry(toolbar,width=15);ent.pack(side='left');self.values[k]=ent
        self.save_button=ttk.Button(self,text='Thêm / cập nhật',command=self.save)
        self.save_button.pack(anchor='w',pady=5)
        if user['role']!='admin': self.save_button.state(['disabled'])
        self.tree=ttk.Treeview(self,columns=[k for k,_ in self.fields],show='headings')
        for k,title in self.fields:self.tree.heading(k,text=title);self.tree.column(k,width=200)
        self.tree.pack(fill='both',expand=True,pady=8)
        self.tree.bind('<<TreeviewSelect>>',self.choose)
        ttk.Button(self,text='Xóa mục đã chọn (quản trị viên)',command=self.delete).pack(anchor='w')
        self.load_data()
    def load_data(self):
        self.tree.delete(*self.tree.get_children())
        for row in self.service.list(self.entity):
            self.tree.insert('','end',iid=row['ma_ncc'],values=[row.get(k,'') for k,_ in self.fields])
    def choose(self,event=None):
        selection=self.tree.selection()
        if not selection:return
        data=next((r for r in self.service.list(self.entity) if r['ma_ncc']==selection[0]),None)
        if data:
            for k,e in self.values.items():e.delete(0,'end');e.insert(0,str(data.get(k,'')))
    def save(self):
        if self.user['role']!='admin':return
        try:self.service.upsert(self.entity,{k:e.get().strip() for k,e in self.values.items()});self.load_data()
        except (ValueError,OSError) as e:messagebox.showerror('Lỗi',str(e),parent=self)
    def delete(self):
        if self.user['role']!='admin':messagebox.showwarning('Quyền hạn','Chỉ quản trị viên có quyền xóa',parent=self);return
        selected=self.tree.selection()
        if selected and messagebox.askyesno('Xác nhận','Xóa nhà cung cấp đã chọn?',parent=self):
            try:self.service.delete(self.entity,selected[0]);self.load_data()
            except ValueError as e:messagebox.showerror('Lỗi',str(e),parent=self)

class TransactionFrame(ttk.Frame):
    def __init__(self,parent,service,user):
        super().__init__(parent,padding=12);self.service=service;self.user=user
        form=ttk.LabelFrame(self,text='Lập phiếu nhập hoặc xuất kho',padding=10);form.pack(fill='x')
        self.entries={}
        fields=[('kind','Loại phiếu'),('ma_phieu','Mã phiếu'),('ngay_lap','Ngày YYYY-MM-DD'),('ma_nl','Mã nguyên liệu'),('so_luong','Số lượng'),('don_gia','Giá nhập'),('ma_ncc','Mã NCC'),('ly_do','Lý do')]
        for i,(k,label) in enumerate(fields):
            c=i%4;r=(i//4)*2
            ttk.Label(form,text=label).grid(row=r,column=c,padx=4,sticky='w')
            e=ttk.Combobox(form,values=['nhap','xuat'],state='readonly',width=17) if k=='kind' else ttk.Entry(form,width=20)
            e.grid(row=r+1,column=c,padx=4,pady=(0,8),sticky='ew');self.entries[k]=e
        self.entries['kind'].set('nhap');self.entries['ngay_lap'].insert(0,date.today().isoformat())
        ttk.Button(form,text='Lưu phiếu',command=self.save).grid(row=4,column=0,pady=5)
        ttk.Label(form,text='Mỗi phiếu minh họa một dòng. Có thể dùng API nghiệp vụ để lập phiếu nhiều dòng.').grid(row=4,column=1,columnspan=3,sticky='w')
        self.tree=ttk.Treeview(self,columns=('loai','ma','ngay','nhanvien','tong'),show='headings')
        for k,title in [('loai','Loại'),('ma','Mã phiếu'),('ngay','Ngày'),('nhanvien','Nhân viên'),('tong','Giá trị nhập')]:self.tree.heading(k,text=title);self.tree.column(k,width=160)
        self.tree.pack(fill='both',expand=True,pady=10)
        self.load_data()
    def load_data(self):
        self.tree.delete(*self.tree.get_children())
        for kind in ('nhap','xuat'):
            for row in self.service.list('phieu_'+kind):self.tree.insert('','end',values=(kind,row['ma_phieu'],row['ngay_lap'],row['nhan_vien'],row.get('tong_tien',0)))
    def save(self):
        v={k:e.get().strip() for k,e in self.entries.items()};kind=v['kind']
        voucher={'ma_phieu':v['ma_phieu'],'ngay_lap':v['ngay_lap'],'nhan_vien':self.user['username'],'chi_tiet':[{'ma_nl':v['ma_nl'],'so_luong':v['so_luong'],'don_gia':v['don_gia'] if kind=='nhap' else 0}]}
        if kind=='nhap':voucher['ma_ncc']=v['ma_ncc']
        else:voucher['ly_do']=v['ly_do']
        try:self.service.transact(kind,voucher);self.load_data();messagebox.showinfo('Thành công','Đã cập nhật tồn kho',parent=self)
        except (ValueError,OSError) as e:messagebox.showerror('Lỗi phiếu kho',str(e),parent=self)

class RecipeFrame(ttk.Frame):
    def __init__(self,parent,service,user):
        super().__init__(parent,padding=12);self.service=service;self.user=user
        bar=ttk.Frame(self);bar.pack(fill='x',pady=7)
        fields=[('ma_mon','Mã món'),('ten_mon','Tên món'),('gia_ban','Giá bán')]
        self.entries={}
        for k,title in fields:
            ttk.Label(bar,text=title).pack(side='left',padx=5)
            e=ttk.Entry(bar,width=16);e.pack(side='left');self.entries[k]=e
        ttk.Button(bar,text='Lưu món',command=self.save_dish).pack(side='left',padx=8)
        recipe=ttk.Frame(self);recipe.pack(fill='x',pady=8)
        self.recipe_fields={}
        for k,title in [('ma_mon','Mã món'),('ma_nl','Mã nguyên liệu'),('qty','Định mức / suất'),('portions','Số suất')]:
            ttk.Label(recipe,text=title).pack(side='left',padx=4)
            e=ttk.Entry(recipe,width=12);e.pack(side='left');self.recipe_fields[k]=e
        ttk.Button(recipe,text='Thêm/sửa định mức',command=self.save_recipe).pack(side='left',padx=4)
        ttk.Button(recipe,text='Tính nhu cầu',command=self.calculate).pack(side='left',padx=4)
        self.tree=ttk.Treeview(self,columns=('ma','ten','gia','dinhmuc'),show='headings')
        for k,title in [('ma','Mã món'),('ten','Tên món'),('gia','Giá bán'),('dinhmuc','Định mức nguyên liệu / suất')]:self.tree.heading(k,text=title);self.tree.column(k,width=230)
        self.tree.pack(fill='both',expand=True)
        self.load_data()
    def load_data(self):
        self.tree.delete(*self.tree.get_children())
        recipes=self.service.list('dinh_muc')
        for m in self.service.list('mon_an'):
            description=', '.join(f"{r['ma_nl']}: {r['so_luong_can']}" for r in recipes if r['ma_mon']==m['ma_mon'])
            self.tree.insert('','end',values=(m['ma_mon'],m['ten_mon'],m['gia_ban'],description))
    def save_dish(self):
        if self.user['role']!='admin':messagebox.showwarning('Quyền hạn','Chỉ quản trị viên được sửa món',parent=self);return
        try:self.service.upsert('mon_an',{k:e.get().strip() for k,e in self.entries.items()});self.load_data()
        except ValueError as e:messagebox.showerror('Lỗi',str(e),parent=self)
    def save_recipe(self):
        if self.user['role']!='admin':messagebox.showwarning('Quyền hạn','Chỉ quản trị viên được sửa định mức',parent=self);return
        v={k:e.get().strip() for k,e in self.recipe_fields.items()}
        try:
            existing=[(d['ma_nl'],d['so_luong_can']) for d in self.service.list('dinh_muc') if d['ma_mon']==v['ma_mon'] and d['ma_nl']!=v['ma_nl']]
            self.service.set_recipe(v['ma_mon'],existing+[(v['ma_nl'],v['qty'])]);self.load_data()
        except ValueError as e:messagebox.showerror('Lỗi định mức',str(e),parent=self)
    def calculate(self):
        v={k:e.get().strip() for k,e in self.recipe_fields.items()}
        try:
            rows=self.service.recipe(v['ma_mon'],v['portions'])
            messagebox.showinfo('Nhu cầu nguyên liệu','\n'.join(f"{r['ten_nl']}: cần {r['so_luong_can']:g} {r['don_vi']} | tồn {r['ton_kho']:g} | "+('ĐỦ' if r['du_hang'] else 'THIẾU') for r in rows),parent=self)
        except ValueError as e:messagebox.showerror('Lỗi',str(e),parent=self)

def main():
    app=LoginWindow();app.mainloop()
if __name__=='__main__':main()
