import os
import pandas as pd
import matplotlib.pyplot as plt
import joblib
from sklearn.neural_network import MLPRegressor

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Nhận dữ liệu chính xác từ Workstream 03
X_TRAIN_PATH = os.path.join(BASE_DIR, "..", "workstream03", "X_train_preprocessed.csv")
Y_TRAIN_PATH = os.path.join(BASE_DIR, "..", "workstream03", "y_train.csv")
X_TEST_PATH = os.path.join(BASE_DIR, "..", "workstream03", "X_test_preprocessed.csv")

def main():
    print("=== BẮT ĐẦU TRAINING NEURAL NETWORK ===")
    
    # Đọc dữ liệu
    X_train = pd.read_csv(X_TRAIN_PATH)
    y_train = pd.read_csv(Y_TRAIN_PATH).values.ravel()
    X_test = pd.read_csv(X_TEST_PATH)

    print(f"Kiểm tra kích thước dữ liệu:")
    print(f" - Train features: {X_train.shape}")
    print(f" - Test features : {X_test.shape}")

    # Thiết kế Neural Network với cơ chế kiểm soát Overfitting (Early Stopping & Validation)
    model = MLPRegressor(
        hidden_layer_sizes=(64, 32),
        activation='relu',
        solver='adam',
        max_iter=500,
        early_stopping=True,       # Kiểm soát overfitting bằng validation split
        validation_fraction=0.1,  # 10% dữ liệu train dùng làm validation
        n_iter_no_change=10,
        random_state=42
    )

    print("\nĐang huấn luyện mô hình MLPRegressor...")
    model.fit(X_train, y_train)
    print("Huấn luyện hoàn tất!")

    # Lưu Model (.pkl)
    model_path = os.path.join(BASE_DIR, "nn_model.pkl")
    joblib.dump(model, model_path)
    print(f"[Output] Đã lưu mô hình tại: nn_model.pkl")

    # biểu đồ Training / Validation Loss Curve
    plt.figure(figsize=(8, 5))
    plt.plot(model.loss_curve_, label='Training Loss', color='blue')
    if hasattr(model, 'validation_scores_') and model.validation_scores_ is not None:
        val_loss = [1 - score for score in model.validation_scores_]
        plt.plot(val_loss, label='Validation Loss (1 - score)', color='orange')
    plt.title('Neural Network Training History (Loss Curve)')
    plt.xlabel('Iterations')
    plt.ylabel('Loss')
    plt.legend()
    plt.grid(True)
    
    fig_path = os.path.join(BASE_DIR, "loss_curve.png")
    plt.savefig(fig_path)
    plt.close()
    print(f"[Output] Đã lưu biểu đồ training loss tại: loss_curve.png")

    # Dự báo trên cùng Test Set với baseline
    y_pred = model.predict(X_test)
    pred_df = pd.DataFrame({"y_pred": y_pred})
    pred_path = os.path.join(BASE_DIR, "pred_nn.csv")
    pred_df.to_csv(pred_path, index=False)
    print(f"[Output] Đã lưu kết quả dự báo tại: pred_nn.csv")

if __name__ == "__main__":
    main()