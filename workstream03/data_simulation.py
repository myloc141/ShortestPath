"""
Workstream 3: Data Engineering - Lại Gia Huy
Kịch bản mô phỏng dữ liệu giao thông mạng Seervada Park
Tuân thủ nguyên tắc khoa học: Reproducible (Seed cố định), Logic giao thông thực tế, Phân phối lệch phải.
"""

import numpy as np
import pandas as pd
import json

def generate_rcsp_teaching_data():
    """Tạo bảng RCSP dạy học chuẩn mực phục vụ Workstream 2 (Ngọc Hân)."""
    edges_data = [
        {"node_u": "O", "node_v": "A", "distance": 2, "time": 4, "directed": False},
        {"node_u": "O", "node_v": "B", "distance": 5, "time": 6, "directed": False},
        {"node_u": "O", "node_v": "C", "distance": 4, "time": 5, "directed": False},
        {"node_u": "A", "node_v": "B", "distance": 2, "time": 3, "directed": False},
        {"node_u": "A", "node_v": "D", "distance": 7, "time": 8, "directed": False},
        {"node_u": "B", "node_v": "C", "distance": 1, "time": 2, "directed": False},
        {"node_u": "B", "node_v": "D", "distance": 4, "time": 7, "directed": False},
        {"node_u": "B", "node_v": "E", "distance": 3, "time": 4, "directed": False},
        {"node_u": "C", "node_v": "E", "distance": 4, "time": 5, "directed": False},
        {"node_u": "D", "node_v": "E", "distance": 1, "time": 2, "directed": False},
        {"node_u": "D", "node_v": "T", "distance": 5, "time": 6, "directed": False},
        {"node_u": "E", "node_v": "T", "distance": 7, "time": 8, "directed": False},
    ]
    df = pd.DataFrame(edges_data)
    df.to_csv("workspace_ws3/data/seervada_rcsp_teaching.csv", index=False)
    print("Saved seervada_rcsp_teaching.csv successfully.")
    return df

def generate_simulated_travel_time(num_days=30, seed=42, output_path="workspace_ws3/data/seervada_travel_time_SIMULATED.csv"):
    """
    Tạo bộ dữ liệu mô phỏng thời gian di chuyển (SIMULATED travel time).
    Quy mô: num_days x 5 khung giờ x 12 cạnh.
    """
    np.random.seed(seed)
    
    # Định nghĩa cấu trúc mạng và base travel time (phút)
    edges = [
        ("O", "A", 2, 4.0),
        ("O", "B", 5, 6.0),
        ("O", "C", 4, 5.0),
        ("A", "B", 2, 3.0),
        ("A", "D", 7, 8.0),
        ("B", "C", 1, 2.0),
        ("B", "D", 4, 7.0),
        ("B", "E", 3, 4.0),
        ("C", "E", 4, 5.0),
        ("D", "E", 1, 2.0),
        ("D", "T", 5, 6.0),
        ("E", "T", 7, 8.0),
    ]
    
    # 5 khung giờ trong ngày
    time_slots = [
        {"slot_id": 1, "name": "06:00-08:00", "desc": "Sáng sớm", "weekday_factor": 0.90, "weekend_factor": 0.85},
        {"slot_id": 2, "name": "08:00-10:00", "desc": "Cao điểm sáng", "weekday_factor": 1.45, "weekend_factor": 1.15},
        {"slot_id": 3, "name": "11:30-13:30", "desc": "Buổi trưa", "weekday_factor": 1.10, "weekend_factor": 1.30},
        {"slot_id": 4, "name": "16:30-18:30", "desc": "Cao điểm chiều", "weekday_factor": 1.60, "weekend_factor": 1.25},
        {"slot_id": 5, "name": "19:30-21:30", "desc": "Buổi tối", "weekday_factor": 1.05, "weekend_factor": 1.35},
    ]
    
    # Các cạnh chịu áp lực tắc nghẽn cao trong giờ cao điểm
    congested_edges = [("O", "A"), ("A", "B"), ("B", "D"), ("D", "T"), ("A", "D")]
    
    records = []
    
    for day in range(1, num_days + 1):
        # Giả định Ngày 1 bắt đầu là Thứ Hai (Day of week: 0 = Mon, 6 = Sun)
        day_of_week = (day - 1) % 7
        day_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][day_of_week]
        is_weekend = 1 if day_of_week in [5, 6] else 0
        
        for slot in time_slots:
            slot_id = slot["slot_id"]
            slot_name = slot["name"]
            base_slot_factor = slot["weekend_factor"] if is_weekend else slot["weekday_factor"]
            
            for u, v, dist, base_t in edges:
                edge_id = f"{u}-{v}"
                
                # Hệ số tắc nghẽn cục bộ theo tuyến
                edge_congestion_boost = 1.0
                if (u, v) in congested_edges or (v, u) in congested_edges:
                    if slot_id in [2, 4]: # Cao điểm
                        edge_congestion_boost = 1.25 if not is_weekend else 1.10
                    elif slot_id == 5 and is_weekend:
                        edge_congestion_boost = 1.20
                else:
                    # Các tuyến danh lam / nhánh phụ (như B-E, E-T) đông hơn vào cuối tuần
                    if is_weekend and slot_id in [3, 5]:
                        edge_congestion_boost = 1.15
                
                mean_time = base_t * base_slot_factor * edge_congestion_boost
                
                # Nhiễu giao thông ngẫu nhiên mô hình hóa bằng Log-Normal (đảm bảo t > 0 và đuôi lệch phải)
                sigma = 0.12 # Độ biến động giao thông
                noise = np.random.lognormal(mean=0.0, sigma=sigma)
                simulated_t = round(float(mean_time * noise), 2)
                
                records.append({
                    "day": day,
                    "day_of_week": day_name,
                    "is_weekend": is_weekend,
                    "time_slot": slot_id,
                    "time_slot_name": slot_name,
                    "edge_id": edge_id,
                    "node_u": u,
                    "node_v": v,
                    "distance": dist,
                    "travel_time": simulated_t
                })
                
    df = pd.DataFrame(records)
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} rows to {output_path}")
    return df

if __name__ == "__main__":
    generate_rcsp_teaching_data()
    # 1. Dataset 30 ngày chuẩn mực theo đề cương (1,800 dòng)
    generate_simulated_travel_time(num_days=30, seed=42, output_path="workspace_ws3/data/seervada_travel_time_SIMULATED.csv")
    # 2. Dataset mở rộng 90 ngày cho Neural Network (5,400 dòng)
    generate_simulated_travel_time(num_days=90, seed=101, output_path="workspace_ws3/data/seervada_travel_time_EXTENDED_NN.csv")
