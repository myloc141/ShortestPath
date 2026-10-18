"""
Workstream 3: Data Engineering - Lại Gia Huy (MSSV: K24419)
Unit Tests: test_artifact_contract.py
Kiểm thử tính toàn vẹn của hợp đồng bàn giao artifacts và checksum SHA-256.
"""

from pathlib import Path
import hashlib
import json
import pandas as pd
import pytest

TEST_DIR = Path(__file__).resolve().parent
WS3_DIR = TEST_DIR.parent
DATA_PROCESSED_DIR = WS3_DIR / "data" / "processed"
DATA_RAW_DIR = WS3_DIR / "data" / "raw"

EXPECTED_HASHES = {
    "train.csv": "25cbf4050e916280bdcbd298e1cb8fe81a0776991c115d485efe53b12bf5bd21",
    "test.csv": "460da2f86a3e8ea0c395da2f2214e4dc3a0ee893471940754046c756658e97df",
    "X_train_preprocessed.csv": "4f42865e1e8f26b991dbfd3b786a4b829adfa2cc8bf86ca93a3fb427e471b24e",
    "X_test_preprocessed.csv": "181c0544eb2c0518022772de00ec79bb9368afe68b3d3e7ef6153ef11be5e5e2",
    "y_train.csv": "ad8f5dc7ba16af7cac7f2c147f7dc4a3e4d9bf01eaea986b7fd8af55a971aac9",
    "y_test.csv": "c3fab4791e1e7d127cc1c22bf78e9a601c8eff422c07184e8125457018e24b85",
    "preprocessing_pipeline.json": "9420f3e79c3161a6424d94d193e46c5e4294b3892f9ba95d62799d85a54f9fd9",
    "seervada_network.csv": "0afa87aa1a2189054848b008e7fd0b5c40e1b86b7867379afbc526ae6c3e3d17",
    "seervada_rcsp_teaching.csv": "c3c864a0a1f39d7613ec34f18bcb288167622f74961e8275dc52d402e4cd6830",
    "seervada_travel_time_SIMULATED.csv": "19c1391ec53141069136657597e9557bbad33c4e716c0ca6cbf91d50f936c501",
    "seervada_travel_time_EXTENDED_NN.csv": "2927b836f5fd86c3127aaa4fcca422df2af2afc492f26d8a46dee1c846202e91"
}

def calculate_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

@pytest.mark.parametrize("filename,expected_sha", EXPECTED_HASHES.items())
def test_artifact_sha256_checksum(filename, expected_sha):
    # Tìm file ở thư mục con tương ứng hoặc ở root workstream03
    candidates = [
        DATA_PROCESSED_DIR / filename,
        DATA_RAW_DIR / filename,
        WS3_DIR / filename
    ]
    target_file = None
    for c in candidates:
        if c.exists():
            target_file = c
            break
            
    assert target_file is not None, f"Không tìm thấy artifact bàn giao: {filename}"
    actual_sha = calculate_sha256(target_file)
    assert actual_sha == expected_sha, (
        f"LỖI TOÀN VẸN ARTIFACT {filename}: SHA-256 bị thay đổi!\n"
        f"Kỳ vọng: {expected_sha}\n"
        f"Thực tế: {actual_sha}"
    )

def test_dataframe_shapes():
    p = DATA_PROCESSED_DIR if (DATA_PROCESSED_DIR / "train.csv").exists() else WS3_DIR
    assert pd.read_csv(p / "train.csv").shape == (1440, 10)
    assert pd.read_csv(p / "test.csv").shape == (360, 10)
    assert pd.read_csv(p / "X_train_preprocessed.csv").shape == (1440, 26)
    assert pd.read_csv(p / "X_test_preprocessed.csv").shape == (360, 26)
    assert pd.read_csv(p / "y_train.csv").shape == (1440, 1)
    assert pd.read_csv(p / "y_test.csv").shape == (360, 1)
