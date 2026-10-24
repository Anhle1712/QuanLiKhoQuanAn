class NguyenLieu:
    def __init__(self, ma_nl, ten_nl, don_vi, gia_nhap, so_luong_ton=0.0):
        self.ma_nl = ma_nl
        self.ten_nl = ten_nl
        self.don_vi = don_vi
        self.gia_nhap = float(gia_nhap)
        self.so_luong_ton = float(so_luong_ton)

    def to_dict(self):
        return {
            "ma_nl": self.ma_nl,
            "ten_nl": self.ten_nl,
            "don_vi": self.don_vi,
            "gia_nhap": self.gia_nhap,
            "so_luong_ton": self.so_luong_ton
        }

    @staticmethod
    def from_dict(data):
        return NguyenLieu(
            data["ma_nl"], data["ten_nl"], data["don_vi"], 
            data["gia_nhap"], data["so_luong_ton"]
        )