# Đề tài 10 – Quản lý kho nguyên liệu quán ăn

## Nguồn gốc
Bản phát triển tiếp từ repository `QuanLiKhoQuanAn-main` của nhóm, giữ các thư mục `models/`, `managers/`, `services/`, `gui/` và JSON mẫu. Không thay thế bằng dự án khác.

## Chạy trên Windows
1. Cài Python 3.10+ (đánh dấu Add Python to PATH).
2. Mở terminal tại thư mục có `main.py`.
3. `python -m pip install -r requirements.txt`
4. `python main.py`
5. Dữ liệu gốc có tài khoản mẫu `admin` / `123456` (chỉ dùng demo); lần đăng nhập đầu, mật khẩu được tự động băm PBKDF2. **Đổi mật khẩu ngay** trong ứng dụng. Không công khai tài khoản này khi triển khai thực tế.
6. Nếu xóa file tài khoản và tạo mới, tài khoản đầu tiên là quản trị viên; các tài khoản đăng ký tiếp theo là nhân viên.

## Chạy kiểm thử
`python -m unittest discover -s tests -v`

## Chức năng
- Thêm/sửa/xóa/tìm nguyên liệu và nhà cung cấp; ngăn xóa dữ liệu có giao dịch/định mức.
- Nhập/xuất và đối chiếu tồn; ngăn phiếu trùng mã, số lượng âm và xuất vượt kho.
- Món ăn, định mức và tính nhu cầu nguyên liệu theo số suất.
- Giá trị kho, biểu đồ Canvas, cảnh báo tồn thấp/hết hạn; xuất CSV.
- Đăng nhập, đăng ký, đổi mật khẩu, phân quyền sửa danh mục; dữ liệu JSON với ghi file nguyên tử và sao lưu.
- Tải tên món ăn tham khảo từ TheMealDB API, lọc và lưu `data/api_mon_an.json` riêng; cần internet.

## Lưu ý
- Mã nguồn tiếp tục phát triển từ nhóm; có 5 tab GUI, **chưa kiểm chứng bằng thao tác thực tế trên máy Windows** và chưa có bản EXE.
- Form nhập/xuất hiện cung cấp 1 dòng hàng cho mỗi phiếu; lớp nghiệp vụ đã hỗ trợ nhiều dòng khi gọi chương trình.
- Cơ chế lưu hai file tồn kho/phiếu có rollback khi ghi lỗi trong tiến trình, **không phải transaction ACID thực sự khi mất điện đột ngột**. Hãy sao lưu thường xuyên.
- Trường `han_su_dung` hiện quản lý hạn đại diện cho mỗi nguyên liệu, chưa theo từng lô nhập. Đây là hạn chế cần nêu khi bảo vệ.
- API chỉ tải dữ liệu tham khảo, không tự động thêm món vào menu hoặc chỉnh sửa kho.
- Nếu không cài được tkcalendar, giao diện sử dụng ô nhập ngày thay thế.

## Đóng gói Windows
`python -m pip install pyinstaller`
`pyinstaller --noconfirm --onedir --windowed --name QuanLyKho main.py`
Sao chép thư mục `data/` vào `dist/QuanLyKho/data/`. Hãy kiểm tra EXE trên Windows trước khi nộp.

## Phân công 3 thành viên (điền tên thực tế)
- Thành viên 1: models/ + services/kho_service.py, nghiệp vụ nhập/xuất và định mức; demo luồng kho.
- Thành viên 2: gui/ + main.py, Tkinter, đăng nhập, UI; demo thao tác chính.
- Thành viên 3: managers/ + services/auth_service.py + tests/, JSON, bảo mật, API, kiểm thử và tài liệu; demo thống kê/API.
- Cả nhóm: đọc và giải thích phần code của nhau, phối hợp kiểm thử và thuyết trình.
