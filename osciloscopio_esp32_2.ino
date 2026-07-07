#include <GxEPD2_BW.h>
#include <RotaryEncoder.h>
#include "arduinoFFT.h"

#define PINO_SAIDA 27
#define PINO_ADC 34

const int N = 256;

double vReal[N];
double vImag[N];
uint16_t amostrasBrutas[N];
uint8_t pinos[] = {PINO_ADC};
uint32_t taxaAtual = 20000;

const int frequenciasTeste[] = {500, 1000, 1500};
const int qtdFrequencias = 3;
int indiceFreq = 0;
unsigned long ultimaTroca = 0;
const unsigned long tempoTroca = 5000;

GxEPD2_290_T94_V2 modeloTela(5, 0, 2, 15);
GxEPD2_BW<GxEPD2_290_T94_V2, GxEPD2_290_T94_V2::HEIGHT> tela(modeloTela);

RotaryEncoder encoder(32, 33);
RotaryEncoder encoder2(25, 26);

String escalas[] = {"0.5V/div", "1V/div", "2V/div", "5V/div"};
float voltsPorDiv[] = {0.5, 1, 2, 5};
int indiceEscala = 1;
int posicaoAnterior = 0;

String escalasTempoStr[] = {"1ms/div", "5ms/div", "10ms/div", "50ms/div"};
int pixelsPorDiv[] = {40, 30, 20, 10};
int indiceEscalaTempo = 2;
int posicaoAnterior2 = 0;

void tickDoEncoder() {
  encoder.tick();
}

void tickDoEncoder2() {
  encoder2.tick();
}

// Envia o frame atual pela serial no formato que o script Python espera:
// uma linha marcadora de sincronismo com o tempo de coleta (em segundos),
// seguida de N linhas, uma amostra bruta (0..4095) por linha.
void enviarFrameSerial(double tempoColeta) {
  Serial.print("_Update:");
  Serial.println(tempoColeta, 6);   // 6 casas decimais, tempoColeta em segundos
  for (int i = 0; i < N; i++) {
    Serial.println(amostrasBrutas[i]);
  }
}

void desenharOnda() {
  tela.fillRect(0, 0, 296, 102, GxEPD_WHITE);

  // eixo X (linha do zero) subiu 10px
  tela.drawLine(0, 54, 296, 54, GxEPD_BLACK);

  // grid horizontal - sempre 20px por div
  for (int d = 20; d <= 50; d += 20) {
    for (int x = 0; x < 296; x += 6) {
      tela.drawPixel(x, 54 - d, GxEPD_BLACK);
    }
    for (int x = 0; x < 296; x += 6) {
      tela.drawPixel(x, 54 + d, GxEPD_BLACK);
    }
  }

  // grid vertical - sempre 20px por div
  for (int x = 20; x < 296; x += 20) {
    for (int y = 0; y < 102; y += 6) {
      tela.drawPixel(x, y, GxEPD_BLACK);
    }
  }

  // onda
  for (int i = 0; i < 255; i++) {
    float v1 = ((amostrasBrutas[i] / 4095.0) * 3.3);
    float v2 = ((amostrasBrutas[i+1] / 4095.0) * 3.3);
    int y1 = 54 - (v1 / voltsPorDiv[indiceEscala]) * 20;
    int y2 = 54 - (v2 / voltsPorDiv[indiceEscala]) * 20;
    int x1 = i * pixelsPorDiv[indiceEscalaTempo];
    int x2 = (i+1) * pixelsPorDiv[indiceEscalaTempo];
    tela.drawLine(x1, y1, x2, y2, GxEPD_BLACK);
  }

  tela.display(true);
}

void atualizarEscala() {
  tela.fillRect(5, 112, 60, 15, GxEPD_WHITE);
  tela.setTextColor(GxEPD_BLACK);
  tela.setTextSize(1);
  tela.setCursor(5, 120);
  tela.print(escalas[indiceEscala]);
  desenharOnda();
}

