# Wallos (fork) — lộ trình và trạng thái

Repo này là fork của [ellite/Wallos](https://github.com/ellite/Wallos), chạy cho nhà dùng ở `wallos.cuongn.com`. Lộ trình sản phẩm do upstream quyết (`CHANGELOG.md`, release-please); fork không có backlog tính năng riêng — việc của mình là giữ bản chạy, cập nhật theo upstream và giữ khả năng merge. Tóm từ `git log`, `README.md`, `CHANGELOG.md` (không bịa thêm).

| # | Việc | Trạng thái | Ghi chú |
|---|---|---|---|
| 1 | Chạy production `wallos.cuongn.com` trên Railway (project `wallos`) | Đang chạy | kiểm 8/11/2026: `/` 302 → `/login.php`, `/health.php` 200 `OK` |
| 2 | Xác nhận Railway build từ repo GitHub này hay kéo image `bellamy/wallos` | Chưa rõ | repo không có `railway.json`/commit cấu hình; ảnh hưởng `pushDeploys` và cách cập nhật — `devops` kiểm trên Railway, anh duyệt |
| 3 | Đồng bộ upstream | Chưa có lịch | `main` fork = upstream 4.8.0 (23/3/2026); chưa fetch upstream nên chưa biết có bản mới hơn không |
| 4 | Quy chuẩn repo v1 (company.json, AGENTS.md, health/test, ROADMAP, logs/, `.dockerignore`) | Đợt 5, 8/11/2026 | không sửa mã upstream; `php` không có trên máy nên `check.sh` chưa chạy được `php -l` |
| 5 | Đổi tên repo theo quy chuẩn (`fork-wallos`) | Chưa quyết | registry ghi "gợi ý khi tiện"; cần anh duyệt, kéo theo đổi tên thư mục, remote, Railway |
| 6 | Tính năng riêng cho fork | Không có | giữ fork sạch để merge upstream không xung đột |

## Trạng thái hiện tại (8/11/2026)

- Bản upstream: 4.8.0 — mới nhất trong `CHANGELOG.md`: host OpenAI-compatible cho gợi ý AI, chạy gợi ý theo lịch, banner cập nhật ở dashboard.
- Fork chưa có commit riêng nào ngoài đợt 5. Dữ liệu thật (SQLite, logo) nằm trong volume Railway, không có trên máy.
- Việc nên làm tiếp (đề xuất, chưa duyệt): a) `devops` xác nhận nguồn deploy trên Railway (mục 2) rồi sửa `company.json.deploy.note`/`pushDeploys` cho đúng; b) thêm remote `upstream` và đặt nhịp sync (vd. mỗi tháng), đọc `CHANGELOG.md` trước mỗi lần vì migration chạy tự động; c) cài `php` trên máy dev để `tools/check.sh` kiểm được cú pháp PHP.
