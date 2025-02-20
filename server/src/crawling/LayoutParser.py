import os
import pandas as pd
from dotenv import load_dotenv
from langchain_upstage import UpstageLayoutAnalysisLoader

# 환경변수 로드
load_dotenv()

# 이미지 및 CSV 경로 설정
image_dir = "../data/images"
csv_file_path = "../data/mjc_image_data.csv"

def parse_images():
    # 결과를 저장할 리스트
    image_data = []

    # 이미지 파일들을 순차적으로 처리
    for img_file in os.listdir(image_dir):
        img_path = os.path.join(image_dir, img_file)
        
        if img_file.endswith(('.jpg', '.jpeg', '.png')):  # 이미지 파일인지 확인
            print(f"Processing {img_file}...")

            # 문서 로더 설정
            loader = UpstageLayoutAnalysisLoader(
                img_path,
                output_type="text",
                split="page",
                use_ocr=True,
                exclude=["header", "footer"],
            )

            # 문서 로드
            docs = loader.load()

            # 임시 제목 처리 (필요에 따라 수정)
            title = os.path.splitext(img_file)[0]

            # 각 이미지에서 추출된 텍스트를 리스트에 추가
            for doc in docs:
                image_data.append({
                    "image": img_file, 
                    "text": doc, 
                    "title": title
                })

    # 데이터를 DataFrame으로 변환
    df = pd.DataFrame(image_data)

    # CSV 파일로 저장
    df.to_csv(csv_file_path, index=False, encoding="utf-8-sig")

    print(f"텍스트가 '{csv_file_path}'로 저장되었습니다.")
    return df

if __name__ == "__main__":
    parse_images()