import cv2
import face_recognition
import os
import serial
import time  # Importa a biblioteca time

# --- 1. Configuração da Porta Serial ---
# Mude 'COM3' para a porta do seu Arduino (ex: 'COM4', 'COM5', '/dev/ttyACM0')
arduino_port = 'COM7'
baud_rate = 9600

try:
    arduino = serial.Serial(arduino_port, baud_rate, timeout=1)
    time.sleep(2)  # Pausa para a conexão serial ser estabelecida
    print(f"Conexão serial estabelecida na porta {arduino_port}")
except serial.SerialException as e:
    print(f"Erro ao abrir a porta serial {arduino_port}: {e}")
    print("Verifique se o Arduino está conectado e se a porta está correta.")
    exit()

# --- 2. Carregar e codificar as imagens de referência ---
known_face_encodings = []
known_face_names = []
images_folder = "Images"

print("Carregando e codificando as faces conhecidas...")

for filename in os.listdir(images_folder):
    if filename.endswith((".jpg", ".jpeg", ".png")):
        image_path = os.path.join(images_folder, filename)

        try:
            image = face_recognition.load_image_file(image_path)
            face_encoding = face_recognition.face_encodings(image)[0]
            known_face_encodings.append(face_encoding)
            known_face_names.append(os.path.splitext(filename)[0])
            print(f"Face de '{filename}' codificada com sucesso.")
        except IndexError:
            print(f"Aviso: Nenhuma face encontrada em '{filename}'. Arquivo ignorado.")

if not known_face_encodings:
    print("Nenhuma face válida encontrada na pasta 'Images'. Encerrando.")
    arduino.close()
    exit()

# --- 3. Inicializar a webcam ---
video_capture = cv2.VideoCapture(0)
print("\nWebcam ativada. Pressione 'q' para sair.")

while True:
    ret, frame = video_capture.read()
    if not ret:
        print("Erro ao capturar quadro da webcam. Encerrando.")
        break

    small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_small_frame)
    face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

    # Variável para rastrear se uma face conhecida foi encontrada no quadro
    known_face_detected_in_frame = False

    for face_encoding, face_location in zip(face_encodings, face_locations):
        matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
        name = "Desconhecido"
        color = (0, 0, 255)  # Vermelho

        if True in matches:
            first_match_index = matches.index(True)
            name = known_face_names[first_match_index]
            color = (0, 255, 0)  # Verde
            known_face_detected_in_frame = True  # Marca que uma face conhecida foi encontrada

        top, right, bottom, left = [coord * 4 for coord in face_location]
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        font = cv2.FONT_HERSHEY_DUPLEX
        cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.7, (255, 255, 255), 1)

    # --- 4. Enviar Comando Serial ---
    # Envia 'A' se uma face conhecida foi encontrada no quadro, senão envia 'F'
    if known_face_detected_in_frame:
        arduino.write(b'A')  # Envia 'A' em bytes
        print("Enviando 'A'...")
    else:
        arduino.write(b'F')  # Envia 'F' em bytes
        print("Enviando 'F'...")

    # --- 5. Exibir o resultado ---
    cv2.imshow('Reconhecimento Facial', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# --- 6. Limpar e liberar os recursos ---
video_capture.release()
cv2.destroyAllWindows()
arduino.close()  # Fecha a conexão serial
print("Processo finalizado.")