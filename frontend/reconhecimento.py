import cv2  # OpenCV para processamento de imagem e captura de vídeo
import face_recognition  # Para detecção e reconhecimento de faces
import mysql.connector  # Para interagir com o banco de dados MySQL
import pickle  # Para serializar/desserializar objetos Python (os encodings faciais)
import requests  # Para fazer requisições HTTP para a API backend
from datetime import datetime, timedelta  # Adicionado timedelta e datetime
import base64  # Para codificar os encodings faciais em base64 antes de enviar
import time   # Adicionado para usar time.time() para o cooldown

# !!! IMPORTANTE: Ajuste esta URL para apontar para o SEU ARQUIVO PHP específico !!!
# Exemplo: "https://<seu_replit_id>.replit.dev/registrar_ponto_api.php"
API_URL = "****************************************************"

# Suas credenciais de conexão ao banco de dados MySQL para carregar os rostos conhecidos
MYSQL_HOST = "*******************************"
MYSQL_PORT = *****
MYSQL_USER = "***************************"
MYSQL_PASSWORD = "*******************************"
MYSQL_DATABASE = "++++++++++++++++++++++++++++++++++++++"

# Preparar listas e caches
nomes_conhecidos = []
matriculas_conhecidas = []
encodings_conhecidos = [] # Lista para armazenar os vetores de características faciais
company_status_cache = {} # Cache: chave = idEmpresa, valor = status_contrato (ex: {101: 'Ativo', 102: 'Inativo'})

# --- LÓGICA DE COOLDOWN LOCAL NO PYTHON ---
COOLDOWN_SECONDS_PYTHON = 5 # Tempo mínimo em segundos entre envios de requisições para o mesmo colaborador
last_sent_time = {} # Dicionário: chave = matrícula, valor = último timestamp (time.time()) de envio
# --- FIM DA LÓGICA DE COOLDOWN LOCAL ---

## Conectar ao banco de dados MySQL e carregar dados de pessoas conhecidas e status de empresas
try:
    print(f"Conectando ao MySQL em {MYSQL_HOST}:{MYSQL_PORT}...")
    conn_mysql = mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        connection_timeout=10
    )
    cursor_mysql = conn_mysql.cursor()
    print("Conexão MySQL bem-sucedida.")

    # Carregar dados dos colaboradores
    print("Carregando dados dos colaboradores...")
    cursor_mysql.execute("SELECT nome, matricula, encoding FROM Colaborador WHERE encoding IS NOT NULL")
    dados_mysql = cursor_mysql.fetchall()

    if not dados_mysql:
        print("AVISO: Nenhum colaborador com encoding encontrado no banco de dados MySQL.")
    else:
        for nome_db, matricula_db, encoding_blob in dados_mysql:
            if encoding_blob:
                try:
                    nomes_conhecidos.append(nome_db)
                    matriculas_conhecidas.append(matricula_db)
                    encodings_conhecidos.append(pickle.loads(encoding_blob))
                except pickle.UnpicklingError as pe:
                    print(f"Erro ao desserializar encoding para {nome_db} ({matricula_db}): {pe}")
            else:
                print(f"AVISO: Encoding nulo para {nome_db} ({matricula_db}).")
    print(f"Dados de {len(encodings_conhecidos)} colaboradores carregados do MySQL com sucesso.")
    if not encodings_conhecidos:
        print("AVISO IMPORTANTE: Nenhum encoding facial conhecido foi carregado. O reconhecimento não funcionará.")

    # Carregar status de todas as empresas para o cache
    print("Carregando status das empresas...")
    cursor_mysql.execute("SELECT empresa, status_contrato FROM BDEmpresaInterno")
    empresas_db = cursor_mysql.fetchall()
    for empresa_id, status_contrato in empresas_db:
        company_status_cache[empresa_id] = status_contrato.lower() # Armazena em minúsculas para fácil comparação
    print(f"Status de {len(company_status_cache)} empresas carregados para o cache.")


    cursor_mysql.close()
    conn_mysql.close()


