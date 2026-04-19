import pybullet as p
import meshcat
import meshcat.geometry as g
import meshcat.transformations as tf
import time
import numpy as np
import os

def main():
    # 1. PyBulletの設定
    p.connect(p.DIRECT)
    p.setGravity(0, 0, -9.81)

    # 2. 地面（床）の作成
    # 物理的な基準として床だけは残しておきます
    floor_col_id = p.createCollisionShape(p.GEOM_BOX, halfExtents=[1, 1, 0.01])
    p.createMultiBody(baseMass=0, baseCollisionShapeIndex=floor_col_id, basePosition=[0, 0, -0.01])

    # 3. ロボット(URDF)の読み込み
    urdf_path = "simple_arm.urdf"
    if not os.path.exists(urdf_path):
        print(f"Error: {urdf_path} not found!")
        return
    robot_id = p.loadURDF(urdf_path, useFixedBase=True)
    num_joints = p.getNumJoints(robot_id)

    # 4. Meshcatの設定
    vis = meshcat.Visualizer()
    raw_url = vis.url()
    if not raw_url.endswith('/'): raw_url += '/'
    print("-" * 60)
    print(f"Meshcat Server (Robot Arm Only)")
    print(f"Access URL: {raw_url}static/")
    print("-" * 60)

    # 5. Meshcat上の表示設定
    # 床を表示
    vis["floor"].set_object(g.Box([2, 2, 0.01]), g.MeshPhongMaterial(color=0x888888))
    vis["floor"].set_transform(tf.translation_matrix([0, 0, -0.01]))

    # ロボットの表示設定
    visual_offsets = {}
    visual_data = p.getVisualShapeData(robot_id)
    for data in visual_data:
        link_id, geom_type, size, v_pos, v_quat, rgba = data[1], data[2], data[3], data[5], data[6], data[7]
        path = f"robot/link_{link_id}"
        if geom_type == p.GEOM_BOX:
            obj = g.Box(size)
            geom_transform = tf.identity_matrix()
        elif geom_type == p.GEOM_CYLINDER:
            obj = g.Cylinder(size[0], size[1])
            geom_transform = tf.rotation_matrix(np.pi/2, [1, 0, 0])
        else:
            continue
            
        vis[path].set_object(obj, g.MeshPhongMaterial(color=int(rgba[0]*255)<<16 | int(rgba[1]*255)<<8 | int(rgba[2]*255)))
        
        # リンク固有のオフセットを計算
        offset_matrix = tf.translation_matrix(v_pos) @ tf.quaternion_matrix([v_quat[3], v_quat[0], v_quat[1], v_quat[2]]) @ geom_transform
        visual_offsets[link_id] = offset_matrix

    # 6. メインループ
    print("Running simulation... Press Ctrl+C to stop.")
    t = 0
    try:
        while True:
            # アームの制御（現在はサイン波によるテスト動作）
            target_pos1 = np.sin(t) 
            target_pos2 = np.cos(t)
            
            p.setJointMotorControl2(robot_id, 0, p.POSITION_CONTROL, targetPosition=target_pos1)
            p.setJointMotorControl2(robot_id, 1, p.POSITION_CONTROL, targetPosition=target_pos2)
            
            p.stepSimulation()
            
            # 各パーツのMeshcat同期
            for i in range(-1, num_joints):
                if i == -1:
                    pos, quat = p.getBasePositionAndOrientation(robot_id)
                else:
                    state = p.getLinkState(robot_id, i)
                    pos, quat = state[4], state[5]
                
                world_m = tf.translation_matrix(pos) @ tf.quaternion_matrix([quat[3], quat[0], quat[1], quat[2]])
                
                if i in visual_offsets:
                    vis[f"robot/link_{i}"].set_transform(world_m @ visual_offsets[i])
            
            t += 0.05
            time.sleep(0.05)
            
    except KeyboardInterrupt:
        p.disconnect()
        print("\nStopped.")

if __name__ == "__main__":
    main()