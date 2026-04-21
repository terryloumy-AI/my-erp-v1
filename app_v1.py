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

# --- 1. 系統配置 ---
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

def load_risk_words():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return ["治癒", "療效", "根治", "副作用"]

def save_risk_words(words):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        for w in words: f.write(f"{w}\n")

# --- 2. 登入邏輯 ---
st.set_page_config(page_title="跨境大健康 ERP 2.2.1", layout="wide")

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.title("🔒 內部系統登入")
    pwd = st.text_input("輸入授權密碼", type="password")
    if st.button("確定登入"):
        if pwd == "your_password": # ⚠️ 請在此修改密碼
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("密碼錯誤")
else:
    # --- 數據準備 ---
    try:
        products, orders, sales_stats = shopify_engine.get_full_data()
        df_p = pd.DataFrame(products)
        df_o = pd.DataFrame(orders)
        
        # 欄位統一處理 (防出錯)
        stock_col = "現貨庫存" if "現貨庫存" in df_p.columns else ("現有庫存" if "現有庫存" in df_p.columns else "庫存")
    except Exception as e:
        st.error(f"數據加載出錯: {e}")
        st.stop()

    # --- 側邊欄 ---
    with st.sidebar:
        st.title("👤 系統管理")
        if st.button("🔄 同步 Shopify 最新數據"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        if st.button("🚪 安全登出"):
            st.session_state["password_correct"] = False
            st.rerun()

    # --- 分頁系統 ---
    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    # --- Tab 1: 庫存管理 ---
    with tab1:
        st.header("📦 庫存與補貨提醒")
        low_stock = df_p[df_p[stock_col] < 50]
        if not low_stock.empty:
            st.error(f"⚠️ 以下產品庫存低於 50 件，請及時補貨：")
            st.table(low_stock[["產品名稱", stock_col]])
        
        st.subheader("全品項庫存表")
        st.dataframe(df_p[["產品名稱", stock_col, "售價", "成本"]], use_container_width=True)

    # --- Tab 2: 營運看板 (重點修正) ---
    with tab2:
        st.header("💰 營運分析與物流跟進")
        
        # 1. 核心指標
        m1, m2, m3, m4 = st.columns(4)
        total_rev = df_o['Total_USD'].sum() if 'Total_USD' in df_o.columns else 0
        total_profit = sum(sales_stats.get(p['產品名稱'], 0) * p['毛利'] for p in products)
        m1.metric("總銷售額", f"${total_rev:,.2f}")
        m2.metric("總真實利潤", f"${total_profit:,.2f}")
        m3.metric("訂單總數", len(df_o))
        m4.metric("平均毛利率", f"{(df_p['毛利率'].mean()):.1f}%")

        # 2. 數據匯出按鈕
        st.write("### 📥 數據導出")
        c_btn1, c_btn2 = st.columns([1, 4])
        with c_btn1:
            # Excel 匯出
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_p.to_excel(writer, index=False, sheet_name='產品財務')
                df_o.to_excel(writer, index=False, sheet_name='訂單物流')
            st.download_button("📊 匯出完整 Excel", data=output.getvalue(), file_name='erp_data.xlsx')

        # 3. 產品財務明細 (您要求的統計圖上方)
        st.subheader("💵 產品財務獲利明細")
        st.dataframe(df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]].style.format({
            "售價": "${:.2f}", "成本": "${:.2f}", "毛利": "${:.2f}", "毛利率": "{:.1f}%"
        }), use_container_width=True)

        # 4. 銷售數量統計圖 (移至明細下方)
        st.subheader("📊 產品銷售數量統計")
        fig, ax = plt.subplots(figsize=(10, 3))
        df_bar = pd.DataFrame([{"產品": k, "銷量": v} for k, v in sales_stats.items()]).sort_values("銷量", ascending=False)
        if not df_bar.empty:
            ax.bar(df_bar["產品"], df_bar["銷量"], color='#3498db')
            plt.xticks(rotation=30, fontsize=8)
            plt.tight_layout()
            st.pyplot(fig)

        st.divider()

        # 5. 物流信息 (補回功能)
        st.subheader("🚚 訂單即時物流狀態")
        if not df_o.empty:
            # 根據截圖 image_ca4022，顯示關鍵物流欄位
            display_cols = ["Order_Number", "Fulfillment_Status", "Financial_Status", "Total_USD"]
            # 檢查欄位是否存在，不存在則顯示所有
            available_cols = [c for c in display_cols if c in df_o.columns]
            st.dataframe(df_o[available_cols if available_cols else df_o.columns], use_container_width=True)
        else:
            st.info("暫無訂單物流數據")

    # --- Tab 3: 文案合規 ---
    with tab3:
        st.header("🔍 文案檢查與字庫管理")
        cl1, cl2 = st.columns([2, 1])
        
        with cl2:
            st.subheader("🛡️ 字庫設定")
            current_words = load_risk_words()
            word_input = st.text_area("編輯違規詞庫 (每行一個)", value="\n".join(current_words), height=250)
            if st.button("💾 儲存並更新字庫"):
                save_risk_words([w.strip() for w in word_input.split("\n") if w.strip()])
                st.success("字庫已儲存！")
                st.rerun()

        with cl1:
            st.subheader("📝 文案檢測")
            test_text = st.text_area("請輸入待檢查的文案...", height=200)
            if st.button("🚀 執行合規檢查"):
                risks = load_risk_words()
                found = [w for w in risks if w in test_text]
                if found:
                    st.error(f"❌ 警告！發現違規詞彙：{', '.join(found)}")
                else:
                    st.success("✅ 檢測通過，文案安全。")
