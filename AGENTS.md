# Wallos (fork) — hướng dẫn cho AI

Fork của **[ellite/Wallos](https://github.com/ellite/Wallos)**: app tự host theo dõi đăng ký/thuê bao định kỳ (PHP 8.3 + nginx + SQLite, chạy trong một image Docker). Bản này chạy cho nhà dùng tại `wallos.cuongn.com`. **Không đổi hành vi upstream**: toàn bộ mã PHP/JS/CSS, `Dockerfile`, `nginx*.conf`, `startup.sh`, `cronjobs`, `migrations/` là của upstream, `main` của fork trùng `main` upstream (chưa có commit riêng nào). Mình chỉ thêm file theo Quy chuẩn repo v1 của Holdings và vài dòng `.dockerignore` để các file đó không bị copy vào web root của image. Mọi sửa đổi khác phải giữ được khả năng merge upstream (mục 6).

`CLAUDE.md` chỉ chứa `@AGENTS.md`. Upstream không có AGENTS.md/CLAUDE.md riêng; tài liệu của họ là `README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, `SECURITY.md`.

## Tổng quan

- Công ty: tech — Lumen Technologies (Cuong Holdings). Manifest: `company.json` (`id: wallos`; GitHub của mình đặt tên `Wallos`, registry gợi ý đổi `fork-wallos` khi tiện — chưa quyết).
- Production: `https://wallos.cuongn.com` — Railway project `wallos`. Image build từ `Dockerfile` gốc (`php:8.3-fpm-alpine` + nginx + dcron, `COPY . .` vào `/var/www/html`, healthcheck `curl /health.php`). **Chưa xác nhận** Railway build từ repo GitHub này hay kéo thẳng image `bellamy/wallos` của upstream (repo không có `railway.json`, không có commit cấu hình nào); tới khi rõ, coi **mọi push `main` là deploy production** (`pushDeploys: ["/"]`).
- Dữ liệu: SQLite `db/wallos.db` + logo `images/uploads/logos/` nằm trong volume của container (trên máy chỉ có `db/wallos.empty.db` mẫu). Cron trong image chạy `endpoints/cronjobs/*.php` (cập nhật tỷ giá, thông báo, gợi ý AI…).
- Bản upstream đang chạy: 4.8.0 (23/3/2026, `CHANGELOG.md`). Máy này không có `php` (chỉ `node`, `python3`).

## Cấu trúc

```text
*.php                       trang chính của upstream (index, login, subscriptions, settings, admin…) — KHÔNG sửa
endpoints/                  API nội bộ + cronjobs (endpoints/cronjobs/*.php), migrate: endpoints/db/migrate.php
api/                        API công khai có khoá (admin, subscriptions, …)
includes/                   header/footer, kết nối DB, i18n, hàm dùng chung
libs/                       thư viện bên thứ ba vendored (PHPMailer, OTPHP…)
scripts/ styles/ images/    JS/CSS/ảnh giao diện; scripts/i18n/*.js bản dịch (có vi.js)
migrations/                 migration SQLite đánh số, chạy qua endpoints/db/migrate.php
db/wallos.empty.db          DB rỗng mẫu (db/* còn lại bị gitignore — dữ liệu thật ở volume)
Dockerfile nginx.conf nginx.default.conf startup.sh cronjobs   image production (upstream)
health.php                  trả "OK" — healthcheck của image và của tools/health.py
docs/ROADMAP.md             lộ trình và trạng thái fork                                  (quy chuẩn)
tools/health.py             health --json: git, production, công cụ/file build            (quy chuẩn)
tools/check.sh              test offline: php -l (khi có php), JSON, JS, sh, file image   (quy chuẩn)
company.json                manifest cho HQ                                               (quy chuẩn)
logs/                       log/báo cáo của agent, không đưa vào git                      (quy chuẩn)
.dockerignore               upstream + khối cuối của mình: không copy company.json, tools/, docs/, logs/ vào image
```

Nguồn chính khi mâu thuẫn: code và `README.md` upstream thắng tài liệu; `company.json` thắng mọi mô tả về lệnh/deploy của fork.

## Lệnh

Chạy từ gốc repo. Khớp `commands` trong `company.json`.

- `sh tools/check.sh` — **test** (offline, ~2 giây): `php -l` mọi `*.php` ở gốc + `endpoints/` + `includes/` **khi máy có `php`**; cú pháp JSON (`manifest.json`); `node --check` `service-worker.js` + `scripts/**/*.js` khi có node; `sh -n startup.sh`; file image Docker phải tồn tại. Mã thoát 0 = qua. **Giới hạn**: máy này không có `php` → script in cảnh báo và chỉ kiểm phần còn lại (vẫn mã 0, có chữ "giới hạn" trong dòng kết quả); muốn kiểm PHP thật thì cài `php` (brew) hoặc chạy trong image. Upstream không có unit test.
- `python3 tools/health.py --json` — **health**: git (nhánh, chưa push/pull, file chưa commit, phiên bản upstream từ CHANGELOG), production `wallos.cuongn.com` (`/` HEAD — 302 về `/login.php` là ok; `/health.php` GET mong thân `OK`; timeout 5 giây), công cụ/file build (php trên máy, Dockerfile, nginx conf, startup.sh, cronjobs, db mẫu). Có `bad` → mã thoát 1. Không `--json` → bảng. `HQ_SITE` đổi URL khi thử.
- `python3 tools/health.py --only git` — **status**: phần git, không cần mạng.
- Chạy local (không bắt buộc, cần Docker — không tự chạy): `docker compose up` theo `docker-compose.yaml` (image `bellamy/wallos:latest`, cổng 8282) hoặc `docker build .` cho image từ mã này.
- Cập nhật upstream: mục 6. Deploy: push `main` (cần anh duyệt).

## An toàn

**Được tự làm**
- Sửa file của fork: `company.json`, `AGENTS.md`, `docs/ROADMAP.md`, `tools/`, khối cuối `.dockerignore`.
- Chạy lệnh đọc: `sh tools/check.sh`, `python3 tools/health.py`, `git log/status/diff/fetch`.
- Đọc code upstream để trả lời câu hỏi, khoanh vùng lỗi.

**Không được làm**
- Không commit, không push (phiên điều hành commit; push `main` = deploy, cần anh duyệt).
- **Không sửa mã upstream** (mọi `*.php`, `scripts/`, `styles/`, `includes/`, `endpoints/`, `api/`, `migrations/`, `libs/`, `Dockerfile`, `nginx*.conf`, `startup.sh`, `cronjobs`) trừ khi anh giao rõ; sửa thì giữ diff tối thiểu để merge upstream không xung đột. Lỗi của upstream → issue/PR ở upstream (theo `CONTRIBUTING.md`), không vá riêng trong fork.
- Không rebase/force-push `main`: sync upstream bằng merge (hoặc fast-forward khi fork chưa có commit riêng).
- Không đọc/in bí mật: `~/.config/wallos/`, biến môi trường Railway, DB production (`db/wallos.db`), khoá API trong bảng settings, SMTP/OIDC/khoá AI. Trên máy không có file bí mật nào của repo này.
- Không gọi `endpoints/db/migrate.php`, `api/**`, `endpoints/**` trên production khi kiểm; health chỉ HEAD `/` và GET `/health.php`. Không đăng nhập, không vượt chặn.
- Không chạy `docker build`/`docker compose`, không cài thêm thư viện PHP/JS trừ khi được giao.

**Cần anh duyệt**
- Push `main` (deploy production), kể cả sau khi sync upstream.
- Đổi biến môi trường / volume / domain trên Railway, redeploy, rollback; đổi nguồn image (GitHub ↔ `bellamy/wallos`).
- Sync upstream có bước migrate DB (upstream chạy `migrations/` tự động khi khởi động/`migrate.php` — đọc `CHANGELOG.md` trước); nâng phiên bản lớn.
- Đổi tên repo (`fork-wallos`), đổi remote, xoá dữ liệu/volume production.

## Phòng ban

Agent dùng chung của Holdings (cài qua `holdings ./hq install`); repo này không có agent riêng. Agent không gọi được agent khác; việc nhiều phòng do phiên điều hành gọi lần lượt.

| Việc | Giao cho | Ghi chú |
|---|---|---|
| Sync upstream, kiểm diff, cấu hình Railway (đề xuất), xác nhận nguồn image | `devops` | chỉ đọc; đề xuất lệnh chính xác, anh duyệt rồi phiên điều hành chạy |
| Hiểu/khoanh vùng lỗi trong code PHP/JS upstream, vá được giao rõ | `web-dev` | giữ diff tối thiểu; không có php trên máy để chạy thử |
| `tools/health.py`, `tools/check.sh` | `tools-dev` | Python 3.9 stdlib, POSIX sh |
| Chạy test/health, kiểm production | `qa-tester` | `sh tools/check.sh`, `python3 tools/health.py` |
| Thẩm định diff trước khi commit | `reviewer` | trả lời thêm: diff có đụng mã upstream không |
| Chi phí token | `tai-chinh` | `hq cost --repo wallos` |

## 6. Fork và cập nhật upstream

- Upstream: `https://github.com/ellite/Wallos` (nhánh `main`, release bằng release-please: `CHANGELOG.md` + tag `vX.Y.Z`, image `bellamy/wallos`). Remote hiện có trên máy: chỉ `origin` = `https://github.com/cuonghapvn/wallos.git` (GitHub hiển thị `Wallos`), chưa có remote `upstream` (`git remote -v`).
- Fork hiện **không có commit riêng** (`git log --author=Cuong` rỗng): `main` = `main` upstream tại 4.8.0 (23/3/2026). Sau đợt 5 sẽ có một commit thêm file quy chuẩn + khối `.dockerignore`; giữ danh sách file riêng này ngắn.
- Cách cập nhật (cần anh duyệt vì kết thúc bằng push = deploy, nếu Railway build từ repo này):
  1. `git remote add upstream https://github.com/ellite/Wallos.git` (một lần).
  2. `git fetch upstream && git merge upstream/main` (hoặc dùng nút **Sync fork** trên GitHub rồi `git pull`).
  3. Xung đột chỉ có thể ở `.dockerignore` (khối cuối của mình) và file quy chuẩn; giữ phần upstream, thêm lại phần của mình.
  4. Đọc `CHANGELOG.md` phần mới (migration, biến môi trường, đổi cron); `sh tools/check.sh`; rồi xin duyệt push `main`.
- Nếu Railway kéo thẳng image `bellamy/wallos` thì cập nhật production là việc trên Railway (redeploy image mới, cần anh duyệt), còn repo chỉ để đọc code — ghi lại vào `company.json.deploy.note` và `docs/ROADMAP.md` khi xác nhận được.
