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

# --- 1. 字庫與 PDF 導出配置 ---
DB_FILE = "risk_words.txt"

def get_chinese_font():
    # 嘗試多個路徑以確保不同系統都能找到中文字型
    font_paths = [
        "C:/Windows/Fonts/msjh.ttc",    # Windows 微軟正黑體
        "C:/Windows/Fonts/simhei.ttf",  # Windows 黑體
        "/System/Library/Fonts/STHeiti Light.ttc", # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf" # Linux 後備
    ]
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
    return ["治癒", "療效", "根治", "副作用", "抗癌"]

def save_risk_words(words):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        for w in words: f.write(f"{w}\n")

# --- 2. 登入系統 ---
st.set_page_config(page_title="跨境大健康 ERP 完美版 V2.2.4", layout="wide")

if "password_correct" not in st.session_state:
    st.session_state["password_correct"] = False

if not st.session_state["password_correct"]:
    st.title("🔒 跨境大健康 ERP 內部管理系統")
    pwd = st.text_input("輸入授權密碼", type="password")
    if st.button("登入系統"):
        if pwd == "your_password": # ⚠️ 請在此修改密碼
            st.session_state["password_correct"] = True
            st.rerun()
        else: st.error("密碼錯誤")
else:
    # --- 3. 數據加載 ---
    try:
        products, orders, sales_stats = shopify_engine.get_full_data()
        df_p = pd.DataFrame(products)
        df_o = pd.DataFrame(orders)
        stock_col = "現貨庫存" if "現貨庫存" in df_p.columns else ("現有庫存" if "現有庫存" in df_p.columns else "庫存")
    except Exception as e:
        st.error(f"數據加載出錯: {e}")
        st.stop()

    # --- 4. 側邊欄 ---
    with st.sidebar:
        st.title("👤 系統管理")
        if st.button("🔄 同步數據"):
            st.cache_data.clear()
            st.rerun()
        st.divider()
        if st.button("🚪 安全登出"):
            st.session_state["password_correct"] = False
            st.rerun()
        st.info("版本: V 2.2.4 (全功能整合)")

    # --- 5. 分頁功能 ---
    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    # --- Tab 1: 庫存管理 ---
    with tab1:
        st.header("📦 庫存監控")
        low_stock = df_p[df_p[stock_col] < 50]
        if not low_stock.empty:
            st.error(f"⚠️ 缺貨提醒：有 {len(low_stock)} 項產品庫存低於 50 件")
            st.dataframe(low_stock[["產品名稱", stock_col, "售價"]], use_container_width=True)
        else:
            st.success("✅ 庫存水平安全")
        
        st.divider()
        st.subheader("實時庫存清單")
        st.dataframe(df_p[["產品名稱", stock_col, "售價", "成本"]], use_container_width=True)

    # --- Tab 2: 營運看板 (核心修正版) ---
    with tab2:
        st.header("💰 營運分析看板")
        
        # A. 核心指標
        m1, m2, m3, m4 = st.columns(4)
        total_rev = df_o['Total_USD'].sum() if 'Total_USD' in df_o.columns else 0
        total_profit = sum(sales_stats.get(p['產品名稱'], 0) * p['毛利'] for p in products)
        m1.metric("總銷售額", f"${total_rev:,.2f}")
        m2.metric("總真實利潤", f"${total_profit:,.2f}")
        m3.metric("訂單總數", len(df_o))
        m4.metric("平均毛利率", f"{(df_p['毛利率'].mean()):.1f}%")

        # B. 匯出功能按鈕 (回歸！)
        st.write("### 📥 數據導出中心")
        btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 3])
        
        with btn_col1:
            # Excel 導出邏輯
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_p.to_excel(writer, index=False, sheet_name='財務明細')
                df_o.to_excel(writer, index=False, sheet_name='物流訂單')
            st.download_button("📊 匯出 Excel", data=output.getvalue(), file_name='ERP_Report.xlsx')

        with btn_col2:
            # PDF 導出邏輯 (簡化版示意)
            pdf_buffer = io.BytesIO()
            p_pdf = canvas.Canvas(pdf_buffer, pagesize=A4)
            p_pdf.setFont(CHINESE_FONT, 16)
            p_pdf.drawString(100, 800, f"營運報告 - 總銷售: ${total_rev:,.2f}")
            p_pdf.save()
            st.download_button("📄 匯出 PDF", data=pdf_buffer.getvalue(), file_name='ERP_Report.pdf')

        st.divider()

        # C. 產品財務獲利明細
        st.subheader("💵 產品財務獲利明細")
        st.dataframe(df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]].style.format({
            "售價": "${:.2f}", "成本": "${:.2f}", "毛利": "${:.2f}", "毛利率": "{:.1f}%"
        }), use_container_width=True)

        # D. 產品銷售情況彙總 (表格)
        st.subheader("📋 產品銷售情況彙總")
        sales_summary = []
        for p_name, qty in sales_stats.items():
            price = df_p[df_p["產品名稱"] == p_name]["售價"].iloc[0] if p_name in df_p["產品名稱"].values else 0
            sales_summary.append({"產品名稱": p_name, "銷售數量": qty, "銷售總額": qty * price})
        df_summary = pd.DataFrame(sales_summary).sort_values("銷售數量", ascending=False)
        st.dataframe(df_summary.style.format({"銷售總額": "${:.2f}"}), use_container_width=True)

        # E. 產品銷售數量分布 (圖表)
        st.subheader("📊 產品銷售數量分布圖")
        fig, ax = plt.subplots(figsize=(10, 3.5))
        if not df_summary.empty:
            ax.bar(df_summary["產品名稱"], df_summary["銷售數量"], color='#3498db')
            plt.xticks(rotation=30, fontsize=8)
            plt.tight_layout()
            st.pyplot(fig)

        st.divider()

        # F. 物流跟進 (確保顯示正確)
        st.subheader("🚚 訂單即時物流狀態")
        if not df_o.empty:
            log_cols = ["Order_Number", "name", "Fulfillment_Status", "fulfillment_status", "Financial_Status", "Total_USD"]
            valid_log_cols = [c for c in log_cols if c in df_o.columns]
            st.dataframe(df_o[valid_log_cols] if len(valid_log_cols) > 1 else df_o, use_container_width=True)

    # --- Tab 3: 文案合規 ---
    with tab3:
        st.header("🔍 文案合規檢測")
        c1, c2 = st.columns([2, 1])
        with c2:
            st.subheader("🛡️ 字庫管理")
            current_words = load_risk_words()
            edited = st.text_area("編輯詞庫 (每行一詞)", value="\n".join(current_words), height=300)
            if st.button("💾 儲存字庫"):
                save_risk_words([w.strip() for w in edited.split("\n") if w.strip()])
                st.success("字庫已儲存")
                st.rerun()
        with c1:
            st.subheader("📝 內容掃描")
            text_to_check = st.text_area("在此輸入文案...", height=200)
            if st.button("🚀 開始檢測"):
                risk_list = load_risk_words()
                found = [w for w in risk_list if w in text_to_check]
                if found: st.error(f"❌ 發現禁語：{', '.join(found)}")
                else: st.success("✅ 文案安全")
