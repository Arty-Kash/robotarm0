import meshcat
import meshcat.geometry as g
import meshcat.transformations as tf
import time

def main():
    # 1. ビジュアライザの起動
    # サーバーが立ち上がり、アクセスするためのURLが表示されます
    vis = meshcat.Visualizer()

    # 2. ブラウザを開くためのURLを表示
    url = vis.url()
    print(f"Meshcat server started. Access this URL in your browser: {url}")

    # 3. 表示する物体の定義（ここでは赤い立方体）
    # 形状: 0.1m x 0.1m x 0.1m のボックス
    # 素材: 色は赤(0xff0000)
    box_geometry = g.Box([0.1, 0.1, 0.1])
    box_material = g.MeshPhongMaterial(color=0xff0000)

    # 4. シーンに物体を追加
    # "my_cube" という名前（パス）で物体を登録します
    vis["my_cube"].set_object(box_geometry, box_material)

    # 5. 物体の位置を変更（例：Z軸方向に少し上げる）
    vis["my_cube"].set_transform(tf.translation_matrix([0, 0, 0.05]))

    print("Cube should be visible now. Press Ctrl+C to stop.")

    # 6. プログラムが終了してサーバーが閉じないように待機
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping...")

if __name__ == "__main__":
    main()
