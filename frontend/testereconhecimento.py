import cv2
import face_recognition
import sqlite3
import pickle

# Conectar ao banco e carregar dados
conn = sqlite3.connect('banco.db')
cursor = conn.cursor()
cursor.execute("SELECT nome, matricula, encoding FROM pessoas")
dados = cursor.fetchall()
conn.close()

# Separar nomes e encodings
nomes = []
matriculas = []
encodings_conhecidos = []

for nome, matricula, encoding_blob in dados:
    nomes.append(nome)
    matriculas.append(matricula)
    encodings_conhecidos.append(pickle.loads(encoding_blob))

# Iniciar câmera
camera = cv2.VideoCapture(0)
print("Pressione 'q' para sair.")

while True:
    ret, frame = camera.read()
    if not ret:
        break

    # Reduzir tamanho para acelerar
    frame_pequeno = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_pequeno = cv2.cvtColor(frame_pequeno, cv2.COLOR_BGR2RGB)

    # Detectar rostos e encodings na imagem
    face_locations = face_recognition.face_locations(rgb_pequeno)
    face_encodings = face_recognition.face_encodings(rgb_pequeno, face_locations)

    for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
        matches = face_recognition.compare_faces(encodings_conhecidos, face_encoding)
        nome = "Desconhecido"
        matricula = ""

        if True in matches:
            index = matches.index(True)
            nome = nomes[index]
            matricula = matriculas[index]

        # Voltar ao tamanho original
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        # Mostrar rosto e nome na tela
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        texto = f"{nome} - {matricula}" if nome != "Desconhecido" else nome
        cv2.putText(frame, texto, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

    # Mostrar imagem
    cv2.imshow("Reconhecimento Facial", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()
