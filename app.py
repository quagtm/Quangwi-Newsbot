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

# --- HÀM LẤY TIN NÂNG CAO ---
def get_rss_feed(url):
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            return feedparser.parse(response.read())
    except Exception as e:
        return None

# --- CẤU HÌNH GIAO DIỆN ---
st.set_page_config(page_title="Stock AI Assistant Pro", layout="wide")
st.title("🕵️ Bot Tổng hợp & Phân tích Tin tức Chứng khoán")

# --- XỬ LÝ API KEY BẢO MẬT ---
# Lấy trực tiếp từ Secrets, không hiện ô nhập liệu
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-2.5-flash')
else:
    st.error("❌ Lỗi: Chưa cấu hình GEMINI_API_KEY trong phần Secrets của Streamlit!")
    st.stop()

# --- DANH SÁCH NGUỒN TIN ---
SOURCES = {
    "CafeF (Chứng khoán)": "https://cafef.vn/thi-truong-chung-khoan.rss",
    "Vietstock (Thị trường)": "https://vietstock.vn/rss/thi-truong-chung-khoan.rss",
    "Investing.com (Tin thế giới)": "https://vn.investing.com/rss/news_25.rss"
}

st.sidebar.title("Cấu hình")
selected_source = st.sidebar.selectbox("Chọn nguồn tin:", list(SOURCES.keys()))
st.sidebar.success("✅ Đã kết nối API bảo mật")

# --- HIỂN THỊ TIN TỨC ---
st.subheader(f"📥 Tin mới nhất từ {selected_source}")
feed = get_rss_feed(SOURCES[selected_source])

if feed and feed.entries:
    for i, entry in enumerate(feed.entries[:10]): 
        # Làm sạch dữ liệu gốc
        raw_summary = clean_content(entry.get('summary', entry.get('description', '')))
        
        with st.expander(f"📰 {entry.title}"):
            st.markdown("### 📝 Tóm tắt chi tiết từ AI:")
            
            # Sử dụng session_state để lưu tóm tắt, tránh load lại khi nhấn nút khác
            summary_key = f"sum_{selected_source}_{i}"
            if summary_key not in st.session_state:
                with st.spinner("AI đang đọc bản tin..."):
                    try:
                        sum_prompt = f"Hãy tóm tắt chi tiết các ý chính và số liệu quan trọng của bản tin sau: {entry.title}. Nội dung: {raw_summary}"
                        summary_res = model.generate_content(sum_prompt)
                        st.session_state[summary_key] = summary_res.text
                    except:
                        st.session_state[summary_key] = raw_summary

            st.write(st.session_state[summary_key])
            st.write(f"[🔗 Đọc tin gốc tại đây]({entry.link})")
            
            st.divider()
            
            # NÚT PHÂN TÍCH CHUYÊN SÂU
            if st.button(f"🔍 Đánh giá tác động & Mã cổ phiếu", key=f"btn_{i}"):
                analysis_prompt = f"""
                Dựa trên tin tức: {entry.title}
                Nội dung: {raw_summary}
                
                Hãy thực hiện đánh giá chuyên sâu cho nhà đầu tư chứng khoán Việt Nam:
                1. **Đánh giá tác động:** (Tích cực/Tiêu cực/Trung lập) và mức độ ảnh hưởng (1-10).
                2. **Phân tích mã cổ phiếu:** Liệt kê các mã/ngành bị ảnh hưởng và giải thích lý do.
                3. **Chiến lược đề xuất:** Hành động cụ thể (Mua/Bán/Quan sát).
                
                Trả lời bằng tiếng Việt, định dạng Markdown rõ ràng.
                """
                with st.spinner("AI đang phân tích chuyên sâu..."):
                    try:
                        response = model.generate_content(analysis_prompt)
                        st.info(response.text)
                    except Exception as e:
                        st.error(f"Lỗi AI: {e}")
else:
    st.error("Không thể lấy dữ liệu. Vui lòng kiểm tra lại nguồn tin hoặc kết nối mạng.")
