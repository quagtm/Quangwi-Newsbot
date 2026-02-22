import streamlit as st
import google.generativeai as genai                                                                                                                                                                                                                               
import feedparser
import re
import urllib.request

# --- HÀM LỌC NỘI DUNG SIÊU SẠCH ---
def clean_content(raw_html):
    if not raw_html:
        return "Không có mô tả."
    # 1. Loại bỏ tất cả thẻ HTML
    clean = re.sub(r'<.*?>', '', raw_html)
    # 2. Loại bỏ các ký tự thừa như &nbsp; hoặc khoảng trắng dư
    clean = clean.replace('&nbsp;', ' ').strip()
    return clean

# --- HÀM LẤY TIN NÂNG CAO (Sửa lỗi chặn truy cập) ---
def get_rss_feed(url):
    try:
        # Giả lập trình duyệt để không bị Vietstock/Investing chặn
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        return feedparser.parse(response.read())
    except Exception as e:
        st.error(f"Không thể kết nối nguồn tin: {e}")
        return None

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Stock AI Assistant", layout="wide")
st.title("🕵️ Bot Tổng hợp & Phân tích Tin tức Chứng khoán")

# --- CẤU HÌNH API KEY ---
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    st.error("Chưa cấu hình API Key trong Secrets!")
    st.stop()

# --- DANH SÁCH NGUỒN TIN ---
SOURCES = {
    "CafeF (Chứng khoán)": "https://cafef.vn/thi-truong-chung-khoan.rss",
    "Vietstock (Thị trường)": "https://vietstock.vn/rss/thi-truong-chung-khoan.rss",
    "Investing.com (Tin thế giới)": "https://vn.investing.com/rss/news_25.rss"
}

selected_source = st.sidebar.selectbox("Chọn nguồn tin:", list(SOURCES.keys()))

if api_key:

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-2.5-flash')

    st.subheader(f"📥 Tin mới nhất từ {selected_source}")
    
    # Sử dụng hàm lấy tin nâng cao
    feed = get_rss_feed(SOURCES[selected_source])

    if feed and feed.entries:
        for i, entry in enumerate(feed.entries[:10]): 
            # Làm sạch dữ liệu gốc từ RSS
            raw_summary = clean_content(entry.get('summary', entry.get('description', '')))
            
            with st.expander(f"📰 {entry.title}"):
                # HIỂN THỊ TÓM TẮT CHI TIẾT TỪ AI NGAY ĐẦU
                st.markdown("### 📝 Tóm tắt chi tiết:")
                
                # Tạo một key riêng cho việc tóm tắt tự động để tránh load lại liên tục
                if f"summary_{i}" not in st.session_state:
                    with st.spinner("AI đang soạn bản tóm tắt chi tiết..."):
                        summary_prompt = f"Hãy tóm tắt chi tiết các ý chính và số liệu quan trọng của bản tin sau (khoảng 150 từ): {entry.title}. Nội dung: {raw_summary}"
                        try:
                            summary_res = model.generate_content(summary_prompt)
                            st.session_state[f"summary_{i}"] = summary_res.text
                        except:
                            st.session_state[f"summary_{i}"] = raw_summary

                st.write(st.session_state[f"summary_{i}"])
                st.write(f"[🔗 Đọc tin gốc tại đây]({entry.link})")
                
                st.divider()
                
                # NÚT PHÂN TÍCH CHUYÊN SÂU (ĐÁNH GIÁ MÃ CỔ PHIẾU)
                if st.button(f"🔍 Đánh giá tác động & Mã cổ phiếu", key=f"btn_{i}"):
                    analysis_prompt = f"""
                    Dựa trên tin tức: {entry.title}
                    Nội dung: {raw_summary}
                    
                    Hãy thực hiện đánh giá chuyên sâu:
                    1**Đánh giá tác động:** (Tích cực/Tiêu cực/Trung lập) và mức độ ảnh hưởng (1-10).
                    3. **Phân tích mã cổ phiếu:** Liệt kê các mã bị ảnh hưởng và giải thích tại sao họ bị tác động.
                    4. **Chiến lược đề xuất:** Nhà đầu tư nên làm gì (Mua/Bán/Quan sát) đối với các mã liên quan.
                    
                    Trả lời bằng tiếng Việt, trình bày sạch sẽ bằng Markdown.
                    """
                    with st.spinner("AI đang phân tích mã cổ phiếu..."):
                        response = model.generate_content(analysis_prompt)
                        st.info(response.text)
    else:
        st.error("Không thể kết nối nguồn tin.")
else:
    st.warning("Vui lòng nhập API Key.")
