from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import logging
import mimetypes
import pathlib
import socket
import urllib.parse
from threading import Thread

from datetime import datetime

BUFFER_SIZE = 1024
HTTP_PORT = 4000
HTTP_HOST = '0.0.0.0'
SOCKET_HOST = "127.0.0.1"
SOCKET_PORT = 5000
BASE_DIR = pathlib.Path()
DATA_JSON = BASE_DIR.joinpath('storage/data.json')


class GoitFramework(BaseHTTPRequestHandler):
    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == "/":
            self.send_html_file("index.html")
        elif pr_url.path == '/message.html':
            self.send_html_file("message.html")
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html_file('error.html', 404)

    def send_html_file(self, filename, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())

    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        print(data)
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()

        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()


def save_data_from_form(data):
    data_parse = urllib.parse.unquote(data.decode())

    if not DATA_JSON.exists():
        with open('storage/data.json', 'w', encoding='utf-8') as fd:
            json.dump({}, fd, ensure_ascii=False, indent=4)
    try:
        with open('storage/data.json', 'r', encoding='utf-8') as file:
            data_general = json.load(file)

            data_dict = {key: value for key, value in [el.split('=') for el in data_parse.replace('+', ' ').split('&')]}
            result_dict = {str(datetime.now()): data_dict}
            data_general.update(result_dict)

        with open('storage/data.json', 'w', encoding='utf-8') as file:
            json.dump(data_general, file, ensure_ascii=False, indent=4)
    except ValueError as e:
        logging.error(e)
    except OSError as e:
        logging.error(e)


def run_socket_server(host, port):
    server_socket1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket1.bind((host, port))
    logging.info("Starting socket server")
    try:
        while True:
            msg, address = server_socket1.recvfrom(BUFFER_SIZE)
            save_data_from_form(msg)
    except KeyboardInterrupt:
        pass
    finally:
        server_socket1.close()


def run_http_server(host, port):
    server_address = (host, port)
    http_server = HTTPServer(server_address, GoitFramework)
    logging.info("Starting http server")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http_server.server_close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG, format='%(threadName)s:%(message)s')

    server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    server.start()

    server_socket = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    server_socket.start()
