import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.optimize import root_scalar

# --- CSVファイルリスト ---
DATA_DIR = r"C:\Users\taioh\PlatformIO\Projects\code_3\data"
files = [
    "s8-12-1-1.csv",
    "s8-12-2-1.csv",
    "s8-12-3-1.csv",
    "s8-12-4-1.csv",
    "s8-12-5-1.csv",
]

markers = ["o", "s", "D", "^", "v", "x", "+", "*", "P", "h"]

# ================================
# 理論モデル線（Brent法）
# ================================

# モデル定数
n = 1.5
b = 0.124
D0 = 0.0156
L0 = 0.1
F_target = 29   # 吊り下げ荷重

# モデル式
def F_model(P, L):
    term1 = (P * (3 * L**2 - b**2)) / (4 * np.pi * n**2)
    term2 = 1.98e-6 * (
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

# 探索用P
P_values_MPa = np.linspace(0.01, 0.65, 100)
P_values_Pa = P_values_MPa * 1e6

L_values = []

# ★ Brent法で高速に求める
for P in P_values_Pa:
    try:
        sol = root_scalar(lambda L: F_model(P, L) - F_target,
                          bracket=[0.06, 0.12], method='brentq')
        if sol.converged:
            L_values.append(sol.root)
        else:
            L_values.append(np.nan)
    except:
        L_values.append(np.nan)

L_values = np.array(L_values)
delta_L_mm = (L0 - L_values) * 1000

mask = ~np.isnan(delta_L_mm)
P_valid = P_values_MPa[mask]
delta_L_valid = delta_L_mm[mask]

# オフセット補正
offset = delta_L_valid[0]
delta_L_shifted = delta_L_valid - offset

# 描画
plt.plot(P_valid, delta_L_shifted,
         color="red", linewidth=2,
         label="Theoretical model (Brent method, shifted)")


# --- 外れ値除外設定 ---
trim_n = 3

# --- グラフ初期化 ---
plt.figure(figsize=(10, 6))

# ================================
# CSVファイルの読み込み・平均点プロット
# ================================
for i, filename in enumerate(files):
    filepath = os.path.join(DATA_DIR, filename)
    if not os.path.exists(filepath):
        print(f"⚠ ファイルが見つかりません: {filename}")
        continue

    df = pd.read_csv(filepath, encoding="utf-8-sig")

    # 数値変換
    for col in ["Pressure(MPa)", "Displacement(mm)", "Feedback(MPa)", "LoadCell(N)"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df.dropna(subset=["Feedback(MPa)", "Displacement(mm)"], inplace=True)

    disp_min = df["Displacement(mm)"].min()

    # FBを0.1MPa単位に丸め
    df["FB_round"] = df["Feedback(MPa)"].round(1)

    # 外れ値除外して平均
    mean_values = []
    for fb, group in df.groupby("FB_round"):
        group_sorted = group.sort_index()
        n = len(group_sorted)
        if n > trim_n * 2:
            trimmed = group_sorted.iloc[trim_n:-trim_n]
        else:
            trimmed = group_sorted

        mean_disp = trimmed["Displacement(mm)"].mean()
        delta_disp = mean_disp - disp_min
        mean_values.append({"FB_round": fb, "DeltaDisp(mm)": delta_disp})

    mean_df = pd.DataFrame(mean_values)

    # プロット
    plt.scatter(
        mean_df["FB_round"],
        mean_df["DeltaDisp(mm)"],
        s=60,
        marker=markers[i % len(markers)],
        label=f"file {i+1}: {filename}",
        edgecolor="black"
    )

# ----------------------------
# グラフ装飾
# ----------------------------
plt.xlabel("Pressure (MPa)")
plt.ylabel("Amount of contraction (mm)")
plt.title("Relationship between contraction and FB pressure (29 N load)")
plt.legend()
plt.grid(True)
plt.ylim(0, 30)
plt.tight_layout()
plt.show()
