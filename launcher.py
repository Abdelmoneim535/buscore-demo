# -*- coding: utf-8 -*-
"""
BusCore Launcher v2
- يدعم العربية على Windows
- يفحص المنفذ
- يفتح المتصفح
"""
import sys
import os
import socket
import time
import threading
import webbrowser
from pathlib import Path


# 
# إصلاح الترميز على Windows
# 
if sys.platform == "win32":
    try:
        # تعيين stdout/stderr إلى UTF-8
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


# 
# الإعدادات
# 
HOST = "0.0.0.0"
DEFAULT_PORT = 8000
OPEN_BROWSER = True
BROWSER_DELAY = 2
PROGRAM_NAME = "BusCore"
VERSION = "1.0.0"


def get_local_ip():
    """يحصل على IP الحاسب في الشبكة المحلية"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def is_port_available(port):
    """يفحص إذا كان المنفذ متاحاً"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(("127.0.0.1", port)) != 0
    except Exception:
        return False


def find_available_port(start_port, max_attempts=20):
    """يبحث عن منفذ متاح"""
    for i in range(max_attempts):
        port = start_port + i
        if is_port_available(port):
            return port
    return None


def open_browser(url):
    """يفتح المتصفح بعد تأخير"""
    time.sleep(BROWSER_DELAY)
    try:
        webbrowser.open(url)
        print(f"[OK] Browser opened: {url}")
    except Exception as e:
        print(f"[WARN] Could not open browser: {e}")
        print(f"[INFO] Open manually: {url}")


def safe_print(text):
    """طباعة آمنة مع معالجة الأخطاء"""
    try:
        print(text)
    except UnicodeEncodeError:
        try:
            print(text.encode('ascii', 'replace').decode('ascii'))
        except Exception:
            pass


def main():
    """الدالة الرئيسية"""
    
    # 
    # 1) فحص المنفذ
    # 
    port = DEFAULT_PORT
    
    if not is_port_available(port):
        safe_print(f"[WARN] Port {port} is busy - searching...")
        new_port = find_available_port(port + 1)
        if new_port:
            safe_print(f"[OK] Using port {new_port}")
            port = new_port
        else:
            safe_print("[ERROR] No available port")
            input("Press Enter to exit...")
            sys.exit(1)
    
    # 
    # 2) احسب الروابط
    # 
    url_local = f"http://127.0.0.1:{port}"
    local_ip = get_local_ip()
    url_mobile = f"http://{local_ip}:{port}" if local_ip != "127.0.0.1" else "(no network)"
    
    # 
    # 3) عرض الرسائل (بالإنجليزية لتفادي مشاكل الترميز)
    # 
    banner = f"""
==============================================================
   {PROGRAM_NAME} - Transport Management System
   Version {VERSION}
==============================================================

[PC Access]
   {url_local}

[Mobile Access - Same WiFi]
   {url_mobile}

--------------------------------------------------------------
[Login]
   Username: demo
   Password: demo

[Exit]
   Press Ctrl+C or close this window
--------------------------------------------------------------
"""
    safe_print(banner)
    
    # 
    # 4) فتح المتصفح
    # 
    if OPEN_BROWSER:
        threading.Thread(
            target=open_browser,
            args=(url_local,),
            daemon=True
        ).start()
    
    # 
    # 5) تشغيل FastAPI
    # 
    try:
        import uvicorn
        from app.main import app
        
        safe_print("[START] Starting server...")
        
        uvicorn.run(
            app,
            host=HOST,
            port=port,
            log_level="info",
        )
    except KeyboardInterrupt:
        safe_print("\n[STOP] BusCore closed. Goodbye!")
    except Exception as e:
        safe_print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        input("Press Enter to exit...")


if __name__ == "__main__":
    main()
