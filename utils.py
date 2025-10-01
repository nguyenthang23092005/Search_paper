import os
import glob
import json
from datetime import datetime, timedelta

RESULTS_DIR = "results"
RESULTS_DIR_AGENT = "results_agent"
DATABASE_DIR = "database"
DATABASE_FILE = "papers_db.json"

def normalize_key(paper):
    """
    Chuẩn hóa key để so sánh trùng lặp:
    - Ưu tiên DOI (lowercase, bỏ khoảng trắng).
    - Nếu không có DOI → dùng link.
    - Nếu không có link → dùng title.
    """
    doi = (paper.get("doi") or "").strip().lower()
    link = (paper.get("link") or "").strip().lower()
    title = (paper.get("title") or "").strip().lower()

    if doi:
        return doi
    elif link:
        return link
    elif title:
        return title
    return ""

# ==============================
# Lấy file JSON mới nhất
# ==============================
def get_latest_json():
    """
    Lấy file JSON mới nhất theo ngày có dạng: YYYY-MM-DD_allapi_scholar_ndt.json
    """
    pattern = os.path.join(RESULTS_DIR, "*_allapi_scholar_ndt.json")
    json_files = glob.glob(pattern)

    if not json_files:
        print("⚠️ Không tìm thấy file JSON nào trong thư mục results/")
        return None

    # Lấy ngày từ tên file và chọn ngày mới nhất
    files_with_dates = []
    for f in json_files:
        base = os.path.basename(f)
        try:
            date_part = base.split("_")[0]  # Lấy phần YYYY-MM-DD
            datetime.strptime(date_part, "%Y-%m-%d")  # kiểm tra format
            files_with_dates.append((date_part, f))
        except Exception:
            continue

    if not files_with_dates:
        print("⚠️ Không tìm thấy file JSON hợp lệ theo ngày")
        return None

    # Chọn file có ngày mới nhất
    latest_file = max(files_with_dates, key=lambda x: x[0])[1]
    print(f"📂 File JSON mới nhất theo ngày: {latest_file}")
    return latest_file

def get_latest_json_agent():
    """
    Lấy file JSON mới nhất theo ngày có dạng: YYYY-MM-DD_allapi_scholar_ndt.json
    """
    pattern = os.path.join(RESULTS_DIR_AGENT, "*_allapi_scholar_ndt.json")
    json_files = glob.glob(pattern)

    if not json_files:
        print("⚠️ Không tìm thấy file JSON nào trong thư mục results_agent/")
        return None

    # Lấy ngày từ tên file và chọn ngày mới nhất
    files_with_dates = []
    for f in json_files:
        base = os.path.basename(f)
        try:
            date_part = base.split("_")[0]  # Lấy phần YYYY-MM-DD
            datetime.strptime(date_part, "%Y-%m-%d")  # kiểm tra format
            files_with_dates.append((date_part, f))
        except Exception:
            continue

    if not files_with_dates:
        print("⚠️ Không tìm thấy file JSON hợp lệ theo ngày")
        return None

    # Chọn file có ngày mới nhất
    latest_file = max(files_with_dates, key=lambda x: x[0])[1]
    print(f"📂 File JSON mới nhất theo ngày: {latest_file}")
    return latest_file

# ==============================
# Lưu file JSON với timestamp
# ==============================
def save_results_to_json(data, output_dir=RESULTS_DIR, prefix="allapi_scholar_ndt"):
    """
    Lưu kết quả vào file JSON với tên chứa timestamp.
    Nếu cùng 1 ngày đã có file -> load dữ liệu cũ, merge thêm dữ liệu mới (lọc trùng), rồi ghi đè lại.
    """
    os.makedirs(output_dir, exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")

    # Tìm file trong ngày hôm nay
    existing_file = None
    for fname in os.listdir(output_dir):
        if fname.startswith(today_str) and fname.endswith(f"{prefix}.json"):
            existing_file = os.path.join(output_dir, fname)
            break

    merged_data = []
    if existing_file:
        try:
            with open(existing_file, "r", encoding="utf-8") as f:
                old_data = json.load(f)
        except Exception as e:
            print(f"⚠️ Lỗi khi đọc file cũ {existing_file}: {e}")
            old_data = []
        merged_data = old_data
    else:
        # Nếu chưa có file -> tạo file mới
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = f"{timestamp}_{prefix}.json"
        existing_file = os.path.join(output_dir, filename)

    # Merge dữ liệu (lọc trùng theo key chuẩn hóa)
    existing_keys = {normalize_key(item) for item in merged_data if normalize_key(item)}
    new_filtered = [p for p in data if normalize_key(p) not in existing_keys]

    if not new_filtered:
        print("⏩ Không có dữ liệu mới để thêm.")
        return existing_file

    merged_data.extend(new_filtered)

    try:
        with open(existing_file, "w", encoding="utf-8") as f:
            json.dump(merged_data, f, ensure_ascii=False, indent=2)
        print(f"💾 Đã cập nhật file: {existing_file} (thêm {len(new_filtered)} bài báo)")
        return existing_file
    except Exception as e:
        print(f"❌ Lỗi khi lưu file JSON: {e}")
        return None


# ==============================
# Load Database DOI
# ==============================
def load_database(db_dir=DATABASE_DIR, db_file=DATABASE_FILE):
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, db_file)

    if os.path.exists(db_path):
        with open(db_path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return []


def save_database(data, db_dir=DATABASE_DIR, db_file=DATABASE_FILE):
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, db_file)

    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Database đã được cập nhật: {db_path}")

