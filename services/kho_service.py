import os
from managers.data_manager import DataManager

class KhoService:
    @staticmethod
    def xu_ly_phieu_nhap(phieu_nhap):
        """Lưu phiếu nhập và tự động cộng dồn số lượng tồn kho của nguyên liệu"""
        ds_nhap = DataManager.doc_json("data/phieu_nhap.json")
        if any(p["ma_phieu"] == phieu_nhap.ma_phieu for p in ds_nhap):
            raise ValueError("Mã phiếu nhập đã tồn tại trong hệ thống!")
        
        ds_nhap.append(phieu_nhap.to_dict())
        DataManager.ghi_json("data/phieu_nhap.json", ds_nhap)

        # Cập nhật tăng số lượng tồn trong kho
        ds_nl = DataManager.doc_json("data/nguyen_lieu.json")
        for item in phieu_nhap.chi_tiet:
            for nl in ds_nl:
                if nl["ma_nl"] == item["ma_nl"]:
                    nl["so_luong_ton"] += item["so_luong"]
                    nl["gia_nhap"] = item["don_gia"]
        DataManager.ghi_json("data/nguyen_lieu.json", ds_nl)

    @staticmethod
    def xu_ly_phieu_xuat(phieu_xuat):
        """Kiểm tra tồn kho, lưu phiếu xuất và trừ số lượng tồn kho"""
        ds_nl = DataManager.doc_json("data/nguyen_lieu.json")
        
        # 1. Kiểm tra xem nguyên liệu có đủ số lượng để xuất không
        for item in phieu_xuat.chi_tiet:
            nl_found = None
            for nl in ds_nl:
                if nl["ma_nl"] == item["ma_nl"]:
                    nl_found = nl
                    break
            if not nl_found:
                raise ValueError(f"Không tìm thấy mã nguyên liệu: {item['ma_nl']}")
            if nl_found["so_luong_ton"] < item["so_luong"]:
                raise ValueError(f"Nguyên liệu [{nl_found['ten_nl']}] không đủ số lượng trong kho!")

        # 2. Lưu phiếu xuất vào file JSON
        ds_xuat = DataManager.doc_json("data/phieu_xuat.json")
        if any(p["ma_phieu"] == phieu_xuat.ma_phieu for p in ds_xuat):
            raise ValueError("Mã phiếu xuất đã tồn tại trong hệ thống!")
        
        ds_xuat.append(phieu_xuat.to_dict())
        DataManager.ghi_json("data/phieu_xuat.json", ds_xuat)

        # 3. Trừ số lượng tồn kho thực tế
        for item in phieu_xuat.chi_tiet:
            for nl in ds_nl:
                if nl["ma_nl"] == item["ma_nl"]:
                    nl["so_luong_ton"] -= item["so_luong"]
        DataManager.ghi_json("data/nguyen_lieu.json", ds_nl)

    @staticmethod
    def tinh_nguyen_lieu_theo_suat(ma_mon, so_suat):
        """Tính toán nguyên liệu cần dùng dựa theo số suất ăn đặt"""
        ds_dinh_muc = DataManager.doc_json("data/dinh_muc.json")
        ds_nl = DataManager.doc_json("data/nguyen_lieu.json")
        
        dinh_mucs = [dm for dm in ds_dinh_muc if dm["ma_mon"] == ma_mon]
        
        ket_qua = []
        for dm in dinh_mucs:
            ma_nl = dm["ma_nl"]
            so_luong_can = dm["so_luong_can"] * float(so_suat)
            
            ten_nl = ""
            ton_kho = 0
            for nl in ds_nl:
                if nl["ma_nl"] == ma_nl:
                    ten_nl = nl["ten_nl"]
                    ton_kho = nl["so_luong_ton"]
                    break
            
            ket_qua.append({
                "ma_nl": ma_nl,
                "ten_nl": ten_nl,
                "so_luong_can": so_luong_can,
                "ton_kho": ton_kho,
                "du_hang": ton_kho >= so_luong_can
            })
        return ket_qua

    @staticmethod
    def canh_bao_ton_kho(nguong_toi_thieu=5.0):
        """Cảnh báo các nguyên liệu có số lượng tồn kho thấp hơn hoặc bằng ngưỡng"""
        ds_nl = DataManager.doc_json("data/nguyen_lieu.json")
        return [nl for nl in ds_nl if nl["so_luong_ton"] <= nguong_toi_thieu]