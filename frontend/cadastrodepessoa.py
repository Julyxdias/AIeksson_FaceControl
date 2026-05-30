import tkinter as tk
from tkinter import messagebox
import face_recognition
import cv2
import pickle
import os
import mysql.connector

# Suas credenciais de conexão ao banco de dados
host = "******************"
port = ****
user = "***********************"
password = "***********************"
database = "****************************"

# ---
## Função Captura e Atualiza Encoding
def capturar_rosto():
    # As linhas abaixo estavam sem indentação, causando o IndentationError
    nome = entry_nome.get().strip()
    matricula = entry_matricula.get().strip()

    # CSS (Este comentário está solto, se for uma classe ou função, precisa de indentação)

    if not nome or not matricula:
        messagebox.showwarning("Campos obrigatórios", "Por favor, preencha nome e matrícula.")
        return

    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        messagebox.showerror("Erro", "Não foi possível acessar a câmera.")
        return

    messagebox.showinfo("Instrução", "Aperte a tecla ESPAÇO para capturar a imagem.")

    while True:
        ret, frame = camera.read()
        if not ret:
            break
        cv2.imshow("Pressione ESPAÇO para capturar - ESC para cancelar", frame)
        key = cv2.waitKey(1)
        if key % 256 == 27:  # ESC
            camera.release()
            cv2.destroyAllWindows()
            return
        elif key % 256 == 32:  # Espaço
            cv2.imwrite("foto.jpg", frame)
            break

    camera.release()
    cv2.destroyAllWindows()

    image = face_recognition.load_image_file("foto.jpg")
    encodings = face_recognition.face_encodings(image)

    if not encodings:
        messagebox.showerror("Erro", "Nenhum rosto foi detectado na imagem.")
        os.remove("foto.jpg")
        return

    encoding = encodings[0]
    encoding_blob = pickle.dumps(encoding)

    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()

        # Verifica se o colaborador existe
        sql_select = "SELECT matricula FROM Colaborador WHERE matricula = %s"
        cursor.execute(sql_select, (matricula,))
        result = cursor.fetchone()

        if result is None:
            messagebox.showwarning("Aviso", f"Nenhum Colaborador encontrado com matrícula {matricula}.")
        else:
            # Atualiza o campo encoding
            sql_update = "UPDATE Colaborador SET encoding = %s WHERE matricula = %s"
            cursor.execute(sql_update, (encoding_blob, matricula))
            conn.commit()
            messagebox.showinfo("Sucesso", f"Encoding atualizado para {nome} (Matrícula: {matricula})")

        cursor.close()
        conn.close()

    except mysql.connector.Error as err:
        messagebox.showerror("Erro no Banco", f"Erro: {err}")

    finally:
        if os.path.exists("foto.jpg"):
            os.remove("foto.jpg")


## Interface Estilizada - Recepcionista

janela = tk.Tk()
janela.title("🔐 Cadastro Facial")
janela.geometry("350x300")
janela.configure(bg="#f0f4f7")

tk.Label(janela, text="Cadastro de Rosto", font=("Helvetica", 18, "bold"), fg="#2c3e50", bg="#f0f4f7").pack(pady=15)

tk.Label(janela, text="Nome completo:", font=("Helvetica", 12), bg="#f0f4f7").pack()
entry_nome = tk.Entry(janela, font=("Helvetica", 12), width=30)
entry_nome.pack(pady=5)

tk.Label(janela, text="Matrícula:", font=("Helvetica", 12), bg="#f0f4f7").pack()
entry_matricula = tk.Entry(janela, font=("Helvetica", 12), width=30)
entry_matricula.pack(pady=5)

btn_capturar = tk.Button(
    janela,
    text="📸 Capturar Foto e Atualizar Encoding",
    command=capturar_rosto,
    font=("Helvetica", 12, "bold"),
    bg="#3498db",
    fg="white",
    padx=10,
    pady=5,
    relief="raised",
    bd=3
)
btn_capturar.pack(pady=20)

tk.Label(janela, text="Sistema de Reconhecimento Facial", font=("Helvetica", 9), bg="#f0f4f7", fg="#7f8c8d").pack(side="bottom", pady=5)

janela.mainloop()
