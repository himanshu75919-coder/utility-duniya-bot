"""v48 TEST — IMEI full specs (hub v2.4/2.5) + YouTube 1080p quality + size fallback.

Kya test hota hai:
  1. imei_lookup: hub v2.4 shape parse (photo + 12 sections + JSON file), purana TAC shape fallback
  2. IMEI validation (15 digit + Luhn), caption/text limits, specs filename
  3. api_hub.hub_yt_download: 1080p sabse pehle, backup (480p) link alag
  4. media_downloader._hub_youtube_download: chhota file bhejta hai, bada file → backup
     quality, dono bade → "link" (truncated video kabhi nahi)
  5. _remote_size: Content-Range / Content-Length parsing
"""
import io
import json
import os
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

os.environ["DB_PATH"] = "/tmp/_v48.db"
os.environ["BOT_TOKEN"] = "123456789:AAHtesttoken_testtoken_testtoken_testtok"
os.environ["ADMIN_ID"] = "8607774564"
if os.path.exists("/tmp/_v48.db"):
    os.remove("/tmp/_v48.db")

PORT = 8901
os.environ["HUB_API_BASE"] = f"http://127.0.0.1:{PORT}/api"
os.environ["HUB_API_KEY"] = "testkey123"
sys.path.insert(0, "/home/user/fix")

from modules import api_hub as hub                     # noqa: E402
from modules import imei_lookup as il                  # noqa: E402
from modules import media_downloader as md             # noqa: E402

PASS, FAIL = [], []
OK_KEY = "testkey123"

# file sizes (bytes) — mock server inhi ko bhejta hai
HD_SIZE = 60 * 1024 * 1024        # 60 MB (48MB limit se bada)
SD_SIZE = 8 * 1024 * 1024         # 8 MB
SMALL_SIZE = 4 * 1024 * 1024      # 4 MB


def ok(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"{'✅' if cond else '❌'} {name}" + (f"  — {str(detail)[:200]}" if detail and not cond else ""))


IMEI_PAYLOAD = {
    "success": True, "tac": "35635642", "brand": "SAMSUNG", "device": "SAMSUNG GALAXY TAB A9+",
    "extra": "", "model_codes": ["SM-X210", "SM-X216B"], "released": 2023,
    "image": "https://nanoreview.net/common/images/tablet/samsung-galaxy-tab-a9-plus-mini@2x.jpeg",
    "specs": {
        "name": "Samsung Galaxy Tab A9+ (Plus)",
        "url": "https://nanoreview.net/en/tablet/samsung-galaxy-tab-a9-plus",
        "image": "https://nanoreview.net/common/images/tablet/samsung-galaxy-tab-a9-plus-mini@2x.jpeg",
        "row_count": 122,
        "sections": [
            {"title": "Display", "rows": [["Type", "TFT LCD"], ["Size", "11 inches"],
                                          ["Resolution", "1200 x 1920 pixels"], ["Refresh rate", "90 Hz"]]},
            {"title": "Design and build", "rows": [["Height", "257.1 mm"], ["Width", "168.7 mm"],
                                                   ["Weight", "480 g"]]},
            {"title": "Performance", "rows": [["Chipset", "Qualcomm Snapdragon 695"],
                                              ["Max clock", "2200 MHz"], ["Cores", "8"]]},
            {"title": "Memory", "rows": [["RAM size", "4 GB"], ["Memory type", "LPDDR4X"]]},
            {"title": "Software", "rows": [["Operating system", "Android 13"], ["ROM", "One UI 5.1"]]},
            {"title": "Battery", "rows": [["Capacity", "7040 mAh"], ["Fast charging", "15 W"]]},
            {"title": "Main camera", "rows": [["Matrix", "8 megapixels"], ["Video", "1080p"]]},
            {"title": "Connectivity", "rows": [["Wi-Fi standard", "Wi-Fi 5"], ["Bluetooth", "5.1"]]},
        ],
    },
    "links": {"gsmarena": "https://www.gsmarena.com/res.php3?sSearch=SAMSUNG+GALAXY+TAB+A9%2B",
              "nanoreview": "https://nanoreview.net/en/tablet/samsung-galaxy-tab-a9-plus",
              "imei_info": "https://www.imei.info/?imei=35635642"},
    "source": "tac-db (248364 rows)", "specs_source": "nanoreview.net",
}


