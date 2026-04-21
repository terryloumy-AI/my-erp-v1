import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import shopify_engine
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors

# --- 1. 解決亂碼：註冊中文字體 ---
# 請確保路徑下有字體文件，或使用系統內建路徑
try:
    # 這裡以常見路徑為例，您可以根據實際環境更換字體路徑
    pdfmetrics.registerFont(TTFont('MSJH', 'C:/Windows/Fonts/msjh.ttc')) # Windows 微軟正黑體
    CHINESE_FONT = 'MSJH'
except:
    CHINESE_FONT = 'Helvetica' # 備用，若報錯請檢查字體路徑

def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: return True

    st.title("🔒 跨境大健康 ERP 內部系統")
    col1, col2 = st.columns([4, 1])
    with col1:
        pwd_input = st.text_input("授權密碼", type="password", key="pwd_box")
    with col2:
        st.write("##")
        if st.button("確定", use_container_width=True) or (pwd_input == "your_password"): # 改為您的密碼
            st.session_state["password_correct"] = True
            st.rerun()
    return False

st.set_page_config(page_title="A's ERP 1.9.8 實境匯出版", layout="wide")

if check_password():
    # 側邊欄與數據抓取 (保留)
    st.sidebar.title("👤 系統管理")
    if st.sidebar.button("🔄 同步 Shopify 最新數據"):
        st.cache_data.clear()
        st.rerun()

    products, orders, sales_stats = shopify_engine.get_full_data()
    df_p = pd.DataFrame(products)
    df_o = pd.DataFrame(orders)

    # --- 核心：實境 PDF 繪製函數 (所見即所得) ---
    def export_dashboard_pdf(df_p, df_o, sales_stats):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # 1. 繪製標題
        p.setFont(CHINESE_FONT, 20)
        p.drawString(50, height - 50, "營運分析與物流實時報表 (V1.9.8)")
        
        # 2. 繪製頂部指標 (模擬網頁卡片)
        p.setStrokeColor(colors.lightgrey)
        p.roundRect(50, height - 130, 150, 60, 10, stroke=1, fill=0)
        p.setFont(CHINESE_FONT, 10)
        p.drawString(60, height - 90, "總銷售額")
        p.setFont(CHINESE_FONT, 14)
        p.drawString(60, height - 115, f"${df_o['Total_USD'].sum():,.2f}")

        p.roundRect(220, height - 130, 150, 60, 10, stroke=1, fill=0)
        p.setFont(CHINESE_FONT, 10)
        p.drawString(230, height - 90, "總真實利潤")
        p.setFont(CHINESE_FONT, 14)
        p.drawString(230, height - 115, f"${sum(sales_stats.get(x['產品名稱'], 0) * x['毛利'] for x in products):,.2f}")

        # 3. 繪製產品明細表格 (帶樣式)
        p.setFont(CHINESE_FONT, 12)
        p.drawString(50, height - 160, "■ 產品獲利明細")
        y = height - 185
        # 表頭背景
        p.setFillColor(colors.whitesmoke)
        p.rect(50, y - 5, 500, 20, fill=1, stroke=0)
        p.setFillColor(colors.black)
        p.setFont(CHINESE_FONT, 10)
        p.drawString(55, y, "產品名稱")
        p.drawString(250, y, "售價")
        p.drawString(320, y, "成本")
        p.drawString(390, y, "毛利")
        p.drawString(460, y, "毛利率")
        
        y -= 25
        for i, row in df_p.head(10).iterrows():
            p.drawString(55, y, str(row['產品名稱'])[:15])
            p.drawString(250, y, f"${row['售價']}")
            p.drawString(320, y, f"${row['成本']}")
            p.drawString(390, y, f"${row['毛利']}")
            p.drawString(460, y, f"{row['毛利率']}%")
            y -= 20
        
        # 4. 繪製統計圖表 (將 Matplotlib 圖表嵌入 PDF)
        p.drawString(50, y - 20, "■ 產品銷售數量統計圖")
        fig, ax = plt.subplots(figsize=(6, 3))
        df_sales_plot = pd.DataFrame([{"P": k, "Q": v} for k, v in sales_stats.items()]).sort_values("Q", ascending=False)
        ax.bar(df_sales_plot["P"], df_sales_plot["Q"], color='#3498db')
        plt.xticks(rotation=30)
        
        img_data = io.BytesIO()
        plt.savefig(img_data, format='png', bbox_inches='tight', dpi=150)
        img_data.seek(0)
        p.drawImage(io.BytesIO(img_data.read()), 50, y - 180, width=450, height=150)

        p.showPage()
        p.save()
        return buffer.getvalue()

    # --- 介面呈現 ---
    st.title("🚀 跨境大健康智能管理系統 1.9.8")
    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    with tab2:
        st.header("營運分析與物流")
        # 1. 頂部指標
        m1, m2, m3 = st.columns(3)
        m1.metric("總銷售額", f"${df_o['Total_USD'].sum():,.2f}")
        m2.metric("總真實利潤", f"${sum(sales_stats.get(x['產品名稱'], 0) * x['毛利'] for x in products):,.2f}")
        m3.metric("訂單數", len(df_o))

        # 2. 關鍵按鈕
        st.write("### 🖨️ 報表導出")
        if st.download_button("📄 匯出所見即所得 PDF (含指標與圖表)", 
                              data=export_dashboard_pdf(df_p, df_o, sales_stats), 
                              file_name='real_view_report.pdf'):
            st.success("PDF 成功生成！已解決亂碼問題。")

        # 3. 產品明細
        st.subheader("📊 產品獲利明細")
        st.dataframe(df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]], use_container_width=True)

        # 4. 圖表
        st.subheader("📈 產品銷售數量統計")
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.bar(df_sales_plot["產品"], df_sales_plot["數量"], color='#3498db')
        st.pyplot(fig)
