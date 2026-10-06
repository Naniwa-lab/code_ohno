import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# 日本語ラベルの文字化け(tofu表示)を防ぐフォント指定
plt.rcParams["font.family"] = ["Yu Gothic", "MS Gothic", "Meiryo", "sans-serif"]

# ======================
# CSV読み込み
# ======================
df = pd.read_csv(r"C:\code_3\data\ex1_100.csv")

time = df["Time"].to_numpy()

x1, y1 = df["1/X"].to_numpy(), df["1/Y"].to_numpy()
x2, y2 = df["2/X"].to_numpy(), df["2/Y"].to_numpy()
x3, y3 = df["3/X"].to_numpy(), df["3/Y"].to_numpy()
x4, y4 = df["4/X"].to_numpy(), df["4/Y"].to_numpy()

# ======================
# 中点の計算
# ======================
mid12x, mid12y = (x1 + x2) / 2, (y1 + y2) / 2
mid34x, mid34y = (x3 + x4) / 2, (y3 + y4) / 2

# ======================
# l : 2つの中点間の距離
# ======================
l = np.sqrt((mid12x - mid34x) ** 2 + (mid12y - mid34y) ** 2)

# ======================
# α用: 直線同士のなす角(-90〜90度に畳み込み)
# ======================
def line_angle_diff_deg(vx1, vy1, vx2, vy2):
    """2本の直線(方向ベクトルで表現)のなす角を -90〜+90度で返す"""
    ang1 = np.arctan2(vy1, vx1)
    ang2 = np.arctan2(vy2, vx2)
    diff = ang1 - ang2
    diff = (diff + np.pi) % (2 * np.pi) - np.pi
    diff = np.where(diff > np.pi / 2, diff - np.pi, diff)
    diff = np.where(diff <= -np.pi / 2, diff + np.pi, diff)
    return np.degrees(diff)

# ======================
# β用: 畳み込みをせず -180〜180度の生の角度差をそのまま返す
# ======================
def vector_angle_diff_deg_raw(vx1, vy1, vx2, vy2):
    """2つの方向ベクトルのなす角を -180〜180度でそのまま返す(畳み込みなし)"""
    ang1 = np.arctan2(vy1, vx1)
    ang2 = np.arctan2(vy2, vx2)
    diff = ang1 - ang2
    diff = (diff + np.pi) % (2 * np.pi) - np.pi  # -180〜180に正規化のみ
    return np.degrees(diff)

perp34_x = -(y4 - y3)
perp34_y = (x4 - x3)

spine_x = mid12x - mid34x
spine_y = mid12y - mid34y

EPS = 1e-9
line34_len = np.hypot(x4 - x3, y4 - y3)
spine_len = np.hypot(spine_x, spine_y)

alpha = line_angle_diff_deg(spine_x, spine_y, perp34_x, perp34_y)
alpha = np.where((line34_len < EPS) | (spine_len < EPS), np.nan, alpha)

# ======================
# β : ①②を結ぶ直線 と lの直線(spine) のなす角
# 畳み込み・符号の付け替えは一切行わず、生の角度差をそのまま使う
# ======================
v12_x, v12_y = (x2 - x1), (y2 - y1)

line12_len = np.hypot(v12_x, v12_y)

a1, b1 = v12_y, -v12_x
c1 = a1 * x1 + b1 * y1

a2, b2 = spine_y, -spine_x
c2 = a2 * mid34x + b2 * mid34y

det = a1 * b2 - a2 * b1

is_degenerate = (line12_len < EPS) | (spine_len < EPS)
is_parallel = np.isclose(det, 0.0, atol=EPS)
invalid = is_degenerate | is_parallel

with np.errstate(divide="ignore", invalid="ignore"):
    inter_x = np.where(~invalid, (c1 * b2 - c2 * b1) / det, np.nan)
    inter_y = np.where(~invalid, (a1 * c2 - a2 * c1) / det, np.nan)

beta = vector_angle_diff_deg_raw(v12_x, v12_y, spine_x, spine_y)
beta = np.where(invalid, np.nan, beta)

# ======================
# βを0〜180度の範囲に変換
# (180度の周期性を持つ「直線同士のなす角」として畳み込む)
# ======================
beta = np.mod(beta, 180)

