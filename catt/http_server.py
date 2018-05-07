import socketserver
import time
import traceback
from http.server import BaseHTTPRequestHandler
from pathlib import Path


def serve_file(filename, address="", port=45114, content_type=None):
    class FileHandler(BaseHTTPRequestHandler):

        def format_size(self, size):
            for size_unity in ["B", "KB", "MB", "GB", "TB"]:
                if size < 1024:
                    return size, size_unity
                size = size / 1024
            return size * 1024, size_unity

        def log_message(self, format, *args, **kwargs):
            size, size_unity = self.format_size(length)
            format += " {} - {:0.2f} {}".format(content_type, size, size_unity)
            return super(FileHandler, self).log_message(format, *args, **kwargs)

        def do_GET(self):  # noqa
            try:
                mtime = mediapath.stat().st_mtime
                mediafile = open(str(mediapath), "rb")

                self.send_response(200)
                self.send_header("Content-type", content_type)
                self.send_header("Content-Length", length)
                self.send_header('Access-Control-Allow-Origin', '*')
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

    if content_type is None:
        content_type = "video/mp4"

    mediapath = Path(filename)
    length = mediapath.stat().st_size

    httpd = socketserver.TCPServer((address, port), FileHandler)
    httpd.serve_forever()
    httpd.server_close()
