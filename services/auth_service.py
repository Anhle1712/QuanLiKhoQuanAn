import hashlib
import hmac
import os
import re
from managers.data_manager import DataManager
from config import DATA_DIR

class AuthService:
    def __init__(self,path=None):
        self.path=path or DATA_DIR/'tai_khoan.json'

    def accounts(self): return DataManager.doc_json(self.path)

    @staticmethod
    def hash_password(password):
        salt=os.urandom(16)
        digest=hashlib.pbkdf2_hmac('sha256',password.encode(),salt,260000)
        return 'pbkdf2_sha256$260000$'+salt.hex()+'$'+digest.hex()

    @staticmethod
    def check(password,stored):
        if stored.startswith('pbkdf2_sha256$'):
            try:
                _,rounds,salt,digest=stored.split('$')
                calculated=hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),int(rounds))
                return hmac.compare_digest(calculated,bytes.fromhex(digest))
            except (ValueError,TypeError): return False
        return hmac.compare_digest(password,stored)  # legacy one-time migration

    def register(self,username,password,fullname='',role='user'):
        if not re.fullmatch('[A-Za-z0-9_]{3,24}',username): raise ValueError('Tên tài khoản 3–24 ký tự chữ, số hoặc _')
        if len(password)<8: raise ValueError('Mật khẩu cần ít nhất 8 ký tự')
        if role not in ('user','admin'): raise ValueError('Vai trò không hợp lệ')
        users=self.accounts()
        if any(u['username'].casefold()==username.casefold() for u in users): raise ValueError('Tài khoản đã tồn tại')
        if users and role=='admin': raise ValueError('Chỉ tài khoản đầu tiên được tự nhận quyền quản trị')
        account={'username':username,'password':self.hash_password(password),'fullname':fullname or username,'role':'admin' if not users else 'user'}
        DataManager.ghi_json(self.path,users+[account])
        return {k:v for k,v in account.items() if k!='password'}

    def login(self,username,password):
        users=self.accounts()
        for item in users:
            if item['username']==username and self.check(password,item['password']):
                if not item['password'].startswith('pbkdf2_sha256$'):
                    item['password']=self.hash_password(password)
                    DataManager.ghi_json(self.path,users)
                return {k:v for k,v in item.items() if k!='password'}
        raise ValueError('Sai tài khoản hoặc mật khẩu')

    def change_password(self,username,old,new):
        if len(new)<8: raise ValueError('Mật khẩu mới phải có ít nhất 8 ký tự')
        users=self.accounts()
        for user in users:
            if user['username']==username and self.check(old,user['password']):
                user['password']=self.hash_password(new)
                DataManager.ghi_json(self.path,users)
                return
        raise ValueError('Mật khẩu hiện tại không đúng')
