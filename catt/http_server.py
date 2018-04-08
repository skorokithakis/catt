import socketserver
import time
import traceback
from http.server import BaseHTTPRequestHandler
from pathlib import Path


def serve_file(filename, address="", port=45114):
    class FileHandler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa
            try:
                mediapath = Path(filename)
                length = mediapath.stat().st_size
                mtime = mediapath.stat().st_mtime
                mediafile = open(str(mediapath), "rb")

                self.send_response(200)
                self.send_header("Content-type", "video/mp4")
                self.send_header("Content-Length", length)
                self.send_header(
                    "Last-Modified",
                    time.strftime(
                        "%a %d %b %Y %H:%M:%S GMT",
                        time.localtime(mtime)
                    )
                )
                self.end_headers()

                while True:
                    data = mediafile.read(100 * 1024)

                    if not data:
                        break
                    self.wfile.write(data)
            except:  # noqa
                traceback.print_exc()

            mediafile.close()

    httpd = socketserver.TCPServer((address, port), FileHandler)
    httpd.serve_forever()
    httpd.server_close()
