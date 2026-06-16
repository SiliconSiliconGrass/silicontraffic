"""
将 CityFlow 路网转换为 SUMO 格式
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from silicontraffic.road_net.road_net import RoadNet
from silicontraffic.scityflow import load_cityflow_road_net
from silicontraffic.save_net import save_as_sumo

def convert_cityflow_to_sumo():
    """将 CityFlow 路网转换为 SUMO 格式"""
    print("开始将 CityFlow 路网转换为 SUMO 格式...")
    
    # 输入文件路径
    input_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'data', 'cityflow', 'hangzhou', 'roadnet_4_4.json'
    )
    
    # 输出文件路径
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'data', 'sumo', 'hangzhou', 'roadnet_4_4.net.xml'
    )
    
    # 确保输出目录存在
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 加载 CityFlow 路网
    print(f"  加载 CityFlow 路网: {input_path}")
    net = load_cityflow_road_net(input_path)
    
    # 保存为 SUMO 格式
    print(f"  保存为 SUMO 格式: {output_path}")
    save_as_sumo(net, output_path)
    
    print("转换完成！")
    
    # 打印路网统计信息
    print(f"\n路网统计信息:")
    print(f"  交叉口数量: {len(net.junction_bank)}")
    print(f"  边数量: {len(net.edge_bank)}")
    print(f"  车道数量: {len(net.lane_bank)}")
    print(f"  交通灯数量: {len(net.traffic_light_bank)}")


if __name__ == '__main__':
    convert_cityflow_to_sumo()
