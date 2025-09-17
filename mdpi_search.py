from browser_use import Agent, ChatGoogle
from dotenv import load_dotenv
import asyncio
import json
import os
from datetime import datetime
import nest_asyncio
nest_asyncio.apply()
import asyncio
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Load .env file
load_dotenv()

async def mdpi_search(keyword: str = "ndt", max_papers: int = 5):
    # Nhập từ khóa tìm kiếm từ bàn phím
    if not keyword:
        print("❌ Bạn chưa nhập từ khóa!")
        return
    llm = ChatGoogle(model="gemini-2.5-flash", api_key=os.getenv("GOOGLE_API_KEY"))

    task = f"""
You are an autonomous agent. Your task is to:

1. Open the website: https://www.mdpi.com/journal
2. Locate the search interface—this may be a global search box or journal-specific “Advanced Search” (e.g., see the search box available on journal pages such as “Computers”).
3. Enter the keyword: "{keyword}".
4. Submit the search.
5. Once results are presented, **filter** them to include only papers published **from September 1, 2025** onward:
   - If MDPI provides a "Publication Date" or date-range filter, set it accordingly.
   - Otherwise, manually check each result’s publication date and only select those with a date of September 1, 2025 or later.
6. Click on the **RSS feed** option for the search results (if available).
7. From the **top {max_papers} matching papers** (by relevance or latest date), extract:
   a. Rank paper
   b. Title of the paper.
   c. Abstract or summary (if visible).
   d. Authors (if visible).
   e. The **direct link** to the paper.
   f. Number of citations (if available). If the citation count is not visible, return 0 or "Not Available".
   g. Status of the paper (e.g., "Available", "Paywalled", "Preprint", etc.).
   h. The public date.
8. Output the collected data as a **JSON list**, with each item containing the keys:
   ["rank", "title", "abstract", "authors", "link", "citations", "status", "pub_date"]

IMPORTANT:
- Wait for pages to **fully load** before interacting.
- If any step fails, **retry up to two times** before moving on.
- The **final output must be strictly JSON**, with no additional explanation or text.
"""

    agent = Agent(task=task, llm=llm)
    result = await agent.run()

    # Lấy text kết quả từ agent
    result_text = result.final_result()

    # Lưu file JSON trong cùng thư mục với file Python
    current_dir = os.path.dirname(os.path.abspath(__file__))
    results_folder = os.path.join(current_dir, "results")
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)
    # Lấy ngày giờ hiện tại: YYYYMMDD_HHMMSS
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(results_folder, f"mdpi_results_{timestamp}.json")

    try:
        new_data = json.loads(result_text)  # Parse kết quả JSON từ Agent

        # Ghi trực tiếp dữ liệu vào file mà không kiểm tra dữ liệu cũ
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(new_data, f, indent=2, ensure_ascii=False)

        print(f"\n✅ Dữ liệu đã được lưu thành công vào: {output_path}")
        print(json.dumps(new_data, indent=2, ensure_ascii=False))

    except json.JSONDecodeError:
        print("⚠️ Lỗi: Kết quả không đúng định dạng JSON.")
        print("Raw Output:", result_text)
    except Exception as e:
        print(f"⚠️ Đã xảy ra lỗi: {e}")
    return {
        "file": output_path,
        "data": new_data
    }

def run_mdpi_search(keyword, max_papers):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # Nếu không có event loop, tự tạo một cái mới
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(mdpi_search(keyword, max_papers))
