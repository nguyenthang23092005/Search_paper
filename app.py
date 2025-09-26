import streamlit as st
from springer_search import run_springer_search
from mdpi_search import run_mdpi_search
from scholar_search import run_scholar_search
from search_api import search_openalex, search_semantic_scholar, search_arxiv, search_crossref,enrich_with_firecrawl, summarize_filtered_papers, filter_irrelevant_papers
import pandas as pd
from datetime import datetime

import json
import os
import glob
import asyncio
import sys
from dotenv import load_dotenv, set_key

# ===================== WINDOWS FIX =====================
if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# ===================== PAGE CONFIG =====================
st.set_page_config(page_title="Paper Search App", layout="wide")

# -------------------- CONFIG FILE --------------------
RESULTS_DIR = "results"
ENV_PATH = ".env"

if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

if not os.path.exists(ENV_PATH):
    open(ENV_PATH, "a").close()

load_dotenv(ENV_PATH)

# ===================== SUPPORT FUNCTION =====================
def merge_and_save_results(all_results, filename):
    """
    Hợp nhất kết quả từ nhiều nguồn, loại bỏ bài báo trùng nhau dựa vào tiêu đề.
    """
    seen_titles = set()
    merged_results = []

    for source_data in all_results:
        for paper in source_data:
            title = paper.get("title", "").strip().lower()
            if title and title not in seen_titles:
                merged_results.append(paper)
                seen_titles.add(title)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # ví dụ: 20250919_103045
    filename_with_time = f"{timestamp}_{filename}"

    filepath = os.path.join(RESULTS_DIR, filename_with_time)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(merged_results, f, indent=2, ensure_ascii=False)

    return filepath, merged_results

# ===================== TABS =====================
tab1, tab2, tab3 = st.tabs([
    "🌐 All APIs + Scholar",
    "📘 Springer + MDPI",
    "📁 Danh sách kết quả"
])

# ===================== TAB 1 =====================
with tab1:
    st.subheader("🔹 Tìm kiếm trên All APIs + Google Scholar")

    # Nhập từ khóa và số lượng bài một lần
    keyword_tab1 = st.text_input("Nhập từ khóa tìm kiếm (All APIs + Scholar):", key="keyword_tab1")
    max_results_tab1 = st.number_input("Số lượng bài muốn lấy mỗi nguồn", min_value=1, max_value=20, value=10, key="max_results_tab1")

    if st.button("🔍 Tìm kiếm All APIs + Scholar"):
        if not keyword_tab1.strip():
            st.warning("⚠️ Vui lòng nhập từ khóa tìm kiếm!")
        else:
            with st.spinner("Đang tìm kiếm trên tất cả các API..."):
                # Gọi API
                openalex_res = search_openalex(query=keyword_tab1, rows=max_results_tab1)
                # semantic_res = search_semantic_scholar(query=keyword_tab2, rows=max_results_tab2)
                arxiv_res = search_arxiv(query=keyword_tab1, rows=max_results_tab1)
                crossref_res = search_crossref(query=keyword_tab1, rows=max_results_tab1)

                # Google Scholar
                scholar_data = run_scholar_search(keyword_tab1, max_results_tab1)

                # Merge kết quả
                merged_results = []
                for res in [openalex_res, arxiv_res, crossref_res, scholar_data]:
                    merged_results.extend(res)

                # Crawl bổ sung bằng Firecrawl
                st.info("⏳ Đang crawl abstract bổ sung bằng Firecrawl...")
                enriched_results = enrich_with_firecrawl(merged_results)
                filter_results = filter_irrelevant_papers(enriched_results)
                summarize_results = summarize_filtered_papers(filter_results)

                # Lưu enriched
                current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"{current_time}_allapi_scholar_{keyword_tab1.replace(' ', '_')}.json"
                merged_file = os.path.join(RESULTS_DIR, filename)
                with open(merged_file, "w", encoding="utf-8") as f:
                    json.dump(summarize_results, f, indent=2, ensure_ascii=False)

                # Hiển thị enriched trực tiếp
                st.success(f"✅ Đã lưu kết quả enriched vào: {merged_file}")
                df = pd.DataFrame(summarize_results)
                st.dataframe(df)

                st.download_button(
                    label="📥 Tải kết quả JSON",
                    data=json.dumps(summarize_results, indent=2, ensure_ascii=False),
                    file_name=os.path.basename(merged_file),
                    mime="application/json"
                )




