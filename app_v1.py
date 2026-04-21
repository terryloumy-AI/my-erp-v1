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

# --- 1. 基礎配置與持久化字庫 ---
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
    return ["治癒", "療效", "根治", "抗癌", "副作用"]

def save_risk_words(words):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        for w in words: f.write(f"{w}\n")

# --- 2. 登入系統 ---
st.set_page_config(page_title="跨境大健康 ERP 2.2.3", layout="wide")

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.title("🔒 跨境大健康 ERP 內部系統")
    pwd_input = st.text_input("請輸入授權密碼", type="password")
    if st.button("確定登入"):
        if pwd_input == "your_password": # ⚠️ 請在此修改密碼
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ 密碼錯誤")
else:
    # --- 3. 核心數據處理 ---
    try:
        products, orders, sales_stats = shopify_engine.get_full_data()
        df_p = pd.DataFrame(products)
        df_o = pd.DataFrame(orders)
        # 自動匹配庫存欄位
        stock_col = "現貨庫存" if "現貨庫存" in df_p.columns else ("現有庫存" if "現有庫存" in df_p.columns else "庫存")
    except Exception as e:
        st.error(f"Shopify 數據加載失敗: {e}")
        st.stop()

    # --- 4. 側邊欄 ---
    with st.sidebar:
        st.title("👤 系統管理")
        if st.button("🔄 同步最新數據"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        if st.button("🚪 安全登出"):
            st.session_state["password_correct"] = False
            st.rerun()
        st.info("版本: V 2.2.3 (回歸銷售情況表)")

    # --- 5. 功能分頁 ---
    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    # --- Tab 1: 庫存管理 ---
    with tab1:
        st.header("📦 庫存預警與清單")
        low_stock = df_p[df_p[stock_col] < 50]
        if not low_stock.empty:
            st.error(f"⚠️ 缺貨報警：以下產品庫存低於 50 件")
            st.dataframe(low_stock[["產品名稱", stock_col, "售價"]], use_container_width=True)
        else:
            st.success("✅ 庫存狀態良好")
        
        st.divider()
        st.subheader("🛒 實時庫存表")
        st.dataframe(df_p[["產品名稱", stock_col, "售價", "成本"]], use_container_width=True)

    # --- Tab 2: 營運看板 (重點回歸修正) ---
    with tab2:
        st.header("💰 營運與銷售分析")
        
        # A. 頂部核心指標
        m1, m2, m3, m4 = st.columns(4)
        total_rev = df_o['Total_USD'].sum() if 'Total_USD' in df_o.columns else 0
        total_profit = sum(sales_stats.get(p['產品名稱'], 0) * p['毛利'] for p in products)
        m1.metric("總銷售額", f"${total_rev:,.2f}")
        m2.metric("總真實利潤", f"${total_profit:,.2f}")
        m3.metric("訂單總數", len(df_o))
        m4.metric("平均毛利率", f"{(df_p['毛利率'].mean()):.1f}%")

        # B. 產品財務獲利明細
        st.subheader("💵 產品財務獲利明細")
        st.dataframe(df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]].style.format({
            "售價": "${:.2f}", "成本": "${:.2f}", "毛利": "${:.2f}", "毛利率": "{:.1f}%"
        }), use_container_width=True)

        st.divider()

        # C. 銷售情況表 (這是本次補回的核心表格)
        st.subheader("📋 產品銷售情況彙總")
        sales_summary = []
        for p_name, qty in sales_stats.items():
            price = df_p[df_p["產品名稱"] == p_name]["售價"].iloc[0] if p_name in df_p["產品名稱"].values else 0
            sales_summary.append({
                "產品名稱": p_name,
                "銷售數量": qty,
                "銷售總額": qty * price
            })
        df_summary = pd.DataFrame(sales_summary).sort_values("銷售數量", ascending=False)
        if not df_summary.empty:
            st.dataframe(df_summary.style.format({
                "銷售總額": "${:.2f}", "銷售數量": "{:,.0f}"
            }), use_container_width=True)
        else:
            st.info("暫無銷售統計數據")

        # D. 產品銷售數量分布圖
        st.subheader("📊 產品銷售數量分布圖")
        fig, ax = plt.subplots(figsize=(10, 3.5))
        if not df_summary.empty:
            ax.bar(df_summary["產品名稱"], df_summary["銷售數量"], color='#3498db')
            plt.xticks(rotation=30, fontsize=8)
            plt.tight_layout()
            st.pyplot(fig)

        st.divider()

        # E. 物流跟進 (修復欄位顯示)
        st.subheader("🚚 訂單即時物流狀態")
        if not df_o.empty:
            logistics_cols = ["Order_Number", "name", "Fulfillment_Status", "fulfillment_status", "Financial_Status", "Total_USD"]
            valid_cols = [c for c in logistics_cols if c in df_o.columns]
            # 確保不會只顯示金額，至少顯示訂單號與狀態
            st.dataframe(df_o[valid_cols] if len(valid_cols) > 1 else df_o, use_container_width=True)

    # --- Tab 3: 文案合規 ---
    with tab3:
        st.header("🔍 合規檢查與字庫管理")
        c_l, c_r = st.columns([2, 1])
        
        with c_r:
            st.subheader("🛡️ 字庫設定")
            current_words = load_risk_words()
            new_text = st.text_area("編輯違規詞庫 (每行一詞)", value="\n".join(current_words), height=300)
            if st.button("💾 永久儲存字庫"):
                save_risk_words([w.strip() for w in new_text.split("\n") if w.strip()])
                st.success("字庫已更新並寫入 risk_words.txt")
                st.rerun()

        with c_l:
            st.subheader("📝 文案掃描")
            input_text = st.text_area("貼入待測文案...", height=200)
            if st.button("🚀 開始檢測"):
                risks = load_risk_words()
                found = [w for w in risks if w in input_text]
                if found: st.error(f"❌ 發現違規詞：{', '.join(found)}")
                else: st.success("✅ 檢測通過")
