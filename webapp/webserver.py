import http.server
import socketserver
import requests
import json
from urllib.parse import urlparse
from urllib.parse import parse_qs
import os
import sys
import glob
from pathlib import Path

sys.path.append('../')
import main_single

class HttpHandler(http.server.SimpleHTTPRequestHandler):
  def end_headers(self):
    self.send_header('Access-Control-Allow-Origin', '*')
    http.server.SimpleHTTPRequestHandler.end_headers(self)
  
  def do_GET(self):
    if self.path.startswith('/check'):
      self.send_response(200)
      self.send_header('Content-type', 'text/html')
      self.end_headers()
      data = json.dumps({'clients': 0, 'available': True, 'queue': 0})
      self.wfile.write(bytes(data, 'utf8'))
      return

    if self.path.startswith('/data'):
      data = ''
      self.send_response(200)
      self.send_header('Content-type', 'text/html')
      self.end_headers()
      q = parse_qs(urlparse(self.path).query)
      json_string = ''
      os.chdir('..')
      try:
        json_string = main_single.generate_for_server(q['genre'][0], q['key'][0], q['instrument'][0])
      except Exception as err:
        print('Exception: ' + str(err))
      os.chdir('./webapp')
      data = json.dumps({'song': json_string})
      print('sending data')
      self.wfile.write(bytes(data, 'utf8'))
      post_data = {'id': '0', 'song': ''}
      requests.post('https://friml-conductor.glitch.me/ready', post_data)
      return
    return http.server.SimpleHTTPRequestHandler.do_GET(self)
    

def start_http():
  port = int(os.environ.get("PORT", 5000))
  socketserver.TCPServer.allow_reuse_address = True
  with socketserver.TCPServer(('', port), HttpHandler) as httpd:
    print('http server started on port ' + str(port))
    httpd.serve_forever()

def main():
  # delete old generated files
  Path('outputs').mkdir(parents=True, exist_ok=True)
  for f in glob.glob('outputs/*'):
    os.remove(f)
  start_http()

if __name__ == '__main__':
  main()