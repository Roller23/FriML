import http.server
import socketserver
import json
from urllib.parse import urlparse
from urllib.parse import parse_qs
import os
import sys
import glob

sys.path.append('../')
import main_single

class HttpHandler(http.server.SimpleHTTPRequestHandler):
  processed_clients = 0
  max_clients = 1

  def end_headers (self):
    self.send_header('Access-Control-Allow-Origin', '*')
    http.server.SimpleHTTPRequestHandler.end_headers(self)
  
  def do_GET(self):
    if self.path.startswith('/check'):
      self.send_response(200)
      self.send_header('Content-type', 'text/html')
      self.end_headers()
      available = self.processed_clients < self.max_clients
      queue = self.max_clients - self.processed_clients + 1
      data = json.dumps({'clients': self.processed_clients, 'available': available, 'queue': queue})
      self.wfile.write(bytes(data, 'utf8'))
      return

    if self.path.startswith('/data'):
      if self.processed_clients >= self.max_clients:
        return
      data = ''
      self.processed_clients += 1
      self.send_response(200)
      self.send_header('Content-type', 'text/html')
      self.end_headers()
      q = parse_qs(urlparse(self.path).query)
      json_string = ''
      os.chdir('..')
      try:
        json_string = main_single.generate_for_server(q['genre'][0], q['key'][0], q['instrument'][0])
      except Exception as err:
        print(err)
      os.chdir('./webapp')
      data = json.dumps({'song': json_string})
      print('sending data')
      self.wfile.write(bytes(data, 'utf8'))
      self.processed_clients -= 1
      return
    return http.server.SimpleHTTPRequestHandler.do_GET(self)
    

def start_http():
  port = 8000
  socketserver.TCPServer.allow_reuse_address = True
  with socketserver.TCPServer(('', port), HttpHandler) as httpd:
    print('http server started on port ' + str(port))
    httpd.serve_forever()

def main():
  # delete old generated files
  for f in glob.glob('outputs/*'):
    os.remove(f)
  start_http()

if __name__ == '__main__':
  main()