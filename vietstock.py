import re
import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import Chrome
from selenium.webdriver import ChromeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException


# set options for selenium can performance on colab
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

driver = webdriver.Chrome('chromedriver',options=chrome_options)

# TODO: Suy nghĩ các lựa chọn để tối ưu
path = input("Nhập đường dẫn tới folder chứa file data\n")  # Nhập liệu
file = input("Nhập tên file ví dụ: Ma_CK_Betong.xlsx\n")  # Nhập liệu
year = input("Nhập năm muốn lấy báo cáo, ví dụ: 2021\n")  # Nhập liệu

file_ma_ck = os.path.join(path, file)
df = pd.read_excel(file_ma_ck)
stocks = df['Mã CK Stockbiz + Vietstock']  #
#  dem vong
count = 0

for index, stock in enumerate(stocks):
    #  0. Tạo folder tương ứng cty đã mã hóa chứa dữ liệu BCTC sẽ tải về
    os.makedirs(path + '/' + str(df.iloc[index, 3]), exist_ok=True)

    # 1. crawl link download BCTC
    BCTC = 'https://finance.vietstock.vn//{}/tai-tai-lieu.htm?doctype=1'.format(stock)  # có thể fix lại cho gọn hơn
    driver.get(BCTC)
    #  presence_of_element_located expected condition wait for 8 seconds
    try:
        w = WebDriverWait(driver, 8)
        w.until(ec.presence_of_element_located((By.CLASS_NAME, "text-link")))
        print("Page load happened")
    except TimeoutException:
        print("Timeout happened no page load")

    #  Tìm link download từ html đã load by selenium
    soup = BeautifulSoup(driver.page_source, features="html.parser")
    elements_by_soup = soup.select('a.text-link')
    pattern = "{}.*NAM".format(year)    # set pattern mong muốn 
    links = []  # Tạo list để chứa links tìm được
    
    for element in elements_by_soup:
        if re.search(pattern, element.get('href')):
            links.append(element.get('href'))  # Tạo danh sách link download
            df.iloc[index, 4] = "yes"          # Điền vào dánh sách tổng kết

    # 2. crawl link download BCTN
    BCTN = 'https://finance.vietstock.vn//{}/tai-tai-lieu.htm?doctype=2'.format(stock)
    driver.get(BCTN)  # Thay đổi pattern
    #  presence_of_element_located expected condition wait for 8 seconds
    try:
        w = WebDriverWait(driver, 8)
        w.until(ec.presence_of_element_located((By.CLASS_NAME, "text-link")))
        print("Page load happened")
    except TimeoutException:
        print("Timeout happened no page load")
        
    #  Tìm link download từ html đã load by selenium
    soup = BeautifulSoup(driver.page_source, features="html.parser")
    elements_by_soup = soup.select('a.text-link')  # bs4.element.Tag'
    pattern = "{}".format(year)  # Thay đổi pattern
    
    for element in elements_by_soup:
        if re.search(pattern, element.get('href')):
            links.append(element.get('href'))       # Tạo danh sách link download          
            df.iloc[index,5] = "yes"                # Điền vào dánh sách tổng kết
            
    #  3. Tải file về folder dựa trên links đã lọc
    for link in links:
        # Dem vong
        count += 1
        response = requests.get(link, stream=True)
        print("Vong : " + str(count) + " Trang thai: " + str(response.status_code) + " link: " + link)
        pdfFile = open(
            os.path.join(path + '/' + str(df.iloc[index, 3]), os.path.basename(link)), 'wb')
        for chunk in response.iter_content(100000):
            pdfFile.write(chunk)
        pdfFile.close()

driver.quit()

# 4 Ghi và lưu file danh sách kết quả
result = 'result.xlsx'
Name = os.path.join(path, result)
df.to_excel(Name, index=False, header=True)
