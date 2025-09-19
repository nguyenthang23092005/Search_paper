import os
import json
import re
import time
from datetime import datetime
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options


class ScholarFinder:
    def __init__(self):
        self.driver = None

    def setup_browser(self):
        """Setup Chrome browser với các tùy chọn an toàn"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return self.driver

    def extract_pub_date(self, authors_text: str):
        """
        Lấy năm xuất bản từ chuỗi thông tin tác giả trên Google Scholar
        """
        year_match = re.search(r'\b(19|20)\d{2}\b', authors_text)
        if year_match:
            return year_match.group(0)
        return "Not Available"

    def get_paper_details_from_link(self, paper_url: str, paper_rank: int) -> Dict:
        """
        Mở link bài báo để lấy đầy đủ title và abstract
        """
        print(f"Accessing paper {paper_rank}: {paper_url}")
        try:
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.get(paper_url)
            time.sleep(4)

            title = "Not Available"
            abstract = "Not Available"

            # Title selectors
            title_selectors = [
                "h1", "h2", ".title", "#title",
                "h1[class*='title']", "h2[class*='title']",
                ".paper-title", ".article-title",
                ".entry-title", ".post-title"
            ]
            for selector in title_selectors:
                try:
                    title_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if title_element.text.strip() and len(title_element.text.strip()) > 10:
                        title = title_element.text.strip()
                        break
                except:
                    continue

            # Abstract selectors
            abstract_selectors = [
                ".abstract", "#abstract", "[class*='abstract']",
                ".summary", "#summary", "[class*='summary']",
                "p[class*='abstract']", "div[class*='abstract']",
                ".paper-abstract", ".article-abstract",
                "section[class*='abstract']", "[id*='abstract']"
            ]
            for selector in abstract_selectors:
                try:
                    abstract_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    if abstract_element.text.strip() and len(abstract_element.text.strip()) > 50:
                        abstract = abstract_element.text.strip()
                        break
                except:
                    continue

            # Nếu vẫn chưa tìm thấy abstract -> thử tìm trong các đoạn văn dài
            if abstract == "Not Available":
                try:
                    paragraphs = self.driver.find_elements(By.TAG_NAME, "p")
                    for p in paragraphs:
                        text = p.text.strip()
                        if len(text) > 100 and any(word in text.lower() for word in
                                                    ['abstract', 'this paper', 'this study', 'we present', 'we propose']):
                            abstract = text
                            break
                except:
                    pass

            # Đóng tab hiện tại, quay về tab chính
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])

            return {
                "title": title,
                "abstract": abstract,
                "url": paper_url,
                "access_status": "success" if title != "Not Available" else "failed"
            }

        except Exception as e:
            print(f"Error accessing paper {paper_rank}: {e}")
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
            except:
                pass
            return {
                "title": "Error accessing paper",
                "abstract": f"Error: {str(e)}",
                "url": paper_url,
                "access_status": "error"
            }

    def search_google_scholar(self, search_query: str, max_papers: int = 5) -> List[Dict]:
        """
        Tìm kiếm Google Scholar và trả về danh sách bài báo mới nhất
        """
        print(f"Searching Google Scholar for: {search_query}")
        self.driver.get("https://scholar.google.com")
        time.sleep(3)

        # Nhập từ khóa vào ô tìm kiếm
        search_box = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        search_box.clear()
        search_box.send_keys(search_query)

        # Nhấn nút tìm kiếm
        self.driver.find_element(By.XPATH, "//button[@type='submit']").click()
        time.sleep(4)

        # Nhấn "Sort by date" nếu có
        try:
            # Chờ tối đa 10s để phần tử xuất hiện
            sort_by_date_button = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//a[normalize-space(text())='Sắp xếp theo ngày' or normalize-space(text())='Sort by date']")
                )
            )

            # Scroll đến vị trí nút
            self.driver.execute_script("arguments[0].scrollIntoView(true);", sort_by_date_button)
            time.sleep(1)

            # Click bằng JS để tránh bị che khuất
            self.driver.execute_script("arguments[0].click();", sort_by_date_button)
            time.sleep(2)

            print("✔ Đã click 'Sắp xếp theo ngày'")
        except Exception as e:
            print(f"⚠ Không click được 'Sắp xếp theo ngày': {e}")


        papers = []
        try:
            results = self.driver.find_elements(By.CSS_SELECTOR, "div.gs_r.gs_or.gs_scl")[:max_papers]
            print(f"Found {len(results)} papers to process")

            for idx, result in enumerate(results, 1):
                try:
                    # Lấy tiêu đề và link
                    title_element = result.find_element(By.CSS_SELECTOR, "h3.gs_rt a")
                    link = title_element.get_attribute("href")
                    basic_title = title_element.text

                    # Lấy thông tin tác giả và năm
                    try:
                        authors_text = result.find_element(By.CSS_SELECTOR, "div.gs_a").text
                    except:
                        authors_text = "Authors not found"

                    pub_date = self.extract_pub_date(authors_text)

                    # Lấy số lần trích dẫn
                    try:
                        citation_element = result.find_element(By.XPATH, ".//a[contains(text(), 'Cited by')]")
                        citations = citation_element.text.replace("Cited by ", "")
                    except:
                        citations = "Not Available"

                    # Mở link để lấy abstract
                    full_details = self.get_paper_details_from_link(link, idx)

                    # Chuẩn hóa dữ liệu output
                    paper = {
                        "source": "Google Scholar",
                        "title": full_details['title'],
                        "abstract": full_details['abstract'],
                        "authors": authors_text,
                        "link": link,
                        "citations": citations,
                        "status": "Open Access",  # Google Scholar không trả quyền truy cập
                        "pub_date": pub_date
                    }

                    papers.append(paper)
                    print(f"✓ Processed paper {idx}: {paper['title'][:80]}")

                    time.sleep(3)

                except Exception as e:
                    print(f"Error processing paper {idx}: {e}")
                    continue

        except Exception as e:
            print(f"Error during search: {e}")

        # Nếu không thể click sort by date -> sắp xếp thủ công
        try:
            papers.sort(key=lambda x: int(x['pub_date']) if x['pub_date'].isdigit() else 0, reverse=True)
        except Exception as e:
            print(f"⚠ Could not sort manually: {e}")

        print(f"\n=== Successfully processed {len(papers)} papers ===")
        return papers

    def run(self, keyword: str, max_papers: int = 5):
        """
        Wrapper để chạy từ setup browser -> search -> đóng browser
        """
        self.setup_browser()
        try:
            return self.search_google_scholar(keyword, max_papers)
        finally:
            if self.driver:
                self.driver.quit()


def run_scholar_search(keyword: str, max_papers: int = 5):
    finder = ScholarFinder()
    return finder.run(keyword, max_papers)



if __name__ == "__main__":
    run_scholar_search("ndt", 5)