# ======================
# 計算結果をまとめてCSV出力
# ======================
result = pd.DataFrame({
    "Time": time,
    "l": l,
    "alpha_deg": alpha,
    "beta_deg": beta,
    "mid12_x": mid12x, "mid12_y": mid12y,
    "mid34_x": mid34x, "mid34_y": mid34y,
    "intersection_x": inter_x, "intersection_y": inter_y,
})
result.to_csv(r"C:\code_3\data\test3_kiseki_計算結果.csv", index=False)

# ======================
# グラフ化
# ======================
fig, axes = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

axes[0].plot(time, l, marker=".", markersize=3, linestyle="none", color="tab:blue")
axes[0].set_ylabel("l  [中点間距離]")
axes[0].set_xlabel("Time [s]")
axes[0].set_title("中点①②-中点③④ 間の距離 l")
axes[0].set_ylim(400, 800)  # 縦軸範囲を固定
axes[0].grid(True)

axes[1].plot(time, alpha, marker=".", markersize=3, linestyle="none", color="tab:orange")
axes[1].set_ylabel("α [deg]")
axes[1].set_xlabel("Time [s]")
axes[1].set_title("③④の垂線 と 中点同士の直線 のなす角 α")
axes[1].set_ylim(-50, 40)  # 縦軸範囲を固定
axes[1].grid(True)

axes[2].plot(time, beta, marker=".", markersize=3, linestyle="none", color="tab:green")
axes[2].set_ylabel("β [deg]")
axes[2].set_xlabel("Time [s]")
axes[2].set_title("①②の直線 と lの直線(中点同士を結ぶ直線) のなす角 β (0〜180度)")
axes[2].set_ylim(60, 120)  # 縦軸範囲を固定
axes[2].grid(True)

plt.tight_layout()

# ======================
# FFT解析(周期性の確認)
# ======================
dt = np.median(np.diff(time))
fs = 1.0 / dt
n = len(time)

freqs = np.fft.rfftfreq(n, d=dt)
window = np.hanning(n)
window_correction = 1.0 / np.mean(window)

def fft_amplitude_spectrum(signal):
    s = pd.Series(signal).interpolate(limit_direction="both").to_numpy()
    s = s - np.mean(s)
    s = s * window
    spec = np.fft.rfft(s)
    amp = np.abs(spec) * (2.0 / n) * window_correction
    return amp

def dominant_frequency(freqs, amp, f_min=0.05):
    mask = freqs >= f_min
    idx = np.argmax(amp[mask])
    f_peak = freqs[mask][idx]
    return f_peak, (1.0 / f_peak if f_peak > 0 else np.nan)

amp_l = fft_amplitude_spectrum(l)
amp_alpha = fft_amplitude_spectrum(alpha)
amp_beta = fft_amplitude_spectrum(beta)

f_peak_l, period_l = dominant_frequency(freqs, amp_l)
f_peak_alpha, period_alpha = dominant_frequency(freqs, amp_alpha)
f_peak_beta, period_beta = dominant_frequency(freqs, amp_beta)

print(f"サンプリング周波数 fs = {fs:.2f} Hz  (dt = {dt*1000:.3f} ms)")
print(f"l     : 主要周波数 = {f_peak_l:.3f} Hz  (周期 = {period_l:.3f} s)")
print(f"alpha : 主要周波数 = {f_peak_alpha:.3f} Hz  (周期 = {period_alpha:.3f} s)")
print(f"beta  : 主要周波数 = {f_peak_beta:.3f} Hz  (周期 = {period_beta:.3f} s)")

f_max_plot = 10.0

fig2, axes2 = plt.subplots(3, 1, figsize=(10, 10), sharex=True)

for ax, amp, color, label, f_peak, period in zip(
    axes2,
    [amp_l, amp_alpha, amp_beta],
    ["tab:blue", "tab:orange", "tab:green"],
    ["l", "α", "β"],
    [f_peak_l, f_peak_alpha, f_peak_beta],
    [period_l, period_alpha, period_beta],
):
    ax.plot(freqs, amp, color=color)
    ax.axvline(f_peak, color="red", linestyle="--", linewidth=1)
    ax.set_xlim(0, f_max_plot)
    ax.set_ylabel(f"|{label}| 振幅")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_title(f"{label} のFFT振幅スペクトル  (主要周波数={f_peak:.3f}Hz, 周期={period:.3f}s)")
    ax.grid(True)

plt.tight_layout()
plt.show()