import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import shopify_engine
import os
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

# --- 🔐 1. 安全登入模組 ---
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
        # ⚠️ 請在此處改回你原本的正確密碼
        if pwd_input == "kingterryERP": 
            st.session_state["password_correct"] = True
            st.rerun()
        elif btn_login:
            st.error("❌ 密碼錯誤")
    return False

# 啟動設定
st.set_page_config(page_title="A's 大健康 ERP 1.9.6 完整版", layout="wide")

if check_password():
    # --- 2. 側邊欄控制中心 (確保存在) ---
    st.sidebar.title("👤 系統管理")
    if st.sidebar.button("🔄 同步 Shopify 最新數據"):
        st.cache_data.clear()
        st.rerun()
    if st.sidebar.button("🚪 安全登出"):
        st.session_state["password_correct"] = False
        st.rerun()
    st.sidebar.markdown("---")
    st.sidebar.info("版本：V 1.9.6 (功能全整合)")

    # 數據抓取
    with st.spinner('🚀 數據同步中...'):
        products, orders, sales_stats = shopify_engine.get_full_data()

    # --- 3. 報表生成工具 ---
    def to_excel(df):
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    def to_pdf(df, title):
        output = io.BytesIO()
        p = canvas.Canvas(output, pagesize=A4)
        p.drawString(50, 800, f"Report: {title}")
        y = 750
        for i, row in df.head(15).iterrows():
            line = " | ".join([str(val) for val in row.values[:4]])
            p.drawString(50, y, line[:110])
            y -= 25
        p.save()
        return output.getvalue()

    # --- 4. 違規字庫儲存邏輯 ---
    DB_FILE = "risk_words.txt"
    def load_risk_words():
        if os.path.exists(DB_FILE):
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return [line.strip() for line in f.readlines() if line.strip()]
        return ["治癒", "療效", "根治", "抗癌"]

    def save_risk_words(words):
        with open(DB_FILE, "w", encoding="utf-8") as f:
            for w in words: f.write(f"{w}\n")

    # --- 5. 主內容切換 ---
    st.title("🚀 跨境大健康智能管理系統 1.9.6")
    tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

    # --- Tab 1: 庫存管理 ---
    with tab1:
        st.header("庫存監控")
        if products:
            df_inv = pd.DataFrame(products)[["產品名稱", "現貨庫存"]]
            c1, c2, _ = st.columns([1, 1, 2])
            c1.download_button("📥 庫存 Excel", data=to_excel(df_inv), file_name='inventory.xlsx')
            c2.download_button("📄 庫存 PDF", data=to_pdf(df_inv, "Inventory"), file_name='inventory.pdf')
            st.dataframe(df_inv.style.apply(lambda x: ['background-color: #ffcccc' if val < 50 else '' for val in x], subset=['現貨庫存'], axis=1), use_container_width=True)

    # --- Tab 2: 營運看板 ---
    with tab2:
        st.header("營運分析與物流")
        if products and orders:
            df_p = pd.DataFrame(products)
            df_o = pd.DataFrame(orders)
            
            # 指標
            m1, m2, m3 = st.columns(3)
            total_sales = df_o['Total_USD'].sum()
            real_profit = sum(sales_stats.get(p['產品名稱'], 0) * p['毛利'] for p in products)
            m1.metric("總銷售額", f"${total_sales:,.2f}")
            m2.metric("總真實利潤", f"${real_profit:,.2f}")
            m3.metric("訂單數", len(df_o))

            # 匯出
            st.write("### 📥 數據導出")
            c_e, c_p, _ = st.columns([1, 1, 2])
            c_e.download_button("📊 財務 Excel", data=to_excel(df_p), file_name='profit_analysis.xlsx')
            c_p.download_button("📄 財務 PDF", data=to_pdf(df_p, "Profit Analysis"), file_name='profit_analysis.pdf')

            st.subheader("💵 產品獲利細節")
            st.dataframe(df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]].style.format({"售價": "${:.2f}", "成本": "${:.2f}", "毛利": "${:.2f}", "毛利率": "{:.1f}%"}), use_container_width=True)

            st.markdown("---")
            # 🔥 銷售統計圖 (確保存在)
            st.subheader("📊 產品銷售數量統計")
            df_sales_plot = pd.DataFrame([{"產品": k, "數量": v} for k, v in sales_stats.items()]).sort_values(by="數量", ascending=False)
            if not df_sales_plot.empty:
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.bar(df_sales_plot["產品"], df_sales_plot["數量"], color='#3498db')
                plt.xticks(rotation=45, ha='right')
                st.pyplot(fig)

            st.markdown("---")
            # 🔥 物流訂單追蹤 (確保存在)
            st.subheader("🚚 物流訂單追蹤")
            st.dataframe(df_o, use_container_width=True)

    # --- Tab 3: 文案合規 (全面恢復) ---
    with tab3:
        st.header("🔍 廣告文案合規掃描")
        col_scan, col_db = st.columns([2, 1])
        
        with col_db:
            st.subheader("🛡️ 管理違規字庫")
            current_words = load_risk_words()
            new_words_str = st.text_area("編輯字庫 (每行一個詞)", value="\n".join(current_words), height=250)
            if st.button("💾 儲存並更新字庫"):
                save_risk_words([w.strip() for w in new_words_str.split("\n") if w.strip()])
                st.success("字庫已儲存！")
                st.rerun()

        with col_scan:
            st.subheader("📝 文案安全檢測")
            user_text = st.text_area("請輸入產品描述...", height=200, placeholder="例如：這款 NMN 能有效治癒...")
            if st.button("🚀 開始掃描"):
                if user_text:
                    risk_list = load_risk_words()
                    found = [w for w in risk_list if w in user_text]
                    if found:
                        st.error(f"❌ 發現違規字眼：{', '.join(found)}")
                    else:
                        st.success("✅ 掃描完成：目前未發現違規風險。")
                else:
                    st.warning("請先輸入文字。")
