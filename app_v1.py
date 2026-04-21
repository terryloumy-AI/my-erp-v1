import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import shopify_engine
import os

# --- 1. 🔐 安全鎖：強制 Google 登入與白名單檢查 ---
def initial_security_check():
    # 檢查是否已登入
    if not st.experimental_user.get("is_logged_in", False):
        st.title("🔒 內部 ERP 系統 - 身份驗證")
        st.info("本系統僅供授權內部人員使用。")
        if st.button("使用 Google 帳號登入"):
            st.login()
        st.stop() # 未登入則停止執行後續所有代碼

    # 檢查 Email 是否在白名單內
    # ⚠️ 請在此處輸入你自己的 Gmail 帳號
    ALLOWED_EMAILS = ["你的gmail@gmail.com"] 
    
    user_email = st.experimental_user.get("email")
    if user_email not in ALLOWED_EMAILS:
        st.error(f"🚫 存取拒絕：帳號 {user_email} 未獲授權。")
        if st.button("切換帳號"):
            st.logout()
        st.stop() # 未獲授權則停止執行

# 啟動設定與安全檢查
st.set_page_config(page_title="A's 大健康 ERP 內部專用", layout="wide")
initial_security_check()

# --- 2. 側邊欄：顯示登入狀態 ---
st.sidebar.title("👤 系統權限")
st.sidebar.success(f"已登入: {st.experimental_user.get('email')}")
if st.sidebar.button("🚪 安全登出"):
    st.logout()

st.sidebar.markdown("---")
if st.sidebar.button("🔄 同步 Shopify 最新數據"):
    st.cache_data.clear()
    st.rerun()

# --- 3. 業務邏輯與數據抓取 (只有通過檢查才會執行到這裡) ---
products, orders, sales_stats = shopify_engine.get_full_data()

# 違規字庫管理
DB_FILE = "risk_words.txt"
def load_risk_words():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    return ["治癒", "療效", "根治"]

def save_risk_words(words):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        for w in words: f.write(f"{w}\n")

# --- 4. 介面呈現 ---
st.title("🚀 跨境大健康智能管理系統 1.7.1 (安全加強版)")

tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

# --- Tab 1: 庫存管理 ---
with tab1:
    st.header("實時產品庫存 (預警機制)")
    if products:
        df_p = pd.DataFrame(products)
        df_inv = df_p[["產品名稱", "現貨庫存"]].copy()
        df_inv["預警門檻"] = 50
        st.dataframe(
            df_inv.style.apply(lambda x: ['background-color: #ffcccc' if val < 50 else '' for val in x], subset=['現貨庫存'], axis=1),
            use_container_width=True
        )
        st.markdown("---")
        st.subheader("📊 庫存佔比圖")
        fig1, ax1 = plt.subplots(figsize=(10, 4))
        ax1.bar(df_inv["產品名稱"], df_inv["現貨庫存"], color='skyblue')
        plt.xticks(rotation=45)
        st.pyplot(fig1)

# --- Tab 2: 營運看板 ---
with tab2:
    st.header("📉 財務營運與利潤分析")
    if products and orders:
        df_p = pd.DataFrame(products)
        df_o = pd.DataFrame(orders)
        
        c1, c2, c3 = st.columns(3)
        total_sales = df_o['Total_USD'].sum()
        real_profit = sum(sales_stats.get(p['產品名稱'], 0) * p['毛利'] for p in products)
        c1.metric("總銷售額", f"${total_sales:,.2f}")
        c2.metric("累積真實利潤", f"${real_profit:,.2f}")
        c3.metric("實時毛利率", f"{(real_profit/total_sales*100 if total_sales>0 else 0):.1f}%")

        st.markdown("---")
        st.subheader("💵 產品獲利明細 (成本與毛利)")
        st.dataframe(
            df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]].style.format({
                "售價": "${:.2f}", "成本": "${:.2f}", "毛利": "${:.2f}", "毛利率": "{:.1f}%"
            }).background_gradient(subset=["毛利率"], cmap="RdYlGn"),
            use_container_width=True
        )

        st.subheader("🏆 產品銷量排行榜")
        df_sales = pd.DataFrame([{"產品名稱": k, "賣出數量": v} for k, v in sales_stats.items()]).sort_values(by="賣出數量", ascending=False)
        st.table(df_sales)

        st.markdown("---")
        st.subheader("📊 產品銷售統計 (豎形圖)")
        if not df_sales.empty:
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            ax2.bar(df_sales["產品名稱"], df_sales["賣出數量"], color='green')
            st.pyplot(fig2)
            
        st.subheader("🚚 物流訂單追蹤")
        st.dataframe(df_o, use_container_width=True)

# --- Tab 3: 文案合規 ---
with tab3:
    st.header("🔍 文案合規與字庫管理")
    col_a, col_b = st.columns([2, 1])
    with col_b:
        st.subheader("🛡️ 管理違規字庫")
        current_words = load_risk_words()
        new_words_str = st.text_area("編輯字庫 (每行一個詞)", value="\n".join(current_words), height=250)
        if st.button("💾 儲存並更新字庫"):
            save_risk_words([w.strip() for w in new_words_str.split("\n") if w.strip()])
            st.success("字庫已存儲！")
            st.rerun()
    with col_a:
        st.subheader("📝 文案掃描")
        user_text = st.text_area("請在此輸入產品描述文案...", height=200)
        if st.button("🚀 開始安全掃描"):
            if user_text:
                found = [w for w in load_risk_words() if w in user_text]
                if found: st.error(f"❌ 發現違規字眼：{', '.join(found)}")
                else: st.success("✅ 掃描完成，未發現已知違規詞。")
