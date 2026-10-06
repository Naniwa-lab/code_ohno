import pandas as pd
import matplotlib.pyplot as plt

# CSV読み込み
df = pd.read_csv(r"C:\code_3\data\test3_kiseki.csv")

time = df["Time"]

# X列とY列
x_cols = [c for c in df.columns if c.endswith("/X")]
y_cols = [c for c in df.columns if c.endswith("/Y")]

# 丸数字
labels = ["①","②","③","④","⑤","⑥","⑦","⑧","⑨","⑩",
          "⑪","⑫","⑬","⑭","⑮","⑯","⑰","⑱","⑲","⑳"]

# ======================
# Xのみ
# ======================
plt.figure(figsize=(10,5))

for i, col in enumerate(x_cols):
    plt.plot(time, df[col], linewidth=2, label=labels[i])

plt.title("X")
plt.xlabel("Time [s]")
plt.ylabel("X")
plt.grid(True)
plt.legend(
    title="No.",
    bbox_to_anchor=(1.02, 1),
    loc="upper left",
    borderaxespad=0
)

# ======================
# Yのみ
# ======================
plt.figure(figsize=(10,5))

for i, col in enumerate(y_cols):
    plt.plot(time, df[col], linewidth=2, label=labels[i])

plt.title("Y")
plt.xlabel("Time [s]")
plt.ylabel("Y")
plt.grid(True)
plt.legend(
    title="No.",
    bbox_to_anchor=(1.02, 1),
    loc="upper left",
    borderaxespad=0
)

plt.tight_layout()

plt.show()