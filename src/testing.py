import serial
import csv
import time
import os
import re
from datetime import datetime

# --- シリアル設定 ---
ser = serial.Serial('COM5', 9600, timeout=1)
time.sleep(2)  # シリアル安定化

# --- 状態管理 ---
phase = 0  # 0=未開始, 1=昇圧中, 2=加工中(降圧)
data = []
experiment_start_time = None
recording = False  # 実験開始まではFalse

# --- 保存先フォルダ設定 ---
SAVE_DIR = "C:/Users/taioh/PlatformIO/Projects/code_3/data"
os.makedirs(SAVE_DIR, exist_ok=True)

# --- CSV保存関数 ---
def save_csv(data, phase):
    """CSV保存用関数（UTF-8 BOM付きで保存）"""
    if not data:
        print("⚠ データが空のため保存をスキップします。")
        return

    filename = f"data_phase{phase}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(SAVE_DIR, filename)

    with open(filepath, "w", newline='', encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(["Pressure(MPa)", "Displacement(mm)", "Feedback(MPa)", "LoadCell(N)"])
        writer.writerows(data)

    os.startfile(filepath)
    print(f"✅ 完了：{filepath} に保存されました。")

# --- メイン処理 ---
try:
    print("Arduinoウォームアップ待ち...")
    while True:
        if ser.in_waiting:
            line = ser.read_until(b'\n').decode('utf-8', errors='replace').strip()
            print(line)
            if "Sキーを押すと実験を開始します。" in line:
                ser.write(b'S')
                experiment_start_time = time.time()
                print("Arduinoに実験開始命令を送信しました。")
                phase = 1
                recording = True
                break

    print("データ受信中...")
    while True:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='replace').strip()
            if not line:
                continue
            print("受信:", repr(line))

            # --- 常にフェーズで recording を制御 ---
            if phase in (1, 2):
                recording = True

            # --- フェーズ制御 ---
            if "0.5MPa到達" in line and phase == 1:
                print(">>> 昇圧フェーズ最終到達（保持中...）")
                continue

            if "加工開始" in line and phase == 1:
                print(">>> 昇圧データ（0.5MPa含む）を保存します。")
                save_csv(data, phase=1)
                data = []
                phase = 2
                recording = True
                continue

            if "実験終了" in line and phase == 2:
                print(">>> 実験終了、CSV保存（残りデータ読取り中...）")
                # 残りバッファ読取り
                end_time = time.time() + 5  # 5秒間追加読み取り
                while time.time() < end_time:
                    if ser.in_waiting:
                        extra = ser.readline().decode('utf-8', errors='replace').strip()
                        print("追加:", repr(extra))
                        try:
                            pressure_match = re.search(r"目標圧\s*:\s*(-?[0-9.]+)", extra)
                            displacement_match = re.search(r"変位\s*:\s*(-?[0-9.]+)", extra)
                            feedback_match = re.search(r"FB圧力\s*:\s*(-?[0-9.]+)", extra)
                            loadcell_match = re.search(r"荷重\(補正後\)\s*:\s*(-?[0-9.]+)", extra)

                            if all([pressure_match, displacement_match, feedback_match, loadcell_match]):
                                pressure = float(pressure_match.group(1))
                                displacement = float(displacement_match.group(1))
                                feedback = float(feedback_match.group(1))
                                loadcell = float(loadcell_match.group(1))
                                data.append([pressure, displacement, feedback, loadcell])
                        except:
                            pass

                recording = False
                save_csv(data, phase=2)
                break

            # --- データ記録 ---
            if not recording:
                continue

            try:
                # 正規表現で数値抽出（負の値対応）
                pressure_match = re.search(r"目標圧\s*:\s*(-?[0-9.]+)", line)
                displacement_match = re.search(r"変位\s*:\s*(-?[0-9.]+)", line)
                feedback_match = re.search(r"FB圧力\s*:\s*(-?[0-9.]+)", line)
                loadcell_match = re.search(r"荷重\(補正後\)\s*:\s*(-?[0-9.]+)", line)

                if all([pressure_match, displacement_match, feedback_match, loadcell_match]):
                    pressure = float(pressure_match.group(1))
                    displacement = float(displacement_match.group(1))
                    feedback = float(feedback_match.group(1))
                    loadcell = float(loadcell_match.group(1))
                    data.append([pressure, displacement, feedback, loadcell])

            except Exception as e:
                print("⚠ パースエラー:", e)

except KeyboardInterrupt:
    print("中断されました。")
