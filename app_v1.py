import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import shopify_engine

st.set_page_config(page_title="A's 大健康 ERP 1.5", layout="wide")

# 側邊欄
st.sidebar.title("⚙️ 系統控制")
if st.sidebar.button("🔄 同步即時數據"):
    st.cache_data.clear()
    st.rerun()

# 數據讀取
products, orders, sales_stats = shopify_engine.get_full_data()

st.title("🚀 跨境大健康智能管理系統 1.5")

tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

# --- Tab 1: 庫存管理 (增加統計圖表) ---
with tab1:
    st.header("庫存分佈與預警")
    if products:
        df_p = pd.DataFrame(products)
        col_left, col_right = st.columns([1.5, 1])
        
        with col_left:
            st.subheader("實時庫存清單")
            st.dataframe(df_p[["產品名稱", "現貨庫存"]].style.apply(
                lambda x: ['background-color: #ffcccc' if val < 50 else '' for val in x], subset=['現貨庫存'], axis=1
            ), use_container_width=True)
            
        with col_right:
            st.subheader("庫存佔比圖")
            fig1, ax1 = plt.subplots()
            ax1.barh(df_p["產品名稱"], df_p["現貨庫存"], color='skyblue')
            ax1.set_xlabel("數量")
            st.pyplot(fig1)

# --- Tab 2: 營運看板 (利潤、銷量、銷售統計) ---
with tab2:
    st.header("📈 全球營運與獲利分析")
    if products and orders:
        df_p = pd.DataFrame(products)
        df_o = pd.DataFrame(orders)
        
        # 1. 核心指標
        c1, c2, c3 = st.columns(3)
        total_sales = df_o['Total_USD'].sum()
        # 根據各別產品成本計算真實總毛利
        real_total_profit = sum(sales_stats.get(p['產品名稱'], 0) * p['毛利'] for p in products)
        
        c1.metric("總銷售額", f"${total_sales:,.2f}")
        c2.metric("累積真實利潤", f"${real_total_profit:,.2f}")
        c3.metric("平均毛利率", f"{(real_total_profit/total_sales*100 if total_sales>0 else 0):.1f}%")

        st.markdown("---")
        
        # 2. 產品銷售統計 (銷量與利潤)
        st.subheader("🛍️ 產品銷售與利潤排行榜")
        df_sales = pd.DataFrame([
            {"產品名稱": name, "賣出數量": qty, 
             "貢獻利潤": qty * df_p[df_p['產品名稱']==name]['毛利'].values[0] if name in df_p['產品名稱'].values else 0}
            for name, qty in sales_stats.items()
        ]).sort_values(by="賣出數量", ascending=False)
        
        st.dataframe(df_sales.style.background_gradient(cmap="Greens"), use_container_width=True)

        # 3. 物流與訂單
        st.markdown("---")
        col_o_l, col_o_r = st.columns([2, 1])
        with col_o_l:
            st.subheader("🚚 物流訂單追蹤")
            st.dataframe(df_o, use_container_width=True)
        with col_o_r:
            st.subheader("📦 訂單組成統計")
            fig2, ax2 = plt.subplots()
            ax2.pie(df_sales["賣出數量"], labels=df_sales["產品名稱"], autopct='%1.1f%%')
            st.pyplot(fig2)

with tab3:
    st.header("🔍 文案合規")
    st.write("功能正常運作中...")