void atualizarEscalaTempo() {
  tela.fillRect(70, 112, 80, 15, GxEPD_WHITE);
  tela.setTextColor(GxEPD_BLACK);
  tela.setTextSize(1);
  tela.setCursor(70, 120);
  tela.print(escalasTempoStr[indiceEscalaTempo]);
  desenharOnda();
}

void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(PINO_SAIDA, OUTPUT);
  tone(PINO_SAIDA, frequenciasTeste[indiceFreq]);
  analogReadResolution(12);
  analogSetPinAttenuation(PINO_ADC, ADC_11db);
  analogContinuous(pinos, 1, 1, taxaAtual, NULL);
  analogContinuousStart();

  attachInterrupt(digitalPinToInterrupt(32), tickDoEncoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(33), tickDoEncoder, CHANGE);
  attachInterrupt(digitalPinToInterrupt(25), tickDoEncoder2, CHANGE);
  attachInterrupt(digitalPinToInterrupt(26), tickDoEncoder2, CHANGE);

  tela.init();
  tela.setRotation(1);
  tela.fillScreen(GxEPD_WHITE);
  tela.drawLine(0, 54, 296, 54, GxEPD_BLACK);
  tela.setTextColor(GxEPD_BLACK);
  tela.setTextSize(1);
  tela.setCursor(5, 120);
  tela.print(escalas[indiceEscala]);
  tela.setCursor(70, 120);
  tela.print(escalasTempoStr[indiceEscalaTempo]);
  tela.display(false);
}

void loop() {
  if (millis() - ultimaTroca >= tempoTroca) {
    ultimaTroca = millis();
    indiceFreq++;
    if (indiceFreq >= qtdFrequencias) indiceFreq = 0;
    tone(PINO_SAIDA, frequenciasTeste[indiceFreq]);
  }

  adc_continuous_result_t *leitura;
  double media = 0;

  unsigned long inicioColeta = micros();

  for (int i = 0; i < N; i++) {
    analogContinuousRead(&leitura, 1000);
    amostrasBrutas[i] = leitura->avg_read_raw;
    vReal[i] = amostrasBrutas[i];
    vImag[i] = 0;
    media += vReal[i];
  }

  unsigned long fimColeta = micros();

  double tempoColeta = (fimColeta - inicioColeta) / 1000000.0;
  double taxaReal = N / tempoColeta;
  media = media / N;

  for (int i = 0; i < N; i++) vReal[i] -= media;

  ArduinoFFT<double> FFT(vReal, vImag, N, taxaReal);
  FFT.windowing(FFTWindow::Hamming, FFTDirection::Forward);
  FFT.compute(FFTDirection::Forward);
  FFT.complexToMagnitude();

  double frequenciaDetectada = FFT.majorPeak();

  uint32_t novaTaxa = frequenciaDetectada * 20.0;
  if (novaTaxa < 5000) novaTaxa = 5000;
  if (novaTaxa > 50000) novaTaxa = 50000;
  if (novaTaxa > taxaAtual + 3000 || novaTaxa + 3000 < taxaAtual) {
    taxaAtual = novaTaxa;
    analogContinuous(pinos, 1, 1, taxaAtual, NULL);
    analogContinuousStart();
  }

  enviarFrameSerial(tempoColeta);
  desenharOnda();

  int posicaoAtual = encoder.getPosition();
  if (posicaoAtual != posicaoAnterior) {
    if (posicaoAtual > posicaoAnterior && indiceEscala < 3) {
      indiceEscala++;
      atualizarEscala();
    } else if (posicaoAtual < posicaoAnterior && indiceEscala > 0) {
      indiceEscala--;
      atualizarEscala();
    }
    posicaoAnterior = posicaoAtual;
  }

  int posicaoAtual2 = encoder2.getPosition();
  if (posicaoAtual2 != posicaoAnterior2) {
    if (posicaoAtual2 > posicaoAnterior2 && indiceEscalaTempo < 3) {
      indiceEscalaTempo++;
      atualizarEscalaTempo();

    } else if (posicaoAtual2 < posicaoAnterior2 && indiceEscalaTempo > 0) {
      indiceEscalaTempo--;
      atualizarEscalaTempo();
    }
    posicaoAnterior2 = posicaoAtual2;
  }

  delay(1000);
}
