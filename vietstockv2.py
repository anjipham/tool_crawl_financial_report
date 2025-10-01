import re
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException

# ----------------------
# Cấu hình selenium
# ----------------------
service = Service(executable_path=r'/usr/bin/chromedriver')
options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(service=service, options=options)

# ----------------------
# Thông số mặc định
# ----------------------
d_path = "/content/drive/MyDrive/repository"
d_file = "stock_list.xlsx"
d_year = "2021"

path = input("Nhập đường dẫn tới folder chứa file data\n") or d_path
file = input("Nhập tên file chứa danh sách mã chứng khoán đã upload\n") or d_file
year = input("Nhập năm muốn lấy báo cáo tài chính\n") or d_year

file_ma_ck = os.path.join(path, file)
df = pd.read_excel(file_ma_ck)
stocks = df['Mã CK Stockbiz + Vietstock']

# Thêm cột mới nếu chưa có
for col in ["Có BCTC", "Có BCTN", "Link BCTC", "Link BCTN"]:
    if col not in df.columns:
        df[col] = ""

# ----------------------
# Tạo 2 folder tổng
# ----------------------
bctc_folder = os.path.join(path, "BCTC")
bctn_folder = os.path.join(path, "BCTN")
os.makedirs(bctc_folder, exist_ok=True)
os.makedirs(bctn_folder, exist_ok=True)

# ----------------------
# Hàm crawl link
# ----------------------
def get_links(url, pattern):
    driver.get(url)
    try:
        WebDriverWait(driver, 8).until(ec.presence_of_element_located((By.CLASS_NAME, "text-link")))
    except TimeoutException:
        print(f"Timeout tại {url}")
        return []
    soup = BeautifulSoup(driver.page_source, "html.parser")
    return [a.get('href') for a in soup.select('a.text-link') if re.search(pattern, a.get('href'))]

# ----------------------
# Bắt đầu crawl
# ----------------------
count = 0
for index, stock in enumerate(stocks):
    stock_code = str(df.iloc[index, 3])  # Lấy mã công ty

    # Crawl BCTC (doctype=1)
    bctc_url = f'https://finance.vietstock.vn/{stock.strip()}/tai-tai-lieu.htm?doctype=1'
    links_bctc = get_links(bctc_url, f"{year}.*NAM")
    if links_bctc:
        df.loc[index, "Có BCTC"] = "yes"
        df.loc[index, "Link BCTC"] = "; ".join(links_bctc)

    # Crawl BCTN (doctype=2)
    bctn_url = f'https://finance.vietstock.vn/{stock.strip()}/tai-tai-lieu.htm?doctype=2'
    links_bctn = get_links(bctn_url, f"{year}")
    if links_bctn:
        df.loc[index, "Có BCTN"] = "yes"
        df.loc[index, "Link BCTN"] = "; ".join(links_bctn)

    # Download tất cả file
    for link in links_bctc + links_bctn:
        count += 1
        try:
            response = requests.get(link, stream=True, timeout=15)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Lỗi tải {link}: {e}")
            continue

        # Đặt tên file
        loai_bc = "BCTC" if "doctype=1" in link else "BCTN"
        file_name = f"{stock_code}_{loai_bc}_{year}_{os.path.basename(link)}"

        # Lưu đúng folder
        save_path = os.path.join(bctc_folder if loai_bc == "BCTC" else bctn_folder, file_name)
        with open(save_path, 'wb') as pdfFile:
            for chunk in response.iter_content(100000):
                pdfFile.write(chunk)

        print(f"Loop {count}: Đã lưu {save_path}")

driver.quit()

# ----------------------
# Lưu kết quả cuối
# ----------------------
result = os.path.join(path, "result.xlsx")
df.to_excel(result, index=False, header=True)
print("Hoàn tất, kết quả lưu tại:", result)
