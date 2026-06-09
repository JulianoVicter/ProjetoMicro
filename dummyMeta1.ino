#define PINO_SAIDA 25
#define PINO_ADC 34

const int N = 200;

int leituras[N];
float leiturasEmV[N];

void setup() {
  Serial.begin(115200);
  pinMode(PINO_SAIDA, OUTPUT);
  tone(PINO_SAIDA, 1000);
  
  analogReadResolution(12);
  analogSetPinAttenuation(PINO_ADC, ADC_11db);

  uint8_t pinos[] = {PINO_ADC};

  analogContinuous(pinos, 1, 1, 20000, NULL);
}

void loop() {
  adc_continuous_data_t *leitura;

  analogContinuousStart();
  
  for (int i = 0; i < N; i++) {
    analogContinuousRead(&leitura, 1000);
    leituras[i] = leitura[0].avg_read_raw;
    leiturasEmV[i] = leitura[0].avg_read_mvolts;
  }

  analogContinuousStop();

  for (int i = 0; i < N; i++) {
    Serial.println(leituras[i]);
    Serial.println(leiturasEmV[i]/1000);
  }
  
  delay(10000);
}

