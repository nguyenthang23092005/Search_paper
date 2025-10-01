from browser_use import Agent, ChatGoogle
from dotenv import load_dotenv
import asyncio
import json
import os
from datetime import datetime, timedelta
import nest_asyncio
nest_asyncio.apply()
import asyncio
import sys

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Load .env file
load_dotenv()

async def springer_search(keyword: str = "ndt", max_papers: int = 5):
    # Nhập từ khóa tìm kiếm từ bàn phím
    if not keyword:
        print("❌ Bạn chưa nhập từ khóa!")
        return

    llm = ChatGoogle(model="gemini-2.5-flash", api_key=os.getenv("GEMINI_API_KEY"))
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    task = f"""
You are an autonomous agent. Your task is to:
1. Open the website: https://link.springer.com/search
2. Locate the search box and type the keyword: "{keyword}".
3. Press Enter to search.
4. Use any available filters (date range, publication date) to only include papers published on or after {yesterday}.
   - If no filter exists, manually check each result’s publication date and ignore papers older than {yesterday}.
5. Click the RSS feed option for the search results (if available).
6. For the **top {max_papers} papers**, perform the following steps:
    - Extract the following information for each latest paper:
        a. Rank paper
        b. Title of the paper.
        c. Abstract or summary (if visible).
        d. Authors (if visible).
        e. The **direct link** to the paper.
        f. Number of citations (if available). If the citation count is not visible, return 0 or "Not Available".
        g. Status of the paper (e.g., "Available", "Paywalled", "Preprint", etc.).
        h. The public date.

7. Return the final extracted data as a **JSON list**.
   - Each item in the JSON list must have the following keys:
     ["rank", "title", "abstract", "authors", "link", "citations", "status", "pub_date"]

IMPORTANT:
- Always wait for pages to **fully load** before interacting.
- If a step fails, **retry up to 2 times** before moving to the next step.
- The **final output must be strictly in JSON format**, with no extra explanations or text.
"""

    agent = Agent(task=task, llm=llm)
    result = await agent.run()

    result_text = result.final_result()

    # Lưu file JSON trong cùng thư mục với file Python
    current_dir = os.path.dirname(os.path.abspath(__file__))
    results_folder = os.path.join(current_dir, "results")
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)
    # Lấy ngày giờ hiện tại: YYYYMMDD_HHMMSS
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = os.path.join(results_folder, f"springer_results_{timestamp}.json")

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

def run_springer_search(keyword, max_papers):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # Nếu không có event loop, tự tạo một cái mới
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(springer_search(keyword, max_papers))


