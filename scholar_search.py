import asyncio
import os
import json
from datetime import datetime
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import time

class ScholarFinder:
    
    def __init__(self):
        self.driver = None
        
    def setup_browser(self):
        """Setup Chrome browser with basic options"""
        options = Options()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        self.driver = webdriver.Chrome(options=options)
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return self.driver
    
    def get_paper_details_from_link(self, paper_url: str, paper_rank: int) -> Dict:
        """Get full title and abstract from individual paper link"""
        print(f"Accessing paper {paper_rank}: {paper_url}")
        
        try:
            # Open paper in new tab
            self.driver.execute_script("window.open('');")
            self.driver.switch_to.window(self.driver.window_handles[-1])
            self.driver.get(paper_url)
            time.sleep(4)  # Wait longer for page load
            
            title = "Title not found"
            abstract = "Abstract not found"
            
            # Try different title selectors
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
                        print(f"Found title with selector: {selector}")
                        break
                except:
                    continue
            
            # Try different abstract selectors
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
                        print(f"Found abstract with selector: {selector}")
                        break
                except:
                    continue
            
            # If still no abstract, try to find paragraphs that look like abstract
            if abstract == "Abstract not found":
                try:
                    paragraphs = self.driver.find_elements(By.TAG_NAME, "p")
                    for p in paragraphs:
                        text = p.text.strip()
                        if len(text) > 100:
                            text_lower = text.lower()
                            # Look for abstract indicators
                            if any(word in text_lower for word in ['abstract', 'this paper', 'this study', 'we present', 'we propose', 'this work']):
                                abstract = text
                                print("Found abstract in paragraph")
                                break
                except Exception as e:
                    print(f"Error finding abstract in paragraphs: {e}")
            
            # Close current tab and switch back to main window
            self.driver.close()
            self.driver.switch_to.window(self.driver.window_handles[0])
            
            return {
                "title": title,
                "abstract": abstract,
                "url": paper_url,
                "access_status": "success" if title != "Title not found" else "failed"
            }
            
        except Exception as e:
            print(f"Error accessing paper {paper_rank}: {e}")
            # Make sure to close tab and return to main window
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
        """Search Google Scholar for NDT papers and get full details"""
        print(f"Searching Google Scholar for: {search_query}")
        
        # Navigate to Google Scholar
        self.driver.get("https://scholar.google.com")
        time.sleep(3)
        
        # Find search box and enter query
        search_box = WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.NAME, "q"))
        )
        search_box.clear()
        search_box.send_keys(search_query)
        
        # Click search button
        search_button = self.driver.find_element(By.XPATH, "//button[@type='submit']")
        search_button.click()
        time.sleep(4)
        
        # Try to sort by date (recent first) - optional
        try:
            # Look for sort options
            sort_elements = self.driver.find_elements(By.XPATH, "//a[contains(text(), 'Sort by date')]")
            if sort_elements:
                sort_elements[0].click()
                time.sleep(3)
                print("Sorted by date successfully")
            else:
                print("Date sorting not available, using default sorting")
        except:
            print("Could not sort by date, continuing with default sorting")
        
        # Get paper links first
        papers = []
        paper_links = []
        
        try:
            # Get results
            results = self.driver.find_elements(By.CSS_SELECTOR, "div.gs_r.gs_or.gs_scl")[:max_papers]
            print(f"Found {len(results)} papers to process")
            
            # Collect basic info and links first
            for idx, result in enumerate(results, 1):
                try:
                    # Get title link
                    title_element = result.find_element(By.CSS_SELECTOR, "h3.gs_rt a")
                    link = title_element.get_attribute("href")
                    basic_title = title_element.text
                    
                    # Get authors and publication info
                    try:
                        authors_element = result.find_element(By.CSS_SELECTOR, "div.gs_a")
                        authors_text = authors_element.text
                    except:
                        authors_text = "Authors not found"
                    
                    # Get citation count if available
                    try:
                        citation_element = result.find_element(By.XPATH, ".//a[contains(text(), 'Cited by')]")
                        citation_text = citation_element.text
                        citations = citation_text.replace("Cited by ", "")
                    except:
                        citations = "0"
                    
                    paper_info = {
                        "rank": idx,
                        "basic_title": basic_title,
                        "authors": authors_text,
                        "link": link,
                        "citations": citations,
                        "found_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    paper_links.append((link, paper_info))
                    
                except Exception as e:
                    print(f"Error extracting basic info for paper {idx}: {e}")
                    continue
            
            # Now get full details from each paper
            print(f"\nAccessing {len(paper_links)} papers to get full title and abstract...")
            
            for link, basic_info in paper_links:
                print(f"\n--- Processing paper {basic_info['rank']}/{len(paper_links)} ---")
                
                # Get full paper details
                full_details = self.get_paper_details_from_link(link, basic_info['rank'])
                
                # Combine basic info with full details
                paper = {
                    "rank": basic_info['rank'],
                    "title": full_details['title'],
                    "abstract": full_details['abstract'],
                    "authors": basic_info['authors'],
                    "link": link,
                    "citations": basic_info['citations'],
                    "access_status": full_details['access_status'],
                    "found_date": basic_info['found_date']
                }
                
                papers.append(paper)
                
                # Show immediate result
                print(f"✓ Title: {full_details['title'][:100]}...")
                print(f"✓ Abstract: {full_details['abstract'][:200]}...")
                print(f"✓ Status: {full_details['access_status']}")
                
                # Small delay between paper accesses
                time.sleep(3)
                
        except Exception as e:
            print(f"Error during search: {e}")
            
        print(f"\n=== Successfully processed {len(papers)} papers ===")
        return papers

    def save_results(self, papers: List[Dict], filename: str = None, folder: str = "results"):
        """
        Save results to JSON file trong thư mục 'results'
        """
        # Nếu không truyền filename -> tạo tên file mặc định
        if filename is None:
            filename = f"schoolar_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Lấy đường dẫn tuyệt đối của folder hiện tại (nơi chứa file script)
        current_dir = os.path.dirname(os.path.abspath(__file__))

        # Tạo folder 'results' nếu chưa tồn tại
        results_folder = os.path.join(current_dir, folder)
        if not os.path.exists(results_folder):
            os.makedirs(results_folder)

        # Đường dẫn đầy đủ đến file JSON trong thư mục 'results'
        file_path = os.path.join(results_folder, filename)

        # Chuẩn bị dữ liệu để lưu
        results = {
            "search_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_papers": len(papers),
            "successfully_accessed": len([p for p in papers if p.get('access_status') == 'success']),
            "papers": papers
        }

        # Lưu file JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"✅ Results saved to: {file_path}")
        return file_path
    def run(self, keyword: str, max_papers: int = 5):
        """Wrapper để tự động setup browser, search và đóng browser"""
        self.setup_browser()
        try:
            results = self.search_google_scholar(keyword, max_papers)
            return results
        finally:
            if self.driver:
                self.driver.quit()
    # def run_search(self, ndt_keywords: str = "NDT non-destructive testing", max_papers: int = 5):
    #     """Main method to run the complete search"""
    #     try:
    #         # Setup browser
    #         self.setup_browser()
            
    #         # Search for papers and get full details
    #         print("=== Starting NDT paper search with full content extraction ===")
    #         papers = self.search_google_scholar(ndt_keywords, max_papers)
            
    #         # Print results summary
    #         successful_papers = [p for p in papers if p['access_status'] == 'success']
    #         print(f"\n{'='*60}")
    #         print(f"SEARCH RESULTS SUMMARY")
    #         print(f"{'='*60}")
    #         print(f"Total papers processed: {len(papers)}")
    #         print(f"Successfully accessed: {len(successful_papers)}")
    #         print(f"Failed to access: {len(papers) - len(successful_papers)}")
            
    #         # Show detailed results
    #         print(f"\n{'='*60}")
    #         print(f"DETAILED RESULTS")
    #         print(f"{'='*60}")
            
    #         for paper in papers:
    #             print(f"\n--- PAPER {paper['rank']} [{paper['access_status'].upper()}] ---")
    #             print(f"Title: {paper['title']}")
    #             print(f"Authors: {paper['authors']}")
    #             print(f"Citations: {paper['citations']}")
    #             print(f"Abstract: {paper['abstract']}")
    #             print(f"Link: {paper['link']}")
    #             print("-" * 60)
            
    #         # Save results
    #         filename = self.save_results(papers)
            
    #         print(f"\n{'='*50}")
    #         print(f"COMPLETED!")
    #         print(f"{'='*50}")
    #         print(f"Results saved to: {filename}")
            
    #         return papers
            
    #     except Exception as e:
    #         print(f"Error during search: {e}")
    #         return []
            
    #     finally:
    #         if self.driver:
    #             self.driver.quit()

# def main():
#     """Main function to run the NDT paper finder"""
    
#     # Create finder instance
#     finder = NDTPaperFinder()
    
#     # Nhập từ bàn phím
#     query = input("Nhập từ khóa tìm kiếm Google Scholar: ").strip()
#     if not query:
#         print("❌ Bạn chưa nhập từ khóa!")
#         return
    
#     try:
#         # Nhập số lượng bài muốn lấy
#         max_papers = input("Nhập số lượng bài muốn lấy (mặc định 5): ").strip()
#         max_papers = int(max_papers) if max_papers.isdigit() else 5
        
#         print(f"\n{'='*60}")
#         print(f"SEARCHING: {query}")
#         print('='*60)

#         # Thực hiện tìm kiếm
#         papers = finder.run_search(query, max_papers=max_papers)
        
#         print(f"\nFound {len(papers)} papers with full content!")

#     except Exception as e:
#         print(f"❌ Lỗi: {e}")
def run_scholar_search(keyword: str, max_papers: int = 5):
    finder = ScholarFinder()
    data = finder.run(keyword, max_papers)

    current_dir = os.path.dirname(os.path.abspath(__file__))
    results_folder = os.path.join(current_dir, "results")
    os.makedirs(results_folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(results_folder, f"scholar_results_{timestamp}.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return {"data": data, "file": output_path}


# if __name__ == "__main__":
#     main()