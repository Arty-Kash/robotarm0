import pybullet as p
import meshcat
import meshcat.transformations as tf
import numpy as np
import asyncio
import json
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sse_starlette.sse import EventSourceResponse

app = FastAPI()

# 1. MeshcatとPyBulletの初期化 (グローバルに設定)
vis = meshcat.Visualizer()
p.connect(p.DIRECT)
p.setGravity(0, 0, -9.81)

# 地面とロボットの読み込み
floor_col = p.createCollisionShape(p.GEOM_BOX, halfExtents=[1, 1, 0.01])
p.createMultiBody(baseMass=0, baseCollisionShapeIndex=floor_col, basePosition=[0, 0, -0.01])
robot_id = p.loadURDF("simple_arm.urdf", useFixedBase=True)
num_joints = p.getNumJoints(robot_id)

# 描画用のオフセット取得
visual_offsets = {}
visual_data = p.getVisualShapeData(robot_id)
for data in visual_data:
    link_id, v_pos, v_quat = data[1], data[5], data[6] # 円柱の向き補正（90度回転）を含むオフセット
    geom_transform = tf.rotation_matrix(np.pi/2, [1, 0, 0]) if data[2] == p.GEOM_CYLINDER else tf.identity_matrix()
    visual_offsets[link_id] = tf.translation_matrix(v_pos) @ tf.quaternion_matrix([v_quat[3], v_quat[0], v_quat[1], v_quat[2]]) @ geom_transform

# --- 強化学習のダミーデータ用変数 ---
current_step = 0
current_reward = 0.0

# 2. ロボットの計算ループ (非同期で実行)
async def simulation_loop():
    global current_step, current_reward
    t = 0
    while True:
        # 物理計算
        target_pos1 = np.sin(t)
        target_pos2 = np.cos(t)
        p.setJointMotorControl2(robot_id, 0, p.POSITION_CONTROL, targetPosition=target_pos1)
        p.setJointMotorControl2(robot_id, 1, p.POSITION_CONTROL, targetPosition=target_pos2)
        p.stepSimulation()

        # Meshcat同期
        for i in range(-1, num_joints):
            pos, quat = (p.getBasePositionAndOrientation(robot_id)) if i == -1 else (p.getLinkState(robot_id, i)[4:6])
            m = tf.translation_matrix(pos) @ tf.quaternion_matrix([quat[3], quat[0], quat[1], quat[2]])
            if i in visual_offsets:
                vis[f"robot/link_{i}"].set_transform(m @ visual_offsets[i])

        # ダミーの学習進捗を更新
        current_step += 1
        current_reward = np.sin(t) * 10 # 報酬の代わりにサイン波を送ってみる
        
        t += 0.05
        await asyncio.sleep(0.05)

# FastAPI起動時にシミュレーションを開始
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulation_loop())

# 3. Webエンドポイントの設定
@app.get("/")
async def get_index():
    with open("index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read())

# SSE配信エンドポイント
@app.get("/stream")
async def message_stream(request: Request):
    async def event_generator():
        while True:
            if await request.is_disconnected():
                break
            
            # クライアントに送るデータ
            data = {
                "step": current_step,
                "reward": round(current_reward, 2),
                "status": "Learning..." if current_step % 100 < 50 else "Optimizing..."
            }
            yield json.dumps(data)
            await asyncio.sleep(0.5) # 0.5秒おきに送信

    return EventSourceResponse(event_generator())

if __name__ == "__main__":
    import uvicorn
    # メッシュキャットのURLをコンソールに表示
    raw_url = vis.url()
    print(f"\nMeshcat Internal URL: {raw_url}static/\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)