#include <Wire.h>
#include <Adafruit_MCP4725.h>

Adafruit_MCP4725 dac;

#define MCP4725_ADDR 0x60
const int   FEEDBACK_PIN = A1;       // R4ではA0がDACなのでA1を使用

const float targetPressure = 0.7;    // MPa

// DAC側
const float DAC_VREF = 4.6;

// フィードバック側
const float ADC_VREF     = 5.0;
const int   ADC_BITS     = 14;
const float ADC_MAX      = 16383.0;
const float FB_V_MIN     = 1.0;
const float FB_V_MAX     = 5.0;
const float FB_FULLSCALE = 0.9;
const int   FB_SAMPLES   = 16;

// 計測設定
const unsigned long INTERVAL_MS = 20;   // サンプリング間隔
const unsigned long DURATION_MS = 30000; // 計測時間(60秒)

void  setPressureMPa(float pressure);
float readFeedbackVoltage();
float readFeedbackPressure(float voltage);

void setup() {
  Serial.begin(115200);
  while (!Serial && millis() < 3000);   // R4のUSBシリアル待ち

  analogReadResolution(ADC_BITS);
  Wire.begin();

  if (!dac.begin(MCP4725_ADDR, &Wire)) {
    Serial.println("# MCP4725 NOT FOUND");
    while (1);
  }
  setPressureMPa(targetPressure);
  Serial.println("# READY");   // 圧力は出力開始済み。's' を受け取ると計測開始
}

void loop() {
  // PCから 's' が来るまで待機(圧力は出し続ける)
  if (Serial.available() && Serial.read() == 's') {
    Serial.println("time_ms,voltage_V,pressure_MPa");

    unsigned long t0 = millis();
    unsigned long next = t0;
    while (millis() - t0 < DURATION_MS) {
      if ((long)(millis() - next) >= 0) {
        next += INTERVAL_MS;
        float v = readFeedbackVoltage();
        float p = readFeedbackPressure(v);
        Serial.print(millis() - t0);
        Serial.print(",");
        Serial.print(v, 4);
        Serial.print(",");
        Serial.println(p, 4);
      }
    }
    Serial.println("END");
  }
}

void setPressureMPa(float pressure) {
  float correctedPressure = (pressure - 0.002) / 1.02;
  if (pressure < 0.02) correctedPressure = pressure * 0.8;
  if (correctedPressure < 0) correctedPressure = 0.0;

  float voltage = (correctedPressure - 0.005) / 0.176 + 0.005;
  int dacValue = constrain((int)(voltage / DAC_VREF * 4095), 0, 4095);
  dac.setVoltage(dacValue, false);
}

float readFeedbackVoltage() {
  long sum = 0;
  for (int i = 0; i < FB_SAMPLES; i++) sum += analogRead(FEEDBACK_PIN);
  return (float)sum / FB_SAMPLES / ADC_MAX * ADC_VREF;
}

float readFeedbackPressure(float voltage) {
  float p = (voltage - FB_V_MIN) / (FB_V_MAX - FB_V_MIN) * FB_FULLSCALE;
  return max(p, 0.0f);
}