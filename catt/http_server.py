import os
import time
import traceback
try:
    import SocketServer
except ImportError:
    import socketserver as SocketServer
try:
    from BaseHTTPServer import BaseHTTPRequestHandler
except ImportError:
    from http.server import BaseHTTPRequestHandler


def serve_file(filename, address="", port=45114):
    class FileHandler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa
            try:
                file = open(filename, "rb")
                stat = os.fstat(file.fileno())
                length = stat.st_size

                self.send_response(200)
                self.send_header("Content-type", "video/mp4")
                self.send_header("Content-Length", length)
                self.send_header("Accept-Ranges", "bytes")
                self.send_header(
                    "Last-Modified",
                    time.strftime(
                        "%a %d %b %Y %H:%M:%S GMT",
                        time.localtime(os.path.getmtime(filename))
                    )
                )
                self.end_headers()

                while True:
                    data = file.read(100 * 1024)

                    if not data:
                        break
                    self.wfile.write(data)
            except:  # noqa
                traceback.print_exc()

            file.close()

    httpd = SocketServer.TCPServer((address, port), FileHandler)
    httpd.serve_forever()
    httpd.server_close()
