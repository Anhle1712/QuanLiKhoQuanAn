from abc import ABC, abstractmethod

class GiaoDichKho(ABC):
    """Lớp trừu tượng (Abstract Class) cho giao dịch kho"""
    def __init__(self, ma_phieu, ngay_lap, nhan_vien):
        self.ma_phieu = ma_phieu
        self.ngay_lap = ngay_lap
        self.nhan_vien = nhan_vien
        self.chi_tiet = []  # Danh sách mặt hàng: [{ma_nl, so_luong, don_gia}]

    @abstractmethod
    def tinh_tong_tien(self):
        """Bắt buộc các lớp con phải viết lại hàm này"""
        pass

    @abstractmethod
    def to_dict(self):
        """Bắt buộc các lớp con phải viết lại hàm này để chuyển dữ liệu thành JSON"""
        pass


class PhieuNhap(GiaoDichKho):
    """Lớp Phiếu Nhập kế thừa từ GiaoDichKho"""
    def __init__(self, ma_phieu, ngay_lap, nhan_vien, ma_ncc):
        super().__init__(ma_phieu, ngay_lap, nhan_vien)
        self.ma_ncc = ma_ncc

    def them_chi_tiet(self, ma_nl, so_luong, don_gia):
        self.chi_tiet.append({
            "ma_nl": ma_nl,
            "so_luong": float(so_luong),
            "don_gia": float(don_gia)
        })

    def tinh_tong_tien(self):
        return sum(item["so_luong"] * item["don_gia"] for item in self.chi_tiet)

    def to_dict(self):
        return {
            "ma_phieu": self.ma_phieu,
            "ngay_lap": self.ngay_lap,
            "nhan_vien": self.nhan_vien,
            "ma_ncc": self.ma_ncc,
            "loai": "nhap",
            "chi_tiet": self.chi_tiet,
            "tong_tien": self.tinh_tong_tien()
        }


class PhieuXuat(GiaoDichKho):
    """Lớp Phiếu Xuất kế thừa từ GiaoDichKho"""
    def __init__(self, ma_phieu, ngay_lap, nhan_vien, ly_do):
        super().__init__(ma_phieu, ngay_lap, nhan_vien)
        self.ly_do = ly_do

    def them_chi_tiet(self, ma_nl, so_luong):
        self.chi_tiet.append({
            "ma_nl": ma_nl,
            "so_luong": float(so_luong)
        })

    def tinh_tong_tien(self):
        return 0.0  # Phiếu xuất kho không tính tiền bán hàng

    def to_dict(self):
        return {
            "ma_phieu": self.ma_phieu,
            "ngay_lap": self.ngay_lap,
            "nhan_vien": self.nhan_vien,
            "ly_do": self.ly_do,
            "loai": "xuat",
            "chi_tiet": self.chi_tiet
        }