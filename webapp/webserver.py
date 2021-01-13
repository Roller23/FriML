import http.server
import socketserver
import json
from urllib.parse import urlparse
from urllib.parse import parse_qs
import os
import sys
import glob
from pathlib import Path

sys.path.append('../')
import main_single

from flask import Flask, request
from flask_cors import CORS

max_clients = 1
current_clients = 0
average_time = 30

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
      return
    return http.server.SimpleHTTPRequestHandler.do_GET(self)
    

def start_http():
  # port = int(os.environ.get("PORT", 5000))
  # socketserver.TCPServer.allow_reuse_address = True
  # with socketserver.TCPServer(('', port), HttpHandler) as httpd:
  #   print('http server started on port ' + str(port))
  #   httpd.serve_forever()
  port = int(os.environ.get("PORT", 5000))
  app = Flask(__name__)
  CORS(app)
  @app.route('/check')
  def check():
    global current_clients
    global max_clients
    global average_time
    full = current_clients >= max_clients
    return json.dumps({'available': not full, 'time': average_time})

  @app.route('/data')
  def data():
    global current_clients
    current_clients += 1
    q = {
      'genre': request.args.get('genre'),
      'key': request.args.get('key'),
      'instrument': request.args.get('instrument')
    }
    json_string = ''
    os.chdir('..')
    try:
      json_string = main_single.generate_for_server(q['genre'], q['key'], q['instrument'])
    except Exception as err:
      print('Exception: ' + str(err))
    os.chdir('./webapp')
    print('sending data')
    current_clients -= 1
    return json.dumps({'song': json_string})
  app.run(host='0.0.0.0', port=port, threaded=True)

def main():
  # delete old generated files
  Path('outputs').mkdir(parents=True, exist_ok=True)
  for f in glob.glob('outputs/*'):
    os.remove(f)
  start_http()

if __name__ == '__main__':
  main()