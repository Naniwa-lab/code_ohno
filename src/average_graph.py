import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ==============================
# データフォルダ
# ==============================
DATA_DIR = r"C:\Users\taioh\PlatformIO\Projects\code_3\data"

# ==============================
# 条件ごとのCSVファイル群
# ==============================
groups = {
        "s8-10": [
        "s8-10-1-1.csv",
        "s8-10-2-1.csv",
        "s8-10-3-1.csv",
        "s8-10-4-1.csv",
        "s8-10-5-1.csv",
    ],
    "kuugeki-5": [
        "kuugeki-5-1-1.csv",
        "kuugeki-5-2-1.csv",
        "kuugeki-5-3-1.csv",
        "kuugeki-5-4-1.csv",
        "kuugeki-5-5-1.csv",
    ],
    "kuugeki-10": [
        "kuugeki-10-1-1.csv",
        "kuugeki-10-2-1.csv",
        "kuugeki-10-3-1.csv",
        "kuugeki-10-4-1.csv",
        "kuugeki-10-5-1.csv",
    ],
     "kuugeki-15": [
        "kuugeki-15-1-1.csv",
        "kuugeki-15-2-1.csv",
        "kuugeki-15-3-1.csv",
        "kuugeki-15-4-1.csv",
        "kuugeki-15-5-1.csv",
    ],
    "kuugeki-20": [
        "kuugeki-20-1-1.csv",
        "kuugeki-20-2-1.csv",
        "kuugeki-20-3-1.csv",
        "kuugeki-20-4-1.csv",
        "kuugeki-20-5-1.csv",
    ],
}

# マーカー
markers = ["o", "s", "D", "^", "v", "x", "+", "*", "P", "h"]

# 外れ値除外数
trim_n = 3

# ==============================
# グラフ初期化
# ==============================
plt.figure(figsize=(10, 6))

# ==============================
# 条件ごとの平均処理
# ==============================
for gi, (group_name, file_list) in enumerate(groups.items()):

    all_points = []

    for filename in file_list:
        filepath = os.path.join(DATA_DIR, filename)

        if not os.path.exists(filepath):
            print(f"⚠ ファイルが見つかりません: {filename}")
            continue

        df = pd.read_csv(filepath, encoding="utf-8-sig")

        # 数値変換
        for col in ["Feedback(MPa)", "Displacement(mm)"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df.dropna(subset=["Feedback(MPa)", "Displacement(mm)"], inplace=True)

        # 変位の最小値（基準）
        disp_min = df["Displacement(mm)"].min()

        # FBを0.1MPa刻みに
        df["FB_round"] = df["Feedback(MPa)"].round(1)

        # FBごとに平均（外れ値除外）
        for fb, g in df.groupby("FB_round"):
            g = g.sort_index()

            if len(g) > trim_n * 2:
                g = g.iloc[trim_n:-trim_n]

            mean_disp = g["Displacement(mm)"].mean()
            delta_disp = mean_disp - disp_min

            all_points.append({
                "FB_round": fb,
                "DeltaDisp(mm)": delta_disp
            })

    # ==========================
    # 条件内（5ファイル）平均
    # ==========================
    all_df = pd.DataFrame(all_points)

    group_mean = (
        all_df
        .groupby("FB_round", as_index=False)
        .mean()
    )

    # プロット（条件ごとに1系列）
    plt.scatter(
        group_mean["FB_round"],
        group_mean["DeltaDisp(mm)"],
        s=80,
        marker=markers[gi % len(markers)],
        label=group_name,
        edgecolor="black"
    )

# ==============================
# グラフ装飾
# ==============================
plt.xlabel("Pressure (MPa)")
plt.ylabel("Amount of contraction (mm)")
plt.title("Average contraction vs pressure (5 trials averaged for each condition)")
plt.legend()
plt.grid(True)
plt.ylim(0, 30)
plt.tight_layout()
plt.show()
