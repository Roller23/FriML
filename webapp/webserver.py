import http.server
import socketserver
import requests
import json
import os
import sys
import glob
import gc
from pathlib import Path
from urllib.parse import urlparse
from urllib.parse import parse_qs
from threading import Thread, Lock

sys.path.append('../')
import main_single

mutex = Lock()

def dump(obj):
  for attr in dir(obj):
    print("obj.%s = %r" % (attr, getattr(obj, attr)))

def generate_song(q):
  global mutex
  with mutex:
    os.chdir('..')
    json_string = json.dumps([])
    print('starting generation for ' + q['id'][0])
    try:
      json_string = main_single.generate_for_server(q['genre'][0], q['key'][0], q['instrument'][0])
    except Exception as err:
      print('Exception: ' + str(err))
    os.chdir('./webapp')
    print('finished generation for ' + q['id'][0])
    gc.collect()
    print('sending data')
    post_data = {'id': q['id'][0], 'song': json_string}
    requests.post('https://friml-conductor.glitch.me/ready', data=post_data)
    print('mutex released')

class HttpHandler(http.server.SimpleHTTPRequestHandler):
  def end_headers(self):
    self.send_header('Access-Control-Allow-Origin', 'https://friml-conductor.glitch.me')
    http.server.SimpleHTTPRequestHandler.end_headers(self)
  
  def do_GET(self):
    if self.path.startswith('/data'):
      dump(self)
      self.send_response(200)
      self.send_header('Content-type', 'text/html')
      self.end_headers()
      q = parse_qs(urlparse(self.path).query)
      thread = Thread(target=generate_song, args=(q,))
      thread.setDaemon(True)
      thread.start()
      self.wfile.write(bytes('ok', 'utf8'))
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