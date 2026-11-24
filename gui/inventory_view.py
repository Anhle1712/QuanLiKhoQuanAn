import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import date
try:
    from tkcalendar import DateEntry
except ImportError:
    class DateEntry(ttk.Entry):
        def __init__(self, parent, date_pattern=None, **kwargs):
            super().__init__(parent, **kwargs)
            self.insert(0, date.today().strftime('%d/%m/%Y'))

from services.kho_service import KhoService
from managers.data_manager import DataManager

GREEN = '#1f5f43'
GREEN_LIGHT = '#e8f2df'
RED_LIGHT = '#ffd9d5'
CREAM = '#faf7ef'

class InventoryFrame(ttk.Frame):
    def __init__(self, parent, service=None, user=None):
        super().__init__(parent, padding=16)
        self.service = service or KhoService()
        self.user = user or {'role': 'admin'}
        self.values = {}
        self.build_style()
        self.build_form()
        self.build_table()
        self.load_data()

    def build_style(self):
        style = ttk.Style(self)
        try: style.theme_use('clam')
        except tk.TclError: pass
        style.configure('Inv.TLabelframe', background='white', bordercolor='#d7ded8')
        style.configure('Inv.TLabelframe.Label', foreground=GREEN, font=('Arial', 12, 'bold'))
        style.configure('Inv.TLabel', background='white', foreground='#27433a', font=('Arial', 10, 'bold'))
        style.configure('Inv.TEntry', fieldbackground='white', padding=8)
        style.configure('Inv.TCombobox', fieldbackground='white', padding=7)
        style.configure('Inv.Treeview', rowheight=32, font=('Arial', 10), background='white', fieldbackground='white')
        style.configure('Inv.Treeview.Heading', background=GREEN, foreground='white', font=('Arial', 10, 'bold'))
        style.map('Inv.Treeview', background=[('selected', '#dcefcf')], foreground=[('selected', '#173f2e')])

    def label(self, parent, text, row, col):
        ttk.Label(parent, text=text, style='Inv.TLabel').grid(row=row, column=col, sticky='w', padx=8, pady=(4, 5))

    def entry(self, parent, key, row, col, width=24):
        e = ttk.Entry(parent, width=width, style='Inv.TEntry')
        e.grid(row=row, column=col, sticky='ew', padx=8, pady=(0, 13))
        self.values[key] = e
        return e

    def build_form(self):
        form = ttk.LabelFrame(self, text='  Thông tin nguyên liệu  ', style='Inv.TLabelframe', padding=12)
        form.pack(fill='x', pady=(0, 12))
        for c in range(3): form.columnconfigure(c, weight=1)
        fields = [
            ('ma_nl', 'Mã NL'), ('ten_nl', 'Tên nguyên liệu'), ('don_vi', 'Đơn vị'),
            ('gia_nhap', 'Giá nhập'), ('so_luong_ton', 'Tồn đầu kỳ'), ('nguong_toi_thieu', 'Ngưỡng tối thiểu')]
        for i, (key, title) in enumerate(fields):
            c = i % 3; r = (i // 3) * 2
            self.label(form, title, r, c)
            if key == 'don_vi':
                e = ttk.Combobox(form, values=['kg', 'g', 'lít', 'ml', 'cái', 'hộp', 'chai', 'gói'], state='readonly', style='Inv.TCombobox')
                e.grid(row=r+1, column=c, sticky='ew', padx=8, pady=(0, 13)); self.values[key] = e
            else: self.entry(form, key, r+1, c)
        r = 4
        self.label(form, 'Hạn sử dụng', r, 0)
        self.expiry = DateEntry(form, date_pattern='yyyy-mm-dd', width=22)
        self.expiry.grid(row=r+1, column=0, sticky='ew', padx=8, pady=(0, 13))
        self.values['han_su_dung'] = self.expiry
        self.values['ma_nl'].config(state='readonly')
        self.values['so_luong_ton'].insert(0, '0')
        self.values['nguong_toi_thieu'].insert(0, '5')
        self.values['don_vi'].set('kg')

        actions = ttk.Frame(form)
        actions.grid(row=4, column=1, columnspan=2, rowspan=2, sticky='e', padx=8, pady=4)
        self.button(actions, 'Làm mới', self.clear_form, False)
        self.button(actions, 'Thêm mới', self.add_new, True)
        self.button(actions, 'Xóa', self.delete, False)
        self.button(actions, 'Xuất CSV', self.export, False)
        self.status = ttk.Label(self, text='', font=('Arial', 9))
        self.status.pack(anchor='w', pady=(0, 7))

        search = ttk.Frame(self)
        search.pack(fill='x', pady=(0, 7))
        ttk.Label(search, text='Tìm nguyên liệu:', font=('Arial', 10, 'bold')).pack(side='left')
        self.search = tk.StringVar()
        ttk.Entry(search, textvariable=self.search, width=32).pack(side='left', padx=8)
        self.search.trace_add('write', lambda *_: self.show_data())
        ttk.Button(search, text='＋ Thêm mới', command=self.add_new).pack(side='right')

    def button(self, parent, text, command, primary):
        b = tk.Button(parent, text=text, command=command, width=11, height=1,
                      font=('Arial', 10, 'bold'), cursor='hand2',
                      bg=GREEN if primary else 'white', fg='white' if primary else GREEN,
                      activebackground='#174d35' if primary else '#eef5ed',
                      relief='flat', bd=0)
        b.pack(side='left', padx=4)

    def build_table(self):
        box = ttk.Frame(self)
        box.pack(fill='both', expand=True)
        self.tree = ttk.Treeview(box, columns=('ma','ten','dvt','qty','price','expiry','action'), show='headings', style='Inv.Treeview')
        titles = [('ma','Mã NL',90),('ten','Tên nguyên liệu',210),('dvt','Đơn vị',80),('qty','Tồn kho',100),('price','Đơn giá',120),('expiry','Hạn sử dụng',120),('action','Thao tác',100)]
        for key,title,width in titles:
            self.tree.heading(key, text=title); self.tree.column(key, width=width, anchor='center' if key not in ('ten',) else 'w')
        self.tree.pack(side='left', fill='both', expand=True)
        scroll = ttk.Scrollbar(box, orient='vertical', command=self.tree.yview); scroll.pack(side='right', fill='y'); self.tree.configure(yscrollcommand=scroll.set)
        self.tree.tag_configure('low', background=RED_LIGHT)
        self.tree.tag_configure('normal', background='white')
        self.tree.bind('<<TreeviewSelect>>', self.choose)
        self.tree.bind('<Double-1>', self.choose)

    def new_item(self):
        self.clear_form()
        self.values['ma_nl'].config(state='normal'); self.values['ma_nl'].delete(0,'end')
        code = DataManager.next_code(self.items if hasattr(self, 'items') else self.service.list('nguyen_lieu'), 'ma_nl', 'NL')
        self.values['ma_nl'].insert(0, code); self.values['ma_nl'].config(state='readonly')
        self.values['ten_nl'].focus_set()

    def add_new(self):
        if self.user.get('role') != 'admin':
            messagebox.showwarning('Quyền hạn', 'Chỉ quản trị viên được thêm nguyên liệu.', parent=self)
            return
        try:
            # Luôn tạo mã mới khi bấm Thêm mới, tránh ghi đè bản ghi đang chọn.
            self.values['ma_nl'].config(state='normal')
            self.values['ma_nl'].delete(0, 'end')
            self.values['ma_nl'].insert(0, DataManager.next_code(self.items, 'ma_nl', 'NL'))
            self.values['ma_nl'].config(state='readonly')
            row = {k: e.get().strip() for k, e in self.values.items()}
            self.service.upsert('nguyen_lieu', row)
            self.load_data()
            self.status.config(text=f"✓ Đã thêm {row['ma_nl']} vào JSON.", foreground='#18794e')
            messagebox.showinfo('Thành công', f"Đã thêm nguyên liệu {row['ten_nl']} vào JSON.", parent=self)
            self.clear_form()
            self.new_item()
        except (ValueError, OSError) as e:
            messagebox.showerror('Thêm thất bại', str(e), parent=self)

    def clear_form(self):
        self.values['ma_nl'].config(state='normal')
        for k,e in self.values.items():
            e.delete(0,'end')
        self.values['ma_nl'].config(state='readonly')
        self.values['so_luong_ton'].insert(0,'0'); self.values['nguong_toi_thieu'].insert(0,'5'); self.values['don_vi'].set('kg')
        self.status.config(text='Đã làm mới biểu mẫu.', foreground='#56705f')

    def load_data(self):
        try:
            self.items = self.service.list('nguyen_lieu')
            self.show_data()
            if not self.values['ma_nl'].get(): self.new_item()
        except (ValueError, OSError) as e: messagebox.showerror('Lỗi dữ liệu', str(e), parent=self)

    def show_data(self):
        if not hasattr(self, 'items'): return
        self.tree.delete(*self.tree.get_children())
        term = self.search.get().casefold().strip() if hasattr(self,'search') else ''
        low = 0
        for item in self.items:
            text = f"{item.get('ma_nl','')} {item.get('ten_nl','')}".casefold()
            if term and term not in text: continue
            qty = float(item.get('so_luong_ton', 0)); threshold = float(item.get('nguong_toi_thieu',5))
            tag = 'low' if qty <= threshold else 'normal'
            if tag == 'low': low += 1
            self.tree.insert('', 'end', iid=item['ma_nl'], values=(item['ma_nl'], item['ten_nl'], item['don_vi'], qty, f"{float(item['gia_nhap']):,.0f}", item.get('han_su_dung','—'), '✎  🗑'), tags=(tag,))
        self.status.config(text=f'Hiển thị {len(self.tree.get_children())}/{len(self.items)} nguyên liệu  •  {low} mặt hàng cần chú ý.', foreground='#9b2c2c' if low else GREEN)

    def choose(self, event=None):
        selected = self.tree.selection()
        if not selected: return
        item = next((x for x in self.items if x['ma_nl'] == selected[0]), None)
        if item:
            self.values['ma_nl'].config(state='normal')
            for k,e in self.values.items():
                e.delete(0,'end'); e.insert(0,str(item.get(k,'')))
            self.values['ma_nl'].config(state='readonly')
            self.status.config(text=f"Đang chọn {item['ma_nl']} – {item['ten_nl']}", foreground=GREEN)

    def save(self):
        if self.user.get('role') != 'admin':
            messagebox.showwarning('Quyền hạn','Chỉ quản trị viên được sửa nguyên liệu.',parent=self); return
        try:
            row = {k:e.get().strip() for k,e in self.values.items()}
            if not row['ma_nl']:
                row['ma_nl'] = DataManager.next_code(self.items,'ma_nl','NL')
            self.service.upsert('nguyen_lieu', row)
            self.load_data()
            self.status.config(text='✓ Đã lưu dữ liệu vào JSON.', foreground='#18794e')
            messagebox.showinfo('Thành công','Đã lưu nguyên liệu vào file JSON.',parent=self)
        except (ValueError,OSError) as e: messagebox.showerror('Lưu thất bại',str(e),parent=self)

    def delete(self):
        if self.user.get('role') != 'admin':
            messagebox.showwarning('Quyền hạn','Chỉ quản trị viên được xóa nguyên liệu.',parent=self); return
        code = self.tree.selection()[0] if self.tree.selection() else self.values['ma_nl'].get().strip()
        if not code: return
        if messagebox.askyesno('Xác nhận',f'Xóa nguyên liệu {code}?',parent=self):
            try:
                self.service.delete('nguyen_lieu',code); self.load_data(); self.clear_form()
                self.status.config(text='✓ Xóa thành công.', foreground='#18794e')
            except ValueError as e: messagebox.showerror('Xóa thất bại',str(e),parent=self)

    def export(self):
        path = filedialog.asksaveasfilename(parent=self, defaultextension='.csv', filetypes=[('CSV','*.csv')], initialfile='nguyen_lieu.csv')
        if path:
            try:
                self.service.export_csv('nguyen_lieu',path)
                self.status.config(text='✓ Đã xuất CSV thành công.', foreground='#18794e')
                messagebox.showinfo('Xuất CSV',f'Đã xuất dữ liệu đến:\n{path}',parent=self)
            except (ValueError,OSError) as e: messagebox.showerror('Xuất CSV thất bại',str(e),parent=self)
