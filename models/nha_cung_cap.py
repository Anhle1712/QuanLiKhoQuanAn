class NhaCungCap:
    def __init__(self, ma_ncc, ten_ncc, sdt, dia_chi):
        self.ma_ncc = ma_ncc
        self.ten_ncc = ten_ncc
        self.sdt = sdt
        self.dia_chi = dia_chi

    def to_dict(self):
        return {
            "ma_ncc": self.ma_ncc,
            "ten_ncc": self.ten_ncc,
            "sdt": self.sdt,
            "dia_chi": self.dia_chi
        }

    @staticmethod
    def from_dict(data):
        return NhaCungCap(data["ma_ncc"], data["ten_ncc"], data["sdt"], data["dia_chi"])