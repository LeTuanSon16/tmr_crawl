# thong_bao_crawler.py
# Giải pháp kết hợp Selenium và Scrapy trong một file

import os
import sys
import json
import time
import re
import pandas as pd
from urllib.parse import urljoin, urlparse

# Kiểm tra và cài đặt các gói cần thiết
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    import scrapy
    from scrapy.crawler import CrawlerProcess
except ImportError:
    print("Đang cài đặt các thư viện cần thiết...")
    os.system(f"{sys.executable} -m pip install selenium scrapy pandas openpyxl")
    print("Đã cài đặt xong, vui lòng chạy lại script này.")
    sys.exit(0)

# Biến toàn cục lưu danh sách URL từ tất cả các trang
ALL_URLS = []

# PHẦN 1: SELENIUM - THU THẬP TẤT CẢ URL
def collect_all_urls(excel_file):
    global ALL_URLS
    print("\n=== PHẦN 1: THU THẬP URL VỚI SELENIUM ===")
    
    # Đọc danh sách URL từ file Excel
    df = pd.read_excel(excel_file)
    base_urls = df['Link'].tolist()
    print(f"Đã đọc {len(base_urls)} URL từ file Excel")
    
    # Thiết lập Chrome driver
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36")
    chrome_options.add_argument("--ignore-certificate-errors")
    
    try:
        # Thử phương pháp 1: Tải driver tự động
        print("Đang khởi tạo ChromeDriver...")
        driver = webdriver.Chrome(options=chrome_options)
        print("Khởi tạo ChromeDriver thành công!")
    except Exception as e:
        try:
            # Thử phương pháp 2: Sử dụng webdriver-manager
            print(f"Lỗi khi khởi tạo driver: {e}")
            print("Thử phương pháp khác...")
            from webdriver_manager.chrome import ChromeDriverManager
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
            print("Khởi tạo ChromeDriver thành công với webdriver-manager!")
        except Exception as e2:
            print(f"Vẫn không thể khởi tạo driver: {e2}")
            print("Vui lòng cài đặt thư viện: pip install webdriver-manager")
            sys.exit(1)
    
    # Lưu tất cả các URL từ tất cả các trang
    all_urls = []
    
    try:
        for base_url in base_urls:
            if not base_url or not isinstance(base_url, str):
                continue
                
            print(f"Đang xử lý URL gốc: {base_url}")
            all_urls.append(base_url)  # Thêm URL trang đầu tiên
            
            # Truy cập URL gốc
            try:
                driver.get(base_url)
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(2)
            except Exception as e:
                print(f"Lỗi khi tải URL gốc {base_url}: {e}")
                continue
                
            # Xác định số trang tối đa
            max_pages = 20  # Giới hạn an toàn
            current_page = 1
            
            while current_page < max_pages:
                # Thử tìm các nút phân trang
                try:
                    pagination_found = False
                    
                    # Tìm các nút phân trang
                    pagination_links = driver.find_elements(By.CSS_SELECTOR, 
                                                "a#nextPage, a[href*='javascript:goToPage'], span a, a[href*='javascript:']")
                    
                    # Tìm nút dẫn đến trang tiếp theo
                    next_page = current_page + 1
                    for link in pagination_links:
                        try:
                            href = link.get_attribute("href")
                            text = link.text.strip()
                            
                            # Kiểm tra nếu là liên kết trang tiếp theo
                            if href and "javascript:goToPage" in href:
                                match = re.search(r'goToPage\((\d+)\)', href)
                                if match and int(match.group(1)) == next_page:
                                    print(f"Tìm thấy liên kết đến trang {next_page}")
                                    driver.execute_script("arguments[0].click();", link)
                                    time.sleep(3)
                                    all_urls.append(driver.current_url)
                                    pagination_found = True
                                    break
                            # Hoặc nếu là nút "Tiếp theo"
                            elif text in ["Tiếp", "Tiếp theo", "Next", ">", "»"]:
                                print(f"Tìm thấy nút '{text}'")
                                driver.execute_script("arguments[0].click();", link)
                                time.sleep(3)
                                all_urls.append(driver.current_url)
                                pagination_found = True
                                break
                        except:
                            continue
                    
                    # Nếu không tìm thấy nút phân trang, thử thay đổi URL
                    if not pagination_found:
                        current_url = driver.current_url
                        page_pattern = re.compile(r'/p(\d+)/')
                        match = page_pattern.search(current_url)
                        
                        if match:
                            current_pattern_page = int(match.group(1))
                            next_pattern_page = current_pattern_page + 1
                            next_url = current_url.replace(f'/p{current_pattern_page}/', f'/p{next_pattern_page}/')
                            
                            # Lưu URL hiện tại để có thể quay lại
                            old_url = driver.current_url
                            
                            print(f"Thử tải URL trang tiếp theo: {next_url}")
                            driver.get(next_url)
                            time.sleep(3)
                            
                            # Kiểm tra xem trang mới có dữ liệu không
                            if len(driver.find_elements(By.CSS_SELECTOR, "table.ta_border tr, table tr")) > 1:
                                all_urls.append(next_url)
                                pagination_found = True
                            else:
                                print("Trang mới không có dữ liệu, dừng phân trang")
                                driver.get(old_url)
                                time.sleep(2)
                                break
                        else:
                            print("Không thể xác định mẫu phân trang trong URL")
                            break
                    
                    # Nếu không tìm thấy trang tiếp theo bằng cả hai phương pháp, dừng lại
                    if not pagination_found:
                        print(f"Không tìm thấy trang {next_page}, dừng phân trang")
                        break
                    
                    current_page += 1
                    
                except Exception as e:
                    print(f"Lỗi khi xử lý phân trang: {e}")
                    break
    
    finally:
        driver.quit()
    
    # Loại bỏ URL trùng lặp
    unique_urls = list(dict.fromkeys(all_urls))
    print(f"Đã thu thập được {len(unique_urls)} URL duy nhất")
    
    # Lưu danh sách URL để sử dụng sau
    ALL_URLS = unique_urls
    
    # Lưu danh sách URL vào file để tham khảo sau này
    with open('all_page_urls.json', 'w', encoding='utf-8') as f:
        json.dump(unique_urls, f, ensure_ascii=False, indent=2)
    
    return unique_urls

