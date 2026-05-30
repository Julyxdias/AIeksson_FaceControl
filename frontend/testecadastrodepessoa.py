import tkinter as tk
from tkinter import messagebox
import face_recognition
import cv2
import sqlite3
import pickle
import os

# Banco de dados
conn = sqlite3.connect('banco.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS pessoas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        matricula TEXT NOT NULL,
        encoding BLOB NOT NULL
    )
''')
conn.commit()
conn.close()

# Função para capturar e salvar o rosto
def capturar_rosto():
    nome = entry_nome.get().strip()
    matricula = entry_matricula.get().strip()

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

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO pessoas (nome, matricula, encoding) VALUES (?, ?, ?)',
                   (nome, matricula, pickle.dumps(encoding)))
    conn.commit()
    conn.close()

    os.remove("foto.jpg")
    messagebox.showinfo("Sucesso", f"{nome} cadastrado com sucesso!")

# Interface estilizada
janela = tk.Tk()
janela.title("🔐 Cadastro Facial")
janela.geometry("350x300")
janela.configure(bg="#f0f4f7")

# Título
tk.Label(janela, text="Cadastro de Rosto", font=("Helvetica", 18, "bold"), fg="#2c3e50", bg="#f0f4f7").pack(pady=15)

# Campo nome
tk.Label(janela, text="Nome completo:", font=("Helvetica", 12), bg="#f0f4f7").pack()
entry_nome = tk.Entry(janela, font=("Helvetica", 12), width=30)
entry_nome.pack(pady=5)

# Campo matrícula
tk.Label(janela, text="Matrícula:", font=("Helvetica", 12), bg="#f0f4f7").pack()
entry_matricula = tk.Entry(janela, font=("Helvetica", 12), width=30)
entry_matricula.pack(pady=5)

# Botão
btn_capturar = tk.Button(
    janela,
    text="📸 Capturar Foto e Cadastrar",
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

# Rodapé
tk.Label(janela, text="Sistema de Reconhecimento Facial", font=("Helvetica", 9), bg="#f0f4f7", fg="#7f8c8d").pack(side="bottom", pady=5)

janela.mainloop()
