import os

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'  # Отключаем предупреждения TensorFlow
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.request
import subprocess
import sys
import ctypes
from threading import Thread
import shutil
from PIL import Image, ImageTk
import cv2
from datetime import datetime
from deepface import DeepFace
import tensorflow as tf

tf.get_logger().setLevel('ERROR')  # Дополнительное подавление предупреждений


# ==================== УСТАНОВЩИК ====================
class InstallerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition Installer")
        self.root.geometry("500x350")
        self.root.resizable(False, False)
        self.stop_progress = False
        self.center_window()

        self.setup_styles()
        self.create_widgets()

        self.install_dir = os.path.join(os.environ["USERPROFILE"], "Desktop", "FaceRecognitionApp")
        self.resources = {
            "face_recognition_app.exe": "https://example.com/files/face_recognition_app.exe",
            "icon.ico": "https://drive.google.com/file/d/1E9CjlT-dKLqbIBuCXhwxNiZnoeIwWkLK/view?usp=drive_link",
            "requirements.txt": "https://example.com/files/requirements.txt"
        }

    def setup_styles(self):
        style = ttk.Style()
        style.configure("TFrame", background="#f0f0f0")
        style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10), padding=5)
        style.configure("Title.TLabel", font=("Arial", 12, "bold"))
        style.configure("Progress.Horizontal.TProgressbar", thickness=20)

    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Label(main_frame, text="Установка Face Recognition System",
                  style="Title.TLabel").pack(pady=10)

        ttk.Label(main_frame,
                  text="Эта программа установит необходимое ПО для распознавания лиц.\nНажмите 'Установить' для продолжения.",
                  wraplength=400).pack(pady=10)

        self.progress_frame = ttk.Frame(main_frame)
        self.progress_frame.pack(fill=tk.X, pady=15)

        self.progress = ttk.Progressbar(
            self.progress_frame,
            style="Progress.Horizontal.TProgressbar",
            orient="horizontal",
            length=400,
            mode="determinate"
        )
        self.progress.pack(fill=tk.X)

        self.status_label = ttk.Label(main_frame, text="Готов к установке")
        self.status_label.pack(pady=5)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(pady=10)

        self.btn_install = ttk.Button(
            btn_frame,
            text="Установить",
            command=self.start_installation,
            style="TButton"
        )
        self.btn_install.pack(side=tk.LEFT, padx=5)

        self.btn_cancel = ttk.Button(
            btn_frame,
            text="Отмена",
            command=self.on_cancel
        )
        self.btn_cancel.pack(side=tk.LEFT, padx=5)

    def on_cancel(self):
        self.stop_progress = True
        self.root.destroy()

    def update_status(self, text, color="black"):
        if not self.stop_progress and self.root.winfo_exists():
            self.status_label.config(text=text, foreground=color)
            self.root.update_idletasks()

    def show_error(self, message):
        if not self.stop_progress and self.root.winfo_exists():
            self.btn_install.config(state="normal")
            self.btn_cancel.config(state="normal")
            self.root.after(100, lambda: messagebox.showerror("Ошибка", message))
            self.update_status("Ошибка установки", "red")

    def start_installation(self):
        self.btn_install.config(state="disabled")
        self.btn_cancel.config(state="disabled")
        self.stop_progress = False
        Thread(target=self.run_installation, daemon=True).start()

    def run_installation(self):
        try:
            self.update_status("Проверка подключения...")
            if not self.check_internet():
                self.show_error("Требуется подключение к интернету")
                return

            self.update_status("Создание папки установки...")
            if not self.create_install_dir():
                return

            total_files = len(self.resources)
            for i, (filename, url) in enumerate(self.resources.items()):
                if self.stop_progress:
                    return

                self.update_status(f"Скачивание {filename} ({i + 1}/{total_files})...")
                if not self.download_file(filename, url, i, total_files):
                    return

            self.update_status("Установка зависимостей...")
            if not self.install_requirements():
                return

            self.update_status("Создание ярлыка...")
            if not self.create_shortcut():
                return

            self.progress["value"] = 100
            self.update_status("Установка завершена успешно!", "green")
            if not self.stop_progress:
                self.root.after(100, lambda: messagebox.showinfo("Готово", "Программа успешно установлена!"))
                self.root.after(2000, self.launch_main_app)

        except Exception as e:
            self.show_error(f"Критическая ошибка: {str(e)}")

    def check_internet(self):
        try:
            urllib.request.urlopen("https://google.com", timeout=5)
            return True
        except:
            return False

    def create_install_dir(self):
        try:
            os.makedirs(self.install_dir, exist_ok=True)
            return True
        except Exception as e:
            self.show_error(f"Ошибка создания папки: {str(e)}")
            return False

    def download_file(self, filename, url, current, total):
        try:
            save_path = os.path.join(self.install_dir, filename)

            def update_progress(count, block_size, total_size):
                if total_size > 0 and not self.stop_progress and self.root.winfo_exists():
                    percent = min(100, (count * block_size * 100) / total_size)
                    overall = (current * 100 + percent) / total
                    self.progress["value"] = overall
                    self.root.after(10, lambda: None)  # Плавное обновление

            urllib.request.urlretrieve(url, save_path, update_progress)
            return True
        except Exception as e:
            self.show_error(f"Ошибка скачивания {filename}: {str(e)}")
            return False

    def install_requirements(self):
        try:
            req_path = os.path.join(self.install_dir, "requirements.txt")
            if os.path.exists(req_path):
                subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path],
                                      creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except Exception as e:
            self.show_error(f"Ошибка установки зависимостей: {str(e)}")
            return False

    def create_shortcut(self):
        try:
            desktop = os.path.join(os.environ["USERPROFILE"], "Desktop")
            shortcut_path = os.path.join(desktop, "Face Recognition.lnk")
            target = os.path.join(self.install_dir, "face_recognition_app.exe")
            icon = os.path.join(self.install_dir, "icon.ico")

            if os.path.exists(target):
                ps_script = f"""
                $ws = New-Object -ComObject WScript.Shell
                $sc = $ws.CreateShortcut('{shortcut_path}')
                $sc.TargetPath = '{target}'
                $sc.WorkingDirectory = '{self.install_dir}'
                $sc.IconLocation = '{icon}'
                $sc.Save()
                """
                subprocess.run(["powershell", "-Command", ps_script],
                               check=True,
                               creationflags=subprocess.CREATE_NO_WINDOW)
            return True
        except Exception as e:
            self.show_error(f"Ошибка создания ярлыка: {str(e)}")
            return False

    def launch_main_app(self):
        if not self.stop_progress and self.root.winfo_exists():
            self.root.destroy()
            main_app_path = os.path.join(self.install_dir, "face_recognition_app.exe")
            if os.path.exists(main_app_path):
                subprocess.Popen([main_app_path], creationflags=subprocess.CREATE_NO_WINDOW)
            else:
                messagebox.showerror("Ошибка", "Основная программа не найдена!")


