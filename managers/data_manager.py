import json
import os
import re
import shutil
from datetime import datetime

class DataManager:
    @staticmethod
    def doc_json(file_path):
        if not os.path.exists(file_path):
            return []
        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    @staticmethod
    def ghi_json(file_path, data):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    @staticmethod
    def validate_sdt(sdt):
        pattern = r'^0\d{9}$'
        return bool(re.match(pattern, sdt))

    @staticmethod
    def backup_data():
        backup_folder = "data/backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(backup_folder, exist_ok=True)
        data_files = [
            "dinh_muc.json", "mon_an.json", "nguyen_lieu.json", 
            "nha_cung_cap.json", "phieu_nhap.json", "phieu_xuat.json", "tai_khoan.json"
        ]
        for file in data_files:
            src = os.path.join("data", file)
            if os.path.exists(src):
                shutil.copy(src, backup_folder)
        return backup_folder