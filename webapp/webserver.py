import http.server
import socketserver

def start_http():
  Handler = http.server.SimpleHTTPRequestHandler
  socketserver.TCPServer.allow_reuse_address = True
  with socketserver.TCPServer(("", 80), Handler) as httpd:
    httpd.serve_forever()

def main():
  start_http()


if __name__ == "__main__":
  main()