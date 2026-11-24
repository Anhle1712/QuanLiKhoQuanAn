"""Điểm chạy chính của ứng dụng quản lý kho."""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
from gui.inventory_view import InventoryFrame
from gui.stats_view import StatsFrame
from services.kho_service import KhoService
from services.auth_service import AuthService
from managers.data_manager import DataManager
from services.txt_importer import TxtImporter

GREEN='#1f5f43'; GREEN2='#79b43a'; CREAM='#faf7ef'; RED='#b42318'; SUCCESS='#18794e'

class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('Nhà Bếp Thông Minh • Đăng nhập'); self.geometry('470x430'); self.resizable(False,False); self.configure(bg=CREAM)
        card=tk.Frame(self,bg='white',highlightbackground='#d8e1d8',highlightthickness=1); card.place(relx=.5,rely=.5,anchor='center',width=390,height=350)
        tk.Label(card,text='♨',font=('Arial',28,'bold'),fg=GREEN,bg='white').pack(pady=(20,0))
        tk.Label(card,text='NHÀ BẾP THÔNG MINH',font=('Arial',17,'bold'),fg=GREEN,bg='white').pack(pady=(0,5))
        tk.Label(card,text='Hệ thống quản lý kho nguyên liệu',font=('Arial',10),fg='#63756d',bg='white').pack(pady=(0,20))
        f=tk.Frame(card,bg='white');f.pack(fill='x',padx=30)
        tk.Label(f,text='Tài khoản',bg='white',fg='#29443a',font=('Arial',10,'bold')).pack(anchor='w');self.username=ttk.Entry(f);self.username.pack(fill='x',pady=(4,12))
        tk.Label(f,text='Mật khẩu',bg='white',fg='#29443a',font=('Arial',10,'bold')).pack(anchor='w');self.password=ttk.Entry(f,show='•');self.password.pack(fill='x',pady=(4,15))
        tk.Button(card,text='ĐĂNG NHẬP',command=self.login,bg=GREEN,fg='white',font=('Arial',10,'bold'),relief='flat',height=2,cursor='hand2').pack(fill='x',padx=30)
        tk.Button(card,text='Tạo tài khoản mới',command=self.register,bg='white',fg=GREEN,bd=0).pack(pady=8)
        self.bind('<Return>',lambda e:self.login()); self.username.focus_set()
    def login(self):
        try:user=AuthService().login(self.username.get().strip(),self.password.get())
        except (ValueError,OSError) as e:messagebox.showerror('Đăng nhập thất bại',str(e),parent=self);return
        self.withdraw(); win=MainWindow(self,user); self.wait_window(win); self.destroy()
    def register(self):
        win=tk.Toplevel(self);win.title('Tạo tài khoản');win.geometry('380x280');win.configure(bg=CREAM)
        f=tk.Frame(win,bg='white',padx=22,pady=20);f.pack(fill='both',expand=True,padx=12,pady=12); entries={}
        for i,(k,t,hidden) in enumerate([('username','Tên tài khoản',False),('password','Mật khẩu',True),('fullname','Họ tên',False)]):
            tk.Label(f,text=t,bg='white').grid(row=i,column=0,sticky='w',pady=7);e=ttk.Entry(f,show='•' if hidden else '');e.grid(row=i,column=1,padx=10,pady=7);entries[k]=e
        def save():
            try: AuthService().register(**{k:e.get().strip() for k,e in entries.items()});messagebox.showinfo('Thành công','Tạo tài khoản thành công.',parent=win);win.destroy()
            except (ValueError,OSError) as e:messagebox.showerror('Lỗi',str(e),parent=win)
        tk.Button(f,text='Đăng ký',command=save,bg=GREEN,fg='white',relief='flat',width=18).grid(row=3,columnspan=2,pady=14)

