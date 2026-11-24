"""Lưu trữ JSON, sao lưu và tiện ích tạo mã tự động cho project."""
import json
import os
import re
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from config import DATA_DIR

class DataManager:
    @staticmethod
    def _path(file_path):
        p = Path(file_path)
        if not p.is_absolute() and p.parts and p.parts[0] == "data":
            return DATA_DIR.joinpath(*p.parts[1:])
        return p

    @staticmethod
    def doc_json(file_path):
        path = DataManager._path(file_path)
        if not path.exists():
            return []
        try:
            with path.open('r', encoding='utf-8') as f:
                contents = f.read()
            if not contents.strip():
                return []
            result = json.loads(contents)
            if not isinstance(result, list):
                raise ValueError(f"{path.name}: dữ liệu phải là danh sách JSON")
            return result
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path.name}: JSON không hợp lệ ({exc})") from exc

    @staticmethod
    def ghi_json(file_path, data):
        path = DataManager._path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp_name = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=str(path.parent), prefix='._', suffix='.json', delete=False) as f:
                tmp_name = f.name
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_name, path)
        finally:
            if tmp_name and os.path.exists(tmp_name):
                os.unlink(tmp_name)

    @staticmethod
    def validate_sdt(sdt):
        return re.fullmatch(r'0[0-9]{9}', str(sdt)) is not None

    @staticmethod
    def validate_ma(ma):
        return re.fullmatch(r'[A-Za-z0-9_-]{2,24}', str(ma)) is not None

    @staticmethod
    def next_code(rows, field, prefix, width=2):
        """Tạo mã tiếp theo: NL01, NL02... / M01, M02..."""
        max_number = 0
        for row in rows:
            value = str(row.get(field, ''))
            match = re.fullmatch(re.escape(prefix) + r'(\d+)', value, re.IGNORECASE)
            if match:
                max_number = max(max_number, int(match.group(1)))
        return f'{prefix}{max_number + 1:0{width}d}'

    @staticmethod
    def backup_data():
        folder = DATA_DIR / ('backup_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        folder.mkdir(parents=True, exist_ok=True)
        for src in DATA_DIR.glob('*.json'):
            shutil.copy2(src, folder / src.name)
        return str(folder)
