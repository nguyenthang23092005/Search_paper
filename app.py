import streamlit as st
from springer_search import run_springer_search
from scholar_search import run_scholar_search
from crossref_search import search_crossref_ndt
from mdpi_search import run_mdpi_search
import pandas as pd
import os
import glob
import asyncio
import sys
from dotenv import load_dotenv, set_key

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# -------------------- PAGE CONFIG --------------------
st.set_page_config(page_title="Paper Search App", layout="wide")


# Load .env hiện tại
env_path = ".env"
if not os.path.exists(env_path):
    open(env_path, "a").close()  

load_dotenv(env_path)

st.sidebar.subheader("⚙️ Cấu hình API")
gg_api_key = st.sidebar.text_input(
    "Nhập Google API Key", 
    type="password", 
    placeholder="Nhập API Key..."
)

# Nút lưu vào .env
if st.sidebar.button("💾 Lưu API Key"):
    if gg_api_key.strip():
        # Ghi vào .env
        set_key(env_path, "GOOGLE_API_KEY", gg_api_key.strip())
        st.sidebar.success("✅ API Key đã lưu vào .env")
    else:
        st.sidebar.warning("⚠️ Vui lòng nhập API Key trước khi lưu")

RESULTS_DIR = "results"

# Tạo thư mục lưu kết quả nếu chưa có
if not os.path.exists(RESULTS_DIR):
    os.makedirs(RESULTS_DIR)

st.title("📚 Paper Search App")
st.write("Ứng dụng tìm kiếm bài báo")

# -------------------- TABS --------------------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🔍 Springer Search", 
    "🔎 Google Scholar Search", 
    "🔍 Mdpi Search",
    "⚡ Crossref Search", 
    "📁 Danh sách kết quả"
])

# -------------------- SPRINGER TAB --------------------
with tab1:
    st.subheader("Tìm kiếm trên Springer")
    springer_keyword = st.text_input("Nhập từ khóa tìm kiếm Springer:", key="springer_keyword")
    springer_max = st.number_input("Số lượng bài muốn lấy", min_value=1, max_value=20, value=5,key="springer_max")

    if st.button("Tìm kiếm Springer"):
        with st.spinner("Đang tìm kiếm..."):
            result = run_springer_search(springer_keyword, springer_max)

            if "error" in result:
                st.error(result["error"])
            else:
                # Đổi đường dẫn file sang thư mục results
                filename = os.path.join(RESULTS_DIR, os.path.basename(result['file']))
                os.rename(result['file'], filename)
                result['file'] = filename

                st.success(f"Đã lưu kết quả vào: {result['file']}")
                df = pd.DataFrame(result["data"])
                st.dataframe(df)

                st.download_button(
                    label="📥 Tải kết quả JSON",
                    data=open(result['file'], "rb").read(),
                    file_name=os.path.basename(result['file']),
                    mime="application/json"
                )

# -------------------- SCHOLAR TAB --------------------
with tab2:
    st.subheader("Tìm kiếm trên Google Scholar")
    scholar_keyword = st.text_input("Nhập từ khóa tìm kiếm Google Scholar:", key="scholar_keyword")
    scholar_max = st.number_input("Số lượng bài muốn lấy", min_value=1, max_value=20, value=5, key="scholar_max")

    if st.button("Tìm kiếm Google Scholar"):
        with st.spinner("Đang tìm kiếm..."):
            result = run_scholar_search(scholar_keyword, scholar_max)

            # Đổi đường dẫn file sang thư mục results
            filename = os.path.join(RESULTS_DIR, os.path.basename(result['file']))
            os.rename(result['file'], filename)
            result['file'] = filename

            st.success(f"Đã lưu kết quả vào: {result['file']}")
            df = pd.DataFrame(result["data"])
            st.dataframe(df)

            st.download_button(
                label="📥 Tải kết quả JSON",
                data=open(result['file'], "rb").read(),
                file_name=os.path.basename(result['file']),
                mime="application/json"
            )

# -------------------- MDPI TAB --------------------
with tab3:
    st.subheader("Tìm kiếm trên Mdpi")
    mdpi_keyword = st.text_input("Nhập từ khóa tìm kiếm Mdpi:", key="mdpi_keyword")
    mdpi_max = st.number_input("Số lượng bài muốn lấy", min_value=1, max_value=20, value=5, key="mdpi_max")

    if st.button("Tìm kiếm Mdpi"):
        with st.spinner("Đang tìm kiếm..."):
            result = run_mdpi_search(mdpi_keyword, mdpi_max)

            if "error" in result:
                st.error(result["error"])
            else:
                # Đổi đường dẫn file sang thư mục results
                filename = os.path.join(RESULTS_DIR, os.path.basename(result['file']))
                os.rename(result['file'], filename)
                result['file'] = filename

                st.success(f"Đã lưu kết quả vào: {result['file']}")
                df = pd.DataFrame(result["data"])
                st.dataframe(df)

                st.download_button(
                    label="📥 Tải kết quả JSON",
                    data=open(result['file'], "rb").read(),
                    file_name=os.path.basename(result['file']),
                    mime="application/json"
                )

# -------------------- CROSSREF TAB --------------------
with tab4:
    st.subheader("Tìm kiếm trên Crossref")
    crossref_keyword = st.text_input("Nhập từ khóa tìm kiếm Crossref:", key="crossref_keyword")
    crossref_max = st.number_input("Số lượng bài muốn lấy", min_value=1, max_value=20, value=5, key="crossref_max")

    if st.button("Tìm kiếm Crossref"):
        with st.spinner("Đang tìm kiếm Crossref..."):
            result = search_crossref_ndt(crossref_keyword, crossref_max)

            # Đổi đường dẫn file sang thư mục results
            filename = os.path.join(RESULTS_DIR, os.path.basename(result['file']))
            if result['file'] != filename:  # tránh rename nếu đã đúng
                os.rename(result['file'], filename)
                result['file'] = filename

            st.success(f"Đã lưu kết quả vào: {result['file']}")
            df = pd.DataFrame(result["data"])
            st.dataframe(df)

            st.download_button(
                label="📥 Tải kết quả JSON",
                data=open(result['file'], "rb").read(),
                file_name=os.path.basename(result['file']),
                mime="application/json"
            )

    
# -------------------- HIỂN THỊ TẤT CẢ FILE ĐÃ LƯU --------------------
with tab5:
    st.subheader("📂 Danh sách tất cả các file kết quả")

    # Lấy danh sách file JSON trong thư mục results
    files = sorted(glob.glob(os.path.join(RESULTS_DIR, "*.json")), key=os.path.getmtime, reverse=True)

    if not files:
        st.info("Chưa có file kết quả nào được lưu.")
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