class MainWindow(tk.Toplevel):
    def __init__(self,parent,user):
        super().__init__(parent);self.user=user;self.service=KhoService();self.auth=AuthService();self.title('Nhà Bếp Thông Minh • '+user['fullname']);self.geometry('1260x780');self.minsize(1050,650);self.configure(bg=CREAM);self.protocol('WM_DELETE_WINDOW',self.close)
        self.build_style();self.auto_import_txt();self.build_layout()
    def auto_import_txt(self):
        # Tự đọc các file .txt trong data/import khi mở chương trình.
        folder=DataManager._path('data/import')
        folder.mkdir(parents=True,exist_ok=True)
        for p in sorted(folder.glob('*.txt')):
            try:
                result=TxtImporter(self.service).import_file(p)
                if any(result.values()):
                    messagebox.showinfo('Tự nhập dữ liệu TXT',f'Đã tự nhập dữ liệu từ {p.name}:\n\n{TxtImporter.summary(result)}',parent=self)
            except (ValueError,OSError,UnicodeError) as e:
                messagebox.showwarning('File TXT không hợp lệ',f'Không thể nhập {p.name}:\n{e}',parent=self)

    def build_style(self):
        s=ttk.Style(self)
        try:s.theme_use('clam')
        except tk.TclError:pass
        s.configure('TNotebook',background=CREAM,borderwidth=0);s.configure('TNotebook.Tab',padding=(18,9),font=('Arial',10,'bold'))
        s.configure('Card.TFrame',background='white')
    def build_layout(self):
        side=tk.Frame(self,bg=GREEN,width=220);side.pack(side='left',fill='y');side.pack_propagate(False)
        tk.Label(side,text='♨',font=('Arial',25,'bold'),fg='white',bg=GREEN).pack(pady=(28,0));tk.Label(side,text='Nhà Bếp\nThông Minh',font=('Arial',16,'bold'),fg='white',bg=GREEN).pack(pady=(0,30))
        self.tabs=ttk.Notebook(self);self.tabs.pack(side='right',fill='both',expand=True,padx=0,pady=0)
        items=[('Tổng quan',self.dashboard),('Quản lý kho',lambda:self.add_inventory()),('Đơn nhập / xuất',lambda:self.add_transaction()),('Nhà cung cấp',lambda:self.add_supplier()),('Món ăn',lambda:self.add_recipe()),('Báo cáo',lambda:self.add_stats()),('Cài đặt',self.settings)]
        self.page_map={};
        for name,cmd in items:
            b=tk.Button(side,text='  '+name,anchor='w',command=cmd,bg=GREEN,fg='white',activebackground=GREEN2,activeforeground='white',bd=0,font=('Arial',10,'bold'),height=2,padx=18,cursor='hand2');b.pack(fill='x',padx=14,pady=3)
        tk.Label(side,text=f"{self.user['fullname']}\n{'Quản trị viên' if self.user['role']=='admin' else 'Nhân viên'}",bg=GREEN,fg='#d9ebdf',font=('Arial',9),justify='left').pack(side='bottom',anchor='w',padx=28,pady=25)
        self.dashboard()
    def clear_tabs(self):
        for tab in self.tabs.tabs(): self.tabs.forget(tab)
    def dashboard(self):
        self.clear_tabs();frame=ttk.Frame(self.tabs,padding=28);self.tabs.add(frame,text='Tổng quan')
        ttk.Label(frame,text='HỆ THỐNG QUẢN LÝ KHO',font=('Arial',25,'bold'),foreground=GREEN).pack(anchor='w');ttk.Label(frame,text='Theo dõi tồn kho chính xác – Chủ động nhập xuất – Vận hành hiệu quả',font=('Arial',11),foreground='#53635b').pack(anchor='w',pady=(4,25))
        st=self.service.stats();stock=self.service.list('nguyen_lieu');warnings=self.service.warnings();total_qty=sum(float(x['so_luong_ton']) for x in stock)
        cards=tk.Frame(frame,bg=CREAM);cards.pack(fill='x');vals=[('Tổng mặt hàng',str(st['so_loai']),'#ffe2b2'),('Đang có trong kho',f'{total_qty:g} kg','#dcefd3'),('Sắp hết hàng',f'{len(warnings)} món','#ffd9d5'),('Tổng giá trị kho',f"{st['gia_tri_ton']:,.0f} đ",'#d7eafb')]
        for title,val,bg in vals:
            c=tk.Frame(cards,bg=bg,width=240,height=120);c.pack(side='left',fill='both',expand=True,padx=6);c.pack_propagate(False);tk.Label(c,text=title,bg=bg,fg=GREEN,font=('Arial',11,'bold')).pack(anchor='w',padx=20,pady=(20,0));tk.Label(c,text=val,bg=bg,fg='#173f2e',font=('Arial',20,'bold')).pack(anchor='w',padx=20,pady=12)
        box=tk.Frame(frame,bg='white',highlightbackground='#dbe2db',highlightthickness=1);box.pack(fill='both',expand=True,pady=22);tk.Label(box,text='Cảnh báo gần đây',bg='white',fg=GREEN,font=('Arial',12,'bold')).pack(anchor='w',padx=20,pady=14)
        for x in warnings[:6]:
            fg=RED if ('hết hạn' in x['canh_bao'] or 'thấp' in x['canh_bao']) else GREEN
            tk.Label(box,text=f"• {x['ma_nl']}  {x['ten_nl']}  —  {x['canh_bao']}",bg='white',fg=fg,font=('Arial',10)).pack(anchor='w',padx=28,pady=4)
        if not warnings:tk.Label(box,text='✓ Kho đang ổn định, chưa có cảnh báo.',bg='white',fg=SUCCESS,font=('Arial',10,'bold')).pack(anchor='w',padx=28,pady=8)
    def add_inventory(self):self.clear_tabs();f=InventoryFrame(self.tabs,self.service,self.user);self.tabs.add(f,text='Quản lý kho')
    def add_supplier(self):
        self.clear_tabs();f=CrudFrame(self.tabs,self.service,'nha_cung_cap',self.user);self.tabs.add(f,text='Nhà cung cấp')
    def add_transaction(self):
        self.clear_tabs();f=TransactionFrame(self.tabs,self.service,self.user);self.tabs.add(f,text='Đơn nhập / xuất')
    def add_recipe(self):
        self.clear_tabs();f=RecipeFrame(self.tabs,self.service,self.user);self.tabs.add(f,text='Món ăn')
    def add_stats(self):self.clear_tabs();f=StatsFrame(self.tabs,self.service);self.tabs.add(f,text='Báo cáo')
    def settings(self):
        self.clear_tabs();f=ttk.Frame(self.tabs,padding=28);self.tabs.add(f,text='Cài đặt');ttk.Label(f,text='CÀI ĐẶT HỆ THỐNG',font=('Arial',22,'bold'),foreground=GREEN).pack(anchor='w',pady=(0,20));ttk.Button(f,text='Nhập dữ liệu từ file TXT',command=self.import_txt).pack(anchor='w',pady=6);ttk.Button(f,text='Sao lưu toàn bộ JSON',command=self.backup).pack(anchor='w',pady=6);ttk.Button(f,text='Làm mới dữ liệu',command=self.dashboard).pack(anchor='w',pady=6);ttk.Button(f,text='Đổi mật khẩu',command=self.change_password).pack(anchor='w',pady=6)
    def import_txt(self):
        p=filedialog.askopenfilename(title='Chọn file dữ liệu TXT',filetypes=[('File TXT','*.txt'),('Tất cả file','*.*')],parent=self)
        if not p:return
        try:
            result=TxtImporter(self.service).import_file(p)
            messagebox.showinfo('Nhập TXT thành công','Đã đọc và lưu dữ liệu vào JSON:\n\n'+TxtImporter.summary(result),parent=self)
            self.dashboard()
        except (ValueError,OSError,UnicodeError) as e:
            messagebox.showerror('Nhập TXT thất bại',str(e),parent=self)

    def backup(self):
        try:path=DataManager.backup_data();messagebox.showinfo('Đã lưu JSON',f'Đã sao lưu toàn bộ dữ liệu JSON tại:\n{path}',parent=self)
        except OSError as e:messagebox.showerror('Lỗi',str(e),parent=self)
    def change_password(self):
        win=tk.Toplevel(self);win.title('Đổi mật khẩu');win.geometry('380x220');f=ttk.Frame(win,padding=20);f.pack(fill='both',expand=True);a=ttk.Entry(f,show='•');b=ttk.Entry(f,show='•');ttk.Label(f,text='Mật khẩu hiện tại').pack(anchor='w');a.pack(fill='x',pady=5);ttk.Label(f,text='Mật khẩu mới').pack(anchor='w');b.pack(fill='x',pady=5)
        def save():
            try:self.auth.change_password(self.user['username'],a.get(),b.get());messagebox.showinfo('Thành công','Đã đổi mật khẩu.',parent=win);win.destroy()
            except ValueError as e:messagebox.showerror('Lỗi',str(e),parent=win)
        ttk.Button(f,text='Lưu',command=save).pack(pady=10)
    def close(self):
        if messagebox.askyesno('Xác nhận','Thoát chương trình?',parent=self):self.destroy()

