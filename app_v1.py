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

# --- 1. 基礎配置與字庫管理 ---
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

# --- 2. 登入系統 ---
st.set_page_config(page_title="跨境大健康 ERP 最終整合版", layout="wide")

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.title("🔒 跨境大健康 ERP 內部系統")
    pwd_input = st.text_input("請輸入授權密碼", type="password")
    if st.button("確定登入"):
        if pwd_input == "your_password":  # ⚠️ 請在此修改您的正確密碼
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("❌ 密碼錯誤")
else:
    # --- 3. 數據核心加載 ---
    try:
        products, orders, sales_stats = shopify_engine.get_full_data()
        df_p = pd.DataFrame(products)
        df_o = pd.DataFrame(orders)
        
        # 動態兼容庫存欄位
        stock_col = "現貨庫存" if "現貨庫存" in df_p.columns else ("現有庫存" if "現有庫存" in df_p.columns else "庫存")
    except Exception as e:
        st.error(f"數據加載出錯，請檢查 shopify_engine.py: {e}")
        st.stop()

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
        st.info("版本: V 2.2.2 (全需求覆蓋版)")

    # --- 5. 功能分頁 ---
    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    # --- Tab 1: 庫存管理 ---
    with tab1:
        st.header("📦 庫存監控與缺貨預警")
        
        # 缺貨提醒 (50件臨界點)
        low_stock = df_p[df_p[stock_col] < 50]
        if not low_stock.empty:
            st.error(f"⚠️ 警告：有 {len(low_stock)} 項產品庫存低於 50 件！")
            st.dataframe(low_stock[["產品名稱", stock_col, "售價"]], use_container_width=True)
        else:
            st.success("✅ 目前庫存充足")
            
        st.divider()
        st.subheader("🛒 產品實時清單")
        st.dataframe(df_p[["產品名稱", stock_col, "售價", "成本"]], use_container_width=True)

    # --- Tab 2: 營運看板 ---
    with tab2:
        st.header("💰 財務分析與物流跟進")
        
        # A. 頂部四大指標
        m1, m2, m3, m4 = st.columns(4)
        total_rev = df_o['Total_USD'].sum() if 'Total_USD' in df_o.columns else 0
        total_profit = sum(sales_stats.get(p['產品名稱'], 0) * p['毛利'] for p in products)
        m1.metric("總銷售額", f"${total_rev:,.2f}")
        m2.metric("總真實利潤", f"${total_profit:,.2f}")
        m3.metric("訂單總數", len(df_o))
        m4.metric("平均毛利率", f"{(df_p['毛利率'].mean()):.1f}%")

        # B. 產品財務明細
        st.subheader("💵 產品財務獲利明細")
        st.dataframe(df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]].style.format({
            "售價": "${:.2f}", "成本": "${:.2f}", "毛利": "${:.2f}", "毛利率": "{:.1f}%"
        }), use_container_width=True)

        # C. 銷售數量統計 (置於明細下方)
        st.subheader("📊 產品銷售數量分布")
        fig, ax = plt.subplots(figsize=(10, 3.5))
        df_bar = pd.DataFrame([{"產品": k, "銷量": v} for k, v in sales_stats.items()]).sort_values("銷量", ascending=False)
        if not df_bar.empty:
            ax.bar(df_bar["產品"], df_bar["銷量"], color='#3498db')
            plt.xticks(rotation=30, fontsize=8)
            plt.tight_layout()
            st.pyplot(fig)

        st.divider()

        # D. 物流數據修正 (確保顯示訂單號與配送狀態)
        st.subheader("🚚 訂單即時物流狀態")
        if not df_o.empty:
            # 優先嘗試顯示的物流相關欄位
            logistics_cols = ["Order_Number", "name", "Fulfillment_Status", "fulfillment_status", "Financial_Status", "Total_USD"]
            valid_cols = [c for c in logistics_cols if c in df_o.columns]
            
            # 如果有效欄位只有 Total_USD，說明篩選失敗，顯示全部以保證信息不丟失
            if len(valid_cols) <= 1:
                st.dataframe(df_o, use_container_width=True)
            else:
                st.dataframe(df_o[valid_cols], use_container_width=True)
        else:
            st.info("暫無訂單數據")

    # --- Tab 3: 文案合規 ---
    with tab3:
        st.header("🔍 廣告合規與字庫管理")
        col_left, col_right = st.columns([2, 1])
        
        with col_right:
            st.subheader("🛡️ 字庫設定")
            current_risk_words = load_risk_words()
            edited_words = st.text_area("編輯違規詞庫 (每行一詞)", value="\n".join(current_risk_words), height=300)
            if st.button("💾 儲存字庫設定"):
                save_risk_words([w.strip() for w in edited_words.split("\n") if w.strip()])
                st.success("字庫已成功儲存至文件！")
                st.rerun()

        with col_left:
            st.subheader("📝 文案合規檢測")
            check_text = st.text_area("請輸入待測文案內容...", height=200)
            if st.button("🚀 開始掃描"):
                if check_text:
                    active_risks = load_risk_words()
                    found_risks = [w for w in active_risks if w in check_text]
                    if found_risks:
                        st.error(f"❌ 發現禁語：{', '.join(found_risks)}")
                    else:
                        st.success("✅ 檢測通過，暫無合規風險。")
