"""
Workstream 3: Data Engineering - Lại Gia Huy
Proxy script chuyển tiếp thực thi đến workstream03/src/feature_pipeline.py.
Bảo toàn tính tương thích ngược cho các lệnh gọi từ root hoặc workstream03/.
"""
from pathlib import Path
import sys

SRC_DIR = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC_DIR))

from feature_pipeline import main, SeervadaFeaturePipeline, run_pipeline

if __name__ == "__main__":
    main()
