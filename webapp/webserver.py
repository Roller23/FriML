import http.server
import socketserver
import json
from urllib.parse import urlparse
from urllib.parse import parse_qs
import os
import sys
sys.path.append("../")
import main_single
import glob

class HttpHandler(http.server.SimpleHTTPRequestHandler):
  def do_GET(self):
    if self.path.startswith('/data'):
      self.send_response(200)
      self.send_header("Content-type", "text/html")
      self.end_headers()
      query = parse_qs(urlparse(self.path).query)
      os.chdir('..')
      json_string = main_single.generate_for_server('n64', query['key'], query['instrument'])
      os.chdir('./webapp')
      data = json.dumps({'song': json_string})
      print('sending data')
      self.wfile.write(bytes(data, "utf8"))
      return
    return http.server.SimpleHTTPRequestHandler.do_GET(self)
    

def start_http():
  port = 8000
  socketserver.TCPServer.allow_reuse_address = True
  with socketserver.TCPServer(("", port), HttpHandler) as httpd:
    print('http server started on port ' + str(port))
    httpd.serve_forever()

def main():
  # delete old generated files
  files = glob.glob('../outputs/*')
  for f in files:
    os.remove(f)
  start_http()

if __name__ == "__main__":
  main()