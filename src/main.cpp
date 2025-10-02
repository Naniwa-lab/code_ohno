#include <Wire.h>
#include <SparkFun_Qwiic_Scale_NAU7802_Arduino_Library.h>
#include <Adafruit_MCP4725.h>

// ===== インスタンス定義 =====
NAU7802 myScale;
Adafruit_MCP4725 dac;

// ===== ピン・定数 =====
#define MCP4725_ADDR 0x60
const int laserAnalogPin = A0;
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
const float pressureStep = 0.005;
const float maxPressure = 0.5;
const float minPressure = 0.0;
const unsigned long pressureUpdateInterval = 300;
unsigned long lastPressureUpdate = 0;

// ===== ロードセル一次関数変換用定数 =====
const float BIT_KNOWN = 45527.69435f;     // 1.043kgのときのbit数
const float MASS_KNOWN = 1.043f;          // kg
const float GRAVITY = 9.80665f;           // m/s²
float slope = 1.0f;                       // 傾き（N/bit）

// ===== 実験管理 =====
bool experimentStarted = false;
long loadcellOffset = 0;
unsigned long experimentStartTime = 0;
const unsigned long experimentDuration = 60000; // 60秒

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

  // ---- センサウォームアップ ----
  Serial.println("センサを安定化中...(5秒)");
  setPressureMPa(0.0);
  delay(5000);

  // ---- ロードセルオフセット測定 ----
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
  if (count > 0) {
    loadcellOffset = sum / count;
  }
  Serial.print("ロードセルオフセット = ");
  Serial.println(loadcellOffset);

  // ---- 傾き（一次関数の係数）を算出 ----
  slope = (MASS_KNOWN * GRAVITY) / (BIT_KNOWN);
  Serial.print("換算係数 slope = ");
  Serial.print(slope, 8);
  Serial.println(" N/bit");

  Serial.println("実験開始まで少々お待ちください...(5秒)");
  delay(5000);

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
        lastPressureUpdate = millis();
      }
    }
    return;
  }

  if (millis() - experimentStartTime >= experimentDuration) {
    setPressureMPa(0.0);
    experimentStarted = false;
    Serial.println("=== 実験終了 ===");
    return;
  }

  loopMeasurement();
}

void loopMeasurement() {
  unsigned long now = millis();

  // ===== 0.5MPa到達・加工開始の非同期処理 =====
  static bool reachedMaxPressure = false;       // 0.5MPa到達フラグ
  static unsigned long maxPressureTime = 0;     // 到達時刻
  static bool processingNotified = false;       // 加工開始通知済みフラグ

  // --- 圧力変化処理 ---
  if (!reachedMaxPressure) {
    if (now - lastPressureUpdate >= pressureUpdateInterval) {
      if (increasing) {
        targetPressure += pressureStep;
        if (targetPressure >= maxPressure) {
          targetPressure = maxPressure;
          reachedMaxPressure = true;           // 到達フラグセット
          maxPressureTime = now;               // 到達時刻記録
          Serial.println(">>> 0.5MPa到達！5秒待機中...");
        }
      } else {
        targetPressure -= pressureStep;
        if (targetPressure <= minPressure) {
          targetPressure = minPressure;
          increasing = true;
        }
      }
      setPressureMPa(targetPressure);
      lastPressureUpdate = now;
    }
  } else {
    // 5秒待機後に加工開始通知
    if (!processingNotified && now - maxPressureTime >= 5000) {
      Serial.println(">>> 加工開始！");
      processingNotified = true;
      increasing = false;  // 0.5MPa到達後は圧力下降に移行
    }
  }

  // --- ロードセル読み取り（一次関数でN換算） ---
  static int32_t lastReading = 0;
  if (myScale.available()) {
    lastReading = myScale.getReading();
  }
  int32_t rawReading = lastReading;

  float correctedForce = slope * (rawReading - loadcellOffset);

  // --- レーザ変位計（移動平均） ---
  int rawLaser = analogRead(laserAnalogPin);
  float voltageLaser = rawLaser * (adcRefVoltage / 4095.0);
  float correctedVoltageLaser = 0.893 * voltageLaser + 0.125;

  float sumV = 0.0;
  voltageBuffer[bufferIndex] = correctedVoltageLaser;
  bufferIndex = (bufferIndex + 1) % averageCount;
  if (bufferIndex == 0) bufferFilled = true;
  int count = bufferFilled ? averageCount : bufferIndex;
  for (int i = 0; i < count; i++) sumV += voltageBuffer[i];
  float avgVoltageLaser = sumV / count;
  float displacement_mm = avgVoltageLaser * 32.0 - 80.0;

  // --- フィードバック圧力 ---
  float adcVoltage = readAnalogVoltage(regulatorFeedbackPin, adcRefVoltage);
  float feedbackPressure = 0.225 * (adcVoltage - 1.0);

  // --- データ出力 ---
  Serial.print("目標圧:");
  Serial.print(targetPressure, 3);
  Serial.print(" MPa ");

  Serial.print("変位:");
  Serial.print(avgVoltageLaser, 3);
  Serial.print(" V / ");
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
  float voltage = (pressure - 0.005) / 0.179;
  int dacValue = constrain(voltage / 4.6 * 4095, 0, 4095);
  dac.setVoltage(dacValue, false);
}
