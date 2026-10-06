#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import root_scalar
from matplotlib.ticker import MultipleLocator
# ================================
# CSVファイル設定
# ================================
DATA_DIR = r"C:\Users\taioh\PlatformIO\Projects\code_3\data"
files = [
    "kuugeki-20-1-1.csv",
    "kuugeki-20-2-1.csv",
    "kuugeki-20-3-1.csv",
    "kuugeki-20-4-1.csv",
    "kuugeki-20-5-1.csv",
]
# ================================
# 理論モデル（Brent法）
# ================================
n = 2.89
b = 0.135
D0 = 0.01
L0 = 0.1
F_target = 29  # [N]
def F_model(P, L):
    term1 = (P * (3 * L**2 - b**2)) / (4 * np.pi * n**2)
    term2 = 2.82e-6 * (
        192000 * (
            (2 * L / 0.1**2)
            - (2 * L) / (D0**2 * n**2 * np.pi**2)
            - (2 * 0.1**2 * D0**2 * n**2 * np.pi**2 * (b**2 - 2 * L**2))
            / (L**3 * (b**2 - L**2)**2)
        )
        + 1300 * (
            (-2 * 0.1**2) / L**3
            + (2 * D0**2 * n**2 * np.pi**2 * L) / (b**2 - L**2)**2
            + (2 * L * b**2 - 4 * L**3) / (0.1**2 * D0**2 * n**2 * np.pi**2)
        )
    )
    return term1 + term2
P_values_MPa = np.linspace(0.01, 0.65, 100)
P_values_Pa = P_values_MPa * 1e6
L_values = []
for P in P_values_Pa:
    try:
        sol = root_scalar(
            lambda L: F_model(P, L) - F_target,
            bracket=[0.06, b * 0.99],
            method="brentq"
        )
        L_values.append(sol.root if sol.converged else np.nan)
    except:
        L_values.append(np.nan)
L_values = np.array(L_values)
delta_L_mm = (L0 - L_values) * 1000
mask = ~np.isnan(delta_L_mm)
P_valid = P_values_MPa[mask]
delta_L_shifted = delta_L_mm[mask] - delta_L_mm[mask][0]
# ================================
# 各CSVで「圧力ごとの平均」を計算
# ================================
print(f"\n【読み込むCSVファイル】")
for f in files:
    filepath = os.path.join(DATA_DIR, f)
    exists = "✓" if os.path.exists(filepath) else "✗"
    print(f"  {exists} {f}")
print()
per_file_means = []
files_loaded_count = 0
for filename in files:
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        print(f"警告: ファイルが見つかりません: {filename}")
        continue
    df = pd.read_csv(filepath, encoding="utf-8-sig")
    files_loaded_count += 1
    for col in ["Feedback(MPa)", "Displacement(mm)"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df.dropna(subset=["Feedback(MPa)", "Displacement(mm)"], inplace=True)
    disp_min = df["Displacement(mm)"].min()
    df["DeltaDisp(mm)"] = df["Displacement(mm)"] - disp_min
    df["FB_round"] = df["Feedback(MPa)"].round(1)
    # 各ファイル内で平均
    mean_df = (
        df.groupby("FB_round")["DeltaDisp(mm)"]
        .mean()
        .reset_index()
    )
    mean_df["file"] = filename
    per_file_means.append(mean_df)
print(f"\n【読み込み完了】{files_loaded_count} ファイル\n")
# ================================
# 5ファイル分の平均値を統合
# ================================
all_means_df = pd.concat(per_file_means, ignore_index=True)
stats_df = (
    all_means_df
    .groupby("FB_round")["DeltaDisp(mm)"]
    .agg(["mean", "min", "max"])
    .reset_index()
)
stats_df["yerr_low"] = stats_df["mean"] - stats_df["min"]
stats_df["yerr_high"] = stats_df["max"] - stats_df["mean"]
# ================================
# 描画
# ================================
plt.close('all')
# figsize=(幅, 高さ)で調整可能。幅を短くすると横軸の間隔が詳まり、高さを短くすると縦軸の間隔が詳まります
plt.figure(figsize=(6, 6))
# 理論モデル
plt.plot(
    P_valid,
    delta_L_shifted,
    color="red",
    linewidth=2,
    label="Theoretical model"
)
# 実験結果（5ファイル統合）
plt.errorbar(
    stats_df["FB_round"],
    stats_df["mean"],
    yerr=[stats_df["yerr_low"], stats_df["yerr_high"]],
    fmt="x",
    color="black",
    markersize=6,
    markeredgewidth=1.2,  # xマーカーの線の太さ（細く設定）
    elinewidth=1.2,
    capsize=2,
    capthick=2.5,
    label="Experimental results"
)
plt.xlabel("Pressure (MPa)", fontsize=18)
plt.ylabel("Contraction length (mm)", fontsize=18)
plt.tick_params(axis='both', which='major', labelsize=16)
plt.legend(fontsize=16, loc='upper left', bbox_to_anchor=(0.02, 1.00))
plt.ylim(0, 35)
plt.xlim(-0.05, 0.7)  # 横軸を-0.05から開始して「0の位置を右にずらしたい場合は、一番目の値を計算結果に合わせて調整してください

# ================================
# 目盛りの設定（任意に変更可能）
# ================================
ax = plt.gca()
# 横軸の目盛間隔〃0.1に設定
ax.xaxis.set_major_locator(MultipleLocator(0.1))
# 縦軸の目盛間隔〃5に設定
ax.yaxis.set_major_locator(MultipleLocator(5))

# 目盛マークの長さと太さを設定（任意に変更可能）
# length: 目盛マークの長さ（ピクセル）、width: 目盛マークの太さ（ピクセル）
ax.tick_params(axis='both', which='major', length=10, width=1.5)
ax.tick_params(axis='both', which='minor', length=6, width=1.0)

# 上部と右側の罠線を削除
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
# グラフ表示
print(f"【グラフ生成完了】")
print(f"実験データポイント数: {len(stats_df)}\n")
plt.show()