# ==================== ОСНОВНАЯ ПРОГРАММА ====================
class FaceRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Face Recognition System")
        self.root.state('zoomed')

        # Цветовая схема
        self.blue_bg = "#2C75FF"
        self.white_btn = "#FFFFFF"
        self.btn_hover = "#E6E6E6"
        self.frame_color = "#F0F0F0"
        self.text_color = "#333333"

        # Переменные состояния
        self.cap = None
        self.camera_active = False
        self.photo1 = None
        self.photo2 = None
        self.photos_folder = self.create_photos_folder()

        self.setup_styles()
        self.create_main_window()

    def setup_styles(self):
        style = ttk.Style()
        style.configure('.', background=self.blue_bg, foreground="white")
        style.configure('TFrame', background=self.blue_bg)
        style.configure('TLabelframe', background=self.frame_color, borderwidth=2)
        style.configure('TLabelframe.Label',
                        background=self.frame_color,
                        font=('Arial', 10, 'bold'),
                        foreground=self.text_color)
        style.configure('White.TButton',
                        background=self.white_btn,
                        foreground=self.text_color,
                        font=('Arial', 10),
                        borderwidth=1,
                        relief='raised')
        style.map('White.TButton',
                  foreground=[('pressed', self.text_color), ('active', self.text_color)],
                  background=[('pressed', self.btn_hover), ('active', self.btn_hover)])

    def create_photos_folder(self):
        photos_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Saved_Photos")
        if not os.path.exists(photos_folder):
            os.makedirs(photos_folder)
        return photos_folder

    def create_main_window(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Левая часть: Камера
        left_frame = ttk.Frame(main_frame, width=350)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)

        camera_frame = ttk.LabelFrame(left_frame, text="Камера", padding=10)
        camera_frame.pack(fill=tk.BOTH, expand=True)

        self.camera_canvas = tk.Canvas(camera_frame, bg='black', height=300)
        self.camera_canvas.pack(fill=tk.BOTH, expand=True)

        camera_btns_frame = ttk.Frame(left_frame)
        camera_btns_frame.pack(fill=tk.X, pady=(5, 0))

        camera_buttons = [
            ("1. Вкл. камеру", self.start_camera),
            ("2. Снимок", self.capture_photo),
            ("3. Сохранить фото 1", lambda: self.save_photo(1)),
            ("4. Сохранить фото 2", lambda: self.save_photo(2)),
            ("5. Выкл. камеру", self.stop_camera)
        ]

        for text, cmd in camera_buttons:
            btn = ttk.Button(camera_btns_frame, text=text, command=cmd, style='White.TButton')
            btn.pack(fill=tk.X, pady=2)

        # Центральная часть: Фото 1
        center_frame = ttk.Frame(main_frame)
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.photo1_frame = ttk.LabelFrame(center_frame, text="Фото 1", padding=10)
        self.photo1_frame.pack(fill=tk.BOTH, expand=True)

        self.photo1_canvas = tk.Canvas(self.photo1_frame, bg='white')
        self.photo1_canvas.pack(fill=tk.BOTH, expand=True)

        # Кнопки между окнами
        buttons_frame = ttk.Frame(main_frame, width=150)
        buttons_frame.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        action_buttons = [
            ("Загрузить фото 1", lambda: self.load_photo(1)),
            ("Загрузить фото 2", lambda: self.load_photo(2)),
            ("Сравнить", self.compare_faces),
            ("Открыть папку", self.open_photos_folder),
            ("Выход", self.root.destroy)
        ]

        for text, cmd in action_buttons:
            btn = ttk.Button(buttons_frame, text=text, command=cmd, style='White.TButton')
            btn.pack(pady=5, fill=tk.X)

        # Правая часть: Фото 2
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.photo2_frame = ttk.LabelFrame(right_frame, text="Фото 2", padding=10)
        self.photo2_frame.pack(fill=tk.BOTH, expand=True)

        self.photo2_canvas = tk.Canvas(self.photo2_frame, bg='white')
        self.photo2_canvas.pack(fill=tk.BOTH, expand=True)

    def start_camera(self):
        if not self.camera_active:
            self.cap = cv2.VideoCapture(0)
            self.camera_active = True
            self.update_camera()

    def update_camera(self):
        if self.camera_active:
            ret, frame = self.cap.read()
            if ret:
                img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(img).resize((400, 300))
                self.camera_img = ImageTk.PhotoImage(img)
                self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=self.camera_img)
            self.root.after(10, self.update_camera)

    def stop_camera(self):
        self.camera_active = False
        if self.cap:
            self.cap.release()

    def capture_photo(self):
        if self.camera_active:
            ret, frame = self.cap.read()
            if ret:
                self.current_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                messagebox.showinfo("Успех", "Снимок сделан!")

    def save_photo(self, photo_num):
        if hasattr(self, 'current_frame'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(self.photos_folder, f"photo_{photo_num}_{timestamp}.jpg")
            cv2.imwrite(filename, cv2.cvtColor(self.current_frame, cv2.COLOR_RGB2BGR))

            if photo_num == 1:
                self.photo1 = self.current_frame
                self.show_image(self.photo1, self.photo1_canvas)
            else:
                self.photo2 = self.current_frame
                self.show_image(self.photo2, self.photo2_canvas)
            messagebox.showinfo("Успех", f"Фото сохранено: {filename}")
        else:
            messagebox.showerror("Ошибка", "Сначала сделайте снимок!")

    def load_photo(self, photo_num):
        filetypes = [("Изображения", "*.jpg *.jpeg *.png")]
        filepath = filedialog.askopenfilename(
            title=f"Выберите фото {photo_num}",
            initialdir=self.photos_folder,
            filetypes=filetypes
        )

        if filepath:
            try:
                img = cv2.imread(filepath)
                if img is None:
                    raise ValueError("Не удалось загрузить изображение")

                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

                if photo_num == 1:
                    self.photo1 = img
                    self.show_image(img, self.photo1_canvas)
                else:
                    self.photo2 = img
                    self.show_image(img, self.photo2_canvas)

                messagebox.showinfo("Успех", f"Фото {photo_num} успешно загружено!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка загрузки фото: {str(e)}")

    def show_image(self, image, canvas):
        img = Image.fromarray(image).resize((400, 400))
        tk_img = ImageTk.PhotoImage(img)
        canvas.create_image(0, 0, anchor=tk.NW, image=tk_img)
        canvas.image = tk_img

    def compare_faces(self):
        if self.photo1 is None or self.photo2 is None:
            messagebox.showerror("Ошибка", "Загрузите оба фото!")
            return

        try:
            result = DeepFace.verify(
                cv2.cvtColor(self.photo1, cv2.COLOR_BGR2RGB),
                cv2.cvtColor(self.photo2, cv2.COLOR_BGR2RGB),
                enforce_detection=False
            )
            result_window = tk.Toplevel(self.root)
            result_window.title("Результат сравнения")
            if result['verified']:
                ttk.Label(result_window, text="Совпадение найдено!",
                          font=("Arial", 16), foreground="green").pack(pady=10)
            else:
                ttk.Label(result_window, text="Совпадений нет!",
                          font=("Arial", 16), foreground="red").pack(pady=10)
            ttk.Button(result_window, text="OK", command=result_window.destroy).pack(pady=10)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def open_photos_folder(self):
        os.startfile(self.photos_folder)


# ==================== SPLASH SCREEN ====================
class SplashScreen:
    def __init__(self):
        self.splash_root = tk.Tk()
        self.splash_root.overrideredirect(True)
        self.splash_root.geometry("400x300")
        self.center_window()

        bg_color = "#2C75FF"
        self.splash_root.configure(bg=bg_color)

        tk.Label(
            self.splash_root,
            text="Face Recognition System",
            font=("Arial", 16, "bold"),
            bg=bg_color,
            fg="white"
        ).pack(pady=50)

        self.progress = ttk.Progressbar(
            self.splash_root,
            mode="indeterminate",
            length=200
        )
        self.progress.pack(pady=20)
        self.progress.start(10)

        self.splash_root.after(3000, self.destroy_splash)
        self.splash_root.mainloop()

    def center_window(self):
        self.splash_root.update_idletasks()
        width = self.splash_root.winfo_width()
        height = self.splash_root.winfo_height()
        x = (self.splash_root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.splash_root.winfo_screenheight() // 2) - (height // 2)
        self.splash_root.geometry(f"{width}x{height}+{x}+{y}")

    def destroy_splash(self):
        self.splash_root.destroy()
        if not self.check_installation():
            self.run_installer()
        else:
            self.run_main_app()

    def check_installation(self):
        install_dir = os.path.join(os.environ["USERPROFILE"], "Desktop", "FaceRecognitionApp")
        return os.path.exists(os.path.join(install_dir, "face_recognition_app.exe"))

    def run_installer(self):
        root = tk.Tk()
        app = InstallerApp(root)
        root.mainloop()

    def run_main_app(self):
        root = tk.Tk()
        app = FaceRecognitionApp(root)
        root.mainloop()


# ==================== ТОЧКА ВХОДА ====================
if __name__ == "__main__":
    splash = SplashScreen()
