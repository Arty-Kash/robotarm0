import meshcat
import meshcat.geometry as g
import meshcat.transformations as tf
import time

def main():
    # 1. ビジュアライザの起動
    # これを実行すると、自動的に空いているポート（通常7000番〜）でサーバーが立ち上がります
    vis = meshcat.Visualizer()

    # 2. 割り当てられたURLを取得して表示
    actual_url = vis.url()
    print("-" * 50)
    print(f"Meshcat Server is running at: {actual_url}")
    
    # URLからポート番号を抽出して表示（例: http://127.0.0.1:7000/static/ -> 7000）
    try:
        port = actual_url.split(":")[-2].split("/")[0] # ポート番号部分を抜き出す
        if port == "127.0.0.1": # ポートが最後尾にある場合の処理
            port = actual_url.split(":")[-1].split("/")[0]
    except:
        port = "不明"

    print(f"Detected Port: {port}")
    print("-" * 50)
    print(f"【Codespacesでの操作手順】")
    print(f"1. VS Code下部の『Ports (ポート)』タブを開いてください。")
    print(f"2. ポート {port} がリストにあるか確認してください。")
    print(f"3. もしリストになければ、『Add Port』で {port} を手動追加してください。")
    print(f"4. Forwarded Addressの地球儀マークをクリックして開いてください。")
    print("-" * 50)

    # 3. 物体（赤い立方体）の追加
    box_geometry = g.Box([0.1, 0.1, 0.1])
    box_material = g.MeshPhongMaterial(color=0xff0000)
    vis["my_cube"].set_object(box_geometry, box_material)
    vis["my_cube"].set_transform(tf.translation_matrix([0, 0, 0.05]))

    # 4. プログラムを維持
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")

if __name__ == "__main__":
    main()