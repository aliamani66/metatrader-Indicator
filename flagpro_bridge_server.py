import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler

EXPERTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Experts")
SETTINGS_DIR_FA = os.path.join(EXPERTS_DIR, "تنظیمات")
SETTINGS_DIR_EN = os.path.join(EXPERTS_DIR, "Settings")
TESTER_PROFILES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Profiles", "Tester")

os.makedirs(SETTINGS_DIR_FA, exist_ok=True)
os.makedirs(SETTINGS_DIR_EN, exist_ok=True)
os.makedirs(TESTER_PROFILES_DIR, exist_ok=True)

class BridgeHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-Requested-With')

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self._send_cors_headers()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        data = {
            "status": "ok",
            "message": "FlagPro Settings Bridge Server is running",
            "experts_dir": EXPERTS_DIR,
            "settings_dir_fa": SETTINGS_DIR_FA,
            "settings_dir_en": SETTINGS_DIR_EN
        }
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

    def do_POST(self):
        path = self.path.split('?')[0]
        content_length = int(self.headers.get('Content-Length', 0))
        post_body = self.rfile.read(content_length)

        if path == '/save_set':
            try:
                payload = json.loads(post_body.decode('utf-8'))
                filename = payload.get('filename', 'FlagPro_Settings.set')
                content = payload.get('content', '')

                # Sanitize filename
                safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ()")
                if not safe_name.endswith('.set'):
                    safe_name += '.set'

                path_fa = os.path.join(SETTINGS_DIR_FA, safe_name)
                path_en = os.path.join(SETTINGS_DIR_EN, safe_name)

                # Normalize line breaks to standard CRLF
                lines = [l.strip('\r\n') for l in content.splitlines()]
                clean_content = '\r\n'.join(lines) + '\r\n'

                # MetaTrader 5 strictly requires UTF-16 LE with BOM
                with open(path_fa, 'w', encoding='utf-16') as f:
                    f.write(clean_content)

                with open(path_en, 'w', encoding='utf-16') as f:
                    f.write(clean_content)

                self.send_response(200)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                res = {
                    "success": True,
                    "filename": safe_name,
                    "saved_path_fa": path_fa,
                    "saved_path_en": path_en
                }
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
                print(f"Saved set file: {safe_name}")
            except Exception as e:
                self.send_response(500)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                res = {"success": False, "error": str(e)}
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))

        elif path == '/save_ini':
            try:
                payload = json.loads(post_body.decode('utf-8'))
                filename = payload.get('filename', 'FlagPro_Tester.ini')
                content = payload.get('content', '')

                safe_name = "".join(c for c in filename if c.isalnum() or c in "._- ()")
                if not safe_name.endswith('.ini'):
                    safe_name += '.ini'

                path_ini = os.path.join(TESTER_PROFILES_DIR, safe_name)
                lines = [l.strip('\r\n') for l in content.splitlines()]
                clean_content = '\r\n'.join(lines) + '\r\n'

                with open(path_ini, 'w', encoding='utf-16') as f:
                    f.write(clean_content)

                self.send_response(200)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                res = {
                    "success": True,
                    "filename": safe_name,
                    "saved_path": path_ini
                }
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
                print(f"Saved ini file: {safe_name}")
            except Exception as e:
                self.send_response(500)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                res = {"success": False, "error": str(e)}
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))

        elif path == '/open_tester_folder':
            try:
                os.startfile(TESTER_PROFILES_DIR)
                self.send_response(200)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                res = {"success": True, "opened": TESTER_PROFILES_DIR}
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                res = {"success": False, "error": str(e)}
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))

        elif path == '/open_folder':
            try:
                target = SETTINGS_DIR_FA if os.path.exists(SETTINGS_DIR_FA) else SETTINGS_DIR_EN
                os.startfile(target)
                self.send_response(200)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                res = {"success": True, "opened": target}
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                res = {"success": False, "error": str(e)}
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))

        elif path == '/rebuild':
            try:
                payload = json.loads(post_body.decode('utf-8'))
                filename = payload.get('filename', '')
                content = payload.get('content', '')

                if filename and content:
                    files_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Files")
                    os.makedirs(files_dir, exist_ok=True)
                    csv_target = os.path.join(files_dir, filename)
                    with open(csv_target, 'w', encoding='utf-8') as f:
                        f.write(content)

                import build_master_dashboard
                build_master_dashboard.build_dashboard()

                self.send_response(200)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                res = {"success": True, "message": "Dashboard rebuilt successfully!"}
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.send_response(500)
                self._send_cors_headers()
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.end_headers()
                res = {"success": False, "error": str(e)}
                self.wfile.write(json.dumps(res, ensure_ascii=False).encode('utf-8'))
        else:
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()

    def log_message(self, format, *args):
        pass

def run_server(port=8288):
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, BridgeHandler)
    print(f"FlagPro Bridge Server running on http://127.0.0.1:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()

if __name__ == '__main__':
    p = 8288
    if len(sys.argv) > 1:
        p = int(sys.argv[1])
    run_server(p)
