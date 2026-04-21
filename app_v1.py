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

# --- 1. 字體與基礎配置 ---
def get_chinese_font():
    font_paths = ["C:/Windows/Fonts/msjh.ttc", "C:/Windows/Fonts/simhei.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('ChineseFont', path))
                return 'ChineseFont'
            except: continue
    return 'Helvetica'

CHINESE_FONT = get_chinese_font()

# --- 2. 登入系統 ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    st.title("🔒 跨境大健康 ERP 內部系統")
    pwd_input = st.text_input("授權密碼", type="password")
    if st.button("確定登入"):
        if pwd_input == "your_password": # ⚠️ 請在此修改密碼
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("❌ 密碼錯誤")
    return False

st.set_page_config(page_title="A's ERP 2.1.0 全整合版", layout="wide")

if check_password():
    # --- 3. 側邊欄 (同步功能回歸) ---
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
        st.info("版本: V 2.1.0 (修復空白頁面)")

    # 獲取核心數據
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
        p.drawString(50, height - 50, "營運分析與物流報表 (V2.1.0)")
        
        # 指標顯示
        metrics = [("總銷售額", f"${df_o['Total_USD'].sum():,.2f}"), ("總利潤", f"${sum(sales_stats.get(x['產品名稱'], 0) * x['毛利'] for x in products):,.2f}"), ("訂單數", str(len(df_o)))]
        for i, (label, val) in enumerate(metrics):
            x = 50 + (i * 170)
            p.roundRect(x, height - 130, 150, 60, 10)
            p.setFont(CHINESE_FONT, 10); p.drawString(x + 10, height - 90, label)
            p.setFont(CHINESE_FONT, 14); p.drawString(x + 10, height - 115, val)

        # 數據圖表
        img_buf = io.BytesIO()
        fig_obj.savefig(img_buf, format='png', bbox_inches='tight', dpi=100)
        img_buf.seek(0)
        p.drawImage(ImageReader(img_buf), 50, 50, width=500, height=220)
        p.showPage(); p.save()
        return buffer.getvalue()

    # --- 5. 頁面分頁 (全面修復) ---
    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    # --- Tab 1: 庫存管理 (不再空白) ---
    with tab1:
        st.header("庫存與產品狀態")
        st.write("### 🛒 產品即時清單")
        st.dataframe(df_p[["產品名稱", "現有庫存", "售價", "成本"]], use_container_width=True)
        st.divider()
        st.subheader("⚠️ 缺貨提醒")
        low_stock = df_p[df_p["現有庫存"] < 50]
        if not low_stock.empty:
            st.warning(f"目前有 {len(low_stock)} 項產品庫存不足 50 件")
            st.table(low_stock[["產品名稱", "現有庫存"]])

    # --- Tab 2: 營運看板 (修復 PDF 報錯) ---
    with tab2:
        st.header("營運分析與物流")
        m1, m2, m3 = st.columns(3)
        total_sales = df_o['Total_USD'].sum()
        total_profit = sum(sales_stats.get(x['產品名稱'], 0) * x['毛利'] for x in products)
        m1.metric("總銷售額", f"${total_sales:,.2f}")
        m2.metric("總真實利潤", f"${total_profit:,.2f}")
        m3.metric("訂單數", len(df_o))

        # 準備繪圖
        fig_main, ax = plt.subplots(figsize=(10, 4))
        df_plot = pd.DataFrame([{"P": k, "Q": v} for k, v in sales_stats.items()]).sort_values("Q", ascending=False)
        ax.bar(df_plot["P"], df_plot["Q"], color='#3498db')
        plt.xticks(rotation=30, fontsize=8)
        plt.tight_layout()

        st.write("### 📥 數據導出")
        c_btn1, c_btn2 = st.columns([1, 4])
        with c_btn1:
            st.download_button("📊 財務 Excel", data=to_excel(df_p), file_name='profit_analysis.xlsx')
        with c_btn2:
            pdf_data = export_dashboard_pdf(df_p, df_o, sales_stats, fig_main)
            st.download_button("📄 匯出所見即所得 PDF", data=pdf_data, file_name='erp_report.pdf')

        st.subheader("📊 產品獲利明細")
        st.dataframe(df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]], use_container_width=True)
        st.subheader("📈 產品銷售數量統計")
        st.pyplot(fig_main)

    # --- Tab 3: 文案合規 (不再空白) ---
    with tab3:
        st.header("🔍 廣告文案合規檢查")
        ad_text = st.text_area("請輸入待檢查的文案：", placeholder="例如：本產品能迅速治癒高血壓...")
        if st.button("開始掃描"):
            if ad_text:
                forbidden_words = ["治癒", "療效", "速效", "神藥", "根治"]
                found = [w for w in forbidden_words if w in ad_text]
                if found:
                    st.error(f"❌ 發現違規詞彙：{', '.join(found)}")
                    st.info("建議調整為：輔助、改善、舒緩等較為溫和的詞彙。")
                else:
                    st.success("✅ 未發現明顯違規詞彙。")
            else:
                st.warning("請先輸入文案。")
