# Sistema de Controle de Ponto Inteligente

Este projeto implementa um sistema de controle de ponto utilizando um banco de dados MySQL para o backend, scripts PHP como API e um dispositivo ESP32 (Arduino) como comunicador. O sistema registra o ponto de colaboradores com base em um "encoding" (simulando reconhecimento facial ou biométrico), além de gerenciar empresas, departamentos e dados de ponto.

---

## 🚀 Funcionalidades

- **Gerenciamento de Empresas**: Cadastro e controle de informações.
- **Gerenciamento de Departamentos**: Organização estrutural por áreas.
- **Gerenciamento de Colaboradores**: Cadastro com matrícula, escala, horários e encoding (dados biométricos simulados).
- **Registro de Ponto**: Entrada e saída com data e hora.
- **Backup Automático**: Trigger no banco copia cada ponto para `BackupPontoCompleto`.
- **API (PHP)**:
  - `index.php`: Registro de ponto via HTTP POST.
  - `select.php`: Leitura e esvaziamento da tabela de ponto (sincronização com o frontend).
- **Frontend (ESP32)**:
  - Comunicação via Wi-Fi com a API PHP.
  - Acionamento de saídas digitais (Y1 a Y8).
  - Leitura de entradas digitais (X1 a X8) e analógicas (AI1).
  - Sensor DHT22 (temperatura/umidade).
  - Controle de saída analógica (AO1).

---

## 🏛️ Estrutura do Banco de Dados (MySQL)

### Tabelas Principais

- `BDEmpresaInterno`
- `Departamento`
- `Colaborador`
- `Ponto`
- `BackupPontoCompleto` (via trigger)

---

## ⚙️ Backend (PHP)

### `index.php` – Registro de Ponto

- **Método**: `POST`
- **Corpo**:
```json
{
  "encoding": "base64_string",
  "dataRegistro": "YYYY-MM-DD",
  "horarioentrada": "HH:MM:SS"
}
```
- **Resposta**:
  - Sucesso:
    ```json
    { "status": "success", "message": "Reconhecimento confirmado...", "matricula": "...", "nome": "..." }
    ```
  - Falha:
    ```json
    { "status": "fail", "message": "Nenhum colaborador encontrado com o encoding informado." }
    ```

### `select.php` – Sincronização

- **Método**: `GET`
- **Resposta**:
```json
{
  "status": "success",
  "message": "Dados recuperados e deletados...",
  "count": N,
  "data": [...]
}
```

> ⚠️ **Importante**: Os registros da tabela `Ponto` são apagados após leitura. Os dados permanecem salvos em `BackupPontoCompleto`.

---

## 💻 Frontend (Arduino / ESP32)

### Conexão Wi-Fi

```cpp
const char* ssid = "SEU_SSID";
const char* password = "SUA_SENHA";
```

### URL da API

```cpp
const char* serverName = "https://SEU_DOMINIO.com/select.php";
```

### Pinos Utilizados

- **Saídas Digitais (Y1-Y8)**: 13, 12, 27, 26, 25, 33, 32, 4
- **Entradas Digitais (X1-X8)**: 15, 14, 5, 18, 19, 36, 39, 34
- **Entrada Analógica (AI1)**: 35
- **Saída Analógica (AO1)**: 23
- **Sensor DHT22**: 16 *(recomenda-se evitar conflito com pino 4)*

### Bibliotecas Necessárias

- `WiFi.h`
- `HTTPClient.h`
- `ArduinoJson.h` (v6+)
- `DHT.h`

### Lógica de Funcionamento

- O ESP32 conecta à rede.
- A cada 5 segundos, envia `GET` para `select.php`.
- Se houver dados válidos:
  - Ativa `Y1`.
- Caso contrário:
  - Desativa `Y1`.
- Permite expansão para demais saídas e sensores.

---

## 🛠️ Como Usar

### 1. Banco de Dados

- Execute os scripts SQL para criar tabelas e triggers.

### 2. Backend (PHP)

- Hospede os arquivos `index.php` e `select.php`.
- Configure credenciais do banco nos scripts.

### 3. Frontend (ESP32)

- Suba o sketch para o ESP32 via Arduino IDE.
- Atualize as credenciais Wi-Fi e a URL da API.
- Ajuste o pino do DHT se necessário.

### 4. Teste

- Use Postman, Insomnia ou `curl` para simular POSTs.
- Observe ativação do pino `Y1` no ESP32 quando registros forem processados.

---

## 🤝 Contribuições

- Julya Dias 
- Professor André
- Professor Saulo
