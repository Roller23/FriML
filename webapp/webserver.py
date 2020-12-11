import http.server
import socketserver
import json
from urllib.parse import urlparse
from urllib.parse import parse_qs

import sys
sys.path.append("../")
import main_single

class HttpHandler(http.server.SimpleHTTPRequestHandler):
  def do_GET(self):
    if self.path.startswith('/data'):
      self.send_response(200)
      self.send_header("Content-type", "text/html")
      self.end_headers()
      query = parse_qs(urlparse(self.path).query)
      json_string = main_single.generate_for_server('n64', query['key'], query['instrument'])
      data = json.dumps({'song': json_string})
      self.wfile.write(bytes(data, "utf8"))
      return
    return http.server.SimpleHTTPRequestHandler.do_GET(self)
    

def start_http():
  socketserver.TCPServer.allow_reuse_address = True
  with socketserver.TCPServer(("", 80), HttpHandler) as httpd:
    httpd.serve_forever()

def main():
  start_http()

if __name__ == "__main__":
  main()