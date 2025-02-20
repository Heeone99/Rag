import os
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import uuid
import re
import hashlib
import pandas as pd
from langchain_upstage import UpstageLayoutAnalysisLoader

# 환경 변수 로드
load_dotenv()

BASE_URL = 'https://www.mjc.ac.kr'
CATEGORY_IMAGE_DIRS = {
    "66": "../../data/images/notice",
    "169": "../../data/images/academic",
    "208": "../../data/images/scholarship",
    "2617": "../../data/images/recruitment",
    "2711": "../../data/images/promotion",
}
CATEGORY_PATHS = {
    "66": "../../data/csv/mjc_notice.csv",
    "169": "../../data/csv/mjc_academic.csv",
    "208": "../../data/csv/mjc_scholarship.csv",
    "2617": "../../data/csv/mjc_recruitment.csv",
    "2711": "../../data/csv/mjc_promotion.csv",
}

for image_dir in CATEGORY_IMAGE_DIRS.values():
    os.makedirs(image_dir, exist_ok=True)

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def get_extension_from_content_type(content_type):
    extensions = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/gif': '.gif'}
    return extensions.get(content_type, '.jpg')

def extract_links(soup, menu_idx):
    elements = soup.find_all(class_='cell_type01')
    links = []
    for element in elements:
        a_tag = element.find('a')
        if a_tag:
            href = a_tag.get('href')
            if href and href.startswith('javascript:'):
                parts = href.split("'")
                if len(parts) >= 3:
                    bm_id, bd_id = parts[1], parts[3]
                    links.append({"url": f"{BASE_URL}/bbs/data/view.do?pageIndex=1&SC_KEY=&SC_KEYWORD=&bbs_mst_idx={bm_id}&menu_idx={menu_idx}&tabCnt=&per_menu_idx=&submenu_idx=&data_idx={bd_id}&memberAuth=Y"})
            elif href:
                links.append({"url": href})
    return links

def extract_content(link, downloaded_images, image_dir):
    """
    Extracts title, content, date, and images from the given link.
    """
    try:
        response = requests.get(link, timeout=10)
        response.encoding = 'utf-8'

        if response.status_code != 200:
            return {"error": f"Failed to retrieve content (status code: {response.status_code})"}

        soup = BeautifulSoup(response.text, 'html.parser')

        # 제목 추출
        title = soup.find("h2", class_="tit").get_text(strip=True) if soup.find("h2", class_="tit") else "제목 없음"

        # 내용 추출
        content_text = soup.find("div", class_="memo", id="divMemo").get_text(strip=True) if soup.find("div", class_="memo", id="divMemo") else "Content not found"

        # 날짜 추출
        date = next((td.get_text(strip=True) for td in soup.find("table", class_="tbl_data").find_all("td") if re.match(r"\d{4}-\d{2}-\d{2}", td.get_text(strip=True))), "날짜 없음")

        # 이미지 다운로드 및 OCR
        images = soup.find("div", class_="memo", id="divMemo").find_all("img") if soup.find("div", class_="memo", id="divMemo") else []
        context_data = content_text  # 초기 context는 content_text로 설정

        for img in images:
            img_url = img.get("src")
            if not img_url:
                continue
            if not img_url.startswith("http"):
                img_url = f"{BASE_URL}{img_url}"

            # 이미지 URL의 해시 계산
            img_hash = hashlib.md5(img_url.encode('utf-8')).hexdigest()

            # 중복 확인: 이미 다운로드된 이미지라면 건너뜀
            if img_hash in downloaded_images:
                continue

            img_response = requests.get(img_url, stream=True, timeout=10)
            if img_response.status_code != 200:
                continue

            content_type = img_response.headers.get('Content-Type', '')
            extension = get_extension_from_content_type(content_type)
            unique_name = f"{img_hash}_{sanitize_filename(os.path.basename(img_url).split('?')[0])}{extension}"
            img_path = os.path.join(image_dir, unique_name)

            os.makedirs(os.path.dirname(img_path), exist_ok=True)  # Ensure directory exists

            with open(img_path, 'wb') as img_file:
                for chunk in img_response.iter_content(1024):
                    img_file.write(chunk)

            # 다운로드된 이미지 해시 추가
            downloaded_images.add(img_hash)

            # OCR 및 텍스트 파싱
            loader = UpstageLayoutAnalysisLoader(
                img_path,
                output_type="text",
                split="page",
                use_ocr=True,
                exclude=["header", "footer"],
            )
            docs = loader.load()
            for doc in docs:
                context_data += f"\n{str(doc)}"  # context에 OCR 결과 추가
                break  # 첫 번째 문서만 처리

        return {
            "title": title,
            "context": context_data,
            "date": date,
            "link": link
        }
    except Exception as e:
        return {"error": f"오류 발생: {e}"}

def download_images_and_extract_content(links, menu_idx):
    combined_data = []
    downloaded_images = set()
    image_dir = CATEGORY_IMAGE_DIRS[menu_idx]

    for link_info in links:
        link = link_info["url"]
        result = extract_content(link, downloaded_images, image_dir)
        if "error" in result:
            print(f"오류: {result['error']} (링크: {link})")
            continue

        combined_data.append({
            "title": result["title"],
            "context": result["context"],
            "date": result["date"],
            "link": result["link"]
        })
    return combined_data

def main():
    for menu_idx, csv_path in CATEGORY_PATHS.items():
        try:
            url = f'{BASE_URL}/bbs/data/list.do?pageIndex=1&SC_KEY=&SC_KEYWORD=&bbs_mst_idx=BM0000002205&menu_idx={menu_idx}&tabCnt=&per_menu_idx=&submenu_idx=&data_idx=&memberAuth=Y'
            response = requests.get(url)
            response.encoding = 'utf-8'

            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                links = extract_links(soup, menu_idx)
                print(f"\n총 추출된 링크 수 (menu_idx={menu_idx}): {len(links)}")

                combined_data = download_images_and_extract_content(links, menu_idx)
                print(f"\n총 처리된 게시물 수 (menu_idx={menu_idx}): {len(combined_data)}")

                # DataFrame으로 변환 후 CSV로 저장
                df = pd.DataFrame(combined_data)
                os.makedirs(os.path.dirname(csv_path), exist_ok=True)
                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                print(f"결과가 '{csv_path}'에 저장되었습니다.")
            else:
                print(f"페이지 요청 실패 (menu_idx={menu_idx}): {response.status_code}")
        except Exception as e:
            print(f"크롤링 중 오류 발생 (menu_idx={menu_idx}): {e}")

if __name__ == "__main__":
    main()