class CrudFrame(ttk.Frame):
    def __init__(self,parent,service,entity,user):
        super().__init__(parent,padding=20);self.service=service;self.entity=entity;self.user=user;self.fields=[('ma_ncc','Mã NCC'),('ten_ncc','Tên nhà cung cấp'),('sdt','Số điện thoại'),('dia_chi','Địa chỉ')];self.values={}
        ttk.Label(self,text='NHÀ CUNG CẤP',font=('Arial',20,'bold'),foreground=GREEN).pack(anchor='w',pady=(0,12));form=ttk.Frame(self);form.pack(fill='x');
        for i,(k,t) in enumerate(self.fields):ttk.Label(form,text=t,font=('Arial',10,'bold')).grid(row=0,column=i,padx=6,sticky='w');e=ttk.Entry(form,width=22);e.grid(row=1,column=i,padx=6,pady=6,sticky='ew');form.columnconfigure(i,weight=1);self.values[k]=e
        b=ttk.Frame(self);b.pack(fill='x',pady=8);ttk.Button(b,text='Làm mới',command=self.new).pack(side='left',padx=4);ttk.Button(b,text='Thêm mới',command=self.add_new).pack(side='left',padx=4);ttk.Button(b,text='Xóa',command=self.delete).pack(side='left',padx=4);ttk.Button(b,text='Xuất CSV',command=self.export).pack(side='left',padx=4)
        self.tree=ttk.Treeview(self,columns=[k for k,_ in self.fields],show='headings');
        for k,t in self.fields:self.tree.heading(k,text=t);self.tree.column(k,width=200)
        self.tree.pack(fill='both',expand=True);self.tree.bind('<<TreeviewSelect>>',self.choose);self.load_data();self.new()
    def new(self):self.values['ma_ncc'].delete(0,'end');self.values['ma_ncc'].insert(0,DataManager.next_code(self.service.list(self.entity),'ma_ncc','NCC'));self.values['ma_ncc'].config(state='readonly')
    def load_data(self):
        self.tree.delete(*self.tree.get_children())
        for row in self.service.list(self.entity):self.tree.insert('','end',iid=row['ma_ncc'],values=[row.get(k,'') for k,_ in self.fields])
    def choose(self,event=None):
        s=self.tree.selection();
        if not s:return
        row=next(x for x in self.service.list(self.entity) if x['ma_ncc']==s[0]);self.values['ma_ncc'].config(state='normal')
        for k,e in self.values.items():e.delete(0,'end');e.insert(0,str(row.get(k,'')))
        self.values['ma_ncc'].config(state='readonly')
    def add_new(self):
        if self.user.get('role')!='admin':
            messagebox.showwarning('Quyền hạn','Chỉ quản trị viên được thêm nhà cung cấp.',parent=self)
            return
        try:
            self.values['ma_ncc'].config(state='normal')
            self.values['ma_ncc'].delete(0,'end')
            code=DataManager.next_code(self.service.list(self.entity),'ma_ncc','NCC')
            self.values['ma_ncc'].insert(0,code)
            self.values['ma_ncc'].config(state='readonly')
            self.service.upsert(self.entity,{k:e.get().strip() for k,e in self.values.items()})
            self.load_data(); messagebox.showinfo('Thành công','Đã thêm nhà cung cấp vào JSON.',parent=self); self.new()
        except (ValueError,OSError) as e: messagebox.showerror('Thêm thất bại',str(e),parent=self)
    def save(self):
        if self.user.get('role')!='admin':messagebox.showwarning('Quyền hạn','Chỉ quản trị viên được sửa.',parent=self);return
        try:self.service.upsert(self.entity,{k:e.get().strip() for k,e in self.values.items()});self.load_data();messagebox.showinfo('Thành công','Đã lưu nhà cung cấp vào JSON.',parent=self);self.new()
        except (ValueError,OSError) as e:messagebox.showerror('Lỗi',str(e),parent=self)
    def delete(self):
        s=self.tree.selection();
        if self.user.get('role')!='admin':return
        if s and messagebox.askyesno('Xác nhận','Xóa nhà cung cấp?',parent=self):
            try:self.service.delete(self.entity,s[0]);self.load_data();self.new()
            except ValueError as e:messagebox.showerror('Lỗi',str(e),parent=self)
    def export(self):
        p=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')],initialfile='nha_cung_cap.csv',parent=self)
        if p:
            try:self.service.export_csv(self.entity,p);messagebox.showinfo('Xuất CSV','Đã xuất CSV.',parent=self)
            except (ValueError,OSError) as e:messagebox.showerror('Lỗi',str(e),parent=self)

