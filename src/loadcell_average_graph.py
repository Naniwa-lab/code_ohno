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
        "8-10": [
        "F-8-10-1-1.csv",
        "F-8-10-2-1.csv",
        "F-8-10-3-1.csv",
        "F-8-10-4-1.csv",
        "F-8-10-5-1.csv",
    ],
        "8-10-5": [
        "F-kuugeki-5-1-1.csv",
        "F-kuugeki-5-1-1.csv",
        "F-kuugeki-5-1-1.csv",
        "F-kuugeki-5-1-1.csv",
        "F-kuugeki-5-1-1.csv",
    ],
        "8-10-10": [
        "F-kuugeki-10-1-1.csv",
        "F-kuugeki-10-1-1.csv",
        "F-kuugeki-10-1-1.csv",
        "F-kuugeki-10-1-1.csv",
        "F-kuugeki-10-1-1.csv",
    ],
        "8-10-15": [
        "F-kuugeki-15-1-1.csv",
        "F-kuugeki-15-1-1.csv",
        "F-kuugeki-15-1-1.csv",
        "F-kuugeki-15-1-1.csv",
        "F-kuugeki-15-1-1.csv",
    ],
        "8-10-20": [
        "F-kuugeki-20-1-1.csv",
        "F-kuugeki-20-1-1.csv",
        "F-kuugeki-20-1-1.csv",
        "F-kuugeki-20-1-1.csv",
        "F-kuugeki-20-1-1.csv",
    ],

}

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
        for col in ["Feedback(MPa)", "LoadCell(N)"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        df.dropna(subset=["Feedback(MPa)", "LoadCell(N)"], inplace=True)

        # FBを0.1MPa刻みに
        df["FB_round"] = df["Feedback(MPa)"].round(1)

        # FBごとにロードセル平均（外れ値除外）
        for fb, g in df.groupby("FB_round"):
            g = g.sort_index()

            if len(g) > trim_n * 2:
                g = g.iloc[trim_n:-trim_n]

            mean_load = g["LoadCell(N)"].mean()

            all_points.append({
                "FB_round": fb,
                "LoadCell(N)": mean_load
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

    # プロット
    plt.scatter(
        group_mean["FB_round"],
        group_mean["LoadCell(N)"],
        s=80,
        marker=markers[gi % len(markers)],
        label=group_name,
        edgecolor="black"
    )

# ==============================
# グラフ装飾
# ==============================
plt.xlabel("Pressure (MPa)")
plt.ylabel("Load (N)")
plt.title("Average load vs pressure (5 trials averaged for each condition)")
plt.legend()
plt.ylim(0, 300)
plt.grid(True)
plt.tight_layout()
plt.show()