except mysql.connector.Error as err:
    print(f"ERRO CRÍTICO ao conectar ou carregar dados do MySQL: {err}")
    print("Verifique suas credenciais, a conexão com o banco de dados e as estruturas das tabelas.")
    exit()

# Iniciar a captura de vídeo da câmera padrão
camera = cv2.VideoCapture(0)
if not camera.isOpened():
    print("ERRO: Não foi possível abrir a câmera.")
    exit()
print("Câmera iniciada. Pressione 'q' para sair.")

while True:
    ret, frame = camera.read()
    if not ret:
        print("Erro ao capturar frame da câmera. Encerrando...")
        break

    frame_pequeno = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_pequeno = cv2.cvtColor(frame_pequeno, cv2.COLOR_BGR2RGB)

    face_locations = face_recognition.face_locations(rgb_pequeno)
    face_encodings_detectados = face_recognition.face_encodings(rgb_pequeno, face_locations)

    for (top, right, bottom, left), face_encoding_detectado in zip(face_locations, face_encodings_detectados):
        nome_identificado = "Desconhecido"
        matricula_identificada = ""
        empresa_do_colaborador = None # Variável para armazenar o ID da empresa do colaborador

        if encodings_conhecidos:
            matches = face_recognition.compare_faces(encodings_conhecidos, face_encoding_detectado)
            if True in matches:
                index_match = matches.index(True)
                nome_identificado = nomes_conhecidos[index_match]
                matricula_identificada = matriculas_conhecidas[index_match]

                # --- MELHORIA: VERIFICAR STATUS DA EMPRESA USANDO CACHE ---
                # Pega o ID da empresa do colaborador (assumindo que Colaborador.matricula é a PK e podemos buscá-lo)
                # Para evitar nova consulta ao DB aqui, Colaborador.empresa teria que ser carregado no início.
                # Como a query original do problema pedia apenas nome e matricula, faremos uma nova consulta para empresa
                # SE a otimização com cache de empresa não for suficiente para evitar a query para empresa.
                # No momento, a 'empresa' não está nas listas 'nomes_conhecidos', 'matriculas_conhecidas'.
                # Para otimizar, o SELECT inicial deveria pegar 'empresa' também:
                # "SELECT nome, matricula, encoding, empresa FROM Colaborador WHERE encoding IS NOT NULL"
                # E então passar 'empresa_db' para listas de colaboradores conhecidos.

                # Para simplificar agora, e como o id da empresa não foi carregado junto:
                # Fazemos uma nova busca rápida para pegar o id da empresa do colaborador
                # (Isto é menos eficiente que carregar no início, mas mantém o código anterior)
                try:
                    conn_temp = mysql.connector.connect(
                        host=MYSQL_HOST, port=MYSQL_PORT, user=MYSQL_USER,
                        password=MYSQL_PASSWORD, database=MYSQL_DATABASE, connection_timeout=5
                    )
                    cursor_temp = conn_temp.cursor()
                    cursor_temp.execute("SELECT empresa FROM Colaborador WHERE matricula = %s", (matricula_identificada,))
                    resultado_empresa = cursor_temp.fetchone()
                    if resultado_empresa:
                        empresa_do_colaborador = resultado_empresa[0]
                    cursor_temp.close()
                    conn_temp.close()
                except mysql.connector.Error as err:
                    print(f"ERRO ao buscar empresa para matrícula {matricula_identificada}: {err}")
                    empresa_do_colaborador = None # Garante que a verificação de status falhe
                # --- FIM MELHORIA STATUS DA EMPRESA ---


                # --- LÓGICA DE COOLDOWN LOCAL NO PYTHON ---
                current_time_for_cooldown = time.time() 
                if matricula_identificada in last_sent_time and \
                   (current_time_for_cooldown - last_sent_time[matricula_identificada]) < COOLDOWN_SECONDS_PYTHON:
                    print(f"DEBUG PYTHON: Cooldown ativo para {nome_identificado} ({matricula_identificada}). Não enviando requisição.")
                    continue 
                # --- FIM DA LÓGICA DE COOLDOWN LOCAL ---

                # --- VERIFICAÇÃO FINAL: EMPRESA ATIVA ---
                if empresa_do_colaborador is not None and \
                   company_status_cache.get(empresa_do_colaborador) == 'ativo':
                    
                    # Se chegou até aqui, o cooldown passou e a empresa está ativa.
                    last_sent_time[matricula_identificada] = current_time_for_cooldown # Atualiza o timestamp de envio
                    
                    encoding_para_envio = encodings_conhecidos[index_match]
                    pickled_encoding = pickle.dumps(encoding_para_envio)
                    encoding_serializado_b64 = base64.b64encode(pickled_encoding).decode('utf-8')

                    agora = datetime.now() # Captura a data e hora ATUAL da batida
                    dataRegistro = agora.strftime('%Y-%m-%d')
                    horarioentrada = agora.strftime('%H:%M:%S')

                    payload = {
                        "encoding": encoding_serializado_b64,
                        "dataRegistro": dataRegistro,
                        "horarioentrada": horarioentrada,
                        "matricula": matricula_identificada
                    }
                    
                    print(f"DEBUG PYTHON: Horarioentrada (antes do payload): '{horarioentrada}'")
                    print(f"DEBUG PYTHON: Payload a ser enviado: {payload}")

                    try:
                        response = requests.post(API_URL, json=payload, timeout=10)
                        
                        print(f"DEBUG PYTHON: Status Code da Resposta: {response.status_code}")
                        print(f"DEBUG PYTHON: Cabeçalhos da Resposta: {response.headers}")
                        print(f"DEBUG PYTHON: Texto Bruto da Resposta: '{response.text}'")

                        if 200 <= response.status_code < 300 and \
                           response.headers.get("Content-Type", "").lower().startswith("application/json"):
                            try:
                                json_response = response.json()
                                print(f"Registro para {nome_identificado} ({matricula_identificada}) enviado. Resposta do backend:", json_response)
                            except ValueError as json_err:
                                print(f"ERRO ao DECODIFICAR JSON da resposta para {nome_identificado}. Erro: {json_err}")
                        else:
                            print(f"Resposta do backend não foi 2xx bem-sucedido e/ou não é JSON. Status: {response.status_code}.")

                    except requests.exceptions.HTTPError as http_err:
                        print(f"ERRO HTTP ao enviar dados para {nome_identificado}: {http_err}")
                        if response is not None:
                             print(f"Texto da resposta (HTTP Error): '{response.text}'")
                    except requests.exceptions.Timeout:
                        print(f"TIMEOUT ao enviar dados para {nome_identificado} para a URL: {API_URL}")
                    except requests.exceptions.RequestException as req_err:
                        print(f"ERRO DE REQUISIÇÃO ao enviar dados para {nome_identificado}: {req_err}")
                    except Exception as e:
                        print(f"ERRO INESPERADO ao processar para {nome_identificado}: {e}")
                        if 'response' in locals() and hasattr(response, 'text'):
                            print(f"Texto da resposta (Erro Inesperado): '{response.text}'")
                else: # Empresa não está ativa
                    print(f"❌ A empresa da matrícula {matricula_identificada} está com serviço inativo. Registro bloqueado.")
                    nome_identificado = "Empresa Inativa"
                    matricula_identificada = ""
            else: # Colaborador não encontrado
                print("Rosto detectado, mas nenhum encoding conhecido carregado para comparação.")


        # Reescalar as coordenadas da face de volta para o tamanho do frame original (para exibição)
        top *= 4
        right *= 4
        bottom *= 4
        left *= 4

        texto_display = f"{nome_identificado} ({matricula_identificada})" if matricula_identificada else nome_identificado
        cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
        cv2.putText(frame, texto_display, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

    cv2.imshow("Reconhecimento Facial - Pressione 'q' para sair", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

camera.release()
cv2.destroyAllWindows()
print("Sistema de reconhecimento facial encerrado com sucesso.")
