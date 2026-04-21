import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import shopify_engine
import io
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

# --- 1. 解決亂碼與字體配置 ---
# 嘗試多種常見中文字體路徑，確保 Windows/Linux 都能盡量兼容
def get_chinese_font():
    font_paths = [
        "C:/Windows/Fonts/msjh.ttc",    # Windows 微軟正黑體
        "C:/Windows/Fonts/simhei.ttf",  # Windows 黑體
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" # Linux 備用
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('ChineseFont', path))
                return 'ChineseFont'
            except:
                continue
    return 'Helvetica' # 萬一都失敗的墊底方案

CHINESE_FONT = get_chinese_font()

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
        if st.button("確定", use_container_width=True):
            if pwd_input == "123456": # ⚠️ 請在此修改您的密碼
                st.session_state["password_correct"] = True
                st.rerun()
            else:
                st.error("❌ 密碼錯誤")
    return False

st.set_page_config(page_title="A's ERP 1.9.9 穩定導出版", layout="wide")

if check_password():
    # 側邊欄 (確保功能不丟失)
    st.sidebar.title("👤 系統管理")
    if st.sidebar.button("🔄 同步 Shopify 最新數據"):
        st.cache_data.clear()
        st.rerun()
    if st.sidebar.button("🚪 安全登出"):
        st.session_state["password_correct"] = False
        st.rerun()

    products, orders, sales_stats = shopify_engine.get_full_data()
    df_p = pd.DataFrame(products)
    df_o = pd.DataFrame(orders)

    # --- 核心：修復後的 PDF 導出函數 ---
    def export_dashboard_pdf(df_p, df_o, sales_stats):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # A. 標題
        p.setFont(CHINESE_FONT, 20)
        p.drawString(50, height - 50, "營運分析與物流實時報表 (V1.9.9)")
        
        # B. 指標卡片 (模擬 image_ca4022.png 的佈局)
        p.setStrokeColor(colors.lightgrey)
        metrics = [
            ("總銷售額", f"${df_o['Total_USD'].sum():,.2f}"),
            ("總真實利潤", f"${sum(sales_stats.get(x['產品名稱'], 0) * x['毛利'] for x in products):,.2f}"),
            ("訂單數", str(len(df_o)))
        ]
        for i, (label, val) in enumerate(metrics):
            x_pos = 50 + (i * 170)
            p.roundRect(x_pos, height - 130, 150, 60, 10, stroke=1, fill=0)
            p.setFont(CHINESE_FONT, 10)
            p.drawString(x_pos + 10, height - 90, label)
            p.setFont(CHINESE_FONT, 14)
            p.drawString(x_pos + 10, height - 115, val)

        # C. 產品明細表格
        p.setFont(CHINESE_FONT, 12)
        p.drawString(50, height - 160, "■ 產品獲利明細")
        y = height - 185
        p.setFillColor(colors.whitesmoke)
        p.rect(50, y - 5, 500, 20, fill=1, stroke=0)
        p.setFillColor(colors.black)
        p.setFont(CHINESE_FONT, 10)
        col_headers = ["產品名稱", "售價", "成本", "毛利", "毛利率"]
        x_offsets = [55, 250, 320, 390, 460]
        for txt, x in zip(col_headers, x_offsets):
            p.drawString(x, y, txt)
        
        y -= 20
        for _, row in df_p.head(12).iterrows():
            p.drawString(55, y, str(row['產品名稱'])[:18])
            p.drawString(250, y, f"${row['售價']}")
            p.drawString(320, y, f"${row['成本']}")
            p.drawString(390, y, f"${row['毛利']}")
            p.drawString(460, y, f"{row['毛利率']}%")
            y -= 18
            if y < 250: break # 防止重疊到圖表

        # D. 銷售統計圖 (修復 image_ca4769 中的 drawImage 報表錯誤)
        p.setFont(CHINESE_FONT, 12)
        p.drawString(50, y - 30, "■ 產品銷售數量統計圖")
        
        fig, ax = plt.subplots(figsize=(8, 4))
        df_sales_plot = pd.DataFrame([{"P": k, "Q": v} for k, v in sales_stats.items()]).sort_values("Q", ascending=False)
        ax.bar(df_sales_plot["P"], df_sales_plot["Q"], color='#3498db')
        plt.xticks(rotation=30, fontsize=8)
        
        # 關鍵修復：使用 ImageReader 處理 BytesIO
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format='png', bbox_inches='tight', dpi=150)
        img_buf.seek(0)
        img_reader = ImageReader(img_buf)
        p.drawImage(img_reader, 50, 50, width=500, height=200)

        p.showPage()
        p.save()
        return buffer.getvalue()

    # --- Streamlit 介面呈現 ---
    st.title("🚀 跨境大健康智能管理系統 1.9.9")
    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    with tab2:
        st.header("營運分析與物流")
        # 顯示指標與網頁一致
        c1, c2, c3 = st.columns(3)
        c1.metric("總銷售額", f"${df_o['Total_USD'].sum():,.2f}")
        c2.metric("總真實利潤", f"${sum(sales_stats.get(x['產品名稱'], 0) * x['毛利'] for x in products):,.2f}")
        c3.metric("訂單數", len(df_o))

        st.write("### 🖨️ 報表導出")
        # 點擊按鈕生成 PDF
        pdf_data = export_dashboard_pdf(df_p, df_o, sales_stats)
        st.download_button("📄 匯出所見即所得 PDF (已修復報錯)", data=pdf_data, file_name='erp_report_final.pdf')

        st.subheader("📊 產品獲利明細")
        st.dataframe(df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]], use_container_width=True)

        st.subheader("📈 產品銷售數量統計")
        st.pyplot(fig) # 複用生成的 fig

    # Tab 1 & 3 的功能保持不變...
