"""Đọc dữ liệu quản lý kho từ một file TXT và ghi vào JSON hiện có."""
from pathlib import Path
import re
from datetime import date
from services.kho_service import KhoService


class TxtImporter:
    SECTIONS = {
        'NGUYEN_LIEU': 'nguyen_lieu',
        'NGUYEN LIEU': 'nguyen_lieu',
        'NGUYÊN LIỆU': 'nguyen_lieu',
        'MON_AN': 'mon_an',
        'MON AN': 'mon_an',
        'MÓN ĂN': 'mon_an',
        'NHA_CUNG_CAP': 'nha_cung_cap',
        'NHA CUNG CAP': 'nha_cung_cap',
        'NHÀ CUNG CẤP': 'nha_cung_cap',
        'DINH_MUC': 'dinh_muc',
        'DINH MUC': 'dinh_muc',
        'ĐỊNH MỨC': 'dinh_muc',
        'PHIEU_NHAP': 'phieu_nhap',
        'PHIEU NHAP': 'phieu_nhap',
        'PHIẾU NHẬP': 'phieu_nhap',
        'PHIEU_XUAT': 'phieu_xuat',
        'PHIEU XUAT': 'phieu_xuat',
        'PHIẾU XUẤT': 'phieu_xuat',
    }

    def __init__(self, service=None):
        self.service = service or KhoService()

    @staticmethod
    def _clean(text):
        return str(text).strip().strip('"').strip("'")

    @staticmethod
    def _split(line):
        # Cho phép TXT viết bằng |, tab hoặc ;. Dấu phẩy không dùng để tách
        # vì tên/địa chỉ có thể chứa dấu phẩy.
        if '|' in line:
            return [TxtImporter._clean(x) for x in line.split('|')]
        if '\t' in line:
            return [TxtImporter._clean(x) for x in line.split('\t')]
        if ';' in line:
            return [TxtImporter._clean(x) for x in line.split(';')]
        return [TxtImporter._clean(x) for x in re.split(r'\s{2,}', line)]

    @classmethod
    def _section(cls, line):
        s = line.strip()
        if s.startswith('[') and s.endswith(']'):
            return cls.SECTIONS.get(s[1:-1].strip().upper())
        return None

    def parse(self, path):
        path = Path(path)
        if not path.exists():
            raise ValueError(f'Không tìm thấy file: {path}')
        text = path.read_text(encoding='utf-8-sig')
        sections = {k: [] for k in set(self.SECTIONS.values())}
        current = None
        for lineno, raw in enumerate(text.splitlines(), 1):
            line = raw.strip()
            if not line or line.startswith('#') or line.startswith('//'):
                continue
            sec = self._section(line)
            if sec:
                current = sec
                continue
            if current:
                sections[current].append((lineno, self._split(line)))
        return sections

    @staticmethod
    def _is_header(parts, words):
        if not parts:
            return True
        joined = ' '.join(parts).lower()
        return any(w.lower() in joined for w in words)

    def _import_materials(self, rows):
        count = 0
        for lineno, p in rows:
            if self._is_header(p, ['mã nl', 'tên nguyên liệu']):
                continue
            if len(p) < 2:
                raise ValueError(f'NGUYEN_LIEU dòng {lineno}: cần ít nhất Mã NL | Tên nguyên liệu')
            row = {
                'ma_nl': p[0], 'ten_nl': p[1],
                'don_vi': p[2] if len(p) > 2 and p[2] else 'kg',
                'gia_nhap': p[3] if len(p) > 3 and p[3] else 0,
                'so_luong_ton': p[4] if len(p) > 4 and p[4] else 0,
                'nguong_toi_thieu': p[5] if len(p) > 5 and p[5] else 5,
                'han_su_dung': p[6] if len(p) > 6 else '',
            }
            self.service.upsert('nguyen_lieu', row)
            count += 1
        return count

    def _import_suppliers(self, rows):
        count = 0
        for lineno, p in rows:
            if self._is_header(p, ['mã ncc', 'tên nhà cung cấp']):
                continue
            if len(p) < 3:
                raise ValueError(f'NHA_CUNG_CAP dòng {lineno}: cần Mã NCC | Tên | SĐT | Địa chỉ')
            self.service.upsert('nha_cung_cap', {
                'ma_ncc': p[0], 'ten_ncc': p[1], 'sdt': p[2],
                'dia_chi': p[3] if len(p) > 3 else ''
            })
            count += 1
        return count

    def _import_dishes(self, rows):
        count = 0
        for lineno, p in rows:
            if self._is_header(p, ['mã món', 'tên món']):
                continue
            if len(p) < 2:
                raise ValueError(f'MON_AN dòng {lineno}: cần Mã món | Tên món | Giá bán')
            self.service.upsert('mon_an', {
                'ma_mon': p[0], 'ten_mon': p[1], 'gia_ban': p[2] if len(p) > 2 and p[2] else 0
            })
            count += 1
        return count

    def _import_recipes(self, rows):
        grouped = {}
        for lineno, p in rows:
            if self._is_header(p, ['mã món', 'nguyên liệu', 'định mức']):
                continue
            if len(p) < 3:
                raise ValueError(f'DINH_MUC dòng {lineno}: cần Mã món | Mã NL | Định mức')
            grouped.setdefault(p[0], []).append((p[1].split(' - ')[0].strip(), p[2]))
        count = 0
        for ma_mon, items in grouped.items():
            self.service.set_recipe(ma_mon, items)
            count += len(items)
        return count

    def _import_vouchers(self, rows, kind):
        count = 0
        prefix = 'PHIEU_NHAP' if kind == 'nhap' else 'PHIEU_XUAT'
        for lineno, p in rows:
            if self._is_header(p, ['mã phiếu', 'ngày', 'nguyên liệu']):
                continue
            if kind == 'nhap':
                # Mã phiếu | Ngày | NCC | Mã NL | Số lượng | Đơn giá | Nhân viên
                if len(p) < 6:
                    raise ValueError(f'{prefix} dòng {lineno}: cần Mã phiếu | Ngày | NCC | Mã NL | Số lượng | Đơn giá | Nhân viên')
                code, ngay, ncc, ma_nl, qty, price = p[:6]
                nv = p[6] if len(p) > 6 and p[6] else 'import_txt'
                voucher = {'ma_phieu': code, 'ngay_lap': ngay, 'nhan_vien': nv,
                           'ma_ncc': ncc,
                           'chi_tiet': [{'ma_nl': ma_nl.split(' - ')[0].strip(), 'so_luong': qty, 'don_gia': price}]}
            else:
                # Mã phiếu | Ngày | Mã NL | Số lượng | Nhân viên | Lý do
                if len(p) < 4:
                    raise ValueError(f'{prefix} dòng {lineno}: cần Mã phiếu | Ngày | Mã NL | Số lượng | Nhân viên | Lý do')
                code, ngay, ma_nl, qty = p[:4]
                nv = p[4] if len(p) > 4 and p[4] else 'import_txt'
                ly_do = p[5] if len(p) > 5 else 'Nhập từ TXT'
                voucher = {'ma_phieu': code, 'ngay_lap': ngay, 'nhan_vien': nv,
                           'ly_do': ly_do,
                           'chi_tiet': [{'ma_nl': ma_nl.split(' - ')[0].strip(), 'so_luong': qty, 'don_gia': 0}]}
            existing = {x['ma_phieu'] for x in self.service.list('phieu_' + kind)}
            if code in existing:
                continue
            self.service.transact(kind, voucher)
            count += 1
        return count

    def import_file(self, path):
        data = self.parse(path)
        result = {}
        # Thứ tự này bảo đảm phiếu và định mức có sẵn mã tham chiếu.
        result['nguyen_lieu'] = self._import_materials(data['nguyen_lieu'])
        result['nha_cung_cap'] = self._import_suppliers(data['nha_cung_cap'])
        result['mon_an'] = self._import_dishes(data['mon_an'])
        result['dinh_muc'] = self._import_recipes(data['dinh_muc'])
        result['phieu_nhap'] = self._import_vouchers(data['phieu_nhap'], 'nhap')
        result['phieu_xuat'] = self._import_vouchers(data['phieu_xuat'], 'xuat')
        return result

    @staticmethod
    def summary(result):
        names = [('nguyen_lieu','nguyên liệu'),('mon_an','món ăn'),('nha_cung_cap','nhà cung cấp'),
                 ('dinh_muc','định mức'),('phieu_nhap','phiếu nhập'),('phieu_xuat','phiếu xuất')]
        return '\n'.join(f"• {label}: {result.get(key, 0)}" for key, label in names)
