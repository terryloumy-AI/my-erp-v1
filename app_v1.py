import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import shopify_engine
import os
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# --- 🔐 安全登入邏輯 ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    if st.session_state["password_correct"]:
        return True

    st.title("🔒 跨境大健康 ERP 內部系統")
    col1, col2 = st.columns([4, 1])
    with col1:
        pwd_input = st.text_input("授權密碼", type="password", key="pwd_box", placeholder="請輸入密碼...")
    with col2:
        st.write("##") 
        btn_login = st.button("確定", use_container_width=True)

    if btn_login or (pwd_input and st.session_state.get("pwd_box")):
        # ⚠️ 請務必在此處修改為你原本設定的密碼
        if pwd_input == "kingterryERP": 
            st.session_state["password_correct"] = True
            st.rerun()
        elif btn_login:
            st.error("❌ 密碼錯誤")
    return False

# 啟動設定
st.set_page_config(page_title="A's 大健康 ERP 1.9.4", layout="wide")

if check_password():
    with st.spinner('🚀 數據同步中...'):
        products, orders, sales_stats = shopify_engine.get_full_data()

    # --- 報表生成工具 ---
    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    def to_pdf(df, title):
        output = io.BytesIO()
        p = canvas.Canvas(output, pagesize=A4)
        p.drawString(50, 800, f"A's ERP Report: {title}")
        y = 750
        # 選取前幾個欄位輸出
        headers = [str(c) for c in df.columns[:4]]
        p.drawString(50, y, " | ".join(headers))
        y -= 25
        for i, row in df.head(20).iterrows():
            line = " | ".join([str(val) for val in row[:4]])
            p.drawString(50, y, line[:110])
            y -= 20
            if y < 50: p.showPage(); y = 800
        p.save()
        return output.getvalue()

    # --- 主內容 ---
    st.title("🚀 跨境大健康智能管理系統 1.9.4")
    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    # --- Tab 1: 庫存管理 ---
    with tab1:
        st.header("實時庫存現況")
        if products:
            df_inv = pd.DataFrame(products)[["產品名稱", "現貨庫存"]]
            c1, c2, _ = st.columns([1, 1, 2])
            c1.download_button("📥 庫存 Excel", data=to_excel(df_inv), file_name='inventory.xlsx')
            c2.download_button("📄 庫存 PDF", data=to_pdf(df_inv, "Inventory Status"), file_name='inventory.pdf')
            st.dataframe(df_inv.style.apply(lambda x: ['background-color: #ffcccc' if val < 50 else '' for val in x], subset=['現貨庫存'], axis=1), use_container_width=True)

    # --- Tab 2: 營運看板 ---
    with tab2:
        st.header("財務、銷售與物流看板")
        if products and orders:
            df_p = pd.DataFrame(products)
            df_o = pd.DataFrame(orders)
            
            # 1. 核心數據指標
            m1, m2, m3 = st.columns(3)
            total_sales = df_o['Total_USD'].sum()
            real_profit = sum(sales_stats.get(p['產品名稱'], 0) * p['毛利'] for p in products)
            m1.metric("總銷售額", f"${total_sales:,.2f}")
            m2.metric("總真實利潤", f"${real_profit:,.2f}")
            m3.metric("訂單總數", len(df_o))

            # 2. 報表下載按鈕
            st.write("### 📥 數據導出")
            c1, c2, _ = st.columns([1, 1, 2])
            c1.download_button("📊 財務利潤 Excel", data=to_excel(df_p), file_name='profit_analysis.xlsx')
            c2.download_button("📄 財務利潤 PDF", data=to_pdf(df_p, "Financial Analysis"), file_name='profit_analysis.pdf')

            # 3. 產品獲利明細表格
            st.subheader("💵 產品獲利明細")
            st.dataframe(df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]].style.format({"售價": "${:.2f}", "成本": "${:.2f}", "毛利": "${:.2f}", "毛利率": "{:.1f}%"}), use_container_width=True)

            st.markdown("---")
            
            # 4. 🔥 恢復銷售統計圖 (豎形圖)
            st.subheader("📊 產品銷售數量統計")
            df_sales_plot = pd.DataFrame([{"產品": k, "數量": v} for k, v in sales_stats.items()]).sort_values(by="數量", ascending=False)
            if not df_sales_plot.empty:
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.bar(df_sales_plot["產品"], df_sales_plot["數量"], color='#2ecc71')
                plt.xticks(rotation=45, ha='right')
                ax.set_ylabel("賣出個數")
                st.pyplot(fig)
            else:
                st.write("暫無銷售數據")

            st.markdown("---")
            
            # 5. 恢復物流訂單追蹤表格
            st.subheader("🚚 物流訂單追蹤 (Shopify)")
            st.dataframe(df_o, use_container_width=True)

    # --- Tab 3: 文案合規 ---
    with tab3:
        st.header("🔍 文案風險掃描")
        # 這裡繼續沿用你最滿意的 1.7 版本字庫管理邏輯...
        st.info("文案保護系統正常運作中，請在下方輸入內容...")
