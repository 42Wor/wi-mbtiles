import http.server
import socketserver

PORT = 8000

class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # This tells the browser "Yes, it is safe to load these local images!"
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), CORSRequestHandler) as httpd:
        print(f"Offline Map Server running at http://localhost:{PORT}")
        print("Keep this window open, and open index.html in your browser!")
        httpd.serve_forever()