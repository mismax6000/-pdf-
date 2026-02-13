import customtkinter as ctk
import os
import socket
import qrcode
from PIL import Image
import threading
import json
import requests
from server_module import start_server, UPLOAD_FOLDER

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

CONFIG_FILE = "config.json"

TRANSLATIONS = {
    "ru": {
        "title": "С любовью PDF Приемник",
        "ready": "Готов к получению PDF",
        "scan": "{}\nСканируй камерой телефона",
        "recent": "Полученные файлы",
        "open": "Открыть",
        "received": "Получен: {}",
        "received_reset": "Готов к получению PDF",
        "click_qr": "Нажми на QR для увеличения",
        "btn_copy": "Скопировать Код (IP)",
        "qr_error": "Ошибка генерации QR",
        "btn_send": "Отправить PDF на телефон",
        "btn_send_pc": "Отправить на другой ПК",
        "sending_file": "Раздаю: {}",
        "settings": "Настройки",
        "save_path": "Папка сохранения:",
        "device_name": "Имя устройства:",
        "theme": "Тема:",
        "save": "Сохранить",
        "choose": "Выбрать",
        "enter_ip": "Введите IP получателя:",
        "send": "Отправить",
        "sent_success": "Успешно отправлено!",
        "sent_error": "Ошибка отправки: {}",
        "scanning": "Поиск устройств..."
    },
    "en": {
        "title": "With Love PDF Receiver",
        "ready": "Ready to receive PDF",
        "scan": "{}\nScan with phone camera",
        "recent": "Received Files",
        "open": "Open",
        "received": "Received: {}",
        "received_reset": "Ready to receive PDF",
        "click_qr": "Click QR to enlarge",
        "btn_copy": "Copy Code (IP)",
        "qr_error": "QR Generation Error",
        "btn_send": "Send PDF to Phone",
        "btn_send_pc": "Send to another PC",
        "sending_file": "Sharing: {}",
        "settings": "Settings",
        "save_path": "Save Folder:",
        "device_name": "Device Name:",
        "theme": "Theme:",
        "save": "Save",
        "choose": "Choose",
        "enter_ip": "Enter Receiver IP:",
        "send": "Send",
        "sent_success": "Sent successfully!",
        "sent_error": "Send error: {}",
        "scanning": "Scanning for devices..."
    },
    "es": {
        "title": "Receptor PDF Con Amor",
        "ready": "Listo para recibir PDF",
        "scan": "{}\nEscanear con la cámara",
        "recent": "Archivos Recibidos",
        "open": "Abrir",
        "received": "Recibido: {}",
        "received_reset": "Listo para recibir PDF",
        "click_qr": "Clic para agrandar",
        "btn_copy": "Copiar Código (IP)",
        "qr_error": "Error de QR",
        "btn_send": "Enviar PDF al teléfono",
        "btn_send_pc": "Enviar a otra PC",
        "sending_file": "Compartiendo: {}",
        "settings": "Configuración",
        "save_path": "Carpeta de guardado:",
        "device_name": "Nombre del dispositivo:",
        "theme": "Tema:",
        "save": "Guardar",
        "choose": "Elegir",
        "enter_ip": "Ingrese IP del receptor:",
        "send": "Enviar",
        "sent_success": "¡Enviado con éxito!",
        "sent_error": "Error de envío: {}",
        "scanning": "Buscando dispositivos..."
    },
    "auto": { 
        "title": "PDF Receiver",
    }
}

class AirDropApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.load_config()
        self.current_lang = self.config.get("language", "ru")
        self.t = self.get_translation(self.current_lang)

        ctk.set_appearance_mode(self.config.get("theme", "Dark"))

        self.title(self.t["title"])
        self.geometry("800x800")
        self.resizable(False, False)

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = ctk.CTkFrame(self, corner_radius=20, fg_color="transparent")
        self.main_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.top_bar = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.top_bar.place(relx=0.95, rely=0.02, anchor="ne")

        self.settings_btn = ctk.CTkButton(
            self.top_bar,
            text="⚙️",
            width=40,
            command=self.open_settings,
            fg_color="transparent",
            border_width=1,
            border_color="gray"
        )
        self.settings_btn.pack(side="right", padx=5)

        self.lang_var = ctk.StringVar(value=self.current_lang)
        self.lang_menu = ctk.CTkOptionMenu(
            self.top_bar,
            values=["ru", "en", "es", "fr", "de", "pl", "ar", "he", "zh", "uk"], 
            command=self.change_language,
            variable=self.lang_var,
            width=100
        )
        self.lang_menu.pack(side="right", padx=5)

        self.header_label = ctk.CTkLabel(
            self.main_frame, 
            text=self.t["ready"], 
            font=("Segoe UI", 28, "bold")
        )
        self.header_label.grid(row=0, column=0, pady=(40, 10))

        self.radar_frame = ctk.CTkFrame(self.main_frame, width=300, height=300, corner_radius=20, fg_color=("gray85", "gray20"))
        self.radar_frame.grid(row=1, column=0, pady=20)
        self.radar_frame.grid_propagate(False)
        
        self.qr_label = ctk.CTkLabel(
            self.radar_frame, 
            text="Загрузка...", 
            fg_color="transparent",
            cursor="hand2"
        )
        self.qr_label.place(relx=0.5, rely=0.5, anchor="center")
        self.qr_label.bind("<Button-1>", lambda e: self.show_full_qr())

        self.ip_label = ctk.CTkLabel(
            self.main_frame, 
            text="", 
            font=("Segoe UI", 16),
            text_color="gray"
        )
        self.ip_label.grid(row=2, column=0, pady=(0, 20))
        
        self.btns_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.btns_frame.grid(row=3, column=0, pady=(0, 20))
        
        self.copy_btn = ctk.CTkButton(
            self.btns_frame,
            text=self.t.get("btn_copy", "Copy Code"),
            command=lambda: self.copy_to_clipboard(self.current_url),
            width=150,
            fg_color="transparent",
            border_width=1,
            border_color="gray"
        )
        self.copy_btn.pack(side="left", padx=10)

        self.send_btn = ctk.CTkButton(
            self.btns_frame,
            text=self.t.get("btn_send", "Send to Phone"),
            command=self.select_file_to_send,
            width=150,
            fg_color="#ff6b6b",
            hover_color="#ff4f4f"
        )
        self.send_btn.pack(side="left", padx=10)

        self.send_pc_btn = ctk.CTkButton(
            self.btns_frame,
            text=self.t.get("btn_send_pc", "Send to PC"),
            command=self.open_send_pc_dialog,
            width=150,
            fg_color="#3b82f6",
            hover_color="#2563eb"
        )
        self.send_pc_btn.pack(side="left", padx=10)

        self.files_frame = ctk.CTkScrollableFrame(self.main_frame, height=150, label_text=self.t["recent"])
        self.files_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=20)
        
        self.server = start_server(self.on_file_received)
        self.update_server_config()
        self.generate_qr()

    def load_config(self):
        default_config = {
            "language": "ru",
            "theme": "Dark",
            "save_path": os.path.join(os.getcwd(), 'received_pdfs'),
            "device_name": socket.gethostname()
        }
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    loaded = json.load(f)
                    default_config.update(loaded)
                    self.config = default_config
            except:
                self.config = default_config
        else:
            self.config = default_config
            
    def update_server_config(self):
        self.server.set_config(self.config["save_path"], self.config["device_name"])

    def open_settings(self):
        t = self.t
        top = ctk.CTkToplevel(self)
        top.title(t.get("settings", "Settings"))
        top.geometry("500x400")
        top.attributes("-topmost", True)
        
        ctk.CTkLabel(top, text=t.get("save_path", "Save Folder:")).pack(pady=(20,5))
        path_frame = ctk.CTkFrame(top, fg_color="transparent")
        path_frame.pack(fill="x", padx=20)
        self.path_entry = ctk.CTkEntry(path_frame)
        self.path_entry.insert(0, self.config["save_path"])
        self.path_entry.pack(side="left", fill="x", expand=True)
        
        def choose_folder():
            folder = ctk.filedialog.askdirectory()
            if folder:
                self.path_entry.delete(0, "end")
                self.path_entry.insert(0, folder)
        
        ctk.CTkButton(path_frame, text=t.get("choose", "..."), width=40, command=choose_folder).pack(side="right", padx=5)

        ctk.CTkLabel(top, text=t.get("device_name", "Device Name:")).pack(pady=(20,5))
        self.name_entry = ctk.CTkEntry(top)
        self.name_entry.insert(0, self.config["device_name"])
        self.name_entry.pack(fill="x", padx=20)

        ctk.CTkLabel(top, text=t.get("theme", "Theme:")).pack(pady=(20,5))
        self.theme_var = ctk.StringVar(value=self.config["theme"])
        theme_seg = ctk.CTkSegmentedButton(top, values=["Dark", "Light"], variable=self.theme_var)
        theme_seg.pack(pady=5)
        
        ctk.CTkButton(
            top, 
            text=t.get("save", "Save"), 
            command=lambda: self.save_settings(top),
            fg_color="#4ade80", hover_color="#22c55e", text_color="white"
        ).pack(pady=30)

    def save_settings(self, window):
        new_path = self.path_entry.get()
        new_name = self.name_entry.get()
        new_theme = self.theme_var.get()
        
        self.config["save_path"] = new_path
        self.config["device_name"] = new_name
        
        if new_theme in ["Dark", "Light"]:
             self.config["theme"] = new_theme
             ctk.set_appearance_mode(new_theme)
        
        self.save_config()
        self.update_server_config()
        window.destroy()

    def open_send_pc_dialog(self):
        top = ctk.CTkToplevel(self)
        top.title(self.t.get("btn_send_pc", "Send to PC"))
        top.geometry("400x400")
        top.attributes("-topmost", True)
        
        ctk.CTkLabel(top, text=self.t.get("choose", "Choose Device") + ":", font=("Segoe UI", 16, "bold")).pack(pady=(20,10))
        
        peers_frame = ctk.CTkScrollableFrame(top, height=150)
        peers_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        def refresh_peers():
            if not top.winfo_exists(): return
            for widget in peers_frame.winfo_children(): widget.destroy()
            
            if hasattr(self.server, 'discovery'):
                peers = self.server.discovery.get_peers()
                if not peers:
                    ctk.CTkLabel(peers_frame, text=self.t.get("scanning", "Scanning...")).pack(pady=20)
                
                for ip, data in peers.items():
                    if ip == self.server.server_ip: continue
                    btn_text = f"💻 {data['name']}\n({ip})"
                    btn = ctk.CTkButton(
                        peers_frame, 
                        text=btn_text, 
                        fg_color="#3b82f6",
                        command=lambda i=ip: on_select_peer(i)
                    )
                    btn.pack(fill="x", pady=5)
            
            top.after(2000, refresh_peers)
                
        refresh_peers()
        
        ctk.CTkLabel(top, text=self.t.get("enter_ip", "Enter IP") + ":", text_color="gray").pack(pady=(10,5))
        ip_entry = ctk.CTkEntry(top, placeholder_text="192.168.x.x")
        ip_entry.pack(fill="x", padx=20)

        def on_select_peer(ip):
            send_to_ip(ip)

        def on_manual_send():
            ip = ip_entry.get()
            if ip: send_to_ip(ip)

        def send_to_ip(ip):
            file_path = ctk.filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
            if file_path:
                threading.Thread(target=self._send_file_to_pc, args=(ip, file_path, top)).start()
                
        ctk.CTkButton(top, text=self.t.get("send", "Send Manual"), command=on_manual_send, fg_color="transparent", border_width=1).pack(pady=10)

    def _send_file_to_pc(self, ip, file_path, dialog):
        dialog.destroy()
        self.header_label.configure(text=self.t.get("sending_file", "Sharing..."), text_color="yellow")
        
        try:
            url = f"http://{ip}:5000/upload"
            with open(file_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(url, files=files, timeout=10)
            
            if response.status_code == 200:
                self.header_label.configure(text=self.t.get("sent_success", "Sent!"), text_color="#4ade80")
            else:
                self.header_label.configure(text=f"Error: {response.text}", text_color="red")
        except Exception as e:
            print(e)
            self.header_label.configure(text=self.t.get("sent_error", "Error").format("Fail"), text_color="red")
        
        self.after(3000, lambda: self.header_label.configure(text=self.t["ready"], text_color=("black", "white")))

    def get_translation(self, lang):
        base = TRANSLATIONS.get("en").copy()
        target = TRANSLATIONS.get(lang, {})
        base.update(target)
        return base

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f)

    def change_language(self, choice):
        self.current_lang = choice
        self.config["language"] = choice
        self.save_config()
        self.t = self.get_translation(choice)
        self.update_ui_text()

    def update_ui_text(self):
        self.title(self.t["title"])
        self.header_label.configure(text=self.t["ready"])
        self.files_frame.configure(label_text=self.t["recent"])
        self.copy_btn.configure(text=self.t.get("btn_copy", "Copy Code"))
        self.send_btn.configure(text=self.t.get("btn_send", "Send to Phone"))
        self.send_pc_btn.configure(text=self.t.get("btn_send_pc", "Send to PC"))
        self.generate_qr() 

    def get_wifi_ssid(self):
        try:
            import subprocess
            result = subprocess.check_output("netsh wlan show interfaces", shell=True).decode("cp866", errors="ignore")
            for line in result.split("\n"):
                if "SSID" in line and "BSSID" not in line: 
                    return line.split(":")[1].strip()
        except:
            return None
        return None

    def generate_qr(self):
        try:
            ip = self.server.server_ip
            port = self.server.server_port
            url = f"http://{ip}:{port}"
            self.current_url = url
            
            ssid = self.get_wifi_ssid()
            wifi_text = f"\nWi-Fi: {ssid}" if ssid else "\n(Wi-Fi)"

            hint = self.t.get("click_qr", "Click to enlarge")
            self.ip_label.configure(text=self.t["scan"].format(url) + f"{wifi_text}\n({hint})")

            qr = qrcode.QRCode(box_size=10, border=1)
            qr.add_data(url)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")
            
            try: img.save("scan_me.png") 
            except: pass
            
            self.qr_full_img_pil = img
            img_small = img.resize((240, 240), Image.Resampling.LANCZOS)
            self.qr_image = ctk.CTkImage(light_image=img_small, dark_image=img_small, size=(240, 240))
            self.qr_label.configure(image=self.qr_image, text="") 
        except Exception as e:
            print(f"QR Error: {e}")
            self.qr_label.configure(text=self.t.get("qr_error", "Error"), image=None)
            self.ip_label.configure(text=f"{url}")

    def copy_to_clipboard(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.copy_btn.configure(text="✔️", fg_color="#4ade80", text_color="white")
        self.after(1000, lambda: self.copy_btn.configure(text=self.t.get("btn_copy", "Copy Code"), fg_color="transparent", text_color=("gray10", "gray90")))

    def show_full_qr(self):
        top = ctk.CTkToplevel(self)
        top.title("QR Code")
        top.geometry("600x700")
        top.attributes("-topmost", True)
        top.grid_columnconfigure(0, weight=1)
        top.grid_rowconfigure(0, weight=1)

        if hasattr(self, 'qr_full_img_pil'):
            img_large = self.qr_full_img_pil.resize((500, 500), Image.Resampling.NEAREST)
            ctk_img_large = ctk.CTkImage(light_image=img_large, dark_image=img_large, size=(500, 500))
            lbl = ctk.CTkLabel(top, text="", image=ctk_img_large)
            lbl.grid(row=0, column=0, padx=20, pady=20)
        
        code_lbl = ctk.CTkEntry(top, justify="center", font=("Consolas", 24))
        code_lbl.insert(0, self.current_url)
        code_lbl.configure(state="readonly")
        code_lbl.grid(row=1, column=0, ipady=10, padx=20, pady=(0, 20), sticky="ew")

    def select_file_to_send(self):
        file_path = ctk.filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        if file_path:
            success = self.server.set_file_to_send(file_path)
            if success:
                filename = os.path.basename(file_path)
                self.header_label.configure(text=self.t.get("sending_file", "Sharing: {}").format(filename), text_color="#ff6b6b")
            else:
                self.header_label.configure(text="Error selecting file", text_color="red")
    
    def on_file_received(self, filename, filepath):
        self.after(0, lambda: self.add_file_to_list(filename, filepath))

    def add_file_to_list(self, filename, filepath):
        item_frame = ctk.CTkFrame(self.files_frame)
        item_frame.pack(fill="x", pady=5, padx=5)
        
        icon_label = ctk.CTkLabel(item_frame, text="📄", font=("Segoe UI", 20))
        icon_label.pack(side="left", padx=10)
        
        name_label = ctk.CTkLabel(item_frame, text=filename, font=("Segoe UI", 14, "bold"))
        name_label.pack(side="left", padx=10)
        
        open_btn = ctk.CTkButton(
            item_frame, 
            text=self.t["open"], 
            width=80, 
            command=lambda: os.startfile(filepath)
        )
        open_btn.pack(side="right", padx=10, pady=5)

        self.header_label.configure(text=self.t["received"].format(filename), text_color="#4ade80")
        self.after(3000, lambda: self.header_label.configure(text=self.t["ready"], text_color=("black", "white")))

if __name__ == "__main__":
    app = AirDropApp()
    app.mainloop()