class ThongBaoTongCucThueSpider(scrapy.Spider):
    name = 'thong_bao_tong_cuc_thue'
    
    custom_settings = {
        'FEEDS': {'thong_bao_tong_cuc_thue_data.csv': {'format': 'csv', 'encoding': 'utf-8-sig', 'overwrite': True}},
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 16,
        'DOWNLOAD_TIMEOUT': 30,
        'RETRY_TIMES': 3,
        'ROBOTSTXT_OBEY': False,
        'LOG_LEVEL': 'INFO',
    }
    
    def __init__(self, urls=None, *args, **kwargs):
        super(ThongBaoTongCucThueSpider, self).__init__(*args, **kwargs)
        self.start_urls = urls or []
        self.logger.info(f"Spider khởi tạo với {len(self.start_urls)} URLs")
    
    def parse(self, response):
        # Xử lý bảng dữ liệu
        rows = response.css('table.ta_border tr')
        
        # Nếu không tìm thấy bảng theo cách trên, thử các bộ chọn khác
        if len(rows) <= 1:
            rows = response.css('table tr')  # Thử với bất kỳ bảng nào
        
        # Bỏ qua hàng tiêu đề nếu có nhiều hơn một hàng
        if len(rows) > 1:
            data_rows = rows[1:]  # Bỏ qua hàng đầu tiên (hàng tiêu đề)
            
            for row in data_rows:
                cells = row.css('td')
                
                # Kiểm tra xem có đủ cột không
                if len(cells) >= 7:
                    # Cố gắng trích xuất văn bản từ các thẻ con nếu có
                    cell_values = []
                    for cell in cells:
                        # Thử lấy tất cả văn bản, kể cả từ thẻ con
                        all_text = ''.join(cell.css('*::text').getall()).strip()
                        if all_text:
                            cell_values.append(all_text)
                        else:
                            # Nếu không có văn bản từ thẻ con, lấy văn bản trực tiếp
                            cell_values.append(self.clean_text(cell.css('::text').get('')))
                    
                    # Đảm bảo có đủ giá trị
                    if len(cell_values) >= 7:
                        yield {
                            'url': response.url,
                            'stt': cell_values[0],
                            'mst': cell_values[1],
                            'ten_nnt': cell_values[2],
                            'so_tien_no_thue': cell_values[3],
                            'bien_phap_cuong_che': cell_values[4],
                            'so_thong_bao_cong_khai': cell_values[5],
                            'ngay_thong_bao_cong_khai': cell_values[6],
                        }
    
    def clean_text(self, text):
        """Xử lý và làm sạch văn bản"""
        if text:
            return text.strip().replace('\t', '').replace('\r', '').replace('\n', '')
        return ''


