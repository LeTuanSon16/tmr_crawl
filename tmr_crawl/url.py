# url_collector.py
# Sử dụng Selenium để thu thập tất cả URL và lưu vào file

import os
import sys
import json
import time
import re
import pandas as pd

# Kiểm tra và cài đặt thư viện cần thiết
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except ImportError:
    print("Đang cài đặt thư viện cần thiết...")
    os.system(f"{sys.executable} -m pip install selenium pandas openpyxl")
    print("Đã cài đặt xong, vui lòng chạy lại script này.")
    sys.exit(0)

# Hàm lưu URLs vào file
def save_urls_to_file(urls, filename):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(urls, f, ensure_ascii=False, indent=2)
        print(f"Đã lưu {len(urls)} URLs vào file {filename}")
        
        # Lưu file text riêng để dễ kiểm tra
        with open(f"{os.path.splitext(filename)[0]}.txt", 'w', encoding='utf-8') as f:
            for url in urls:
                f.write(f"{url}\n")
    except Exception as e:
        print(f"Lỗi khi lưu file {filename}: {e}")

# Hàm thu thập tất cả URLs
def collect_all_urls(excel_file):
    print("\n=== THU THẬP URL VỚI SELENIUM ===")
    
    # Đọc danh sách URL từ file Excel
    df = pd.read_excel(excel_file)
    base_urls = df['Link'].tolist()
    print(f"Đã đọc {len(base_urls)} URL từ file Excel")
    
    # Thiết lập Chrome driver
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/91.0.4472.124")
    chrome_options.add_argument("--ignore-certificate-errors")
    
    # Thu thập URLs từ tất cả các trang
    all_urls = []
    
    try:
        # Khởi tạo driver
        try:
            driver = webdriver.Chrome(options=chrome_options)
            print("Khởi tạo ChromeDriver thành công!")
        except Exception as e:
            print(f"Lỗi khởi tạo driver thông thường: {e}")
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
                print("Khởi tạo ChromeDriver thành công với webdriver-manager!")
            except Exception as e2:
                print(f"Không thể khởi tạo driver: {e2}")
                print("Vui lòng cài đặt thư viện: pip install webdriver-manager")
                return []
        
        # Tạo thư mục để lưu URL cho mỗi URL gốc
        urls_dir = "urls_by_source"
        os.makedirs(urls_dir, exist_ok=True)
        
        # Xử lý từng URL gốc
        for i, base_url in enumerate(base_urls):
            if not base_url or not isinstance(base_url, str):
                continue
                
            print(f"\n[{i+1}/{len(base_urls)}] Đang xử lý: {base_url}")
            current_urls = [base_url]  # Lưu URL gốc và các URL phân trang
            
            # Truy cập URL gốc
            try:
                driver.get(base_url)
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(2)
                
                # Lưu URL gốc vào danh sách tổng
                all_urls.append(base_url)
                
                # Xử lý phân trang
                max_pages = 20  # Giới hạn an toàn
                current_page = 1
                
                while current_page < max_pages:
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
                                is_next_page = False
                                if href and "javascript:goToPage" in href:
                                    match = re.search(r'goToPage\((\d+)\)', href)
                                    if match and int(match.group(1)) == next_page:
                                        is_next_page = True
                                # Hoặc nếu là nút "Tiếp theo"
                                elif text in ["Tiếp", "Tiếp theo", "Next", ">", "»"]:
                                    is_next_page = True
                                
                                if is_next_page:
                                    print(f"  - Tìm thấy trang {next_page}, đang click...")
                                    # Lưu URL hiện tại trước khi click
                                    before_url = driver.current_url
                                    
                                    # Click vào nút phân trang
                                    driver.execute_script("arguments[0].click();", link)
                                    time.sleep(3)  # Đợi trang tải xong
                                    
                                    # Kiểm tra URL mới
                                    after_url = driver.current_url
                                    page_url = after_url
                                    
                                    # Nếu URL không thay đổi, thêm tham số page để phân biệt
                                    if before_url == after_url:
                                        if "#page=" in before_url:
                                            page_url = before_url.split("#page=")[0] + f"#page={next_page}"
                                        else:
                                            page_url = before_url + f"#page={next_page}"
                                        print(f"  - URL không thay đổi, sử dụng: {page_url}")
                                    
                                    # Kiểm tra xem trang mới có bảng dữ liệu không
                                    table_exists = len(driver.find_elements(By.CSS_SELECTOR, "table.ta_border tr, table tr")) > 1
                                    
                                    if table_exists:
                                        print(f"  - Tìm thấy bảng dữ liệu trên trang {next_page}")
                                        # Lưu URL mới vào danh sách
                                        current_urls.append(page_url)
                                        all_urls.append(page_url)
                                        
                                        # Lưu danh sách URL hiện tại
                                        url_filename = f"urls_{i+1}.json"
                                        save_urls_to_file(current_urls, os.path.join(urls_dir, url_filename))
                                        
                                        pagination_found = True
                                        break
                                    else:
                                        print(f"  - Không tìm thấy bảng dữ liệu trên trang {next_page}")
                            except Exception as e:
                                print(f"  - Lỗi khi xử lý nút phân trang: {e}")
                                continue
                        
                        # Nếu không tìm thấy nút phân trang, thử thay đổi URL trực tiếp
                        if not pagination_found:
                            current_url = driver.current_url
                            page_pattern = re.compile(r'/p(\d+)/')
                            match = page_pattern.search(current_url)
                            
                            if match:
                                # Thử tạo URL mới bằng cách thay đổi tham số p
                                current_pattern_page = int(match.group(1))
                                next_url = current_url.replace(f'/p{current_pattern_page}/', f'/p{current_pattern_page + 1}/')
                                
                                # Lưu URL hiện tại để có thể quay lại
                                old_url = driver.current_url
                                
                                print(f"  - Thử tải URL trang tiếp theo: {next_url}")
                                driver.get(next_url)
                                time.sleep(3)
                                
                                # Kiểm tra xem trang mới có bảng dữ liệu không
                                table_exists = len(driver.find_elements(By.CSS_SELECTOR, "table.ta_border tr, table tr")) > 1
                                
                                if table_exists:
                                    print(f"  - Tìm thấy bảng dữ liệu trên URL mới")
                                    # Lưu URL mới vào danh sách
                                    current_urls.append(next_url)
                                    all_urls.append(next_url)
                                    
                                    # Lưu danh sách URL hiện tại
                                    url_filename = f"urls_{i+1}.json"
                                    save_urls_to_file(current_urls, os.path.join(urls_dir, url_filename))
                                    
                                    pagination_found = True
                                else:
                                    print(f"  - Không tìm thấy bảng dữ liệu trên URL mới")
                                    driver.get(old_url)
                                    time.sleep(2)
                                    break
                            else:
                                print(f"  - Không thể xác định mẫu phân trang trong URL")
                                break
                        
                        # Nếu không tìm thấy trang tiếp theo, dừng lại
                        if not pagination_found:
                            print(f"  - Không tìm thấy trang {next_page}, dừng phân trang")
                            break
                        
                        # Tăng số trang hiện tại
                        current_page += 1
                    
                    except Exception as e:
                        print(f"  - Lỗi khi xử lý phân trang: {e}")
                        # Lưu URLs hiện tại trước khi dừng
                        url_filename = f"urls_{i+1}.json"
                        save_urls_to_file(current_urls, os.path.join(urls_dir, url_filename))
                        break
                
                # Lưu URLs cho URL gốc này
                url_filename = f"urls_{i+1}.json"
                save_urls_to_file(current_urls, os.path.join(urls_dir, url_filename))
                print(f"  - Đã thu thập {len(current_urls)} URLs (bao gồm cả phân trang)")
                
                # Lưu danh sách tất cả URLs sau mỗi URL gốc
                save_urls_to_file(all_urls, "all_page_urls.json")
                
            except Exception as e:
                print(f"  - Lỗi khi xử lý URL {base_url}: {e}")
                continue
    
    finally:
        try:
            driver.quit()
            print("\nĐã đóng trình duyệt")
        except:
            pass
    
    # Loại bỏ URL trùng lặp
    unique_urls = list(dict.fromkeys(all_urls))
    
    # Lưu danh sách URL vào file lần cuối
    save_urls_to_file(unique_urls, "all_page_urls.json")
    
    print(f"\nĐã thu thập được tổng cộng {len(unique_urls)} URL duy nhất")
    return unique_urls

# Hàm chính
def main():
    print("=== THU THẬP TẤT CẢ URL THÔNG BÁO TỔNG CỤC THUẾ ===")
    
    # Kiểm tra file Excel
    excel_file = 'Thông báo Tổng Cục Thuế.xlsx'
    
    if not os.path.exists(excel_file):
        print(f"Lỗi: Không tìm thấy file '{excel_file}'")
        return
    
    # Thu thập tất cả URLs với Selenium
    collect_all_urls(excel_file)
    
    print("\n=== HOÀN THÀNH THU THẬP URL ===")
    print("Bạn có thể chạy script scrapy_extractor.py để trích xuất dữ liệu từ các URL này")

if __name__ == "__main__":
    main()