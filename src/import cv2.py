import cv2
import numpy as np
import matplotlib.pyplot as plt

# === 設定 ===
image_path = r"C:\Users\taioh\PlatformIO\Projects\code_3\src\aw.jpg"  # ← 解析したい画像ファイル名に変更
canny_low = 50
canny_high = 150
hough_threshold = 80

# === 画像読み込み ===
img = cv2.imread(image_path)
if img is None:
    raise FileNotFoundError(f"画像が見つかりません: {image_path}")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray, canny_low, canny_high, apertureSize=3)

# === Hough変換で線検出 ===
lines = cv2.HoughLines(edges, 1, np.pi / 180, hough_threshold)

if lines is None:
    raise RuntimeError("線が検出されませんでした。パラメータを調整してください。")

angles_deg = []
for line in lines:
    rho, theta = line[0]
    angle_deg = np.degrees(theta)
    if angle_deg > 180:
        angle_deg -= 180
    angles_deg.append(angle_deg)

angles_deg = np.array(angles_deg)

# === Step 1: チューブ軸方向の角度を推定 ===
# 長い線を優先的に考慮することもできるが、ここでは単純に角度分布の最頻値を採用
hist, bin_edges = np.histogram(angles_deg, bins=180, range=(0, 180))
axis_angle = bin_edges[np.argmax(hist)]  # 最頻値がチューブ軸方向（または繊維の一方向）
print(f"チューブ軸方向（推定）: {axis_angle:.2f}°")

# === Step 2: 繊維の2方向を特定（±方向）
# 編組なので2つの角度帯があるはず → 軸角度から±範囲を持つピークを探す
angles_relative = np.abs(angles_deg - axis_angle)
angles_relative = np.where(angles_relative > 90, 180 - angles_relative, angles_relative)

# 平均編み角
avg_weave_angle = np.mean(angles_relative)
print(f"繊維の平均編み角（軸に対する角度）: {avg_weave_angle:.2f}°")

# === 結果の可視化 ===
plt.figure(figsize=(10,5))
plt.hist(angles_relative, bins=60, color='lightgreen', edgecolor='k')
plt.axvline(avg_weave_angle, color='r', linestyle='--', label=f"平均角度: {avg_weave_angle:.2f}°")
plt.title("繊維の編み角分布（軸に対する相対角度）")
plt.xlabel("角度 (°)")
plt.ylabel("検出線数")
plt.legend()
plt.show()

# === デバッグ可視化（線の重ね描き） ===
img_lines = img.copy()
for line in lines[:100]:  # 最初の100本だけ描画
    rho, theta = line[0]
    a = np.cos(theta)
    b = np.sin(theta)
    x0 = a * rho
    y0 = b * rho
    x1 = int(x0 + 1000 * (-b))
    y1 = int(y0 + 1000 * (a))
    x2 = int(x0 - 1000 * (-b))
    y2 = int(y0 - 1000 * (a))
    cv2.line(img_lines, (x1, y1), (x2, y2), (0, 0, 255), 1)

plt.figure(figsize=(8,6))
plt.imshow(cv2.cvtColor(img_lines, cv2.COLOR_BGR2RGB))
plt.title("検出された線分（赤線）")
plt.axis("off")
plt.show()