class HubHandler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _file(self, size, ctype="video/mp4", range_ok=True):
        rng = self.headers.get("Range")
        if rng and range_ok:
            self.send_response(206)
            self.send_header("Content-Range", f"bytes 0-{size - 1}/{size}")
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(size))
            self.end_headers()
            remaining = size
            while remaining > 0:
                chunk = min(262144, remaining)
                try:
                    self.wfile.write(b"V" * chunk)
                except Exception:
                    return
                remaining -= chunk
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(size))
        self.end_headers()
        remaining = size
        while remaining > 0:
            chunk = min(262144, remaining)
            try:
                self.wfile.write(b"V" * chunk)
            except Exception:
                return
            remaining -= chunk

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        raw = u.path
        if raw == "/hd.mp4":
            return self._file(HD_SIZE)
        if raw == "/hd_norange.mp4":
            return self._file(HD_SIZE, range_ok=False)
        if raw == "/sd.mp4":
            return self._file(SD_SIZE)
        if raw == "/small.mp4":
            return self._file(SMALL_SIZE)
        path = raw.replace("/api", "", 1) or "/"
        if q.get("key", [""])[0] != OK_KEY:
            return self._json(401, {"error": "Invalid API key"})
        if path == "/imei":
            if q.get("imei", [""])[0] == "356356426587792":
                return self._json(200, IMEI_PAYLOAD)
            return self._json(200, {"success": False, "error": "Invalid IMEI (not in TAC database)"})
        if path in ("/youtube-download", "/ytdl", "/youtube-mp3"):
            return self._json(200, {
                "success": True, "title": "Test Video 1080", "duration": 240,
                "links": [
                    {"type": "video", "quality": "1080p", "hd": True, "provider": "loader.to",
                     "ext": "mp4", "url": f"http://127.0.0.1:{PORT}/hd.mp4"},
                    {"type": "video", "quality": "480p", "provider": "savetube", "backup": True,
                     "ext": "mp4", "url": f"http://127.0.0.1:{PORT}/sd.mp4"},
                    {"type": "audio", "quality": "audio", "provider": "savetube",
                     "ext": "mp3", "url": f"http://127.0.0.1:{PORT}/a.mp3"},
                ],
                "video_id": "test1234567",
            })
        if path in ("/youtube-all", "/youtube-info"):
            return self._json(200, {"title": "Test Video 1080",
                                    "hd": f"http://127.0.0.1:{PORT}/small.mp4"})
        return self._json(404, {"error": "Endpoint not found"})

    def do_POST(self):
        self.do_GET()


srv = ThreadingHTTPServer(("127.0.0.1", PORT), HubHandler)
threading.Thread(target=srv.serve_forever, daemon=True).start()


# ======================================================================
def test_imei():
    print("\n=== 1) IMEI full details (hub v2.4 shape)")
    good, clean, err = il.validate_imei("356356426587792")
    ok("IMEI validation pass (15 digit + Luhn)", good, err)
    bad, _, berr = il.validate_imei("356356426587790")
    ok("Galat IMEI reject (Luhn fail)", not bad and ("valid" in berr.lower() or "sahi nahi" in berr.lower() or "check digit" in berr.lower()), berr)

    res = il.fetch_imei_details("356356426587792", use_cache=False)
    ok("hub v2.4 payload parse ok", res.get("ok"), res.get("error"))
    ok("brand + model sahi", res.get("brand") == "SAMSUNG" and "TAB A9+" in str(res.get("model")))
    ok("photo mila (nanoreview image)", str(res.get("photo", "")).startswith("https://"), res.get("photo"))
    secs = res.get("sections") or []
    ok("sections >= 9 (Device + 8 spec)", len(secs) >= 9, [s["title"] for s in secs])
    rows_total = sum(len(s["rows"]) for s in secs)
    ok("spec rows >= 20", rows_total >= 20, rows_total)
    ok("TAC dikhaya gaya", res.get("tac") == "35635642", res.get("tac"))
    title = il.device_title(res)
    ok("title pretty (Samsung Galaxy Tab A9+)", title == "Samsung Galaxy Tab A9+", title)

    cap = il.render_caption(res)
    ok("caption < 1024 chars", len(cap) < 1024, len(cap))
    ok("caption me photo heading + specs count", "Samsung Galaxy Tab A9+" in cap and "specification" in cap)
    txt = il.render_text(res)
    ok("text < 4096 chars", len(txt) < 4096, len(txt))
    ok("text me Chipset + Battery", "Snapdragon 695" in txt and "7040 mAh" in txt)

    fn = il.specs_filename(res)
    ok("specs filename format", fn.endswith("_specs.json") and "Samsung" in fn, fn)
    js = il.specs_json_bytes(res)
    d = json.loads(js)
    ok("JSON me specifications + imei", d.get("imei") == "356356426587792"
       and d.get("specifications", {}).get("Display", {}).get("Type") == "TFT LCD", list(d.keys()))
    ok("JSON full sheet (saare rows + 1.2KB+)", len(js) > 1200 and len(d["specifications"]) >= 8, len(js))
    ok("links me nanoreview + imei.info", any("nanoreview" in u for _, u in res["links"])
       and any("imei.info" in u for _, u in res["links"]))
    ok("JSON me powered_by", d.get("powered_by") == "@Supermannn_x", d.get("powered_by"))

    # TAC basic (purana shape) bhi chalta rahe
    old = il.parse_imei_payload({"success": True, "tac": "35301011", "brand": "APPLE",
                                 "model": "iPhone 12 mini"}, "353010111111110")
    ok("purana TAC shape bhi parse hota hai", old.get("ok") and old.get("brand") == "APPLE")

    # data nahi mila → not_found
    nf = il.parse_imei_payload({"success": False, "error": "Invalid IMEI"}, "123456789012345")
    ok("unknown IMEI → not_found flag", not nf.get("ok") and nf.get("not_found"))


