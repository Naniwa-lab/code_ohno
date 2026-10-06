
import numpy as np
import matplotlib.pyplot as plt
# 初期条件
dt = 0.01
t_max = 5
x = 1.0
v = 0.0
# 記録用リスト
t_list = [0]
x_list = [x]
v_list = [v]
t = 0
while t < t_max:
    # 更新（オイラー法）
    x_new = x + v * dt
    v_new = v - x * dt
    # 値を更新
    x = x_new
    v = v_new
    t += dt
    # 記録
    t_list.append(t)
    x_list.append(x)
    v_list.append(v)
# --- グラフ（x-v平面） ---
plt.plot(x_list, v_list)
plt.axhline(0, color="black", linewidth=1)
plt.axvline(0, color="black", linewidth=1)
plt.xlabel("v")
plt.ylabel("x")
plt.title("Phase Space (x-v)")
ax = plt.gca()
for spine in ax.spines.values():
    spine.set_visible(False)
plt.grid(True, which="both", linestyle="--", alpha=0.5)
plt.show()
