import os
import pandas as pd

# 경로 설정
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATHS = {
    "notice": os.path.join(CURRENT_DIR, "../../data/csv/mjc_notice.csv"),
    "academic": os.path.join(CURRENT_DIR, "../../data/csv/mjc_academic.csv"),
    "scholarship": os.path.join(CURRENT_DIR, "../../data/csv/mjc_scholarship.csv"),
    "recruitment": os.path.join(CURRENT_DIR, "../../data/csv/mjc_recruitment.csv"),
    "promotion": os.path.join(CURRENT_DIR, "../../data/csv/mjc_promotion.csv"),
}
MERGED_CSV_PATH = os.path.join(CURRENT_DIR, "../../data/csv/mjc_combined_data.csv")

def check_file_exists(file_path):
    """파일 경로 확인"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"파일이 존재하지 않습니다: {file_path}")

def merge_csv_files(csv_paths, output_path):
    """여러 CSV 파일을 하나로 병합"""
    dataframes = []
    for path in csv_paths.values():
        check_file_exists(path)
        try:
            df = pd.read_csv(path, encoding="utf-8")
        except UnicodeDecodeError:
            df = pd.read_csv(path, encoding="cp949")
        dataframes.append(df)
    merged_df = pd.concat(dataframes, ignore_index=True)
    merged_df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"병합된 CSV 파일이 '{output_path}'에 저장되었습니다.")

if __name__ == "__main__":
    # CSV 파일 병합
    merge_csv_files(CSV_PATHS, MERGED_CSV_PATH)