def test_yt_quality():
    print("\n=== 2) YouTube 1080p quality selection")
    info = hub.hub_yt_download("https://youtube.com/watch?v=test1234567", kind="video")
    ok("hub_yt_download ok", info.get("ok"), info.get("error"))
    ok("best quality 1080p", str(info.get("quality")) == "1080p", info.get("quality"))
    ok("hd flag true", info.get("hd") is True)
    ok("best_url = 1080 file", str(info.get("best_url", "")).endswith("/hd.mp4"), info.get("best_url"))
    ok("backup_url = 480 file", str(info.get("backup_url", "")).endswith("/sd.mp4"), info.get("backup_url"))
    ok("backup quality label", str(info.get("backup_quality")) == "480p", info.get("backup_quality"))
    ok("audio_url alag se mila", str(info.get("audio_url", "")).endswith(".mp3"), info.get("audio_url"))


def test_download_flow():
    print("\n=== 3) Bot download flow (1080 → 480 → link)")
    ok("_remote_size (Content-Range)", md._remote_size(f"http://127.0.0.1:{PORT}/hd.mp4") == HD_SIZE)
    ok("_remote_size (plain Content-Length)",
       md._remote_size(f"http://127.0.0.1:{PORT}/hd_norange.mp4") == HD_SIZE)

    # 1080 (60MB) limit se bada → 480 (8MB) backup bhejna chahiye
    res = md._hub_youtube_download("https://youtube.com/watch?v=test1234567", 48)
    ok("bada 1080 → video bhejta hai (480 backup)", res.get("ok") and res.get("type") == "video", str(res)[:180])
    ok("size 48MB ke andar", (res.get("size_mb") or 0) <= 48, res.get("size_mb"))
    ok("quality label dikhta hai", str(res.get("quality")) in ("1080p", "480p"), res.get("quality"))
    ok("engine me quality/loader likha", "hub" in str(res.get("engine")), res.get("engine"))
    ok("bytes asli mp4 jaisa (V se bharа)", (res.get("bytes") or b"")[:16] == b"V" * 16, (res.get("bytes") or b"")[:8])


def test_truncate_guard():
    print("\n=== 4) Truncated file kabhi nahi (dono bade → link)")
    global HD_SIZE, SD_SIZE
    save_hd, save_sd = HD_SIZE, SD_SIZE
    HD_SIZE, SD_SIZE = 70 * 1024 * 1024, 65 * 1024 * 1024     # dono 48MB se bade
    try:
        res = md._hub_youtube_download("https://youtube.com/watch?v=test1234567", 48)
        ok("dono bade → type=link", res.get("type") == "link", str(res)[:200])
        ok("direct_url diya", str(res.get("direct_url", "")).startswith("http"), res.get("direct_url"))
        ok("size_mb bataya", (res.get("size_mb") or 0) > 48, res.get("size_mb"))
        ok("note me limit ka zikr", "48" in str(res.get("note", "")), res.get("note"))
        ok("Koi truncated bytes nahi bheje", not res.get("bytes"), list((res.get("bytes") or b""))[:5])
    finally:
        HD_SIZE, SD_SIZE = save_hd, save_sd


def main():
    test_imei()
    test_yt_quality()
    test_download_flow()
    test_truncate_guard()
    print(f"\n=== v48 RESULT: {len(PASS)} pass, {len(FAIL)} fail")
    if FAIL:
        print("FAILED:", FAIL)
        sys.exit(1)


if __name__ == "__main__":
    main()
