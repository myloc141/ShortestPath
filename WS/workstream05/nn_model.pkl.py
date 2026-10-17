import os
import joblib

# Lấy đường dẫn thư mục hiện tại của file nn_model.pkl.py (thư mục workstream05)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model_path = os.path.join(BASE_DIR, "nn_model.pkl")

# Tải mô hình
model = joblib.load(model_path)

# In thông tin mô hình
print(model)
print("Số lớp / số node:", model.hidden_layer_sizes)
print("Hàm kích hoạt (Activation):", model.activation)
print("Thuật toán tối ưu (Solver):", model.solver)