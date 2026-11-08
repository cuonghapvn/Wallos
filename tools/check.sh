#!/bin/sh
# Kiểm nhanh OFFLINE cho fork Wallos — lệnh `test` trong company.json (Quy chuẩn repo v1 mục 3).
# Không mạng, không DB, < 30 giây. Mã thoát 0 = qua, 1 = có lỗi, 2 = không chạy được.
#
# Kiểm: (1) `php -l` mọi *.php ở gốc + endpoints/ + includes/ (api/ và libs/ của bên thứ ba bỏ qua cho nhanh;
#       KHÔNG có php trên máy thì bỏ qua và nói rõ — xem giới hạn trong AGENTS.md), (2) cú pháp JSON của mọi
#       *.json git theo dõi (manifest.json), (3) `node --check` service-worker.js + scripts/**/*.js nếu có node,
#       (4) `sh -n startup.sh`, (5) các file image Docker cần phải tồn tại.
# Upstream không có bộ test tự động; kiểm chạy thật phải qua Docker (không làm ở đây).
set -u
cd "$(dirname "$0")/.." || exit 2
command -v git >/dev/null 2>&1 || { echo "✗ không có git"; exit 2; }

fail=0
skip=""
n_php=0
n_json=0
n_js=0
t0=$(date +%s)

if command -v php >/dev/null 2>&1; then
  for f in $(git ls-files '*.php' | grep -E '^(endpoints|includes)/|^[^/]+\.php$'); do
    n_php=$((n_php + 1))
    if ! php -l "$f" >/dev/null 2>&1; then
      fail=$((fail + 1)); echo "✗ cú pháp PHP: $f"
    fi
  done
else
  skip="php không có trên máy → chưa kiểm php -l (chỉ kiểm JSON/JS/sh/file image)"
  echo "⚠ $skip"
fi

for f in $(git ls-files '*.json'); do
  n_json=$((n_json + 1))
  if ! python3 -I -c 'import json, sys; json.load(open(sys.argv[1], encoding="utf-8"))' "$f" 2>/dev/null; then
    fail=$((fail + 1)); echo "✗ JSON hỏng: $f"
  fi
done

if command -v node >/dev/null 2>&1; then
  for f in $(git ls-files 'service-worker.js' 'scripts/*.js' 'scripts/**/*.js'); do
    n_js=$((n_js + 1))
    if ! node --check "$f" 2>/dev/null; then
      fail=$((fail + 1)); echo "✗ cú pháp JS: $f"
    fi
  done
else
  echo "⚠ node không có trên máy → bỏ qua node --check (JS chỉ chạy ở trình duyệt, không bắt buộc)"
fi

if ! sh -n startup.sh 2>/dev/null; then
  fail=$((fail + 1)); echo "✗ cú pháp sh: startup.sh"
fi

for f in Dockerfile nginx.conf nginx.default.conf health.php cronjobs db/wallos.empty.db; do
  if [ ! -f "$f" ]; then
    fail=$((fail + 1)); echo "✗ thiếu file image cần: $f"
  fi
done

dt=$(( $(date +%s) - t0 ))
if [ "$fail" -eq 0 ]; then
  if [ -n "$skip" ]; then
    echo "✓ check.sh (giới hạn): $n_json JSON, $n_js JS, startup.sh, file image hợp lệ (${dt}s) — $skip"
  else
    echo "✓ check.sh: $n_php PHP, $n_json JSON, $n_js JS, startup.sh, file image hợp lệ (${dt}s)"
  fi
  exit 0
fi
echo "✗ check.sh: $fail lỗi (${dt}s)"
exit 1
