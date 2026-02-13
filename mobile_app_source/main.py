from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.filemanager import MDFileManager
from kivymd.toast import toast
import requests
import os
import threading

class PDFSenderApp(MDApp):
    def build(self):
        self.theme_cls.primary_palette = "Pink"
        self.theme_cls.theme_style = "Dark"
        
        self.screen = MDScreen()
        
        layout = MDBoxLayout(orientation="vertical", padding=20, spacing=20)
        
        layout.add_widget(MDLabel(
            text="С любовью к PDF ❤️",
            theme_text_color="Primary",
            font_style="H4",
            halign="center"
        ))

        self.ip_input = MDTextField(
            hint_text="IP адрес ПК (например 192.168.1.5)",
            helper_text="Введите IP, который показывает программа на ПК",
            helper_text_mode="on_focus"
        )
        layout.add_widget(self.ip_input)
        
        self.select_btn = MDFillRoundFlatButton(
            text="Выбрать PDF файл",
            pos_hint={"center_x": 0.5},
            on_release=self.file_manager_open
        )
        layout.add_widget(self.select_btn)
        
        self.upload_btn = MDFillRoundFlatButton(
            text="Отправить с любовью 🚀",
            pos_hint={"center_x": 0.5},
            disabled=True,
            on_release=self.upload_file
        )
        layout.add_widget(self.upload_btn)
        
        self.status = MDLabel(
            text="Готов к отправке...",
            halign="center",
            theme_text_color="Secondary"
        )
        layout.add_widget(self.status)

        self.screen.add_widget(layout)

        # File Manager
        self.file_manager = MDFileManager(
            exit_manager=self.exit_manager,
            select_path=self.select_path,
            ext=['.pdf']
        )
        
        self.selected_file = None

        return self.screen

    def file_manager_open(self, *args):
        # On Android, path starts with /storage/emulated/0
        path = os.path.expanduser("~")
        self.file_manager.show(path)

    def select_path(self, path):
        self.exit_manager()
        self.selected_file = path
        self.status.text = f"Выбран: {os.path.basename(path)}"
        self.upload_btn.disabled = False
        toast(path)

    def exit_manager(self, *args):
        self.file_manager.close()

    def upload_file(self, *args):
        threading.Thread(target=self._upload_thread).start()

    def _upload_thread(self):
        ip = self.ip_input.text
        if not ip:
            self.status.text = "Ошибка: Введите IP адрес!"
            return
            
        # Ensure http:// is present
        if not ip.startswith("http"):
            url = f"http://{ip}:5000/upload"
        else:
            url = f"{ip}:5000/upload"
            
        self.status.text = "Отправляю..."
        
        try:
            files = {'file': open(self.selected_file, 'rb')}
            response = requests.post(url, files=files, timeout=5)
            
            if response.status_code == 200:
                self.status.text = "Успешно отправлено! ❤️"
            else:
                self.status.text = f"Ошибка: {response.text}"
        except Exception as e:
            self.status.text = f"Ошибка соединения: {str(e)}"

if __name__ == "__main__":
    PDFSenderApp().run()
