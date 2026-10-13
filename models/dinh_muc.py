class DinhMuc:
    def __init__(self, ma_mon, ma_nl, so_luong_can):
        self.ma_mon = ma_mon
        self.ma_nl = ma_nl
        self.so_luong_can = float(so_luong_can)

    def to_dict(self):
        return {
            "ma_mon": self.ma_mon,
            "ma_nl": self.ma_nl,
            "so_luong_can": self.so_luong_can
        }

    @staticmethod
    def from_dict(data):
        return DinhMuc(data["ma_mon"], data["ma_nl"], data["so_luong_can"])