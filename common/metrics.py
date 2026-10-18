"""
Module: common/metrics.py
Thư mục dùng chung cho toàn bộ dự án theo quy định của nhóm trưởng (Mỹ Lộc):
'- mọi metrix (vd mse ... ) đều phải để vào thư mục common'

INPUT:
- y_true: array-like (1D vector) of ground truth target values (phút hoặc đơn vị đo lường tương ứng).
- y_pred: array-like (1D vector) of predicted target values.
- Dependencies: numpy.
- Assumptions: y_true và y_pred có cùng độ dài n, các giá trị là số thực hữu hạn (finite real numbers).

PROCESSING:
- Mean Absolute Error (MAE): (1/n) * sum(|y_i - y_hat_i|)
- Mean Squared Error (MSE): (1/n) * sum((y_i - y_hat_i)^2)
- Root Mean Squared Error (RMSE): sqrt(MSE)
- Mean Absolute Percentage Error (MAPE): (100/n) * sum(|(y_i - y_hat_i) / y_i|), với policy bảo vệ chia cho 0: lọc mask y_true != 0.

OUTPUT:
- Trả về số thực float cho từng metric đơn lẻ.
- Trả về dictionary các chỉ số tổng hợp qua hàm evaluate_all(y_true, y_pred).

DOWNSTREAM:
- WS4 (Hà Minh - Baselines): đánh giá mô hình Group Mean và Linear Regression.
- WS5 (Yến Nhi - Neural Network): đánh giá mô hình MLP trên cùng tập test.
- WS6 (Mỹ Lộc - Routing): so sánh sai số dự báo trước và sau khi định tuyến.
"""

import numpy as np

def mean_squared_error(y_true, y_pred):
    """Tính sai số bình phương trung bình (Mean Squared Error - MSE)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean((y_true - y_pred) ** 2))

def root_mean_squared_error(y_true, y_pred):
    """Tính căn bậc hai sai số bình phương trung bình (Root Mean Squared Error - RMSE)."""
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))

def mean_absolute_error(y_true, y_pred):
    """Tính sai số tuyệt đối trung bình (Mean Absolute Error - MAE)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    return float(np.mean(np.abs(y_true - y_pred)))

def mean_absolute_percentage_error(y_true, y_pred):
    """Tính sai số phần trăm tuyệt đối trung bình (Mean Absolute Percentage Error - MAPE)."""
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    # Tránh chia cho 0
    mask = y_true != 0
    if not np.any(mask):
        return 0.0
    return float(np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100)

def evaluate_all(y_true, y_pred):
    """
    Hàm đánh giá tổng hợp trả về toàn bộ metrics chuẩn.
    Dùng cho Hà Minh (WS4 - Baselines), Yến Nhi (WS5 - NN), Mỹ Lộc (WS6 - Routing).
    """
    return {
        "MAE": round(mean_absolute_error(y_true, y_pred), 4),
        "RMSE": round(root_mean_squared_error(y_true, y_pred), 4),
        "MSE": round(mean_squared_error(y_true, y_pred), 4),
        "MAPE_percent": round(mean_absolute_percentage_error(y_true, y_pred), 2)
    }

if __name__ == "__main__":
    # Test thử hàm
    y_t = [10.0, 15.0, 12.0, 8.0]
    y_p = [9.5, 15.8, 11.2, 8.5]
    print("Test common/metrics.py:", evaluate_all(y_t, y_p))
