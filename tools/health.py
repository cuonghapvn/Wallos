#!/usr/bin/python3
"""Sức khoẻ vận hành của fork Wallos (Quy chuẩn repo v1 — holdings/standards/REPO_STANDARD.md mục 3).

Chỉ đọc: git local, production wallos.cuongn.com (HEAD/GET, timeout 5 giây, không gửi token/cookie), công cụ trên máy.
Không sửa mã upstream, không đổi dữ liệu. Python 3.9 stdlib, không dependency ngoài.

  python3 tools/health.py                 bảng ✓ / ⚠ / ✗ (mã thoát 1 nếu có ✗)
  python3 tools/health.py --json          {at, site, checks: [{area, name, level, detail}]}
  python3 tools/health.py --only git      chỉ phần không cần mạng (dùng làm lệnh `status`)
                                          --only web | build cũng được
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = os.environ.get("HQ_SITE", "https://wallos.cuongn.com")
TIMEOUT = 5.0  # giây mỗi request
SLOW = 3.0  # giây → warn
UA = "hq-health/1 (+https://hq.cuongn.com)"

# (area, tên, đường dẫn, method, thân mong đợi (GET) hoặc None)
WEB_CHECKS = [
    ("web", "Trang chủ (302 → /login.php là bình thường)", "/", "HEAD", None),
    ("web", "/health.php (healthcheck của image)", "/health.php", "GET", "OK"),
]


def item(area: str, name: str, level: str, detail: str = "") -> dict:
    return {"area": area, "name": name, "level": level, "detail": detail}


def git(*args: str) -> tuple[int, str]:
    try:
        p = subprocess.run(["git", "--no-optional-locks", *args], cwd=ROOT, capture_output=True, text=True, timeout=20)
    except (OSError, subprocess.TimeoutExpired) as e:
        return 1, str(e)[:120]
    return p.returncode, (p.stdout or p.stderr).strip()


def upstream_version() -> str | None:
    """Phiên bản ở đầu CHANGELOG.md của upstream (release-please): '## [4.8.0](…) (2026-03-23)'."""
    try:
        for line in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8").splitlines()[:40]:
            m = re.match(r"^## \[?v?(\d+\.\d+\.\d+)\]?.*?\((\d{4}-\d{2}-\d{2})\)", line)
            if m:
                return f"{m.group(1)} ({m.group(2)})"
    except OSError:
        return None
    return None


def check_git() -> list[dict]:
    out = []
    rc, branch = git("rev-parse", "--abbrev-ref", "HEAD")
    if rc != 0:
        return [item("git", "Repo git", "bad", branch or "không đọc được git")]
    out.append(item("git", "Nhánh", "ok" if branch == "main" else "warn", branch))

    rc, ahead = git("rev-list", "--count", "@{u}..HEAD")
    if rc != 0:
        out.append(item("git", "Commit chưa push", "warn", "nhánh chưa có upstream (origin)"))
    else:
        out.append(item("git", "Commit chưa push", "ok" if ahead == "0" else "warn", f"{ahead} commit"))
        rc, behind = git("rev-list", "--count", "HEAD..@{u}")
        if rc == 0 and behind != "0":
            out.append(item("git", "Commit chưa pull từ origin", "warn", f"{behind} commit (theo lần fetch gần nhất)"))

    rc, status = git("status", "--porcelain")
    dirty = [l for l in status.splitlines() if l.strip()]
    out.append(item("git", "File chưa commit", "ok" if not dirty else "warn", f"{len(dirty)} file"))

    v = upstream_version()
    out.append(item("git", "Phiên bản upstream (CHANGELOG.md)", "ok" if v else "warn", v or "không đọc được"))
    return out


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Không đi theo 3xx: mã 3xx tự nó là bằng chứng web sống (theo mục 3 chuẩn: 2xx/3xx = ok)."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: D401
        return None


OPENER = urllib.request.build_opener(NoRedirect)


def probe(url: str, method: str) -> tuple[int | None, str, float]:
    """→ (mã HTTP hoặc None khi lỗi mạng, thân (≤ 2 KB, chỉ với GET), giây)."""
    req = urllib.request.Request(url, method=method, headers={"User-Agent": UA, "Accept": "*/*"})
    t0 = time.monotonic()
    try:
        with OPENER.open(req, timeout=TIMEOUT) as r:
            body = r.read(2048).decode("utf-8", "replace") if method == "GET" else ""
            return r.status, body, time.monotonic() - t0
    except urllib.error.HTTPError as e:
        return e.code, "", time.monotonic() - t0
    except Exception as e:  # noqa: BLE001 — mọi lỗi mạng/TLS/timeout báo như nhau
        return None, str(e)[:120], time.monotonic() - t0


def check_web() -> list[dict]:
    out = []
    for area, name, path, method, want in WEB_CHECKS:
        code, body, dt = probe(SITE + path, method)
        if code is None:
            out.append(item(area, name, "bad", f"lỗi mạng: {body} · {dt:.1f}s"))
            continue
        problem = ""
        if not 200 <= code < 400:
            problem = f"HTTP {code}"
        elif want is not None and body.strip() != want:
            problem = f"thân không phải {want!r}"
        level = "bad" if problem else ("warn" if dt > SLOW else "ok")
        out.append(item(area, name, level, problem or f"{code} · {dt:.1f}s"))
    return out


def check_build() -> list[dict]:
    out = []
    php = shutil.which("php")
    out.append(item("build", "php trên máy", "ok" if php else "warn",
                    php or "không có — tools/check.sh bỏ qua php -l (production chạy php 8.3 trong image)"))
    for f in ("Dockerfile", "nginx.conf", "nginx.default.conf", "startup.sh", "health.php", "cronjobs", "db/wallos.empty.db"):
        ok = (ROOT / f).is_file()
        out.append(item("build", f, "ok" if ok else "bad", "có" if ok else "THIẾU — image build/chạy cần file này"))
    return out


PARTS = {"git": check_git, "web": check_web, "build": check_build}
TITLES = {"git": "Git local", "web": "Production " + SITE, "build": "Môi trường build"}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="tools/health.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--only", choices=list(PARTS))
    a = ap.parse_args(argv)
    results = [r for k, fn in PARTS.items() if not a.only or a.only == k for r in fn()]
    if a.json:
        print(json.dumps({"at": datetime.now(timezone.utc).isoformat(), "site": SITE, "checks": results}, ensure_ascii=False, indent=2))
    else:
        icon = {"ok": "✓", "warn": "⚠", "bad": "✗"}
        shown = None
        for r in results:
            part = "git" if r["area"] == "git" else ("build" if r["area"] == "build" else "web")
            if part != shown:
                shown = part
                print(TITLES[part])
            print(f"  {icon[r['level']]} {r['name']}: {r['detail']}")
        bad = sum(r["level"] == "bad" for r in results)
        warn = sum(r["level"] == "warn" for r in results)
        print(f"== {len(results)} mục: {bad} lỗi, {warn} cảnh báo")
    return 1 if any(r["level"] == "bad" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
