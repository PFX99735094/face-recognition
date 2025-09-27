import os
import time
import tkinter.messagebox
# Importação que estava faltando
from tkinter import simpledialog

import customtkinter as ctk
import cv2
import face_recognition
import serial
from PIL import Image

# --- 1. Configurações e Variáveis Globais ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- Variáveis de estado e inicialização ---
        self.title("Sistema de Fechadura Eletrônica")
        self.geometry("800x600")
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.video_capture = None
        self.is_running = False
        self.images_folder = "Images"
        os.makedirs(self.images_folder, exist_ok=True)
        self.known_face_encodings = []
        self.known_face_names = []
        self.after_id = None
        self.photo_references = []
        self.arduino = None
        self.arduino_port = self.read_config()

        # --- Configuração dos frames (telas) ---
        self.main_frame = ctk.CTkFrame(self)
        self.capture_frame = ctk.CTkFrame(self)
        self.recognize_frame = ctk.CTkFrame(self)
        self.list_frame = ctk.CTkFrame(self)
        self.settings_frame = ctk.CTkFrame(self)

        self.connect_arduino()
        self.show_main_menu()

    # --- NOVO: Função para conectar com o Arduino ---
    def connect_arduino(self):
        if self.arduino:
            self.arduino.close()
            self.arduino = None

        baud_rate = 9600
        if self.arduino_port:
            try:
                self.arduino = serial.Serial(self.arduino_port, baud_rate, timeout=1)
                time.sleep(2)
                print(f"Conexão serial estabelecida na porta {self.arduino_port}")
            except serial.SerialException as e:
                print(f"Erro ao abrir a porta serial {self.arduino_port}: {e}")
                print("O programa continuará sem conexão serial.")
        else:
            print("A porta serial não foi especificada.")

    # --- Lê a porta COM do arquivo de configuração ---
    def read_config(self):
        try:
            with open("config.txt", "r") as f:
                port = f.read().strip()
                return port if port else None
        except FileNotFoundError:
            return None

    # --- Escreve a porta COM no arquivo de configuração ---
    def write_config(self, port):
        with open("config.txt", "w") as f:
            f.write(port)
        self.arduino_port = port
        self.connect_arduino()

    def _clear_frame_widgets(self, frame):
        for widget in frame.winfo_children():
            widget.destroy()

    # --- 2. Tela Principal (Menu) ---
    def show_main_menu(self):
        self._clear_frame_widgets(self.main_frame)
        self.capture_frame.pack_forget()
        self.recognize_frame.pack_forget()
        self.list_frame.pack_forget()
        self.settings_frame.pack_forget()
        self.main_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(self.main_frame, text="Sistema de Fechadura Eletrônica", font=("Arial", 24)).pack(pady=20)

        ctk.CTkButton(self.main_frame, text="Capturar Fotos", command=self.start_capture_mode, height=50).pack(pady=10)
        ctk.CTkButton(self.main_frame, text="Iniciar Reconhecimento", command=self.start_recognition_mode,
                      height=50).pack(pady=10)
        ctk.CTkButton(self.main_frame, text="Ver Fotos Salvas", command=self.show_list_photos, height=50).pack(pady=10)
        ctk.CTkButton(self.main_frame, text="Configurar Porta Serial", command=self.show_settings_menu, height=50).pack(
            pady=10)
        ctk.CTkButton(self.main_frame, text="Sair", command=self.on_close, height=50, fg_color="red",
                      hover_color="darkred").pack(pady=10)

    # --- 3. Tela de Captura de Fotos ---
    def start_capture_mode(self):
        self._clear_frame_widgets(self.capture_frame)
        self.main_frame.pack_forget()
        self.capture_frame.pack(fill="both", expand=True)

        self.video_capture = cv2.VideoCapture(0)
        self.is_running = True

        ctk.CTkLabel(self.capture_frame, text="Captura de Fotos", font=("Arial", 24)).pack(pady=10)

        self.password_entry = ctk.CTkEntry(self.capture_frame, placeholder_text="Digite a senha", width=250, show="*")
        self.password_entry.pack(pady=5)

        self.name_entry = ctk.CTkEntry(self.capture_frame, placeholder_text="Nome da pessoa", width=250)
        self.name_entry.pack(pady=5)

        self.photo_count_label = ctk.CTkLabel(self.capture_frame, text="Fotos tiradas: 0", font=("Arial", 14))
        self.photo_count_label.pack(pady=5)

        self.video_label = ctk.CTkLabel(self.capture_frame, text="")
        self.video_label.pack(pady=10)

        ctk.CTkButton(self.capture_frame, text="Tirar Foto", command=self.capture_photo).pack(side="left", padx=10,
                                                                                              pady=10)
        ctk.CTkButton(self.capture_frame, text="Voltar", command=self.stop_camera).pack(side="right", padx=10, pady=10)

        self.photo_count = 0
        self.update_camera_feed(self.video_label)

    def capture_photo(self):
        correct_password = "admin2025"
        entered_password = self.password_entry.get()

        if entered_password != correct_password:
            tkinter.messagebox.showerror("Erro de Autenticação", "Senha incorreta. Acesso negado.")
            return

        person_name = self.name_entry.get().strip()
        if not person_name:
            self.name_entry.configure(placeholder_text="Digite um nome!")
            return

        ret, frame = self.video_capture.read()
        if ret:
            self.photo_count += 1
            filename = f"{person_name}_{self.photo_count}.jpg"
            filepath = os.path.join(self.images_folder, filename)
            cv2.imwrite(filepath, frame)
            self.photo_count_label.configure(text=f"Fotos tiradas: {self.photo_count}")
            print(f"Foto salva: {filepath}")

    # --- 4. Tela de Reconhecimento Facial ---
    def start_recognition_mode(self):
        self._clear_frame_widgets(self.recognize_frame)
        self.main_frame.pack_forget()
        self.recognize_frame.pack(fill="both", expand=True)

        self.load_known_faces()

        self.video_capture = cv2.VideoCapture(0)
        self.is_running = True

        ctk.CTkLabel(self.recognize_frame, text="Reconhecimento Facial", font=("Arial", 24)).pack(pady=10)
        self.video_label = ctk.CTkLabel(self.recognize_frame, text="")
        self.video_label.pack(pady=10)
        ctk.CTkButton(self.recognize_frame, text="Parar", command=self.stop_camera).pack(pady=10)

        self.update_camera_feed(self.video_label, mode="recognize")

    def load_known_faces(self):
        self.known_face_encodings = []
        self.known_face_names = []
        print("Carregando e codificando as faces conhecidas...")
        for filename in os.listdir(self.images_folder):
            if filename.endswith((".jpg", ".jpeg", ".png")):
                image_path = os.path.join(self.images_folder, filename)
                try:
                    image = face_recognition.load_image_file(image_path)
                    face_encoding = face_recognition.face_encodings(image)[0]
                    self.known_face_encodings.append(face_encoding)
                    self.known_face_names.append(os.path.splitext(filename)[0])
                    print(f"Face de '{filename}' codificada.")
                except IndexError:
                    print(f"Aviso: Nenhuma face encontrada em '{filename}'.")
        print("Carga de faces concluída.")

    # --- 5. Tela de Listagem de Fotos Salvas ---
    def show_list_photos(self):
        self._clear_frame_widgets(self.list_frame)
        self.main_frame.pack_forget()
        self.list_frame.pack(fill="both", expand=True)
        self.photo_references.clear()

        ctk.CTkLabel(self.list_frame, text="Fotos Salvas", font=("Arial", 24)).pack(pady=10)

        scrollable_frame = ctk.CTkScrollableFrame(self.list_frame, width=700, height=450)
        scrollable_frame.pack(pady=10, fill="both", expand=True)

        image_files = [f for f in os.listdir(self.images_folder) if f.endswith((".jpg", ".jpeg", ".png"))]

        if not image_files:
            ctk.CTkLabel(scrollable_frame, text="Nenhuma foto encontrada na pasta 'Images'.", font=("Arial", 16)).pack(
                pady=20)
        else:
            for filename in image_files:
                image_path = os.path.join(self.images_folder, filename)
                try:
                    img = Image.open(image_path)
                    img.thumbnail((150, 150))

                    img_ctk = ctk.CTkImage(light_image=img, size=(img.width, img.height))
                    self.photo_references.append(img_ctk)

                    frame = ctk.CTkFrame(scrollable_frame)
                    frame.pack(pady=10, padx=10, fill="x")

                    delete_button = ctk.CTkButton(
                        frame,
                        image=self.photo_references[-1],
                        text=filename,
                        compound="left",
                        width=300,
                        height=100,
                        command=lambda p=image_path: self.delete_photo(p)
                    )
                    delete_button.pack(side="left", padx=10)

                except Exception as e:
                    print(f"Erro ao carregar a imagem {filename}: {e}")

        ctk.CTkButton(self.list_frame, text="Voltar", command=self.show_main_menu).pack(pady=10)

    # --- 6. Tela de Configuração de Porta Serial ---
    def show_settings_menu(self):
        self._clear_frame_widgets(self.settings_frame)
        self.main_frame.pack_forget()
        self.settings_frame.pack(fill="both", expand=True)

        ctk.CTkLabel(self.settings_frame, text="Configurar Porta Serial", font=("Arial", 24)).pack(pady=20)

        ctk.CTkLabel(self.settings_frame, text="Porta Serial Atual: " + (
            self.arduino_port if self.arduino_port else "Não configurada")).pack(pady=5)

        self.port_entry = ctk.CTkEntry(self.settings_frame, placeholder_text="Ex: COM3", width=250)
        self.port_entry.pack(pady=10)

        ctk.CTkButton(self.settings_frame, text="Salvar Porta", command=self.save_port, height=50).pack(pady=10)
        ctk.CTkButton(self.settings_frame, text="Voltar", command=self.show_main_menu, height=50).pack(pady=10)

    def save_port(self):
        new_port = self.port_entry.get().strip().upper()
        if new_port:
            self.write_config(new_port)
            tkinter.messagebox.showinfo("Configuração Salva", f"A porta serial foi salva como '{new_port}'.")
        else:
            tkinter.messagebox.showwarning("Porta Inválida", "Por favor, digite um nome de porta válido.")
        self.show_main_menu()

    # --- 7. Função para deletar a foto ---
    def delete_photo(self, image_path):
        correct_password = "admin2025"
        entered_password = simpledialog.askstring("Senha de Exclusão", "Por favor, digite a senha de administrador:", show='*')

        if entered_password != correct_password:
            tkinter.messagebox.showerror("Erro de Autenticação", "Senha incorreta. Ação negada.")
            return

        if tkinter.messagebox.askyesno("Confirmar Exclusão",
                                       f"Você tem certeza que deseja excluir '{os.path.basename(image_path)}'?"):
            try:
                os.remove(image_path)
                print(f"Foto '{image_path}' excluída com sucesso.")
                self.show_list_photos()
            except OSError as e:
                tkinter.messagebox.showerror("Erro de Exclusão", f"Erro ao excluir a foto: {e}")

    # --- 8. Lógica da Câmera e Comunicação Serial ---
    def update_camera_feed(self, label, mode="capture"):
        if not self.is_running or not self.video_capture.isOpened():
            return

        ret, frame = self.video_capture.read()
        if not ret:
            self.stop_camera()
            return

        if mode == "recognize":
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            known_face_detected_in_frame = False

            for face_encoding, face_location in zip(face_encodings, face_locations):
                matches = face_recognition.compare_faces(self.known_face_encodings, face_encoding, tolerance=0.6)
                name = "Desconhecido"
                color = (0, 0, 255)

                if True in matches:
                    first_match_index = matches.index(True)
                    name = self.known_face_names[first_match_index]
                    color = (0, 255, 0)
                    known_face_detected_in_frame = True

                top, right, bottom, left = [coord * 4 for coord in face_location]
                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.7, (255, 255, 255), 1)

            if self.arduino:
                if known_face_detected_in_frame:
                    self.arduino.write(b'A')
                else:
                    self.arduino.write(b'F')

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img_ctk = ctk.CTkImage(light_image=img, size=(640, 480))
        label.configure(image=img_ctk)
        label.image = img_ctk

        self.after_id = self.after(10, self.update_camera_feed, label, mode)

    def stop_camera(self):
        if self.after_id:
            self.after_cancel(self.after_id)
            self.after_id = None
        self.is_running = False
        if self.video_capture and self.video_capture.isOpened():
            self.video_capture.release()
        self.show_main_menu()

    def on_close(self):
        self.stop_camera()
        if self.arduino and self.arduino.is_open:
            self.arduino.close()
            print("Conexão serial fechada.")
        self.destroy()


# --- 9. Inicialização do Aplicativo ---
if __name__ == "__main__":
    app = App()
    app.mainloop()