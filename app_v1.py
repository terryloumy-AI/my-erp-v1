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

# --- 1. 字體配置 (解決亂碼) ---
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

# --- 2. 登入檢查 ---
def check_password():
    if st.session_state.get("password_correct", False): return True

    st.title("🔒 跨境大健康 ERP 內部系統")
    pwd_input = st.text_input("授權密碼", type="password")
    if st.button("確定登入"):
        if pwd_input == "your_password": # ⚠️ 請在此修改您的密碼
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("❌ 密碼錯誤")
    return False

st.set_page_config(page_title="A's ERP 2.0.1 全功能版", layout="wide")

if check_password():
    # --- 3. 恢復側邊欄與同步功能 ---
    with st.sidebar:
        st.title("👤 系統管理")
        if st.button("🔄 同步 Shopify 最新數據"):
            st.cache_data.clear()
            st.toast("數據已更新！")
            st.rerun()
        st.divider()
        if st.button("🚪 安全登出"):
            st.session_state["password_correct"] = False
            st.rerun()
        st.write(f"版本: V 2.0.1 (全功能回歸)")

    # 數據獲取
    products, orders, sales_stats = shopify_engine.get_full_data()
    df_p = pd.DataFrame(products)
    df_o = pd.DataFrame(orders)

    # --- 4. 匯出工具函數 ---
    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    def export_dashboard_pdf(df_p, df_o, sales_stats, fig_obj):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        
        p.setFont(CHINESE_FONT, 20)
        p.drawString(50, height - 50, "營運分析與物流報表 (V2.0.1)")
        
        # 指標卡
        metrics = [
            ("總銷售額", f"${df_o['Total_USD'].sum():,.2f}"),
            ("總真實利潤", f"${sum(sales_stats.get(x['產品名稱'], 0) * x['毛利'] for x in products):,.2f}"),
            ("訂單數", str(len(df_o)))
        ]
        for i, (label, val) in enumerate(metrics):
            x_pos = 50 + (i * 170)
            p.roundRect(x_pos, height - 130, 150, 60, 10)
            p.setFont(CHINESE_FONT, 10); p.drawString(x_pos + 10, height - 90, label)
            p.setFont(CHINESE_FONT, 14); p.drawString(x_pos + 10, height - 115, val)

        # 內容列表
        p.setFont(CHINESE_FONT, 12); p.drawString(50, height - 160, "■ 產品獲利摘要")
        y = height - 185
        p.setFont(CHINESE_FONT, 9)
        for _, row in df_p.head(15).iterrows():
            p.drawString(55, y, f"{row['產品名稱'][:20]} | 售價: ${row['售價']} | 毛利: ${row['毛利']}")
            y -= 15

        # 穩定嵌入圖表
        img_buf = io.BytesIO()
        fig_obj.savefig(img_buf, format='png', bbox_inches='tight', dpi=100)
        img_buf.seek(0)
        p.drawImage(ImageReader(img_buf), 50, 50, width=500, height=220)
        
        p.showPage(); p.save()
        return buffer.getvalue()

    # --- 5. 介面呈現 ---
    st.title("🚀 跨境大健康智能管理系統 2.0.1")
    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    with tab2:
        st.header("營運分析與物流")
        
        # 指標顯示
        m1, m2, m3 = st.columns(3)
        total_sales = df_o['Total_USD'].sum()
        total_profit = sum(sales_stats.get(x['產品名稱'], 0) * x['毛利'] for x in products)
        m1.metric("總銷售額", f"${total_sales:,.2f}")
        m2.metric("總真實利潤", f"${total_profit:,.2f}")
        m3.metric("訂單數", len(df_o))

        # 核心：先準備好圖表 fig，避免 NameError
        fig_main, ax = plt.subplots(figsize=(10, 4))
        df_plot = pd.DataFrame([{"P": k, "Q": v} for k, v in sales_stats.items()]).sort_values("Q", ascending=False)
        ax.bar(df_plot["P"], df_plot["Q"], color='#3498db')
        plt.xticks(rotation=30, fontsize=8)
        plt.tight_layout()

        # 匯出區塊 (Excel + PDF)
        st.write("### 📥 數據導出")
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            st.download_button("📊 財務 Excel", data=to_excel(df_p), file_name='profit_analysis.xlsx')
        with col_btn2:
            pdf_data = export_dashboard_pdf(df_p, df_o, sales_stats, fig_main)
            st.download_button("📄 匯出所見即所得 PDF", data=pdf_data, file_name='erp_report_full.pdf')

        st.subheader("📊 產品獲利明細")
        st.dataframe(df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]], use_container_width=True)

        st.subheader("📈 產品銷售數量統計")
        st.pyplot(fig_main) # 使用剛創建好的 fig_main

    # 其他 Tab 保持邏輯...
