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
            except: continue
    return 'Helvetica'

CHINESE_FONT = get_chinese_font()

# --- 2. 登入邏輯 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: return True

    st.title("🔒 跨境大健康 ERP 內部系統")
    pwd_input = st.text_input("授權密碼", type="password")
    if st.button("確定登入"):
        if pwd_input == "your_password": # ⚠️ 請在此修改您的密碼
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("❌ 密碼錯誤")
    return False

st.set_page_config(page_title="A's ERP 2.0.0", layout="wide")

if check_password():
    # 數據獲取
    products, orders, sales_stats = shopify_engine.get_full_data()
    df_p = pd.DataFrame(products)
    df_o = pd.DataFrame(orders)

    # --- 3. 匯出工具函數 ---
    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    def export_dashboard_pdf(df_p, df_o, sales_stats, fig_to_draw):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        # 標題與指標
        p.setFont(CHINESE_FONT, 20)
        p.drawString(50, height - 50, "營運分析與物流報表 (V2.0.0)")
        
        # 指標卡片
        metrics = [
            ("總銷售額", f"${df_o['Total_USD'].sum():,.2f}"),
            ("總真實利潤", f"${sum(sales_stats.get(x['產品名稱'], 0) * x['毛利'] for x in products):,.2f}"),
            ("訂單數", str(len(df_o)))
        ]
        for i, (label, val) in enumerate(metrics):
            x = 50 + (i * 170)
            p.roundRect(x, height - 130, 150, 60, 10)
            p.setFont(CHINESE_FONT, 10); p.drawString(x + 10, height - 90, label)
            p.setFont(CHINESE_FONT, 14); p.drawString(x + 10, height - 115, val)

        # 產品明細
        p.setFont(CHINESE_FONT, 12); p.drawString(50, height - 160, "■ 產品獲利明細")
        y = height - 185
        p.setFont(CHINESE_FONT, 10)
        for _, row in df_p.head(10).iterrows():
            p.drawString(55, y, f"{row['產品名稱'][:15]} | ${row['售價']} | 毛利: ${row['毛利']}")
            y -= 18

        # 嵌入圖表 (修復報錯的核心)
        img_buf = io.BytesIO()
        fig_to_draw.savefig(img_buf, format='png', bbox_inches='tight')
        img_buf.seek(0)
        p.drawImage(ImageReader(img_buf), 50, 50, width=500, height=200)
        
        p.showPage(); p.save()
        return buffer.getvalue()

    # --- 4. 介面呈現 ---
    st.title("🚀 跨境大健康智能管理系統 2.0.0")
    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    with tab2:
        st.header("營運分析與物流")
        
        # 指標卡
        c1, c2, c3 = st.columns(3)
        total_sales = df_o['Total_USD'].sum()
        total_profit = sum(sales_stats.get(x['產品名稱'], 0) * x['毛利'] for x in products)
        c1.metric("總銷售額", f"${total_sales:,.2f}")
        c2.metric("總真實利潤", f"${total_profit:,.2f}")
        c3.metric("訂單數", len(df_o))

        # 匯出按鈕 (恢復 Excel 按鈕)
        st.write("### 📥 數據匯出")
        col_ex1, col_ex2 = st.columns([1, 1])
        with col_ex1:
            st.download_button("📊 匯出財務 Excel", data=to_excel(df_p), file_name='profit_analysis.xlsx')
        
        # 準備圖表
        fig, ax = plt.subplots(figsize=(10, 4))
        df_plot = pd.DataFrame([{"P": k, "Q": v} for k, v in sales_stats.items()]).sort_values("Q", ascending=False)
        ax.bar(df_plot["P"], df_plot["Q"], color='#3498db')
        plt.xticks(rotation=30)
        
        with col_ex2:
            # 傳遞 fig 給 PDF 函數，確保不會 NameError
            pdf_data = export_dashboard_pdf(df_p, df_o, sales_stats, fig)
            st.download_button("📄 匯出所見即所得 PDF", data=pdf_data, file_name='erp_report.pdf')

        st.subheader("📊 產品獲利明細")
        st.dataframe(df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]], use_container_width=True)

        st.subheader("📈 產品銷售數量統計")
        st.pyplot(fig) # 現在 fig 已經正確定義，不會報錯了
