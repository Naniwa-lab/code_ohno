import sys, glob, os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

plt.rcParams["font.family"] = "Meiryo"   # Windowsで日本語を表示(文字化け対策)

# ======================
# 軸の設定(ここだけ変えればOK)  None にすると自動調整
# ======================
PRESSURE_YLIM = (0.3, 0.8)   # 時間波形の縦軸 [MPa]
FFT_YLIM = None              # FFTの縦軸(振幅 [MPa])  例: (0, 0.05)
FFT_XLIM = (0, 25)           # FFTの横軸 [Hz]        例: (0, 20)  / None で 0〜ナイキスト周波数
F_MIN = 0.05                 # 主要周波数の探索下限 [Hz](直流・ゆっくりした変動の除外)

# CSVファイルの決定:引数があればそれ、なければ最新のmeasure_*.csv
if len(sys.argv) > 1:
    path = sys.argv[1]
else:
    files = glob.glob("measure_*.csv") + glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "measure_*.csv"))
    if not files:
        sys.exit("measure_*.csv が見つかりません")
    path = max(files, key=os.path.getmtime)
print("読み込み:", path)

# カンマ区切り・タブ区切りのどちらでも読める
df = pd.read_csv(path, sep=None, engine="python")
t = df["time_ms"] / 1000.0   # ms → s

# ======================
# 時間波形
# ======================
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(t, df["pressure_MPa"], linewidth=1.2)
ax.set_xlabel("時間 [s]")
ax.set_ylabel("空気圧 [MPa]")
ax.set_title("空気圧の時間変化")
ax.grid(True, alpha=0.4)
ax.set_xlim(t.min(), t.max())
if PRESSURE_YLIM is not None:
    ax.set_ylim(*PRESSURE_YLIM)   # 縦軸の範囲 [MPa]

fig.tight_layout()
png = os.path.splitext(path)[0] + ".png"
fig.savefig(png, dpi=150)    # 画像としても保存
print("画像を保存:", png)

# ======================
# FFT解析
#  1. 欠損(NaN)を線形補間
#  2. 平均値を引く(直流成分=0Hzの巨大ピークを除く)
#  3. Hann窓をかける(スペクトル漏れを抑える)
#  4. rFFT → 片側振幅スペクトル(窓による振幅低下も補正)
# ======================
tt = t.to_numpy()
dts = np.diff(tt)
dt = np.median(dts)          # サンプリング間隔 [s](中央値で外れ値の影響を回避)
fs = 1.0 / dt                # サンプリング周波数 [Hz]
n = len(tt)

# 等間隔サンプリングかどうかの確認(ばらつきが大きいとFFTの前提が崩れる)
jitter = np.std(dts) / dt
if jitter > 0.05:
    print(f"[警告] サンプリング間隔のばらつきが大きいです(σ/dt = {jitter:.1%})。"
          "FFT結果の精度が落ちる可能性があります。")

s = pd.Series(df["pressure_MPa"].to_numpy()).interpolate(limit_direction="both").to_numpy()
s = s - np.mean(s)
window = np.hanning(n)
s = s * window

freqs = np.fft.rfftfreq(n, d=dt)
amp = np.abs(np.fft.rfft(s)) * (2.0 / n) / np.mean(window)

mask = freqs >= F_MIN
idx = np.argmax(amp[mask])
f_peak = freqs[mask][idx]
period = 1.0 / f_peak if f_peak > 0 else np.nan

print(f"サンプリング周波数 fs = {fs:.2f} Hz  (dt = {dt*1000:.3f} ms, 点数 n = {n})")
print(f"周波数分解能 df = {fs / n:.4f} Hz")
print(f"主要周波数 = {f_peak:.3f} Hz  (周期 = {period:.3f} s,  振幅 = {amp[mask][idx]:.4g} MPa)")

fig2, ax2 = plt.subplots(figsize=(9, 5))
ax2.plot(freqs, amp, linewidth=1.2, color="tab:green")
ax2.axvline(f_peak, color="red", linestyle="--", linewidth=1)
ax2.set_xlabel("周波数 [Hz]")
ax2.set_ylabel("振幅 [MPa]")
ax2.set_title(f"空気圧のFFT振幅スペクトル  (主要周波数={f_peak:.3f}Hz, 周期={period:.3f}s)")
ax2.grid(True, alpha=0.4)
ax2.set_xlim(*(FFT_XLIM if FFT_XLIM is not None else (0, freqs.max())))
if FFT_YLIM is not None:
    ax2.set_ylim(*FFT_YLIM)

fig2.tight_layout()
png_fft = os.path.splitext(path)[0] + "_fft.png"
fig2.savefig(png_fft, dpi=150)
print("画像を保存:", png_fft)

plt.show()