import requests
import json
import os
from datetime import datetime

RESULTS_DIR = "results"

def search_crossref_ndt(query="Non-Destructive Testing", rows=5):
    """
    Tìm kiếm bài báo từ Crossref và trả về dict:
    {
        "data": [...],
        "file": "đường_dẫn_file.json"
    }
    """
    url = "https://api.crossref.org/works"
    params = {"query": query, "rows": rows}

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return {"error": f"Lỗi khi kết nối API Crossref: {e}"}

    data = response.json()
    if "message" not in data or "items" not in data["message"]:
        return {"error": "Không tìm thấy kết quả nào từ Crossref."}

    results = []
    for idx, item in enumerate(data["message"]["items"], start=1):
        title = item.get("title", ["No title"])[0]
        abstract = item.get("abstract", "Not Available")
        if abstract and isinstance(abstract, str):
            abstract = abstract.replace("\n", " ").strip()
        authors = []
        for a in item.get("author", []):
            full_name = f"{a.get('given', '')} {a.get('family', '')}".strip()
            if full_name:
                authors.append(full_name)
        authors_str = ", ".join(authors) if authors else "Not Available"
        doi = item.get("DOI", "")
        link = f"https://doi.org/{doi}" if doi else "Not Available"
        date_parts = item.get("issued", {}).get("date-parts", [[None]])
        pub_date = "-".join(str(p) for p in date_parts[0] if p is not None)
        citations = item.get("is-referenced-by-count", 0)
        status = item.get("publisher", "Not Available")

        results.append({
            "rank": idx,
            "title": title,
            "abstract": abstract,
            "authors": authors_str,
            "link": link,
            "citations": citations,
            "status": status,
            "pub_date": pub_date
        })

    # Lưu file JSON
    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(RESULTS_DIR, f"crossref_results_{timestamp}.json")
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    return {"data": results, "file": filename}
