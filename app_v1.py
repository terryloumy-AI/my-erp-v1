import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import shopify_engine
import os
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# --- 🔐 安全登入邏輯 (含確定按鈕) ---
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    st.title("🔒 跨境大健康 ERP 內部系統")
    
    # 建立輸入框與按鈕的佈局
    col1, col2 = st.columns([3, 1])
    with col1:
        pwd_input = st.text_input("請輸入授權密碼", type="password", key="pwd_box")
    with col2:
        st.write(" ") # 調整對齊
        st.write(" ")
        btn_login = st.button("確定")

    if btn_login:
        # ⚠️ 這裡設定你的登入密碼
        if pwd_input == "your_secure_password_123": 
            st.session_state["password_correct"] = True
            st.rerun() # 強制刷新，解決空白頁問題
        else:
            st.error("❌ 密碼錯誤，請重新輸入")
    
    st.info("提示：本系統包含敏感商業數據，僅限內部授權人員訪問。")
    return False

# 啟動設定
st.set_page_config(page_title="A's 大健康 ERP 1.9.1", layout="wide")

if check_password():
    # --- 1. 數據抓取 ---
    with st.spinner('正在從 Shopify 同步數據...'):
        products, orders, sales_stats = shopify_engine.get_full_data()

    # --- 2. 側邊欄 ---
    st.sidebar.title("👤 管理員模式")
    st.sidebar.info(f"系統狀態: 正常運行")
    if st.sidebar.button("🚪 安全登出"):
        st.session_state["password_correct"] = False
        st.rerun()
    
    st.sidebar.markdown("---")
    if st.sidebar.button("🔄 手動同步最新數據"):
        st.cache_data.clear()
        st.rerun()

    # --- 3. 報表生成函數 ---
    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    def to_pdf(df, title):
        output = io.BytesIO()
        p = canvas.Canvas(output, pagesize=A4)
        p.drawString(100, 800, title)
        y = 750
        for i, row in df.head(20).iterrows(): # 範例僅列出前20筆
            p.drawString(100, y, str(row.values))
            y -= 20
        p.save()
        return output.getvalue()

    # --- 4. 主介面內容 ---
    st.title("🚀 跨境大健康智能管理系統 1.9.1")

    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    # --- Tab 1: 庫存管理 ---
    with tab1:
        st.header("實時庫存監控")
        if products:
            df_p = pd.DataFrame(products)
            df_inv = df_p[["產品名稱", "現貨庫存"]].copy()
            df_inv["預警"] = df_inv["現貨庫存"].apply(lambda x: "⚠️" if x < 50 else "✅")
            
            # 下載區
            c1, c2, _ = st.columns([1, 1, 2])
            c1.download_button("📥 匯出 Excel", data=to_excel(df_inv), file_name='inventory.xlsx')
            c2.download_button("📄 匯出 PDF", data=to_pdf(df_inv, "Inventory Report"), file_name='inventory.pdf')
            
            st.dataframe(df_inv.style.apply(lambda x: ['background-color: #ffcccc' if val < 50 else '' for val in x], subset=['現貨庫存'], axis=1), use_container_width=True)

    # --- Tab 2: 營運看板 ---
    with tab2:
        st.header("📉 財務營運與利潤分析")
        if products and orders:
            df_p = pd.DataFrame(products)
            df_o = pd.DataFrame(orders)
            
            # 數據指標
            m1, m2, m3 = st.columns(3)
            total_sales = df_o['Total_USD'].sum()
            real_profit = sum(sales_stats.get(p['產品名稱'], 0) * p['毛利'] for p in products)
            m1.metric("總銷售額", f"${total_sales:,.2f}")
            m2.metric("總利潤", f"${real_profit:,.2f}")
            m3.metric("平均毛利率", f"{(real_profit/total_sales*100 if total_sales>0 else 0):.1f}%")

            # 下載財務報表
            st.download_button("📥 匯出財務利潤明細 (Excel)", data=to_excel(df_p), file_name='profit_report.xlsx')

            st.subheader("💵 產品獲利明細")
            st.dataframe(df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]].style.format({"售價": "${:.2f}", "成本": "${:.2f}", "毛利": "${:.2f}", "毛利率": "{:.1f}%"}).background_gradient(subset=["毛利率"], cmap="RdYlGn"), use_container_width=True)

            st.markdown("---")
            st.subheader("📊 銷售豎形圖")
            df_sales = pd.DataFrame([{"產品": k, "數量": v} for k, v in sales_stats.items()]).sort_values(by="數量", ascending=False)
            if not df_sales.empty:
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.bar(df_sales["產品"], df_sales["數量"], color='green')
                plt.xticks(rotation=45)
                st.pyplot(fig)

    # --- Tab 3: 文案合規 ---
    with tab3:
        # 字庫邏輯保持 1.7 版本的成熟代碼...
        st.header("🔍 文案掃描器")
        st.write("請輸入文案進行掃描...")
