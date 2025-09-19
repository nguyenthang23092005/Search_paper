import requests
import json
import os
from datetime import datetime
import xml.etree.ElementTree as ET

RESULTS_DIR = "results"

# ========================
# 1. OpenAlex API
# ========================
def decode_openalex_abstract(inverted_index):
    if not inverted_index:
        return "Not Available"
    words = sorted([(pos, word) for word, positions in inverted_index.items() for pos in positions])
    return " ".join(word for pos, word in words)

def search_openalex(query="Non-Destructive Testing", rows=5):
    url = "https://api.openalex.org/works"
    params = {
        "search": query,
        "per_page": rows,
        "sort": "publication_date:desc"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return []

    data = response.json()
    if "results" not in data or len(data["results"]) == 0:
        return []

    results = []
    for idx, item in enumerate(data["results"], start=1):
        title = item.get("title", "No title")
        abstract = decode_openalex_abstract(item.get("abstract_inverted_index"))
        if abstract and isinstance(abstract, str):
            abstract = abstract.replace("\n", " ").strip()

        authors = [a["author"]["display_name"] for a in item.get("authorships", []) if "author" in a]
        authors_str = ", ".join(authors) if authors else "Not Available"

        link = item.get("primary_location", {}).get("landing_page_url", "Not Available")
        citations = item.get("cited_by_count", 0)
        status = item.get("open_access", {}).get("status", "Not Available")
        pub_date = item.get("publication_date", "Not Available")

        results.append({
            "source": "OpenAlex",
            "title": title,
            "abstract": abstract,
            "authors": authors_str,
            "link": link,
            "citations": citations,
            "status": status,
            "pub_date": pub_date
        })
    return results


# ========================
# 2. Semantic Scholar API
# ========================
def search_semantic_scholar(query="Non-Destructive Testing", rows=5):
    url = "https://api.semanticscholar.org/graph/v1/paper/search"
    params = {
        "query": query,
        "limit": rows,
        "fields": "title,abstract,authors,year,url,citationCount"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException:
        return []

    data = response.json()
    if "data" not in data or len(data["data"]) == 0:
        return []

    results = []
    for idx, item in enumerate(data["data"], start=1):
        title = item.get("title", "No title")
        abstract = item.get("abstract")
        
        authors = [a["name"] for a in item.get("authors", [])]
        authors_str = ", ".join(authors) if authors else "Not Available"

        link = item.get("url", "Not Available")
        citations = item.get("citationCount", 0)
        pub_date = str(item.get("year", "Not Available"))

        results.append({
            "source": "Semantic Scholar",
            "title": title,
            "abstract": abstract if abstract else "Not Available",
            "authors": authors_str,
            "link": link,
            "citations": citations,
            "status": "Not Available",
            "pub_date": pub_date
        })

    # Sắp xếp theo pub_date giảm dần (mới -> cũ)
    # results = sorted(
    #     results, 
    #     key=lambda x: int(x['pub_date']) if x['pub_date'].isdigit() else 0, 
    #     reverse=True
    # )

    return results


# ========================
# 3. arXiv API
# ========================
def search_arxiv(query="Non-Destructive Testing", rows=5):
    url = "http://export.arxiv.org/api/query"
    params = {
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": rows,
        "sortBy": "submittedDate",
        "sortOrder": "descending"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return []

    root = ET.fromstring(response.content)
    ns = {"arxiv": "http://www.w3.org/2005/Atom"}

    entries = root.findall("arxiv:entry", ns)
    if not entries:
        return []

    results = []
    for idx, entry in enumerate(entries, start=1):
        title = entry.find("arxiv:title", ns).text.strip()
        abstract = entry.find("arxiv:summary", ns).text.strip()
        link = entry.find("arxiv:id", ns).text.strip()

        authors = [a.find("arxiv:name", ns).text for a in entry.findall("arxiv:author", ns)]
        authors_str = ", ".join(authors) if authors else "Not Available"

        pub_date = entry.find("arxiv:published", ns).text[:10]

        results.append({
            "source": "arXiv",
            "title": title,
            "abstract": abstract,
            "authors": authors_str,
            "link": link,
            "citations": "Not Available",
            "status": "Open Access",
            "pub_date": pub_date
        })
    return results


# ========================
# 4. CrossRef API
# ========================
def search_crossref(query="Non-Destructive Testing", rows=5):
    url = "https://api.crossref.org/works"
    params = {
        "query": query,
        "rows": rows,
        "sort": "published",
        "order": "desc"
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return []

    data = response.json()
    if "message" not in data or "items" not in data["message"]:
        return []

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
            "source": "Crossref",
            "title": title,
            "abstract": abstract,
            "authors": authors_str,
            "link": link,
            "citations": citations,
            "status": status,
            "pub_date": pub_date
        })
    return results


# ========================
# Merge & Save to One File
# ========================
def merge_and_save(all_results, filename):
    """
    Gộp tất cả kết quả vào 1 file và loại bỏ trùng lặp.
    Trùng lặp được xác định bởi: title + authors hoặc link.
    """
    unique = {}
    for paper in all_results:
        key = (paper['title'].lower().strip(), paper['authors'].lower().strip(), paper['link'].lower().strip())
        if key not in unique:
            unique[key] = paper

    final_results = list(unique.values())

    if not os.path.exists(RESULTS_DIR):
        os.makedirs(RESULTS_DIR)

    filepath = os.path.join(RESULTS_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)

    print(f"Saved {len(final_results)} unique papers to {filepath}")


# ========================
# TEST FUNCTION
# ========================
if __name__ == "__main__":
    query = "Non-Destructive Testing"
    combined_results = []

    print("===== Fetching from OpenAlex =====")
    combined_results.extend(search_openalex(query=query, rows=10))

    print("===== Fetching from Semantic Scholar =====")
    combined_results.extend(search_semantic_scholar(query=query, rows=10))

    print("===== Fetching from arXiv =====")
    combined_results.extend(search_arxiv(query=query, rows=10))

    print("===== Fetching from Crossref =====")
    combined_results.extend(search_crossref(query=query, rows=10))

    # Lưu tất cả vào 1 file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    merge_and_save(combined_results, f"merged_results_{timestamp}.json")
