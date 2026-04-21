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

# --- 1. 基礎配置與字庫 ---
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

# --- 2. 數據處理優化 (防止 KeyError) ---
def safe_get_df_p(products):
    df = pd.DataFrame(products)
    # 強制檢查並補齊財務欄位，若遺失則設為 0
    cols = ["產品名稱", "現有庫存", "售價", "成本", "毛利", "毛利率"]
    for col in cols:
        if col not in df.columns:
            if col == "現有庫存" and "現貨庫存" in df.columns:
                df["現有庫存"] = df["現貨庫存"]
            else:
                df[col] = 0
    return df[cols]

# --- 3. 頁面配置 ---
st.set_page_config(page_title="跨境大健康 ERP 2.2.0 整合版", layout="wide")

# 安全登入
if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.title("🔒 內部系統登入")
    pwd = st.text_input("輸入授權密碼", type="password")
    if st.button("登入"):
        if pwd == "your_password": # ⚠️ 請在此修改密碼
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("密碼錯誤")
else:
    # --- 數據加載 ---
    try:
        raw_products, raw_orders, sales_stats = shopify_engine.get_full_data()
        df_p = safe_get_df_p(raw_products)
        df_o = pd.DataFrame(raw_orders)
    except Exception as e:
        st.error(f"數據加載出錯: {e}")
        st.stop()

    # --- 側邊欄 ---
    with st.sidebar:
        st.title("👤 系統管理")
        if st.button("🔄 同步數據"):
            st.cache_data.clear()
            st.rerun()
        st.info("版本: V 2.2.0 (需求完整修復)")

    # --- 分頁系統 ---
    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    # --- Tab 1: 庫存管理 ---
    with tab1:
        st.header("庫存監控")
        low_stock = df_p[df_p["現有庫存"] < 50]
        if not low_stock.empty:
            st.error(f"⚠️ 缺貨警告：有 {len(low_stock)} 項產品庫存低於 50 件")
            st.dataframe(low_stock, use_container_width=True)
        else:
            st.success("✅ 庫存水平正常")
        
        st.divider()
        st.subheader("全品項清單")
        st.dataframe(df_p, use_container_width=True)

    # --- Tab 2: 營運看板 ---
    with tab2:
        st.header("財務指標與營運分析")
        
        # 頂部四大指標
        m1, m2, m3, m4 = st.columns(4)
        total_rev = df_o['Total_USD'].sum() if 'Total_USD' in df_o.columns else 0
        total_profit = (df_p['毛利'] * df_p['產品名稱'].map(sales_stats).fillna(0)).sum()
        avg_margin = df_p['毛利率'].mean()
        
        m1.metric("總銷售額", f"${total_rev:,.2f}")
        m2.metric("總真實利潤", f"${total_profit:,.2f}")
        m3.metric("訂單總數", len(df_o))
        m4.metric("平均毛利率", f"{avg_margin:.1f}%")

        # 銷售圖表 (定義 fig 解決 NameError)
        fig, ax = plt.subplots(figsize=(10, 4))
        df_bar = pd.DataFrame([{"P": k, "Q": v} for k, v in sales_stats.items()]).sort_values("Q", ascending=False)
        if not df_bar.empty:
            ax.bar(df_bar["P"], df_bar["Q"], color='#3498db')
            plt.xticks(rotation=30)
            st.subheader("📈 產品銷售分布")
            st.pyplot(fig)
        
        # 財務表格
        st.subheader("💵 產品財務明細")
        st.dataframe(df_p.style.format({
            "售價": "${:.2f}", "成本": "${:.2f}", "毛利": "${:.2f}", "毛利率": "{:.1f}%"
        }), use_container_width=True)

    # --- Tab 3: 文案合規 ---
    with tab3:
        st.header("文案合規檢查")
        c1, c2 = st.columns([2, 1])
        
        with c2:
            st.subheader("🛡️ 字庫管理")
            words = load_risk_words()
            new_words = st.text_area("編輯違規詞 (每行一個)", value="\n".join(words), height=200)
            if st.button("保存字庫"):
                save_risk_words([w.strip() for w in new_words.split("\n") if w.strip()])
                st.success("字庫已更新")
                st.rerun()

        with c1:
            st.subheader("📝 內容掃描")
            text = st.text_area("貼入待檢查文案", height=200)
            if st.button("開始掃描"):
                risks = load_risk_words()
                found = [w for w in risks if w in text]
                if found: st.error(f"❌ 發現違規詞：{', '.join(found)}")
                else: st.success("✅ 檢查通過")
