#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "DHT.h"
// Remover a linha #include "driver/ledc.h" ao usar analogWrite
// #include "driver/ledc.h" // Esta linha NÃO é necessária com analogWrite()

// Definição dos pinos do controlador para as saídas digitais (Y)
#define pin_Y1 13
#define pin_Y2 12
#define pin_Y3 27
#define pin_Y4 26
#define pin_Y5 25
#define pin_Y6 33
#define pin_Y7 32
#define pin_Y8 4

// Definição dos pinos do controlador para as entradas digitais (X)
#define pin_X1 15
#define pin_X2 14
#define pin_X3 5
#define pin_X4 18
#define pin_X5 19
#define pin_X6 36
#define pin_X7 39
#define pin_X8 34

// Definição dos pinos para entrada analógica (AI) e saída analógica (AO)
#define pin_AI1 35
#define pin_AO1 23 // Pino para saída analógica (PWM)

#define ENTX_pin 2

// --- Configuração do Sensor DHT ---
#define DHTPIN 16
#define DHTTYPE DHT22
DHT dht(DHTPIN, DHTTYPE);

const char* ssid = "Ju";
const char* password = "JUJUJUJU";
const char* serverName = "***********************************************";

unsigned long lastTime = 0;
unsigned long timerDelay = 5000; // Intervalo para buscar dados do servidor (5 segundos)

void setup() {
  Serial.begin(115200);

  dht.begin();

  pinMode(pin_X1, INPUT); pinMode(pin_X2, INPUT); pinMode(pin_X3, INPUT); pinMode(pin_X4, INPUT);
  pinMode(pin_X5, INPUT); pinMode(pin_X6, INPUT); pinMode(pin_X7, INPUT); pinMode(pin_X8, INPUT);

  pinMode(pin_Y1, OUTPUT); pinMode(pin_Y2, OUTPUT); pinMode(pin_Y3, OUTPUT); pinMode(pin_Y4, OUTPUT);
  pinMode(pin_Y5, OUTPUT); pinMode(pin_Y6, OUTPUT); pinMode(pin_Y7, OUTPUT); pinMode(pin_Y8, OUTPUT);
  pinMode(ENTX_pin, OUTPUT);

  digitalWrite(pin_Y1, LOW); digitalWrite(pin_Y2, LOW); digitalWrite(pin_Y3, LOW); digitalWrite(pin_Y4, LOW);
  digitalWrite(pin_Y5, LOW); digitalWrite(pin_Y6, LOW); digitalWrite(pin_Y7, LOW); digitalWrite(pin_Y8, LOW);

  // ** MUDANÇA AQUI: Usando analogWrite() em vez de ledcSetup/ledcAttachPin/ledcWrite *
  analogWrite(pin_AO1, 0); // Define o valor inicial do PWM para 0 (desligado)

  WiFi.begin(ssid, password);
  Serial.print("Conectando-se ao Wi-Fi...");
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.print(".");
  }
  Serial.println("\nConectado ao Wi-Fi.");
  Serial.print("Endereço IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  if (millis() - lastTime > timerDelay) {
    lastTime = millis();
    bool dadosValidosEncontrados = false;

    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      Serial.print("Requisitando dados de: ");
      Serial.println(serverName);
      http.begin(serverName);
      http.setTimeout(10000);

      // --- INÍCIO DA MEDIÇÃO DE LATÊNCIA ---
      unsigned long startTime = millis();
      int httpResponseCode = http.GET();
      unsigned long endTime = millis();
      unsigned long latency = endTime - startTime;

      Serial.print("Latência da resposta da API: ");
      Serial.print(latency);
      Serial.println(" ms");
      // --- FIM DA MEDIÇÃO DE LATÊNCIA ---

      if (httpResponseCode > 0) {
        Serial.print("Resposta HTTP: ");
        Serial.println(httpResponseCode);
        String payload = http.getString();
        Serial.println("Payload recebido:");
        Serial.println(payload);

        DynamicJsonDocument doc(2048);
        DeserializationError error = deserializeJson(doc, payload);

        if (error) {
          Serial.print("Falha na desserialização do JSON: ");
          Serial.println(error.f_str());
        } else {
          const char* status = doc["status"];
          if (status && (strcmp(status, "success") == 0 || strcmp(status, "partial_error") == 0)) {
            JsonArray dataArray = doc["data"].as<JsonArray>();

            if (!dataArray.isNull() && dataArray.size() > 0) {
              JsonObject latestRecord = dataArray[dataArray.size() - 1].as<JsonObject>();
              if (!latestRecord.isNull() && latestRecord.containsKey("idPonto")) {
                dadosValidosEncontrados = true;
                String idPontoValue = latestRecord["idPonto"].as<String>();
                Serial.println("Dados válidos encontrados. Último 'idPonto': " + idPontoValue);

                if (latestRecord.containsKey("valorAO1")) {
                   int ao1_value_from_json = latestRecord["valorAO1"].as<int>();
                   // Converte o valor de 0-4095 (12 bits) para 0-255 (8 bits)
                   int ao1_value_for_analogWrite = map(ao1_value_from_json, 0, 4095, 0, 255);
                   analogWrite(pin_AO1, ao1_value_for_analogWrite);
                   Serial.print("AO1 setado para: ");
                   Serial.println(ao1_value_for_analogWrite);
                }
              } else {
                Serial.println("Array 'data' com registros, mas último registro é inválido ou não contém 'idPonto'.");
              }
            } else {
              Serial.println("Array 'data' está vazio ou nulo no JSON. Nenhum dado para processar.");
            }
          } else {
            Serial.print("Resposta do servidor não foi 'success' ou 'partial_error'. Status: ");
            Serial.println(status ? status : "N/A");
          }
        }
      } else {
        Serial.print("Erro na requisição HTTP: ");
        Serial.println(http.errorToString(httpResponseCode).c_str());
      }
      http.end();
    } else {
      Serial.println("Wi-Fi desconectado. Tentando reconectar...");
      WiFi.begin(ssid, password);
    }

    if (dadosValidosEncontrados) {
      digitalWrite(pin_Y1, HIGH);
      Serial.println("Y1 ACIONADO (dados com 'idPonto' presentes e válidos).");
    } else {
      digitalWrite(pin_Y1, LOW);
      Serial.println("Y1 DESLIGADO (sem dados válidos com 'idPonto', erro ou Wi-Fi desconectado).");
    }
  }

  delay(100);
}
