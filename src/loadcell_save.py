#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import MultipleLocator
# ================================
# CSVファイル設定：複数のグループを指定
# ================================
DATA_DIR = r"C:\Users\taioh\PlatformIO\Projects\code_3\data"
# 複数の実験グループを定義（必要に応じて追加削除）
file_groups = {
    "8-10(gap=5)": [
        "F-kuugeki-5-1-1.csv",
        "F-kuugeki-5-2-1.csv",
        "F-kuugeki-5-3-1.csv",
        "F-kuugeki-5-4-1.csv",
        "F-kuugeki-5-5-1.csv",
    ],
    "8-10(gap=10)": [
        "F-kuugeki-10-1-1.csv",
        "F-kuugeki-10-2-1.csv",
        "F-kuugeki-10-3-1.csv",
        "F-kuugeki-10-4-1.csv",
        "F-kuugeki-10-5-1.csv",
    ],
    "8-10(gap=15)": [
        "F-kuugeki-15-1-1.csv",
        "F-kuugeki-15-2-1.csv",
        "F-kuugeki-15-3-1.csv",
        "F-kuugeki-15-4-1.csv",
        "F-kuugeki-15-5-1.csv",
    ],
    "8-10(gap=20)": [
        "F-kuugeki-20-1-1.csv",
        "F-kuugeki-20-2-1.csv",
        "F-kuugeki-20-3-1.csv",
        "F-kuugeki-20-4-1.csv",
        "F-kuugeki-20-5-1.csv",
    ]
   # さらに追加したい場合はここに足す
}
# ================================
# データ処理と描画
# ================================
plt.close('all')
plt.figure(figsize=(7, 7))
plt.ylim(0, 35)
plt.xlim(-0.05, 0.7)
# 色を定義（グループごとに異なる色）
colors = ["black", "blue", "green", "red"]
markers = ["x", "o", "D", "^", "v", "D"]
# すべてのグループを処理
all_stats = {}
print(f"\n【複数グループの処理開始】\n")
for group_idx, (group_name, files) in enumerate(file_groups.items()):
    print(f"【グループ: {group_name}】")
    # グループ内のファイル確認
    for f in files:
        filepath = os.path.join(DATA_DIR, f)
        exists = "✓" if os.path.exists(filepath) else "✗"
        print(f"  {exists} {f}")
    # データ読み込み
    per_file_means = []
    files_loaded_count = 0
    for filename in files:
        filepath = os.path.join(DATA_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  警告: {filename} が見つかりません")
            continue
        df = pd.read_csv(filepath, encoding="utf-8-sig")
        files_loaded_count += 1
        for col in ["Feedback(MPa)", "LoadCell(N)"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        df.dropna(subset=["Feedback(MPa)", "LoadCell(N)"], inplace=True)
        loadcell_min = df["LoadCell(N)"].min()
        df["DeltaLoadCell(N)"] = df["LoadCell(N)"] - loadcell_min
        df["FB_round"] = df["Feedback(MPa)"].round(1)
        mean_df = (
            df.groupby("FB_round")["DeltaLoadCell(N)"]
            .mean()
            .reset_index()
        )
        mean_df["file"] = filename
        per_file_means.append(mean_df)
    print(f"  → {files_loaded_count} ファイル読み込み完了\n")
    # グループ内のデータを統合
    if per_file_means:
        all_means_df = pd.concat(per_file_means, ignore_index=True)
        stats_df = (
            all_means_df
            .groupby("FB_round")["DeltaLoadCell(N)"]
            .agg(["mean", "min", "max"])
            .reset_index()
        )
        stats_df["yerr_low"] = stats_df["mean"] - stats_df["min"]
        stats_df["yerr_high"] = stats_df["max"] - stats_df["mean"]
        all_stats[group_name] = stats_df
        # グラフにプロット
        color = colors[group_idx % len(colors)]
        marker = markers[group_idx % len(markers)]
        # マーカーサイズの設定（"x"以外のマーカーは大きくする）
        marker_size = 10 if marker == "x" else 10

        plt.errorbar(
            stats_df["FB_round"],
            stats_df["mean"],
            yerr=[stats_df["yerr_low"], stats_df["yerr_high"]],
            fmt=marker,
            color=color,
            markersize=marker_size,
            markeredgewidth=2.0,
            elinewidth=2.0,
            capsize=2,
            capthick=2.5,
            label=f"{group_name}",
            alpha=0.8
        )
    print(f"【{group_name} の統計】")
    print(f"  データポイント数: {len(stats_df)}")
    print(f"  最大変位: {stats_df['mean'].max():.2f} N")
    print(f"  最小変位: {stats_df['mean'].min():.2f} N\n")
# グラフの設定
plt.xlabel("Pressure (MPa)", fontsize=25)
plt.ylabel("Load Cell (N)", fontsize=25)
plt.tick_params(axis='both', which='major', labelsize=25)
plt.legend(fontsize=21, loc='upper left', bbox_to_anchor=(0.02, 1.12))
plt.ylim(0, 300)
plt.xlim(-0.05, 0.7)  # 横軸を-0.05から開始して「0の位置を右にずらしたい場合は、一番目の値を計算結果に合わせて調整してください

# ================================
# 目盛りの設定（任意に変更可能）
# ================================
ax = plt.gca()
# 横軸の目盛間隔を0.1に設定
ax.xaxis.set_major_locator(MultipleLocator(0.1))
# 縦軸の目盛間隔を5に設定
ax.yaxis.set_major_locator(MultipleLocator(50))

# 目盛マークの長さと太さを設定（任意に変更可能）
# length: 目盛マークの長さ（ピクセル）、width: 目盛マークの太さ（ピクセル）
ax.tick_params(axis='both', which='major', length=10, width=1.5)
ax.tick_params(axis='both', which='minor', length=6, width=1.0)

# 上部と右側の枠線を削除
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

plt.tight_layout()
# グラフ表示
print(f"【グラフ生成完了】")
print(f"表示グループ数: {len(all_stats)}\n")
plt.savefig(
    "t4.svg",
    format="svg",
    bbox_inches="tight"
)
plt.show()