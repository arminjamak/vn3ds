"""A local web server for testing the install scripts: serves a folder and
labels every file application/octet-stream (as GitHub Pages may do for .ps1).
    python3 tests/serve_octet.py DIR PORT"""
import functools
import http.server
import sys


class Handler(http.server.SimpleHTTPRequestHandler):
    def guess_type(self, path):
        return "application/octet-stream"


folder, port = sys.argv[1], int(sys.argv[2])
http.server.ThreadingHTTPServer(("127.0.0.1", port),
                                functools.partial(Handler, directory=folder)).serve_forever()
