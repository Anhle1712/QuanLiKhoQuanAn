import unittest
import tempfile
from pathlib import Path
from datetime import date,timedelta
from unittest.mock import patch,Mock
from services.kho_service import KhoService
from services.auth_service import AuthService
from managers.data_manager import DataManager

class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.s=KhoService(self.temp.name)
        self.s.upsert('nha_cung_cap',{'ma_ncc':'N01','ten_ncc':'Công ty A','sdt':'0901234567','dia_chi':'HCM'})
        self.s.upsert('nguyen_lieu',{'ma_nl':'NL01','ten_nl':'Gạo','don_vi':'kg','gia_nhap':20000,'so_luong_ton':10,'nguong_toi_thieu':5,'han_su_dung':(date.today()+timedelta(days=3)).isoformat()})
        self.s.upsert('mon_an',{'ma_mon':'M01','ten_mon':'Cơm','gia_ban':30000})
    def voucher(self,kind,code='P01',qty=2):
        v={'ma_phieu':code,'ngay_lap':'2026-11-16','nhan_vien':'admin','chi_tiet':[{'ma_nl':'NL01','so_luong':qty,'don_gia':22000}]}
        if kind=='nhap':v['ma_ncc']='N01'
        else:v['ly_do']='Nấu ăn'
        return v
    def test_01_create_material(self): self.assertEqual(self.s.list('nguyen_lieu')[0]['so_luong_ton'],10)
    def test_02_update_material_no_stock_overwrite(self):
        self.s.upsert('nguyen_lieu',{'ma_nl':'NL01','ten_nl':'Gạo mới','don_vi':'kg','gia_nhap':23000,'so_luong_ton':1000});self.assertEqual(self.s.list('nguyen_lieu')[0]['so_luong_ton'],10)
    def test_03_duplicate_phone_invalid(self):
        with self.assertRaises(ValueError): self.s.upsert('nha_cung_cap',{'ma_ncc':'N02','ten_ncc':'NCC B','sdt':'123'})
    def test_04_import(self):self.s.transact('nhap',self.voucher('nhap'));self.assertEqual(self.s.list('nguyen_lieu')[0]['so_luong_ton'],12)
    def test_05_export(self):self.s.transact('xuat',self.voucher('xuat'));self.assertEqual(self.s.list('nguyen_lieu')[0]['so_luong_ton'],8)
    def test_06_over_export(self):
        with self.assertRaises(ValueError):self.s.transact('xuat',self.voucher('xuat',qty=999))
        self.assertEqual(len(self.s.list('phieu_xuat')),0)
    def test_07_aggregate_duplicates(self):
        v=self.voucher('xuat');v['chi_tiet']*=6
        with self.assertRaises(ValueError):self.s.transact('xuat',v)
        self.assertEqual(self.s.list('nguyen_lieu')[0]['so_luong_ton'],10)
    def test_08_duplicate_voucher(self):
        self.s.transact('nhap',self.voucher('nhap'))
        with self.assertRaises(ValueError):self.s.transact('nhap',self.voucher('nhap'))
    def test_09_recipe(self):
        self.s.set_recipe('M01',[('NL01',0.2)])
        self.assertAlmostEqual(self.s.recipe('M01',20)[0]['so_luong_can'],4)
    def test_10_recipe_shortage(self):
        self.s.set_recipe('M01',[('NL01',1)])
        self.assertFalse(self.s.recipe('M01',20)[0]['du_hang'])
    def test_11_date_expiry_warning(self):self.assertIn('Sắp hết hạn',self.s.warnings()[0]['canh_bao'])
    def test_12_low_stock_warning(self):
        self.s.transact('xuat',self.voucher('xuat',qty=6));self.assertIn('Tồn kho thấp',self.s.warnings()[0]['canh_bao'])
    def test_13_stats(self):self.assertEqual(self.s.stats()['gia_tri_ton'],200000)
    def test_14_delete_guard(self):
        self.s.set_recipe('M01',[('NL01',1)])
        with self.assertRaises(ValueError):self.s.delete('nguyen_lieu','NL01')
    def test_15_delete_supplier_guard(self):
        self.s.transact('nhap',self.voucher('nhap'))
        with self.assertRaises(ValueError):self.s.delete('nha_cung_cap','N01')
    def test_16_csv(self):
        dest=Path(self.temp.name)/'out.csv';self.s.export_csv('nguyen_lieu',dest)
        self.assertIn('Tên',dest.read_text(encoding='utf-8-sig').replace('ten_nl','Tên'))
    def test_17_atomic_corrupt(self):
        file=Path(self.temp.name)/'bad.json';file.write_text('{garbled',encoding='utf-8')
        with self.assertRaises(ValueError):DataManager.doc_json(file)
    def test_18_api_mock(self):
        resp=Mock();resp.json.return_value={'meals':[{'idMeal':'123','strMeal':'Chicken soup'}]};resp.raise_for_status.return_value=None
        with patch('services.kho_service.requests.get',return_value=resp):self.s.fetch_api()
        self.assertEqual(len(DataManager.doc_json(Path(self.temp.name)/'api_mon_an.json')),1)
    def test_19_invalid_quantity(self):
        with self.assertRaises(ValueError):self.s.transact('nhap',self.voucher('nhap',qty=-1))
    def test_20_invalid_recipe(self):
        with self.assertRaises(ValueError):self.s.set_recipe('M01',[('NL99',2)])

class AccountTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.auth=AuthService(Path(self.temp.name)/'accounts.json')
    def test_21_first_admin(self):self.assertEqual(self.auth.register('admin','password123')['role'],'admin')
    def test_22_user_role(self):
        self.auth.register('admin','password123');self.assertEqual(self.auth.register('staff','password123')['role'],'user')
    def test_23_authentication(self):
        self.auth.register('admin','password123');self.assertEqual(self.auth.login('admin','password123')['username'],'admin')
    def test_24_wrong_password(self):
        self.auth.register('admin','password123')
        with self.assertRaises(ValueError):self.auth.login('admin','no')
    def test_25_legacy_migration(self):
        DataManager.ghi_json(self.auth.path,[{'username':'admin','password':'legacy','role':'admin','fullname':'Admin'}])
        self.auth.login('admin','legacy');self.assertTrue(self.auth.accounts()[0]['password'].startswith('pbkdf2_sha256$'))
    def test_26_change_password(self):
        self.auth.register('admin','password123');self.auth.change_password('admin','password123','newpassword123');self.auth.login('admin','newpassword123')

if __name__=='__main__':unittest.main()
