"""Business rules: extend the team's existing KhoService; no database required."""
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
import csv
import json
import requests
from managers.data_manager import DataManager
from config import DATA_DIR, EXPIRY_WARNING_DAYS

class KhoService:
    def __init__(self, data_dir=None):
        self.data_dir = Path(data_dir) if data_dir else DATA_DIR
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _path(self, entity):
        return self.data_dir / f'{entity}.json'

    def list(self, entity):
        if entity not in ('nguyen_lieu','nha_cung_cap','mon_an','dinh_muc','phieu_nhap','phieu_xuat'):
            raise ValueError('Loại dữ liệu không hợp lệ')
        return DataManager.doc_json(self._path(entity))

    def _save(self, entity, rows):
        DataManager.ghi_json(self._path(entity), rows)

    @staticmethod
    def _num(value, label, positive=False):
        try:
            val = float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f'{label} phải là số') from exc
        import math
        if not math.isfinite(val) or (positive and val <= 0) or (not positive and val < 0):
            raise ValueError(f'{label} không hợp lệ')
        return val

    def upsert(self, entity, row):
        keys = {'nguyen_lieu':'ma_nl','nha_cung_cap':'ma_ncc','mon_an':'ma_mon','dinh_muc':'ma_mon'}
        if entity not in keys or entity == 'dinh_muc':
            raise ValueError('Không hỗ trợ cập nhật trực tiếp loại này')
        key = keys[entity]
        code = str(row.get(key, '')).strip()
        if not DataManager.validate_ma(code):
            raise ValueError('Mã phải gồm 2-24 ký tự chữ/số/_/-')
        result = dict(row)
        result[key] = code
        if entity == 'nguyen_lieu':
            for field in ('ten_nl','don_vi'):
                if not str(result.get(field,'')).strip():
                    raise ValueError(f'Không được bỏ trống {field}')
            result['gia_nhap'] = self._num(result.get('gia_nhap', 0), 'Giá nhập')
            result['so_luong_ton'] = self._num(result.get('so_luong_ton',0), 'Tồn kho')
            result['nguong_toi_thieu'] = self._num(result.get('nguong_toi_thieu',5), 'Ngưỡng tồn')
            expiry = str(result.get('han_su_dung','')).strip()
            if expiry:
                try: date.fromisoformat(expiry)
                except ValueError as e: raise ValueError('Hạn sử dụng phải theo YYYY-MM-DD') from e
            result['han_su_dung'] = expiry
        elif entity == 'nha_cung_cap':
            if not str(result.get('ten_ncc','')).strip(): raise ValueError('Thiếu tên nhà cung cấp')
            if not DataManager.validate_sdt(result.get('sdt','')): raise ValueError('Số điện thoại phải 10 số và bắt đầu bằng 0')
        elif entity == 'mon_an':
            if not str(result.get('ten_mon','')).strip(): raise ValueError('Thiếu tên món ăn')
            result['gia_ban'] = self._num(result.get('gia_ban',0), 'Giá bán')
        rows=self.list(entity)
        previous=next((i for i,x in enumerate(rows) if x[key]==code),None)
        # Existing stock cannot be directly edited: only stock transactions change it.
        if entity=='nguyen_lieu' and previous is not None:
            result['so_luong_ton']=rows[previous]['so_luong_ton']
        if previous is None: rows.append(result)
        else: rows[previous]=result
        self._save(entity,rows)
        return result

    def delete(self, entity, code):
        keys={'nguyen_lieu':'ma_nl','nha_cung_cap':'ma_ncc','mon_an':'ma_mon'}
        if entity not in keys: raise ValueError('Loại dữ liệu không hợp lệ')
        if entity=='nguyen_lieu':
            if any(d['ma_nl']==code for d in self.list('dinh_muc')) or any(any(t['ma_nl']==code for t in ph.get('chi_tiet',[])) for kind in ('phieu_nhap','phieu_xuat') for ph in self.list(kind)):
                raise ValueError('Nguyên liệu đã được dùng trong định mức hoặc phiếu kho')
        if entity=='nha_cung_cap' and any(p.get('ma_ncc')==code for p in self.list('phieu_nhap')):
            raise ValueError('Nhà cung cấp đã có phiếu nhập')
        if entity=='mon_an' and any(d['ma_mon']==code for d in self.list('dinh_muc')):
            raise ValueError('Món ăn đang có định mức; hãy xóa định mức trước')
        rows=self.list(entity)
        filtered=[r for r in rows if r[keys[entity]]!=code]
        if len(filtered)==len(rows): raise ValueError('Không tìm thấy mã cần xóa')
        self._save(entity, filtered)

    def set_recipe(self, ma_mon, items):
        if ma_mon not in {m['ma_mon'] for m in self.list('mon_an')}:
            raise ValueError('Món ăn không tồn tại')
        codes={n['ma_nl'] for n in self.list('nguyen_lieu')}
        new=[]
        seen=set()
        for code,qty in items:
            if code not in codes: raise ValueError(f'Nguyên liệu {code} không tồn tại')
            if code in seen: raise ValueError('Định mức trùng nguyên liệu')
            seen.add(code)
            new.append({'ma_mon':ma_mon,'ma_nl':code,'so_luong_can':self._num(qty,'Định mức',True)})
        rows=[r for r in self.list('dinh_muc') if r['ma_mon']!=ma_mon]+new
        self._save('dinh_muc',rows)

    def recipe(self, ma_mon, portions):
        count=self._num(portions,'Số suất',True)
        if not count.is_integer(): raise ValueError('Số suất phải nguyên')
        stock={r['ma_nl']:r for r in self.list('nguyen_lieu')}
        result=[]
        for dm in self.list('dinh_muc'):
            if dm['ma_mon']!=ma_mon: continue
            nl=stock.get(dm['ma_nl'])
            if not nl: raise ValueError(f"Thiếu nguyên liệu {dm['ma_nl']}")
            need=float(dm['so_luong_can'])*count
            result.append({'ma_nl':nl['ma_nl'],'ten_nl':nl['ten_nl'],'don_vi':nl['don_vi'],'so_luong_can':need,'ton_kho':nl['so_luong_ton'],'du_hang':nl['so_luong_ton']>=need})
        if not result: raise ValueError('Món ăn chưa có định mức')
        return result

    def transact(self, kind, voucher):
        if kind not in ('nhap','xuat'): raise ValueError('Loại phiếu không hợp lệ')
        entity='phieu_'+kind
        rows=self.list(entity)
        if not str(voucher.get('ma_phieu','')).strip() or any(x['ma_phieu']==voucher['ma_phieu'] for x in rows):
            raise ValueError('Mã phiếu trống hoặc trùng')
        try: date.fromisoformat(voucher.get('ngay_lap',''))
        except ValueError as e: raise ValueError('Ngày lập phải là YYYY-MM-DD') from e
        if not str(voucher.get('nhan_vien','')).strip(): raise ValueError('Thiếu nhân viên')
        if kind=='nhap' and voucher.get('ma_ncc') not in {x['ma_ncc'] for x in self.list('nha_cung_cap')}:
            raise ValueError('Nhà cung cấp không tồn tại')
        if not voucher.get('chi_tiet'): raise ValueError('Phiếu chưa có nguyên liệu')
        stock=self.list('nguyen_lieu')
        import copy
        prior_stock=copy.deepcopy(stock)
        by_code={x['ma_nl']:x for x in stock}
        total_changes=defaultdict(float)
        total=0
        for item in voucher['chi_tiet']:
            code=item.get('ma_nl')
            if code not in by_code: raise ValueError(f'Nguyên liệu {code} không tồn tại')
            qty=self._num(item.get('so_luong'),'Số lượng',True)
            price=self._num(item.get('don_gia',0),'Đơn giá') if kind=='nhap' else 0
            total_changes[code]+=qty
            total+=qty*price
        for code,qty in total_changes.items():
            if kind=='xuat' and by_code[code]['so_luong_ton']+1e-9<qty:
                raise ValueError(f"Không đủ tồn kho: {by_code[code]['ten_nl']}")
        for code,qty in total_changes.items():
            by_code[code]['so_luong_ton'] += qty if kind=='nhap' else -qty
        if kind=='nhap':
            for item in voucher['chi_tiet']:
                by_code[item['ma_nl']]['gia_nhap']=float(item['don_gia'])
        voucher=dict(voucher,loai=kind,tong_tien=total if kind=='nhap' else 0)
        # Transaction-like rollback with pre-write snapshots of BOTH files.
        prior_rows=rows[:]
        try:
            self._save('nguyen_lieu',stock)
            self._save(entity,rows+[voucher])
        except Exception:
            self._save('nguyen_lieu',prior_stock)
            self._save(entity,prior_rows)
            raise
        return voucher

    def warnings(self, today=None):
        today=today or date.today()
        results=[]
        for row in self.list('nguyen_lieu'):
            reasons=[]
            if float(row.get('so_luong_ton',0))<=float(row.get('nguong_toi_thieu',5)):
                reasons.append('Tồn kho thấp')
            expiry=row.get('han_su_dung')
            if expiry:
                days=(date.fromisoformat(expiry)-today).days
                if days<0: reasons.append('Đã hết hạn')
                elif days<=EXPIRY_WARNING_DAYS: reasons.append('Sắp hết hạn')
            if reasons: results.append(dict(row,canh_bao=', '.join(reasons)))
        return results

    def stats(self):
        stock=self.list('nguyen_lieu')
        imports=self.list('phieu_nhap')
        exports=self.list('phieu_xuat')
        consumed=defaultdict(float)
        for voucher in exports:
            for detail in voucher.get('chi_tiet',[]): consumed[detail['ma_nl']]+=float(detail['so_luong'])
        return {'so_loai':len(stock),'gia_tri_ton':sum(float(x['gia_nhap'])*float(x['so_luong_ton']) for x in stock),'so_phieu_nhap':len(imports),'so_phieu_xuat':len(exports),'tieu_thu':dict(consumed)}

    def export_csv(self, entity, output_path):
        rows=self.list(entity)
        if not rows: raise ValueError('Chưa có dữ liệu để xuất')
        keys=list(dict.fromkeys(k for row in rows for k in row))
        with open(output_path,'w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=keys)
            writer.writeheader()
            for row in rows:
                writer.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()})
        return output_path

    def fetch_api(self, endpoint='https://www.themealdb.com/api/json/v1/1/search.php?s=chicken'):
        """External sample recipe names, separate from live inventory; never overwrite stock."""
        try:
            response=requests.get(endpoint,timeout=8)
            response.raise_for_status()
            payload=response.json()
            meals=payload.get('meals') or []
            if not isinstance(meals,list): raise ValueError('API không trả danh sách món ăn')
            cleaned=[{'id':str(m.get('idMeal','')),'ten_mon':str(m.get('strMeal','')).strip(),'nguon':endpoint} for m in meals if isinstance(m,dict) and m.get('strMeal')]
            self._save('api_mon_an',cleaned)  # external data are reference only
            return cleaned
        except (requests.RequestException, ValueError) as exc:
            raise ValueError(f'Không lấy được API: {exc}') from exc

    # Compatibility wrappers with original class methods when used in old GUI.
    @staticmethod
    def xu_ly_phieu_nhap(phieu_nhap):
        return KhoService().transact('nhap',phieu_nhap.to_dict())
    @staticmethod
    def xu_ly_phieu_xuat(phieu_xuat):
        return KhoService().transact('xuat',phieu_xuat.to_dict())
    @staticmethod
    def tinh_nguyen_lieu_theo_suat(ma_mon,so_suat):
        return KhoService().recipe(ma_mon,so_suat)
    @staticmethod
    def canh_bao_ton_kho(nguong_toi_thieu=5):
        return [r for r in KhoService().list('nguyen_lieu') if float(r['so_luong_ton'])<=nguong_toi_thieu]
