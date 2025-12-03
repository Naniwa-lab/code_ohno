#include <Wire.h>
#include <SparkFun_Qwiic_Scale_NAU7802_Arduino_Library.h>
#include <Adafruit_MCP4725.h>

// ===== インスタンス定義 =====
NAU7802 myScale;
Adafruit_MCP4725 dac;

// ===== ピン・定数 =====
#define MCP4725_ADDR 0x60
const int laserAnalogPina = A0;
const int regulatorFeedbackPin = A1;

// ===== 電圧補正 =====
const float adcRefVoltage = 5.0;
const float adcCalibration = 1.0 / 1.045;

// ===== 移動平均 =====
const int averageCount = 5;
float voltageBuffer[averageCount];
int bufferIndex = 0;
bool bufferFilled = false;

// ===== 圧力制御用変数 =====
float targetPressure = 0.0;
bool increasing = true;
const float pressureStep = 0.1;           // 1ステップ = 0.1MPa
const float maxPressure = 0.5;
const float minPressure = 0.0;
const unsigned long pressureStepInterval = 5000; // 5秒ごとにステップ更新
unsigned long lastPressureStepTime = 0;

// ===== ロードセル一次関数変換用定数 =====
const float BIT_KNOWN = 45527.69435f;
const float MASS_KNOWN = 1.043f;
const float GRAVITY = 9.80665f;
float slope = 1.0f;

// ===== 実験管理 =====
bool experimentStarted = false;
long loadcellOffset = 0;
unsigned long experimentStartTime = 0;

// ===== 関数プロトタイプ =====
void loopMeasurement();
float readAnalogVoltage(int pin, float refVoltage = 5.0);
void setPressureMPa(float pressure);

void setup() {
  Serial.begin(9600);
  analogReadResolution(12);
  delay(1000);
  Wire.begin();

  if (!myScale.begin()) {
    Serial.println("NAU7802が検出されません。");
    while (1);
  }
  Serial.println("NAU7802 OK");

  if (!dac.begin(MCP4725_ADDR, &Wire)) {
    Serial.println("MCP4725が検出されません。");
    while (1);
  }
  Serial.println("MCP4725 OK");

  Serial.println("センサを安定化中...(5秒)");
  setPressureMPa(0.0);
  delay(5000);

  // ---- ロードセルゼロ点キャリブレーション ----
  Serial.println("ロードセルゼロ点キャリブレーション中 (10秒)...");

  unsigned long calibStart = millis();
  long sum = 0;
  int count = 0;
  while (millis() - calibStart < 10000) {
    if (myScale.available()) {
      sum += myScale.getReading();
      count++;
    }
  }
  if (count > 0) loadcellOffset = sum / count;

  Serial.print("ロードセルオフセット = ");
  Serial.println(loadcellOffset);

  slope = (MASS_KNOWN * GRAVITY) / BIT_KNOWN;
  Serial.print("換算係数 slope = ");
  Serial.print(slope, 8);
  Serial.println(" N/bit");

  Serial.println("実験開始まで少々お待ちください...(5秒)");
  delay(10000);

  Serial.println("Sキーを押すと実験を開始します。");
}

void loop() {
  if (!experimentStarted) {
    if (Serial.available() > 0) {
      char c = Serial.read();
      if (c == 'S' || c == 's') {
        experimentStarted = true;
        experimentStartTime = millis();
        Serial.println("=== 実験開始 ===");
        lastPressureStepTime = millis();
        targetPressure = 0.0;
        increasing = true;
        setPressureMPa(targetPressure);
      }
    }
    return;
  }

  loopMeasurement();
}

void loopMeasurement() {
  unsigned long now = millis();

  // ===== 状態管理 =====
  static bool reachedMaxPressure = false;
  static unsigned long reachedTime = 0;
  static bool processingNotified = false;

  // --- 階段的圧力制御 ---
  if (now - lastPressureStepTime >= pressureStepInterval) {
    if (increasing && !reachedMaxPressure) {
      // 昇圧ステップ
      targetPressure += pressureStep;
      if (targetPressure >= maxPressure) {
        targetPressure = maxPressure;
        reachedMaxPressure = true;
        reachedTime = now;
        Serial.println(">>> 0.5MPa到達！（保持中...）");
      }
      setPressureMPa(targetPressure);
    }
    else if (!increasing && processingNotified) {
      // 降圧ステップ
      targetPressure -= pressureStep;
      if (targetPressure <= minPressure) {
        targetPressure = minPressure;
        setPressureMPa(0.0);  // 最後に0MPa
        Serial.println(">>> 0MPaに到達（減圧完了）");
        Serial.println("=== 実験終了 ===");
        experimentStarted = false;
        return;
      }
      else {
        setPressureMPa(targetPressure); // 降圧でもDAC更新
      }
    }
    lastPressureStepTime = now;
  }

  // --- 0.5MPa保持（5秒データ取得） ---
  if (reachedMaxPressure && !processingNotified) {
    if (now - reachedTime >= 5000) {  // 5秒保持
      Serial.println(">>> 加工開始！（降圧フェーズに移行）");
      increasing = false;
      processingNotified = true;
      lastPressureStepTime = now;
    }
  }

  // --- ロードセル読み取り ---
  static int32_t lastReading = 0;
  if (myScale.available()) lastReading = myScale.getReading();
  int32_t rawReading = lastReading;
  float correctedForce = slope * (rawReading - loadcellOffset);

  // --- レーザ変位計 ---
  int rawLaser = analogRead(laserAnalogPina);
  float voltageLaser = rawLaser * (adcRefVoltage / 4095.0);
  float correctedVoltageLaser = 0.893 * voltageLaser + 0.125;

  float sumV = 0.0;
  voltageBuffer[bufferIndex] = correctedVoltageLaser;
  bufferIndex = (bufferIndex + 1) % averageCount;
  if (bufferIndex == 0) bufferFilled = true;
  int count = bufferFilled ? averageCount : bufferIndex;
  for (int i = 0; i < count; i++) sumV += voltageBuffer[i];
  float avgVoltageLaser = sumV / count;
  float displacement_mm = avgVoltageLaser * 30.0;

  // --- フィードバック圧力 ---
  float adcVoltage = readAnalogVoltage(regulatorFeedbackPin, adcRefVoltage);
  float feedbackPressure = 0.225 * (adcVoltage - 1.0);

  // --- データ出力 ---
  Serial.print("目標圧:");
  Serial.print(targetPressure, 3);
  Serial.print(" MPa ");

  Serial.print("変位:");
  Serial.print(displacement_mm, 3);
  Serial.print(" mm ");

  Serial.print("FB圧力:");
  Serial.print(feedbackPressure, 3);
  Serial.print(" MPa ");

  Serial.print("荷重(補正後):");
  Serial.print(correctedForce, 2);
  Serial.println(" N");

  delay(100);
}

// ===== 補助関数 =====
float readAnalogVoltage(int pin, float refVoltage) {
  int raw = analogRead(pin);
  return raw * (refVoltage / 4095.0) * adcCalibration;
}

void setPressureMPa(float pressure) {
  float correctedPressure = (pressure - 0.002) / 1.02;
  if (pressure < 0.02) correctedPressure = pressure * 0.8;
  if (correctedPressure < 0) correctedPressure = 0.0;

  float voltage = (correctedPressure - 0.005) / 0.179;
  int dacValue = constrain(voltage / 4.6 * 4095, 0, 4095);
  dac.setVoltage(dacValue, false);
}
