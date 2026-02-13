import os
import socket
import qrcode
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "love_and_pdfs"

# Configuration
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'received_pdfs')
ALLOWED_EXTENSIONS = {'pdf'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_ip_address():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('Нет файла часть')
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        flash('Файл не выбран')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return render_template('success.html', filename=filename)
    else:
        flash('Разрешены только PDF файлы')
        return redirect(request.url)

if __name__ == '__main__':
    ip = get_ip_address()
    port = 5000
    url = f"http://{ip}:{port}"
    
    print("\n" + "="*50)
    print(f"♥ С любовью для вас! ♥")
    print(f"Откройте эту ссылку на телефоне:")
    print(f"👉 {url}")
    print("="*50 + "\n")
    
    # Generate QR code for easier access
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(url)
    qr.make(fit=True)
    
    # We can't easily show QR in all terminals, but we can save it to an image
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img.save("scan_me.png")
    print(f"QR-код сохранен в файл 'scan_me.png'. Отсканируйте его телефоном!")
    
    app.run(host='0.0.0.0', port=port, debug=False)