class TransactionFrame(ttk.Frame):
    def __init__(self,parent,service,user):
        super().__init__(parent,padding=20);self.service=service;self.user=user
        ttk.Label(self,text='ĐƠN NHẬP / XUẤT',font=('Arial',20,'bold'),foreground=GREEN).pack(anchor='w',pady=(0,12));form=ttk.Frame(self);form.pack(fill='x');self.e={}
        fields=[('kind','Loại phiếu'),('ma_phieu','Mã phiếu'),('ngay_lap','Ngày lập'),('ma_nl','Nguyên liệu'),('so_luong','Số lượng'),('don_gia','Đơn giá'),('ma_ncc','Nhà cung cấp'),('ly_do','Lý do')]
        for i,(k,t) in enumerate(fields):
            r=i//4;c=i%4;ttk.Label(form,text=t,font=('Arial',10,'bold')).grid(row=r*2,column=c,padx=6,sticky='w')
            if k=='kind':e=ttk.Combobox(form,values=['nhap','xuat'],state='readonly')
            elif k=='ma_nl':e=ttk.Combobox(form,state='readonly');
            elif k=='ma_ncc':e=ttk.Combobox(form,state='readonly')
            else:e=ttk.Entry(form)
            e.grid(row=r*2+1,column=c,padx=6,pady=(4,12),sticky='ew');form.columnconfigure(c,weight=1);self.e[k]=e
        self.e['kind'].set('nhap');self.refresh_choices();self.e['ma_phieu'].insert(0,self.next_voucher());self.e['ngay_lap'].insert(0,date.today().isoformat());self.e['kind'].bind('<<ComboboxSelected>>',lambda e:self.refresh_voucher())
        bar=ttk.Frame(self);bar.pack(fill='x');ttk.Button(bar,text='Làm mới',command=self.refresh_voucher).pack(side='left',padx=4);ttk.Button(bar,text='Thêm mới',command=self.add_new).pack(side='left',padx=4);ttk.Button(bar,text='Xuất CSV',command=self.export).pack(side='left',padx=4)
        self.tree=ttk.Treeview(self,columns=('loai','ma','ngay','nv','tong'),show='headings');
        for k,t in [('loai','Loại'),('ma','Mã phiếu'),('ngay','Ngày'),('nv','Nhân viên'),('tong','Giá trị')]:self.tree.heading(k,text=t);self.tree.column(k,width=180)
        self.tree.pack(fill='both',expand=True,pady=12);self.load_data()
    def refresh_choices(self):
        self.e['ma_nl']['values']=[f"{x['ma_nl']} - {x['ten_nl']}" for x in self.service.list('nguyen_lieu')];self.e['ma_ncc']['values']=[f"{x['ma_ncc']} - {x['ten_ncc']}" for x in self.service.list('nha_cung_cap')]
        if self.e['ma_nl']['values']:self.e['ma_nl'].set(self.e['ma_nl']['values'][0])
        if self.e['ma_ncc']['values']:self.e['ma_ncc'].set(self.e['ma_ncc']['values'][0])
    def next_voucher(self):return DataManager.next_code(self.service.list('phieu_'+self.e['kind'].get() if self.e.get('kind') else 'phieu_nhap'),'ma_phieu','PN' if (self.e.get('kind') and self.e['kind'].get()=='nhap') else 'PX')
    def refresh_voucher(self,event=None):self.e['ma_phieu'].delete(0,'end');self.e['ma_phieu'].insert(0,self.next_voucher())
    def load_data(self):
        self.tree.delete(*self.tree.get_children());self.refresh_choices()
        for kind in ('nhap','xuat'):
            for r in self.service.list('phieu_'+kind):self.tree.insert('','end',values=(kind,r['ma_phieu'],r['ngay_lap'],r['nhan_vien'],f"{float(r.get('tong_tien',0)):,.0f}"))
    def add_new(self):
        # Tạo mã phiếu mới và ghi phiếu ngay khi bấm Thêm mới.
        self.refresh_voucher()
        self.save()
    def save(self):
        kind=self.e['kind'].get();code=self.e['ma_nl'].get().split(' - ')[0];ncc=self.e['ma_ncc'].get().split(' - ')[0]
        v={'ma_phieu':self.e['ma_phieu'].get().strip(),'ngay_lap':self.e['ngay_lap'].get().strip(),'nhan_vien':self.user['username'],'chi_tiet':[{'ma_nl':code,'so_luong':self.e['so_luong'].get().strip(),'don_gia':self.e['don_gia'].get().strip() if kind=='nhap' else 0}]}
        if kind=='nhap':v['ma_ncc']=ncc
        else:v['ly_do']=self.e['ly_do'].get().strip()
        try:self.service.transact(kind,v);self.load_data();self.refresh_voucher();messagebox.showinfo('Thành công','✓ Phiếu đã lưu vào JSON và cập nhật tồn kho.',parent=self)
        except (ValueError,OSError) as e:messagebox.showerror('Lưu phiếu thất bại',str(e),parent=self)
    def export(self):
        p=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')],initialfile='phieu_kho.csv',parent=self)
        if not p:return
        try:
            import csv
            rows=[]
            for kind in ('nhap','xuat'):
                for r in self.service.list('phieu_'+kind):rows.append(dict(r,loai=kind))
            if not rows:raise ValueError('Chưa có dữ liệu để xuất')
            keys=list(dict.fromkeys(k for r in rows for k in r));
            with open(p,'w',encoding='utf-8-sig',newline='') as f: w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
            messagebox.showinfo('Xuất CSV','Đã xuất CSV.',parent=self)
        except (ValueError,OSError) as e:messagebox.showerror('Lỗi',str(e),parent=self)

