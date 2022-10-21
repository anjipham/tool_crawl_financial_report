from selenium.webdriver import Chrome
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
import re
import os
import requests
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.common.exceptions import WebDriverException


# for static sites
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')


#options = ChromeOptions()
#options.headless = True

#service = Service(executable_path=r'C:\WebDriver\bin\chromedriver')  # Local path tới chrome
driver = webdriver.Chrome('chromedriver',options=chrome_options)

# TODO: Suy nghĩ các lựa chọn để tối ưu
"""
1. 'https://finance.vietstock.vn/BCC/tai-tai-lieu.htm?doctype=1' => BCTC hay BCTN
2. pattern = "2021.*NAM"
2.1. năm
2.2. BCTC hay BCTN
"""

path = input("Nhập đường dẫn tới folder chứa file ví dụ: F:\8. data_practice\data_benkmark")  # Nhập liệu vào
file = input("Nhập tên file ví dụ: Ma_CK_Betong.xlsx")  # Nhập liệu
year = input("Nhập năm ví dụ: 2021")  # Nhập liệu

file_ma_ck = os.path.join(path, file)
df = pd.read_excel(file_ma_ck)
stocks = df['Mã CK Stockbiz + Vietstock']  # Giữ tên cột không đổi? Có thể fix lại hoặc nhắc nhở người dùng
#  dem vong
count = 0

for index, stock in enumerate(stocks):
    #  0. Tạo folder tương ứng chứa dữ liệu
    os.makedirs(path + '/' + str(df.iloc[index, 3]), exist_ok=True)  # tạo folder chứa file
    links = []

    # 1. Tải BCTC
    BCTC = 'https://finance.vietstock.vn//{}/tai-tai-lieu.htm?doctype=1'.format(stock)  # có thể fix lại cho gọn hơn
    driver.get(BCTC)
    #  presence_of_element_located expected condition wait for 8 seconds
    try:
        w = WebDriverWait(driver, 8)
        w.until(ec.presence_of_element_located((By.CLASS_NAME, "text-link")))
        print("Page load happened")
    except TimeoutException:
        print("Timeout happened no page load")

    #  Tìm link download
    soup = BeautifulSoup(driver.page_source, features="html.parser")
    elements_by_soup = soup.select('a.text-link')  # bs4.element.Tag'
    pattern = "{}.*NAM".format(year)
    for element in elements_by_soup:
        if re.search(pattern, element.get('href')):
            links.append(element.get('href'))  #  Tạo danh sách link download
            # TODO: Điền vào dánh sách tổng kết
            df.iloc[index, 4] = "yes"  #   Không tối ưu về mặt code do repeat nhiều lần; chưa chi tiết được loại và số lượng

    #  1.1. Download files
    for link in links:
        # Dem vong
        count += 1
        response = requests.get(link, stream=True)  # stream giúp tải được zip, ko hiểu sao luôn! => stream set no limit
        #  Test lai repsonse xem co bi set gioi han request ko
        print("Vong : " + str(count) + " Trang thai: " + str(response.status_code) + " link: " + link)
        pdfFile = open(
            os.path.join(path + '/' + str(df.iloc[index, 3]), os.path.basename(link)), 'wb')
        for chunk in response.iter_content(100000):
            pdfFile.write(chunk)
        pdfFile.close()

    links = []
    # 2. Download BCTN
    BCTN = 'https://finance.vietstock.vn//{}/tai-tai-lieu.htm?doctype=2'.format(stock)
    driver.get(BCTN)  # Thay đổi pattern
    #  presence_of_element_located expected condition wait for 8 seconds
    try:
        w = WebDriverWait(driver, 8)
        w.until(ec.presence_of_element_located((By.CLASS_NAME, "text-link")))
        print("Page load happened")
    except TimeoutException:
        print("Timeout happened no page load")

    soup = BeautifulSoup(driver.page_source, features="html.parser")
    elements_by_soup = soup.select('a.text-link')  # bs4.element.Tag'
    pattern = "{}".format(year)  # Thay đổi pattern
    for element in elements_by_soup:
        if re.search(pattern, element.get('href')):
            links.append(element.get('href'))
            # TODO: Điền vào dánh sách tổng kết
            df.iloc[index,5] = "yes"  # Không tối ưu về mặt code do repeat nhiều lần; chưa chi tiết được loại và số lượng

    #  Tối ưu phần tải BCTN bằng việc: Giữ nguyên link thay đổi năm, mã ck, lấy cấu trúc link của BCTC,type file.
    #  Không thể tối ưu được do, link của BCTC và BCTN có thay đổi cấu trúc về thị trường như t/h BIG

    #  3. Tải file về folder dựa trên link đã lọc
    for link in links:
        # Dem vong
        count += 1
        response = requests.get(link, stream=True)  # stream giúp tải được zip, ko hiểu sao luôn!
        #  Test lai repsonse xem co bi set gioi han request ko
        print("Vong : " + str(count) + " Trang thai: " + str(response.status_code) + " link: " + link)
        pdfFile = open(
            os.path.join(path + '/' + str(df.iloc[index, 3]), os.path.basename(link)), 'wb')
        for chunk in response.iter_content(100000):
            pdfFile.write(chunk)
        pdfFile.close()

driver.quit()

# 4 Ghi và lưu file kết quả
result = 'result.xlsx'
Name = os.path.join(path, result)
df.to_excel(Name, index=False, header=True)
