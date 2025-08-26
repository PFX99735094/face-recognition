import cv2
import os

# --- 1. Configuração de salvamento ---
# Define a pasta onde as imagens serão salvas
images_folder = "Images"
# Garante que a pasta 'Images' exista. Se não existir, ela será criada.
os.makedirs(images_folder, exist_ok=True)

# Solicita o nome da pessoa para usar como prefixo do nome do arquivo
person_name = input("Digite o nome da pessoa para salvar as fotos: ")
if not person_name:
    print("Nome não pode ser vazio. Encerrando o programa.")
    exit()

print("\n--- Instruções ---")
print(f"1. Pressione a tecla 'S' para tirar uma foto.")
print(f"2. Pressione a tecla 'Q' para sair do programa.")

# --- 2. Inicializar a webcam ---
video_capture = cv2.VideoCapture(0)
if not video_capture.isOpened():
    print("Erro: Não foi possível abrir a webcam.")
    exit()

# Contador para o número de imagens salvas
image_count = 0

# --- 3. Loop de captura de imagens ---
while True:
    # Lê um quadro da câmera
    ret, frame = video_capture.read()
    if not ret:
        print("Erro ao capturar quadro. Encerrando.")
        break

    # Exibe o quadro com instruções na tela
    cv2.putText(frame, f"Pressione 'S' para salvar | 'Q' para sair", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow('Captura de Fotos', frame)

    # Captura a tecla pressionada
    key = cv2.waitKey(1) & 0xFF

    # Se a tecla 's' for pressionada, salva a imagem
    if key == ord('s'):
        # Incrementa o contador
        image_count += 1

        # Cria o nome do arquivo com base no nome e no contador
        filename = f"{person_name}_{image_count}.jpg"
        filepath = os.path.join(images_folder, filename)

        # Salva o quadro
        cv2.imwrite(filepath, frame)
        print(f"Foto salva em: {filepath}")

    # Se a tecla 'q' for pressionada, sai do loop
    elif key == ord('q'):
        print("Encerrando a captura de fotos.")
        break

# --- 4. Limpar e liberar os recursos ---
video_capture.release()
cv2.destroyAllWindows()