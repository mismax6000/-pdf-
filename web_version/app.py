import os
import io
import socket
import qrcode
from flask import Flask, render_template, request, jsonify, send_from_directory, send_file, url_for
from werkzeug.utils import secure_filename
import time
import socket

app = Flask(__name__)
app.secret_key = "web_airdrop_secret"

# Configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'png', 'jpg'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Global state for "Send to Phone" functionality
file_to_send_path = None
file_to_send_name = None

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def dashboard():
    # Host Dashboard (PC View)
    ip = get_ip_address()
    port = 5000
    client_url = f"http://{ip}:{port}/client"
    
    # Generate QR
    qr = qrcode.QRCode(box_size=10, border=1)
    qr.add_data(client_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR temporarily to serve
    qr_path = os.path.join(app.root_path, 'static', 'qr_code.png')
    img.save(qr_path)

    # List files
    files = []
    for f in os.listdir(app.config['UPLOAD_FOLDER']):
        if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f)):
            files.append(f)
            
    return render_template('dashboard.html', 
                           client_url=client_url, 
                           files=files, 
                           pc_name=socket.gethostname(),
                           sending_file=file_to_send_name)

@app.route('/client')
def client_view():
    return render_template('mobile.html', pc_name=socket.gethostname())

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': 'No selected file'}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return jsonify({'status': 'success', 'filename': filename})
    return jsonify({'status': 'error', 'message': 'Invalid file type'}), 400

@app.route('/set_send_file', methods=['POST'])
def set_send_file():
    global file_to_send_path, file_to_send_name
    if 'file' not in request.files:
        return jsonify({'status': 'error'}), 400
        
    file = request.files['file']
    if file:
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], 'shared_' + filename)
        file.save(save_path)
        
        file_to_send_path = save_path
        file_to_send_name = filename
        return jsonify({'status': 'success', 'filename': filename})
        
    return jsonify({'status': 'error'}), 400

@app.route('/check_download')
def check_download():
    # Poll for available file
    if file_to_send_name:
        return jsonify({'status': 'available', 'filename': file_to_send_name})
    return jsonify({'status': 'none'})

@app.route('/download_shared')
def download_shared():
    if file_to_send_path and os.path.exists(file_to_send_path):
        return send_file(file_to_send_path, as_attachment=True, download_name=file_to_send_name)
    return "No file shared", 404

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/get_files')
def get_files_json():
    # AJAX helper for dashboard
    files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))]
    return jsonify(files)

if __name__ == '__main__':
    # Ensure static dir exists
    if not os.path.exists(os.path.join(app.root_path, 'static')):
        os.makedirs(os.path.join(app.root_path, 'static'))
        
    app.run(host='0.0.0.0', port=5000, debug=True)
