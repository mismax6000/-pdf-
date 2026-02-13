import os
import socket
import threading
import qrcode
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
import time
import socket

# Default Configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'received_pdfs')
ALLOWED_EXTENSIONS = {'pdf'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

class ReceiverServer:
    def __init__(self, update_callback):
        self.app = Flask(__name__)
        self.app.secret_key = "love_and_pdfs"
        self.app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
        self.update_callback = update_callback
        self.server_port = 5000
        self.server_ip = self.get_ip_address()
        self.running = False
        
        # Dynamic Config
        self.upload_folder = UPLOAD_FOLDER
        self.custom_pc_name = socket.gethostname()

        # State for sending files (PC -> Phone)
        self.file_to_send = None
        self.file_to_send_name = None
        
        # Register routes
        self.app.add_url_rule('/', 'index', self.index)
        self.app.add_url_rule('/upload', 'upload_file', self.upload_file, methods=['POST'])
        self.app.add_url_rule('/status', 'status', self.status_check)
        self.app.add_url_rule('/download', 'download_file', self.download_file)
        self.app.add_url_rule('/check_download', 'check_download', self.check_download)

    def set_config(self, upload_folder, pc_name):
        self.upload_folder = upload_folder
        self.custom_pc_name = pc_name
        # Ensure uploads go to new folder
        if not os.path.exists(self.upload_folder):
            try:
                os.makedirs(self.upload_folder)
            except:
                pass 
        self.app.config['UPLOAD_FOLDER'] = self.upload_folder
        
        if hasattr(self, 'discovery'):
            self.discovery.name = pc_name

    def set_file_to_send(self, filepath):
        if os.path.exists(filepath):
            self.file_to_send = filepath
            self.file_to_send_name = os.path.basename(filepath)
            return True
        return False

    def clear_file_to_send(self):
        self.file_to_send = None
        self.file_to_send_name = None

    def get_ip_address(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    def allowed_file(self, filename):
        return '.' in filename and \
               filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def index(self):
        # Use dynamic pc_name
        return render_template('airdrop_style.html', pc_name=self.custom_pc_name)

    def upload_file(self):
        if 'file' not in request.files:
            return jsonify({'status': 'error', 'message': 'No file'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'status': 'error', 'message': 'No selected file'}), 400
            
        if file and self.allowed_file(file.filename):
            filename = secure_filename(file.filename)
            save_path = os.path.join(self.upload_folder, filename)
            file.save(save_path)
            
            # Notify GUI
            if self.update_callback:
                self.update_callback(filename, save_path)
                
            return jsonify({'status': 'success', 'filename': filename})
        else:
            return jsonify({'status': 'error', 'message': 'PDF only!'}), 400

    def status_check(self):
        return jsonify({'status': 'online', 'pc_name': self.custom_pc_name})

    def download_file(self):
        if self.file_to_send and os.path.exists(self.file_to_send):
            return send_file(self.file_to_send, as_attachment=True, download_name=self.file_to_send_name)
        return jsonify({'status': 'error', 'message': 'No file to download'}), 404

    def check_download(self):
        # Poll this from phone side
        if self.file_to_send:
            return jsonify({
                'status': 'available', 
                'filename': self.file_to_send_name
            })
        return jsonify({'status': 'none'})

    def run(self):
        self.running = True
        self.app.run(host='0.0.0.0', port=self.server_port, debug=False, use_reloader=False)

class PeerDiscovery:
    def __init__(self, port=5000, name="Unknown"):
        self.port = port
        self.name = name
        self.peers = {} # {ip: {'name': name, 'port': port, 'last_seen': time}}
        self.running = True
        self.broadcast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.broadcast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        
        self.listen_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.listen_socket.bind(('', 5001)) # Discovery port
        self.listen_socket.settimeout(1.0)

    def start(self):
        threading.Thread(target=self._broadcast_loop, daemon=True).start()
        threading.Thread(target=self._listen_loop, daemon=True).start()

    def _broadcast_loop(self):
        while self.running:
            try:
                # Broadcast format: AIRDROP_HELLO:Name:Port
                msg = f"AIRDROP_HELLO:{self.name}:{self.port}".encode('utf-8')
                self.broadcast_socket.sendto(msg, ('<broadcast>', 5001))
            except:
                pass
            time.sleep(3)

    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self.listen_socket.recvfrom(1024)
                ip = addr[0]
                msg = data.decode('utf-8')
                if msg.startswith("AIRDROP_HELLO:"):
                    _, name, port = msg.split(":", 2)
                    self.peers[ip] = {'name': name, 'port': int(port), 'last_seen': time.time()}
            except socket.timeout:
                self._cleanup_peers()
            except:
                pass

    def _cleanup_peers(self):
        now = time.time()
        to_remove = [ip for ip, data in self.peers.items() if now - data['last_seen'] > 10]
        for ip in to_remove:
            del self.peers[ip]

    def get_peers(self):
        self._cleanup_peers()
        return self.peers

def start_server(callback):
    server = ReceiverServer(callback)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    
    # Start Discovery
    discovery = PeerDiscovery(port=5000, name=server.custom_pc_name)
    discovery.start()
    server.discovery = discovery 
    
    return server
