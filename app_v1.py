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
from reportlab.lib.utils import ImageReader

# --- 1. 字體與字庫文件配置 ---
DB_FILE = "risk_words.txt"

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

# --- 2. 字庫儲存邏輯 ---
def load_risk_words():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return ["治癒", "療效", "根治", "抗癌", "副作用"]

def save_risk_words(words):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        for w in words: f.write(f"{w}\n")

# --- 3. 權限檢查 ---
def check_password():
    if st.session_state.get("password_correct", False): return True
    st.title("🔒 跨境大健康 ERP 內部系統")
    pwd_input = st.text_input("授權密碼", type="password")
    if st.button("確定登入"):
        if pwd_input == "123456": # ⚠️ 請在此修改密碼
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("❌ 密碼錯誤")
    return False

st.set_page_config(page_title="A's ERP 2.1.2", layout="wide")

if check_password():
    # --- 4. 側邊欄 ---
    with st.sidebar:
        st.title("👤 系統管理")
        if st.button("🔄 同步 Shopify 最新數據"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        if st.button("🚪 安全登出"):
            st.session_state["password_correct"] = False
            st.rerun()

    # 獲取數據
    products, orders, sales_stats = shopify_engine.get_full_data()
    df_p = pd.DataFrame(products)
    df_o = pd.DataFrame(orders)
    
    # 自動偵測庫存欄位 (修復之前的 KeyError)
    stock_col = "現貨庫存" if "現貨庫存" in df_p.columns else ("現有庫存" if "現有庫存" in df_p.columns else None)

    # --- 5. 工具函數 (Excel/PDF) ---
    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    def export_pdf(df_p, df_o, sales_stats, fig_obj):
        buffer = io.BytesIO()
        p = canvas.Canvas(buffer, pagesize=A4)
        p.setFont(CHINESE_FONT, 20)
        p.drawString(50, 800, "營運分析報表 V2.1.2")
        # 繪製指標
        p.setFont(CHINESE_FONT, 12)
        p.drawString(50, 750, f"總銷售額: ${df_o['Total_USD'].sum():,.2f}")
        p.drawString(250, 750, f"訂單總數: {len(df_o)}")
        # 繪製圖表
        img_buf = io.BytesIO()
        fig_obj.savefig(img_buf, format='png', bbox_inches='tight')
        img_buf.seek(0)
        p.drawImage(ImageReader(img_buf), 50, 450, width=500, height=250)
        p.showPage(); p.save()
        return buffer.getvalue()

    # --- 6. 頁面佈局 ---
    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    # Tab 1: 庫存管理
    with tab1:
        st.header("庫存與產品狀態")
        cols = ["產品名稱", "售價", "成本"]
        if stock_col: cols.insert(1, stock_col)
        st.dataframe(df_p[cols], use_container_width=True)

    # Tab 2: 營運看板
    with tab2:
        st.header("營運分析與匯出")
        m1, m2, m3 = st.columns(3)
        total_profit = sum(sales_stats.get(x['產品名稱'], 0) * x['毛利'] for x in products)
        m1.metric("總銷售額", f"${df_o['Total_USD'].sum():,.2f}")
        m2.metric("總真實利潤", f"${total_profit:,.2f}")
        m3.metric("訂單數", len(df_o))

        # 繪圖
        fig, ax = plt.subplots(figsize=(10, 4))
        df_plot = pd.DataFrame([{"P": k, "Q": v} for k, v in sales_stats.items()]).sort_values("Q", ascending=False)
        ax.bar(df_plot["P"], df_plot["Q"], color='#3498db')
        plt.xticks(rotation=30, fontsize=8)
        plt.tight_layout()

        # 匯出按鈕
        c_ex1, c_ex2 = st.columns([1, 4])
        with c_ex1:
            st.download_button("📊 財務 Excel", data=to_excel(df_p), file_name='finance.xlsx')
        with c_ex2:
            st.download_button("📄 所見即所得 PDF", data=export_pdf(df_p, df_o, sales_stats, fig), file_name='report.pdf')
        
        st.pyplot(fig)

    # Tab 3: 文案合規 (加回儲存字庫功能)
    with tab3:
        st.header("🔍 廣告文案合規與字庫管理")
        col_scan, col_db = st.columns([2, 1])
        
        with col_db:
            st.subheader("🛡️ 管理違規字庫")
            current_words = load_risk_words()
            # 讓用戶可以在此輸入並儲存
            new_words_str = st.text_area("編輯字庫 (每行一個詞)", value="\n".join(current_words), height=300)
            if st.button("💾 儲存字庫設定"):
                word_list = [w.strip() for w in new_words_str.split("\n") if w.strip()]
                save_risk_words(word_list)
                st.success("字庫已永久儲存！")
                st.rerun()

        with col_scan:
            st.subheader("📝 文案安全檢測")
            user_text = st.text_area("請輸入產品描述內容...", height=200)
            if st.button("🚀 開始掃描"):
                if user_text:
                    risk_list = load_risk_words()
                    found = [w for w in risk_list if w in user_text]
                    if found:
                        st.error(f"❌ 發現違規字眼：{', '.join(found)}")
                    else:
                        st.success("✅ 掃描完成：未發現預設風險。")