def extract_data_with_scrapy(urls):
    print("\n=== PHẦN 2: TRÍCH XUẤT DỮ LIỆU VỚI SCRAPY ===")
    print(f"Bắt đầu trích xuất dữ liệu từ {len(urls)} URLs...")
    
    # Thiết lập và chạy Scrapy Crawler
    process = CrawlerProcess()
    process.crawl(ThongBaoTongCucThueSpider, urls=urls)
    process.start()


def main():
    print("=== BẮT ĐẦU CRAWL DỮ LIỆU THÔNG BÁO TỔNG CỤC THUẾ ===")
    
    # Kiểm tra file Excel
    excel_file = 'Thông báo Tổng Cục Thuế.xlsx'
    if not os.path.exists(excel_file):
        print(f"Lỗi: Không tìm thấy file '{excel_file}'")
        print(f"Vui lòng đặt file trong thư mục: {os.getcwd()}")
        return
    
    # Đo thời gian thực hiện
    start_time = time.time()
    
    # Bước 1: Thu thập tất cả URLs với Selenium
    selenium_start = time.time()
    urls = collect_all_urls(excel_file)
    selenium_time = time.time() - selenium_start
    
    # Bước 2: Trích xuất dữ liệu với Scrapy
    scrapy_start = time.time()
    extract_data_with_scrapy(urls)
    scrapy_time = time.time() - scrapy_start
    
    # Tổng kết
    total_time = time.time() - start_time
    
    print("\n=== KẾT QUẢ ===")
    # Kiểm tra file đầu ra
    if os.path.exists('thong_bao_tong_cuc_thue_data.csv'):
        try:
            df = pd.read_csv('thong_bao_tong_cuc_thue_data.csv', encoding='utf-8-sig')
            print(f"Đã lưu {len(df)} bản ghi vào file CSV")
        except:
            print("Đã tạo file CSV nhưng không thể đọc để kiểm tra số lượng bản ghi")
    else:
        print("Cảnh báo: Không tìm thấy file CSV đầu ra")
    
    print("\n=== THỐNG KÊ THỜI GIAN ===")
    print(f"Thời gian thu thập URL (Selenium): {selenium_time:.2f} giây")
    print(f"Thời gian trích xuất dữ liệu (Scrapy): {scrapy_time:.2f} giây")
    print(f"Tổng thời gian: {total_time:.2f} giây")
    
    print("\n=== QUÁ TRÌNH HOÀN TẤT ===")
    

if __name__ == "__main__":
    main()


# https://www.gdt.gov.vn/wps/portal/Home/ntl/!ut/p/z1/jU_LboMwEPyWfsGaAEk5EisFWuooqtPEvkQuuIGGlxyD1L-vTSJVPYTG2sPs7MzsGjjsgTdiKI9Cl20jKtMzPj88h8EqXnqzNKLzAG1WAaVrHLiI-LAbBTgKY2-RIvToRQgl3nJNYrxxUOICv8ePbrwQ3eefEPDp-B3wUTL1g_8ymLlhcesGkwZvNkPJJpfqoL87CezaZKdG21nVihKfgOEXQlNLZHUO7CyFygrbDqJ6t1iomWPWWUFR4j674Fxo-aTa-jrpM1r0ZoeLfLPbMqLTxgvssyhcYZn6rC_iThwl6esPqYA5_himqyT_zaWtwV293e7Rl98NxP9Tr-HDDzhqMqU!/dz/d5/L2dBISEvZ0FBIS9nQSEh/p0/IZ7_JA9EHB42LGT690QE9TTOC93G00=CZ6_JA9EHB42LGT690QE9TTOC930N5=MDstb!mst!chiCuc=EcucThue!30500=fileid!5628A3F1FDC75F1D835057F6378FF986=render_type!render_cknt==/