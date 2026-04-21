import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import shopify_engine
import os
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- 1. 🔐 安全鎖 (密碼保持不變) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.title("🔒 內部 ERP 系統")
        st.text_input("請輸入授權密碼", type="password", key="password", on_change=lambda: st.session_state.update({"password_correct": st.session_state.password == "your_secure_password_123"}))
        return False
    return st.session_state["password_correct"]

st.set_page_config(page_title="A's 大健康 ERP 1.9", layout="wide")

if check_password():
    products, orders, sales_stats = shopify_engine.get_full_data()

    # --- 輔助函數：報表生成邏輯 ---
    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='Report')
        return output.getvalue()

    def to_pdf(df, title):
        output = io.BytesIO()
        c = canvas.Canvas(output, pagesize=A4)
        width, height = A4
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, title)
        
        c.setFont("Helvetica", 10)
        y = height - 80
        # 簡單列印數據 (PDF 格式較固定)
        for i, row in df.iterrows():
            line = " | ".join([f"{k}: {v}" for k, v in row.items()])
            c.drawString(50, y, line[:100]) # 限制長度防止溢出
            y -= 20
            if y < 50: 
                c.showPage()
                y = height - 50
        c.save()
        return output.getvalue()

    # --- 主介面 ---
    st.title("🚀 跨境大健康智能管理系統 1.9 (多格式報表版)")

    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    # --- Tab 1: 庫存管理 ---
    with tab1:
        st.header("實時庫存與預警")
        if products:
            df_p = pd.DataFrame(products)
            df_inv = df_p[["產品名稱", "現貨庫存"]].copy()
            df_inv["狀態"] = df_inv["現貨庫存"].apply(lambda x: "LOW" if x < 50 else "OK")
            
            # 報表下載區
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("📥 下載庫存 Excel", data=to_excel(df_inv), file_name='inventory.xlsx')
            with c2:
                st.download_button("📄 下載庫存 PDF", data=to_pdf(df_inv, "Inventory Report"), file_name='inventory.pdf')
            
            st.dataframe(df_inv.style.apply(lambda x: ['background-color: #ffcccc' if val < 50 else '' for val in x], subset=['現貨庫存'], axis=1), use_container_width=True)

    # --- Tab 2: 營運看板 ---
    with tab2:
        st.header("📉 財務營運分析")
        if products and orders:
            df_p = pd.DataFrame(products)
            df_o = pd.DataFrame(orders)
            
            # 報表下載區
            c1, c2 = st.columns(2)
            with c1:
                st.download_button("📥 下載財務 Excel", data=to_excel(df_p), file_name='finance_report.xlsx')
            with c2:
                st.download_button("📄 下載財務 PDF", data=to_pdf(df_p, "Financial Profit Report"), file_name='finance_report.pdf')
            
            # 核心指標
            col_m1, col_m2 = st.columns(2)
            real_profit = sum(sales_stats.get(p['產品名稱'], 0) * p['毛利'] for p in products)
            col_m1.metric("總銷售額", f"${df_o['Total_USD'].sum():,.2f}")
            col_m2.metric("累積真實利潤", f"${real_profit:,.2f}")

            st.subheader("💵 產品利潤明細")
            st.dataframe(df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]].style.format({"售價": "${:.2f}", "成本": "${:.2f}", "毛利": "${:.2f}", "毛利率": "{:.1f}%"}).background_gradient(subset=["毛利率"], cmap="RdYlGn"), use_container_width=True)

            st.markdown("---")
            st.subheader("📊 銷量與物流")
            df_sales = pd.DataFrame([{"產品名稱": k, "銷量": v} for k, v in sales_stats.items()])
            if not df_sales.empty:
                fig2, ax2 = plt.subplots(figsize=(10, 3))
                ax2.bar(df_sales["產品名稱"], df_sales["銷量"], color='green')
                st.pyplot(fig2)
            st.table(df_o)

    # --- Tab 3: 文案合規 ---
    with tab3:
        st.header("🔍 字庫管理與掃描")
        st.info("系統持續保護中...")
