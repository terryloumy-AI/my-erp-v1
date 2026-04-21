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

# --- 1. 系統配置與字庫 ---
DB_FILE = "risk_words.txt"

def get_chinese_font():
    # 支援 Windows 與 Linux 環境的中文字體路徑
    font_paths = ["C:/Windows/Fonts/msjh.ttc", "C:/Windows/Fonts/simhei.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for path in font_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont('ChineseFont', path))
                return 'ChineseFont'
            except: continue
    return 'Helvetica'

CHINESE_FONT = get_chinese_font()

def load_risk_words():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return ["治癒", "療效", "根治", "副作用"]

def save_risk_words(words):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        for w in words: f.write(f"{w}\n")

# --- 2. 安全登入 ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    st.title("🔒 跨境大健康 ERP 內部系統")
    pwd_input = st.text_input("授權密碼", type="password")
    if st.button("確定登入"):
        if pwd_input == "your_password": # ⚠️ 請在此修改您的正確密碼
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("❌ 密碼錯誤")
    return False

st.set_page_config(page_title="A's ERP 2.1.3 完整商業版", layout="wide")

if check_password():
    # --- 3. 側邊欄 (同步功能) ---
    with st.sidebar:
        st.title("👤 系統管理")
        if st.button("🔄 同步 Shopify 最新數據"):
            st.cache_data.clear()
            st.toast("✅ 數據同步完成")
            st.rerun()
        st.divider()
        if st.button("🚪 安全登出"):
            st.session_state["password_correct"] = False
            st.rerun()
        st.info("版本: V 2.1.3 (功能全回歸)")

    # 獲取核心數據
    products, orders, sales_stats = shopify_engine.get_full_data()
    df_p = pd.DataFrame(products)
    df_o = pd.DataFrame(orders)
    
    # 動態匹配庫存欄位名稱 (防止 KeyError)
    stock_col = "現貨庫存" if "現貨庫存" in df_p.columns else ("現有庫存" if "現有庫存" in df_p.columns else "庫存")

    # --- 4. 匯出工具 ---
    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    def export_pdf_full(df_p, df_o, sales_stats, fig_obj):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        width, height = A4
        p.setFont(CHINESE_FONT, 20)
        p.drawString(50, height - 50, "營運分析與財務報表 (V2.1.3)")
        
        # 指標卡
        p.setFont(CHINESE_FONT, 12)
        p.drawString(50, height - 90, f"總銷售額: ${df_o['Total_USD'].sum():,.2f}")
        total_p = sum(sales_stats.get(x['產品名稱'], 0) * x['毛利'] for x in products)
        p.drawString(250, height - 90, f"總真實利潤: ${total_p:,.2f}")
        
        # 繪製圖表
        img_buf = io.BytesIO()
        fig_obj.savefig(img_buf, format='png', bbox_inches='tight')
        img_buf.seek(0)
        p.drawImage(ImageReader(img_buf), 50, 50, width=500, height=250)
        
        p.showPage(); p.save()
        return buffer.getvalue()

    # --- 5. 頁面分頁 ---
    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    # --- Tab 1: 庫存管理 ---
    with tab1:
        st.header("庫存監控與提醒")
        
        # 缺貨提醒區 (補回功能)
        st.subheader("⚠️ 缺貨報警清單")
        low_stock_threshold = 50
        df_low_stock = df_p[df_p[stock_col] < low_stock_threshold]
        if not df_low_stock.empty:
            st.error(f"警告：以下 {len(df_low_stock)} 項產品庫存低於 {low_stock_threshold} 件！")
            st.dataframe(df_low_stock[["產品名稱", stock_col, "售價"]], use_container_width=True)
        else:
            st.success("✅ 目前所有產品庫存充足。")
            
        st.divider()
        st.subheader("🛒 全品項庫存清單")
        st.dataframe(df_p[["產品名稱", stock_col, "售價", "成本"]], use_container_width=True)

    # --- Tab 2: 營運看板 ---
    with tab2:
        st.header("財務指標與營運分析")
        
        # 頂部指標
        m1, m2, m3, m4 = st.columns(4)
        total_rev = df_o['Total_USD'].sum()
        # 計算總利潤與平均毛利率
        total_profit = sum(sales_stats.get(x['產品名稱'], 0) * x['毛利'] for x in products)
        avg_margin = df_p['毛利率'].mean()
        
        m1.metric("總銷售額", f"${total_rev:,.2f}")
        m2.metric("總真實利潤", f"${total_profit:,.2f}")
        m3.metric("訂單總數", len(df_o))
        m4.metric("平均毛利率", f"{avg_margin:.1f}%")

        # 數據繪圖 (先定義 fig)
        fig_main, ax = plt.subplots(figsize=(10, 4))
        df_sales_bar = pd.DataFrame([{"P": k, "Q": v} for k, v in sales_stats.items()]).sort_values("Q", ascending=False)
        ax.bar(df_sales_bar["P"], df_sales_bar["Q"], color='#3498db')
        plt.xticks(rotation=30, fontsize=8)
        plt.tight_layout()

        # 匯出按鈕
        st.write("### 📥 報表導出 (所見即所得)")
        c_ex1, c_ex2 = st.columns([1, 4])
        with c_ex1:
            st.download_button("📊 財務 Excel", data=to_excel(df_p), file_name='finance_full.xlsx')
        with c_ex2:
            pdf_data = export_pdf_full(df_p, df_o, sales_stats, fig_main)
            st.download_button("📄 專業 PDF 報表 (不亂碼)", data=pdf_data, file_name='erp_report.pdf')

        # 財務明細表格 (
