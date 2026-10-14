import serial, sys, os, subprocess, platform, time
from datetime import datetime

PORT = sys.argv[1] if len(sys.argv) > 1 else "COM3"   # 自分のポート番号に変更
BAUD = 115200

filename = datetime.now().strftime("measure_%Y%m%d_%H%M%S.csv")

def open_file(path):
    if platform.system() == "Windows":
        os.startfile(path)
    elif platform.system() == "Darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])

with serial.Serial(PORT, BAUD, timeout=2) as ser:
    print(f"{PORT} を開きました")
    time.sleep(2)
    ser.reset_input_buffer()

    ser.write(b"s")
    print("計測開始コマンドを送信...")

    timeouts = 0
    with open(filename, "w", newline="") as f:
        while True:
            line = ser.readline().decode(errors="ignore").strip()
            if not line:
                timeouts += 1
                print("応答待ち...")
                if timeouts >= 5:
                    print("Arduinoから応答がありません。ポート番号・書き込み・配線を確認してください。")
                    sys.exit(1)
                continue
            timeouts = 0
            if line.startswith("#"):   # # READY などのメッセージ
                print(line)
                continue
            if line == "END":
                break
            f.write(line + "\n")
            print(line)

print(f"保存完了: {filename}")
open_file(filename)