#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
從 Pixabay 抓免費的照片／影片當 B-roll 素材。

只用 Python 標準庫，不用額外安裝套件。

金鑰讀取順序（找到就用）：
  1. 環境變數  PIXABAY_API_KEY
  2. repo 根目錄的檔案  .pixabay-key（一行一把金鑰，這個檔不進 Git）
  3. 參數  --key <金鑰>

用法：
  # 搜尋照片（預設照片＋影片都搜）
  python3 pixabay.py search "睡眠 床" --type all

  # 只搜影片，直式（適合 9:16）
  python3 pixabay.py search "ocean waves" --type video --orientation vertical

  # 下載指定素材到專案（id 從 search 結果來，photo/video 要分開下載）
  python3 pixabay.py fetch --type photo --project projects/example-aspartame 1234567 2345678
  python3 pixabay.py fetch --type video --project projects/example-aspartame 9876543

下載的檔案會放在：
  <專案>/inputs/broll/pixabay/            （素材本身，不進 Git）
出處與授權會寫進：
  <專案>/storyboard/pixabay-credits.md    （會進 Git，發布前對照 sources.md）
"""

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

PHOTO_API = "https://pixabay.com/api/"
VIDEO_API = "https://pixabay.com/api/videos/"
UA = "short-video-kit/1.0 (+broll-video skill)"


# ---------- 共用 ----------

def repo_root():
    # scripts/ 在 .claude/skills/broll-video/scripts/，往上四層是 repo 根
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))


def load_key(cli_key):
    if cli_key:
        return cli_key.strip()
    env = os.environ.get("PIXABAY_API_KEY")
    if env and env.strip():
        return env.strip()
    keyfile = os.path.join(repo_root(), ".pixabay-key")
    if os.path.isfile(keyfile):
        with open(keyfile, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    return line
    return None


def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def no_key_message():
    return (
        "找不到 Pixabay API 金鑰。請擇一設定（詳見 references/pixabay.md）：\n"
        "  1. 設環境變數：export PIXABAY_API_KEY=你的金鑰\n"
        "  2. 在 repo 根目錄建立檔案 .pixabay-key，貼上金鑰（這個檔不會進 Git）\n"
        "  3. 這次先用：加 --key 你的金鑰\n"
        "免費金鑰申請：先到 https://pixabay.com 註冊登入，再到 https://pixabay.com/api/docs/ 看你的金鑰。"
    )


def _opener():
    # ssl.create_default_context 會自動讀 SSL_CERT_FILE / SSL_CERT_DIR；
    # 在雲端 proxy 環境把 SSL_CERT_FILE 指到 CA bundle 即可。
    ctx = ssl.create_default_context()
    bundle = os.environ.get("PIXABAY_CA_BUNDLE") or os.environ.get("REQUESTS_CA_BUNDLE")
    if bundle and os.path.isfile(bundle):
        try:
            ctx.load_verify_locations(bundle)
        except ssl.SSLError:
            pass
    # urllib 會從環境變數讀 http_proxy / https_proxy
    return urllib.request.build_opener(
        urllib.request.HTTPSHandler(context=ctx),
        urllib.request.ProxyHandler(urllib.request.getproxies()),
    )


def api_get(url, params):
    full = url + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(full, headers={"User-Agent": UA})
    try:
        with _opener().open(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode("utf-8", "ignore")
        except Exception:
            pass
        if e.code in (400, 401):
            die("Pixabay 拒絕這次請求（%s）。通常是金鑰不對或參數有誤。\n%s" % (e.code, body))
        if e.code == 429:
            die("Pixabay 請求太頻繁（429）。免費金鑰每分鐘約 100 次，請稍等再試。")
        die("Pixabay 回傳錯誤 %s：%s" % (e.code, body))
    except urllib.error.URLError as e:
        die("連不上 Pixabay：%s\n（公司／雲端網路擋 CDN 時，可設 PIXABAY_CA_BUNDLE 指向 CA 憑證）" % e.reason)


def download(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with _opener().open(req, timeout=300) as resp, open(dest, "wb") as out:
        while True:
            chunk = resp.read(65536)
            if not chunk:
                break
            out.write(chunk)
    return os.path.getsize(dest)


def human_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return "%.1f%s" % (n, unit)
        n /= 1024.0


# ---------- search ----------

def do_search(args):
    key = load_key(args.key)
    if not key:
        die(no_key_message())

    want_photo = args.type in ("photo", "all")
    want_video = args.type in ("video", "all")
    results = {"query": args.query, "photos": [], "videos": []}

    base = {
        "key": key,
        "q": args.query,
        "lang": args.lang,
        "safesearch": "true" if args.safesearch else "false",
        "per_page": str(max(3, min(args.per_page, 50))),
        "page": str(args.page),
    }
    if args.orientation != "any":
        # Pixabay 照片用 orientation=horizontal|vertical；影片沒有這個參數，用長寬自己過濾
        pass

    if want_photo:
        p = dict(base)
        p["image_type"] = "photo"
        if args.orientation != "any":
            p["orientation"] = args.orientation
        if args.editors_choice:
            p["editors_choice"] = "true"
        data = api_get(PHOTO_API, p)
        for h in data.get("hits", []):
            results["photos"].append({
                "type": "photo",
                "id": h["id"],
                "tags": h.get("tags", ""),
                "width": h.get("imageWidth"),
                "height": h.get("imageHeight"),
                "user": h.get("user", ""),
                "page": h.get("pageURL", ""),
                "preview": h.get("previewURL", ""),
                "download": h.get("largeImageURL", ""),
            })

    if want_video:
        p = dict(base)
        if args.editors_choice:
            p["editors_choice"] = "true"
        data = api_get(VIDEO_API, p)
        for h in data.get("hits", []):
            v = h.get("videos", {})
            best = v.get("large") or v.get("medium") or v.get("small") or {}
            w, ht = best.get("width", 0), best.get("height", 0)
            if args.orientation == "vertical" and not (ht > w):
                continue
            if args.orientation == "horizontal" and not (w > ht):
                continue
            results["videos"].append({
                "type": "video",
                "id": h["id"],
                "tags": h.get("tags", ""),
                "width": w,
                "height": ht,
                "duration": h.get("duration"),
                "user": h.get("user", ""),
                "page": h.get("pageURL", ""),
                "preview": (v.get("medium") or {}).get("thumbnail", ""),
                "download": best.get("url", ""),
            })

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return

    total = len(results["photos"]) + len(results["videos"])
    if total == 0:
        print("找不到「%s」的素材。換個關鍵字（英文命中率通常比較高），或放寬 --orientation。" % args.query)
        return

    print("關鍵字：%s\n" % args.query)
    if results["photos"]:
        print("── 照片 %d 筆 ──" % len(results["photos"]))
        for h in results["photos"]:
            print("  [photo %d] %dx%d  by %s" % (h["id"], h["width"] or 0, h["height"] or 0, h["user"]))
            print("    標籤：%s" % h["tags"])
            print("    預覽：%s" % h["page"])
        print()
    if results["videos"]:
        print("── 影片 %d 筆 ──" % len(results["videos"]))
        for h in results["videos"]:
            dur = ("%ss" % h["duration"]) if h.get("duration") else "?"
            print("  [video %d] %dx%d  %s  by %s" % (h["id"], h["width"] or 0, h["height"] or 0, dur, h["user"]))
            print("    標籤：%s" % h["tags"])
            print("    預覽：%s" % h["page"])
        print()
    print("下載方式（photo 和 video 要分開下）：")
    if results["photos"]:
        ids = " ".join(str(h["id"]) for h in results["photos"][:3])
        print("  python3 %s fetch --type photo --project <專案> %s" % (os.path.basename(__file__), ids))
    if results["videos"]:
        ids = " ".join(str(h["id"]) for h in results["videos"][:3])
        print("  python3 %s fetch --type video --project <專案> %s" % (os.path.basename(__file__), ids))


# ---------- fetch ----------

def do_fetch(args):
    key = load_key(args.key)
    if not key:
        die(no_key_message())

    project = os.path.abspath(args.project)
    if not os.path.isdir(project):
        die("找不到專案資料夾：%s" % args.project)

    outdir = os.path.join(project, "inputs", "broll", "pixabay")
    os.makedirs(outdir, exist_ok=True)
    api = PHOTO_API if args.type == "photo" else VIDEO_API

    downloaded = []
    for item_id in args.ids:
        data = api_get(api, {"key": key, "id": str(item_id)})
        hits = data.get("hits", [])
        if not hits:
            print("  ✗ 找不到 %s %s（可能已被下架或 id 打錯）" % (args.type, item_id))
            continue
        h = hits[0]
        if args.type == "photo":
            url = h.get("largeImageURL", "")
            ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or ".jpg"
            w, ht = h.get("imageWidth"), h.get("imageHeight")
            dur = None
        else:
            v = h.get("videos", {})
            best = v.get(args.size) or v.get("large") or v.get("medium") or v.get("small") or {}
            url = best.get("url", "")
            ext = os.path.splitext(urllib.parse.urlparse(url).path)[1] or ".mp4"
            w, ht = best.get("width"), best.get("height")
            dur = h.get("duration")
        if not url:
            print("  ✗ %s %s 沒有可下載的檔案連結" % (args.type, item_id))
            continue
        fname = "pixabay-%s-%s%s" % (args.type, item_id, ext)
        dest = os.path.join(outdir, fname)
        try:
            size = download(url, dest)
        except Exception as e:  # noqa: BLE001
            print("  ✗ 下載 %s 失敗：%s" % (item_id, e))
            continue
        print("  ✓ %s  (%dx%d%s, %s)" % (
            fname, w or 0, ht or 0,
            (", %ss" % dur) if dur else "", human_size(size)))
        downloaded.append({
            "file": os.path.join("inputs", "broll", "pixabay", fname),
            "type": args.type,
            "id": item_id,
            "tags": h.get("tags", ""),
            "user": h.get("user", ""),
            "page": h.get("pageURL", ""),
            "width": w, "height": ht, "duration": dur,
        })

    if not downloaded:
        print("沒有下載到任何檔案。")
        return

    write_manifest(outdir, downloaded)
    write_credits(project, downloaded)
    print("\n素材放在：%s" % os.path.relpath(outdir, os.getcwd()))
    print("出處已寫入：%s" % os.path.relpath(
        os.path.join(project, "storyboard", "pixabay-credits.md"), os.getcwd()))
    print("提醒：把要上畫面的素材，照 compliance.md 一併列進 storyboard/sources.md，發布前逐條確認。")


def write_manifest(outdir, downloaded):
    path = os.path.join(outdir, "manifest.json")
    existing = []
    if os.path.isfile(path):
        try:
            existing = json.load(open(path, encoding="utf-8")).get("items", [])
        except Exception:  # noqa: BLE001
            existing = []
    by_file = {it["file"]: it for it in existing}
    for it in downloaded:
        by_file[it["file"]] = it
    payload = {
        "source": "pixabay",
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items": sorted(by_file.values(), key=lambda x: x["file"]),
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def write_credits(project, downloaded):
    sb = os.path.join(project, "storyboard")
    os.makedirs(sb, exist_ok=True)
    path = os.path.join(sb, "pixabay-credits.md")
    new = not os.path.isfile(path)
    with open(path, "a", encoding="utf-8") as f:
        if new:
            f.write("# Pixabay 素材出處\n\n")
            f.write("所有素材來自 Pixabay，採 Pixabay Content License："
                    "可免費商用、不需註明出處，但**不可**原樣轉售或單獨再散布素材本身，"
                    "且畫面若出現可辨識的人物／商標／作品，仍要留意是否另有限制。\n")
            f.write("詳見 references/pixabay.md。下表供內部備查與對照 sources.md。\n\n")
            f.write("| 檔案 | 類型 | Pixabay 頁面 | 作者 | 標籤 |\n")
            f.write("|---|---|---|---|---|\n")
        for it in downloaded:
            f.write("| `%s` | %s | %s | %s | %s |\n" % (
                os.path.basename(it["file"]), it["type"], it["page"],
                it["user"], (it["tags"] or "").replace("|", "／")))


# ---------- CLI ----------

def build_parser():
    p = argparse.ArgumentParser(
        prog="pixabay.py",
        description="從 Pixabay 抓免費照片／影片當 B-roll（見 references/pixabay.md）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("search", help="搜尋素材")
    s.add_argument("query", help="關鍵字（英文命中率通常較高）")
    s.add_argument("--type", choices=["photo", "video", "all"], default="all", help="要照片、影片、還是都要（預設 all）")
    s.add_argument("--orientation", choices=["any", "horizontal", "vertical"], default="any",
                   help="方向；vertical 適合 9:16 直式（預設 any）")
    s.add_argument("--lang", default="zh", help="關鍵字語言（預設 zh）")
    s.add_argument("--per-page", type=int, default=15, help="每種類型回傳幾筆（3-50，預設 15）")
    s.add_argument("--page", type=int, default=1, help="第幾頁（預設 1）")
    s.add_argument("--safesearch", action="store_true", help="只回傳適合各年齡的素材")
    s.add_argument("--editors-choice", action="store_true", help="只看 Pixabay 精選")
    s.add_argument("--json", action="store_true", help="輸出 JSON（給程式用）")
    s.add_argument("--key", help="直接指定金鑰（不建議，會留在指令紀錄）")
    s.set_defaults(func=do_search)

    f = sub.add_parser("fetch", help="下載指定素材到專案")
    f.add_argument("ids", nargs="+", help="素材 id（從 search 結果來）")
    f.add_argument("--type", choices=["photo", "video"], required=True, help="這批 id 是照片還是影片")
    f.add_argument("--project", required=True, help="專案資料夾，例如 projects/example-aspartame")
    f.add_argument("--size", choices=["large", "medium", "small"], default="large",
                   help="影片畫質（預設 large；照片一律抓 large）")
    f.add_argument("--key", help="直接指定金鑰（不建議，會留在指令紀錄）")
    f.set_defaults(func=do_fetch)
    return p


def main():
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
