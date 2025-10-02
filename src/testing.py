import serial
import csv
import time
import os
from datetime import datetime

# --- シリアル設定 ---
ser = serial.Serial('COM5', 9600, timeout=1)
time.sleep(2)  # シリアル安定化

# --- 状態管理 ---
current_phase = None       # "up", "down", None
data_up = []               # 昇圧データ
data_down = []             # 降圧データ

def save_csv(data, phase):
    """CSV保存"""
    if not data:
        return
    filename = f"data_{phase}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    with open(filename, "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Pressure(MPa)", "Displacement(mm)", "Feedback(MPa)", "LoadCell(N)"])
        writer.writerows(data)
    os.startfile(filename)
    print(f"[保存完了] {filename}")

try:
    print("Arduinoウォームアップ待ち...")
    while True:
        if ser.in_waiting:
            line = ser.readline().decode('utf-8', errors='replace').strip()
            print(line)

            # 実験開始待機
            if "Sキーを押すと実験を開始します。" in line:
                ser.write(b'S')  # 自動でS送信
                print("Arduinoに実験開始命令を送信しました。")

            # === フェーズ切替 ===
            if "到達通知: 目標圧力 0.5MPa に到達しました" in line:
                print("昇圧データ収集終了 → CSV保存")
                save_csv(data_up, "up")
                current_phase = None  # インターバル中は収集しない

            elif "加工開始通知: 降圧を開始します" in line:
                print("降圧データ収集開始")
                current_phase = "down"

            elif "実験終了通知: 実験を終了します" in line:
                print("降圧データ収集終了 → CSV保存")
                save_csv(data_down, "down")
                break

            # === データ受信 ===
            try:
                if any(key in line for key in ["目標圧", "変位", "FB圧力", "荷重"]):
                    pressure = ""
                    displacement = ""
                    feedback = ""
                    loadcell = ""

                    for part in line.split():
                        if "目標圧" in part:
                            pressure = part.split(":")[-1].replace("MPa", "").strip()
                        elif "変位" in part:
                            displacement = part.split(":")[-1].replace("V", "").replace("/", "").replace("mm", "").strip()
                        elif "FB圧力" in part:
                            feedback = part.split(":")[-1].replace("MPa", "").strip()
                        elif "荷重(補正後)" in part:
                            loadcell = part.split(":")[-1].strip()

                    if pressure and displacement and feedback and loadcell:
                        if current_phase == "up":
                            data_up.append([pressure, displacement, feedback, loadcell])
                        elif current_phase == "down":
                            data_down.append([pressure, displacement, feedback, loadcell])

            except Exception as e:
                print("パースエラー:", e)

except KeyboardInterrupt:
    print("中断されました。")
    # 万一途中で止めても保存
    save_csv(data_up, "up_abort")
    save_csv(data_down, "down_abort")