# ==============================
# Cập nhật Database (lưu Title + DOI)
# ==============================
def save_results_to_database(result_file, db_dir=DATABASE_DIR, db_file=DATABASE_FILE):
    """
    Đọc kết quả từ file JSON và lưu vào database.
    Chuẩn hóa key (doi/link/title) và loại bỏ trùng lặp.
    """
    if not os.path.exists(result_file):
        print(f"❌ File kết quả không tồn tại: {result_file}")
        return False

    try:
        with open(result_file, "r", encoding="utf-8") as f:
            results = json.load(f)
    except Exception as e:
        print(f"❌ Lỗi khi đọc file kết quả {result_file}: {e}")
        return False

    db_data = load_database(db_dir, db_file)
    db_dict = {normalize_key(item): item for item in db_data if normalize_key(item)}

    new_count = 0
    for paper in results:
        key = normalize_key(paper)
        if key and key not in db_dict:
            db_dict[key] = {
                "title": paper.get("title", "Untitled"),
                "doi": paper.get("doi", paper.get("link", ""))
            }
            new_count += 1

    save_database(list(db_dict.values()), db_dir, db_file)
    print(f"✅ Đã thêm {new_count} bài báo mới vào database từ {result_file}")
    return True



# ==============================
# Lọc bài báo trùng 
# ==============================
def filter_duplicates(new_results, results_dir=RESULTS_DIR, db_dir=DATABASE_DIR, db_file=DATABASE_FILE):
    """
    Lọc trùng các bài báo mới bằng key chuẩn hóa (doi/link/title).
    - Nếu file mới nhất là hôm nay → không lọc.
    - Nếu file mới nhất là hôm qua → lọc theo hôm qua.
    - Nếu không phải hôm nay và không phải hôm qua → lọc theo database.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # 🔹 Lấy file JSON mới nhất
    latest_file = get_latest_json()
    if not latest_file:
        return new_results

    # 🔹 Đọc dữ liệu file mới nhất
    try:
        with open(latest_file, "r", encoding="utf-8") as f:
            old_results = json.load(f)
    except Exception as e:
        print(f"❌ Lỗi khi đọc file {latest_file}: {e}")
        return new_results

    old_dates = {paper.get("pub_date", "") for paper in old_results}

    # ✅ File hôm nay → không lọc
    if today_str in old_dates:
        print("⏩ File mới nhất đã là hôm nay -> Không lọc trùng.")
        return new_results

    # ✅ Không phải hôm nay → lọc
    # Nếu là hôm qua → lọc theo hôm qua
    if yesterday_str in old_dates:
        old_keys = {normalize_key(p) for p in old_results if normalize_key(p)}
        filtered_results = [p for p in new_results if normalize_key(p) not in old_keys]
        removed_count = len(new_results) - len(filtered_results)
        print(f"🗑️ Đã loại bỏ {removed_count} bài báo trùng với hôm qua.")
        return filtered_results

    # ✅ Không phải hôm qua → lọc theo database
    db_path = os.path.join(db_dir, db_file)
    if not os.path.exists(db_path):
        print("⚠️ Không tìm thấy database -> Trả về toàn bộ dữ liệu mới.")
        return new_results

    try:
        with open(db_path, "r", encoding="utf-8") as f:
            db_data = json.load(f)
            db_keys = {normalize_key(item) for item in db_data if normalize_key(item)}
    except Exception as e:
        print(f"❌ Lỗi khi đọc database {db_path}: {e}")
        return new_results

    filtered_results = [p for p in new_results if normalize_key(p) not in db_keys]
    removed_count = len(new_results) - len(filtered_results)
    print(f"🗑️ Đã loại bỏ {removed_count} bài báo trùng với database.")
    return filtered_results