class RecipeFrame(ttk.Frame):
    def __init__(self,parent,service,user):
        super().__init__(parent,padding=20);self.service=service;self.user=user;ttk.Label(self,text='MÓN ĂN & ĐỊNH MỨC',font=('Arial',20,'bold'),foreground=GREEN).pack(anchor='w',pady=(0,12));self.build();self.load_data()
    def build(self):
        f=ttk.Frame(self);f.pack(fill='x');self.dish={}
        for i,(k,t) in enumerate([('ma_mon','Mã món'),('ten_mon','Tên món'),('gia_ban','Giá bán')]):ttk.Label(f,text=t,font=('Arial',10,'bold')).grid(row=0,column=i,padx=6,sticky='w');e=ttk.Entry(f);e.grid(row=1,column=i,padx=6,pady=5,sticky='ew');f.columnconfigure(i,weight=1);self.dish[k]=e
        b=ttk.Frame(self);b.pack(fill='x',pady=8);ttk.Button(b,text='Làm mới',command=self.new_dish).pack(side='left',padx=4);ttk.Button(b,text='Thêm mới',command=self.add_dish).pack(side='left',padx=4);ttk.Button(b,text='Xuất CSV',command=self.export).pack(side='left',padx=4)
        r=ttk.Frame(self);r.pack(fill='x',pady=8);self.rec={}
        for i,(k,t) in enumerate([('ma_mon','Mã món'),('ma_nl','Nguyên liệu'),('qty','Định mức / suất'),('portions','Số suất')]):ttk.Label(r,text=t,font=('Arial',10,'bold')).grid(row=0,column=i,padx=6,sticky='w');e=ttk.Entry(r) if k in ('qty','portions') else ttk.Combobox(r,state='readonly');e.grid(row=1,column=i,padx=6,pady=5,sticky='ew');r.columnconfigure(i,weight=1);self.rec[k]=e
        ttk.Button(r,text='Lưu định mức',command=self.save_recipe).grid(row=1,column=4,padx=6);ttk.Button(r,text='Tính nhu cầu',command=self.calculate).grid(row=1,column=5,padx=6)
        self.tree=ttk.Treeview(self,columns=('ma','ten','gia','dm'),show='headings');
        for k,t in [('ma','Mã món'),('ten','Tên món'),('gia','Giá bán'),('dm','Định mức nguyên liệu / suất')]:self.tree.heading(k,text=t);self.tree.column(k,width=240)
        self.tree.pack(fill='both',expand=True,pady=10);self.tree.bind('<<TreeviewSelect>>',self.choose)
    def new_dish(self):self.dish['ma_mon'].delete(0,'end');self.dish['ma_mon'].insert(0,DataManager.next_code(self.service.list('mon_an'),'ma_mon','M'))
    def load_data(self):
        self.tree.delete(*self.tree.get_children());self.rec['ma_mon']['values']=[x['ma_mon'] for x in self.service.list('mon_an')];self.rec['ma_nl']['values']=[f"{x['ma_nl']} - {x['ten_nl']}" for x in self.service.list('nguyen_lieu')]
        if self.rec['ma_mon']['values'] and not self.rec['ma_mon'].get():self.rec['ma_mon'].set(self.rec['ma_mon']['values'][0])
        if self.rec['ma_nl']['values'] and not self.rec['ma_nl'].get():self.rec['ma_nl'].set(self.rec['ma_nl']['values'][0])
        dms=self.service.list('dinh_muc')
        for m in self.service.list('mon_an'):
            desc=', '.join(f"{x['ma_nl']}: {x['so_luong_can']}" for x in dms if x['ma_mon']==m['ma_mon']);self.tree.insert('','end',iid=m['ma_mon'],values=(m['ma_mon'],m['ten_mon'],f"{float(m['gia_ban']):,.0f}",desc))
        if not self.dish['ma_mon'].get():self.new_dish()
    def choose(self,event=None):
        s=self.tree.selection();
        if not s:return
        m=next(x for x in self.service.list('mon_an') if x['ma_mon']==s[0]);self.dish['ma_mon'].delete(0,'end');self.dish['ma_mon'].insert(0,m['ma_mon']);self.dish['ten_mon'].delete(0,'end');self.dish['ten_mon'].insert(0,m['ten_mon']);self.dish['gia_ban'].delete(0,'end');self.dish['gia_ban'].insert(0,m['gia_ban'])
    def add_dish(self):
        if self.user.get('role')!='admin':
            messagebox.showwarning('Quyền hạn','Chỉ quản trị viên được thêm món ăn.',parent=self); return
        try:
            self.new_dish()
            self.service.upsert('mon_an',{k:e.get().strip() for k,e in self.dish.items()})
            self.load_data(); messagebox.showinfo('Thành công','Đã thêm món ăn vào JSON.',parent=self); self.new_dish()
        except (ValueError,OSError) as e: messagebox.showerror('Thêm thất bại',str(e),parent=self)
    def save_dish(self):
        if self.user.get('role')!='admin':return
        try:self.service.upsert('mon_an',{k:e.get().strip() for k,e in self.dish.items()});self.load_data();messagebox.showinfo('Thành công','Đã lưu món vào JSON.',parent=self)
        except (ValueError,OSError) as e:messagebox.showerror('Lỗi',str(e),parent=self)
    def save_recipe(self):
        if self.user.get('role')!='admin':return
        v={k:e.get().strip() for k,e in self.rec.items()};code=v['ma_nl'].split(' - ')[0]
        try:
            existing=[(d['ma_nl'],d['so_luong_can']) for d in self.service.list('dinh_muc') if d['ma_mon']==v['ma_mon'] and d['ma_nl']!=code];self.service.set_recipe(v['ma_mon'],existing+[(code,v['qty'])]);self.load_data();messagebox.showinfo('Thành công','Đã lưu định mức vào JSON.',parent=self)
        except ValueError as e:messagebox.showerror('Lỗi',str(e),parent=self)
    def calculate(self):
        try:
            rows=self.service.recipe(self.rec['ma_mon'].get(),self.rec['portions'].get());messagebox.showinfo('Nhu cầu','\n'.join(f"{r['ten_nl']}: cần {r['so_luong_can']:g} {r['don_vi']} | tồn {r['ton_kho']:g} | {'ĐỦ' if r['du_hang'] else 'THIẾU'}" for r in rows),parent=self)
        except ValueError as e:messagebox.showerror('Lỗi',str(e),parent=self)
    def export(self):
        p=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')],initialfile='mon_an.csv',parent=self)
        if p:
            try:self.service.export_csv('mon_an',p);messagebox.showinfo('Xuất CSV','Đã xuất CSV.',parent=self)
            except (ValueError,OSError) as e:messagebox.showerror('Lỗi',str(e),parent=self)

if __name__=='__main__':LoginWindow().mainloop()