# ===================== TAB 2 =====================
with tab2:
    st.subheader("🔹 Tìm kiếm trên Springer và MDPI")

    # --- Nhập Google API Key chỉ hiển thị tại đây ---
    st.markdown("### ⚙️ Cấu hình Google API Key")
    gg_api_key = st.text_input(
        "Nhập Google API Key",
        type="password",
        placeholder="Nhập API Key..."
    )

    if st.button("💾 Lưu Google API Key"):
        if gg_api_key.strip():
            set_key(ENV_PATH, "GOOGLE_API_KEY", gg_api_key.strip())
            st.success("✅ API Key đã được lưu vào file `.env`")
        else:
            st.warning("⚠️ Vui lòng nhập API Key trước khi lưu")

    # Nhập từ khóa và số lượng bài một lần
    keyword_tab2 = st.text_input("Nhập từ khóa tìm kiếm (Springer + MDPI):", key="keyword_tab2")
    max_results_tab2 = st.number_input("Số lượng bài muốn lấy mỗi nguồn", min_value=1, max_value=20, value=10, key="max_results_tab2")

    if st.button("🔍 Tìm kiếm Springer + MDPI"):
        if not keyword_tab2.strip():
            st.warning("⚠️ Vui lòng nhập từ khóa tìm kiếm!")
        else:
            with st.spinner("Đang tìm kiếm trên Springer và MDPI..."):
                springer_result = run_springer_search(keyword_tab2, max_results_tab2)
                mdpi_result = run_mdpi_search(keyword_tab2, max_results_tab2)

                springer_data = [] if "error" in springer_result else springer_result["data"]
                mdpi_data = [] if "error" in mdpi_result else mdpi_result["data"]

                if "error" in springer_result:
                    st.error(f"Springer: {springer_result['error']}")
                if "error" in mdpi_result:
                    st.error(f"MDPI: {mdpi_result['error']}")

                # Hợp nhất kết quả
                merged_results = springer_data + mdpi_data

                # enrich bằng Firecrawl
                st.info("⏳ Đang crawl abstract bổ sung bằng Firecrawl...")
                enriched_results = enrich_with_firecrawl(merged_results)
                filter_results = filter_irrelevant_papers(enriched_results)
                summarize_results = summarize_filtered_papers(filter_results)

                # Lưu kết quả chỉ sau khi đã làm giàu xong
                current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = f"{current_time}_springer_mdpi_{keyword_tab2.replace(' ', '_')}.json"
                merged_file = os.path.join(RESULTS_DIR, filename)

                # Lưu kết quả vào file
                with open(merged_file, "w", encoding="utf-8") as f:
                    json.dump(summarize_results, f, indent=2, ensure_ascii=False)
                st.success(f"✅ Đã lưu kết quả hợp nhất vào: {merged_file}")

                df = pd.DataFrame(enriched_results)
                st.dataframe(df)

                st.download_button(
                    label="📥 Tải kết quả JSON",
                    data=open(merged_file, "rb").read(),
                    file_name=os.path.basename(merged_file),
                    mime="application/json"
                )


# ===================== TAB 3 =====================
with tab3:
    st.subheader("📂 Danh sách tất cả file kết quả đã lưu")

    files = sorted(glob.glob(os.path.join(RESULTS_DIR, "*.json")), key=os.path.getmtime, reverse=True)

    if not files:
        st.info("⚠️ Chưa có file kết quả nào được lưu.")
    else:
        for file_path in files:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path) / 1024  # KB
            st.write(f"**📄 {filename}** ({file_size:.2f} KB)")

            with open(file_path, "rb") as f:
                st.download_button(
                    label=f"📥 Tải {filename}",
                    data=f.read(),
                    file_name=filename,
                    mime="application/json",
                    key=filename
                )
            st.markdown("---")
