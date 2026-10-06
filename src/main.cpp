#include <Wire.h>
#include <Adafruit_MCP4725.h>

// ===== インスタンス定義 =====
Adafruit_MCP4725 dac;

// ===== ピン・定数 =====
#define MCP4725_ADDR 0x60

// ===== 出力する目標圧力 =====
const float targetPressure = 0.4;  // MPa

// ===== 関数プロトタイプ =====
void setPressureMPa(float pressure);

void setup() {
  Serial.begin(9600);
  Wire.begin();

  if (!dac.begin(MCP4725_ADDR, &Wire)) {
    Serial.println("MCP4725が検出されません。");
    while (1);
  }
  Serial.println("MCP4725 OK");

  setPressureMPa(targetPressure);
  Serial.print("目標圧力 ");
  Serial.print(targetPressure, 3);
  Serial.println(" MPaを出力中...");
}

void loop() {
  // 常に一定圧力を出力し続けるだけなので、特に処理は不要
}

// ===== 補助関数 =====
void setPressureMPa(float pressure) {
  float correctedPressure = (pressure - 0.002) / 1.02;
  if (pressure < 0.02) correctedPressure = pressure * 0.8;
  if (correctedPressure < 0) correctedPressure = 0.0;

  float voltage = (correctedPressure - 0.005) / 0.176 + 0.005;
  int dacValue = constrain(voltage / 4.6 * 4095, 0, 4095);
  dac.setVoltage(dacValue, false);
}