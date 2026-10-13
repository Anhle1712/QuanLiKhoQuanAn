class MonAn:
    def __init__(self, ma_mon, ten_mon, gia_ban):
        self.ma_mon = ma_mon
        self.ten_mon = ten_mon
        self.gia_ban = float(gia_ban)

    def to_dict(self):
        return {
            "ma_mon": self.ma_mon,
            "ten_mon": self.ten_mon,
            "gia_ban": self.gia_ban
        }

    @staticmethod
    def from_dict(data):
        return MonAn(data["ma_mon"], data["ten_mon"], data["gia_ban"])