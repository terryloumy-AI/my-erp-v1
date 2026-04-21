import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import shopify_engine

st.set_page_config(page_title="A's 大健康 ERP 1.6", layout="wide")

# 側邊欄控制
st.sidebar.title("⚙️ 系統控制")
if st.sidebar.button("🔄 同步即時數據"):
    st.cache_data.clear()
    st.rerun()

products, orders, sales_stats = shopify_engine.get_full_data()

# 計算平均毛利
avg_m = 0
if products:
    df_p = pd.DataFrame(products)
    avg_m = df_p[df_p["成本"] > 0]["毛利率"].mean()
    st.sidebar.markdown("---")
    st.sidebar.metric("📊 全球平均毛利率", f"{avg_m:.1f}%")

st.title("🚀 跨境大健康智能管理系統 1.6")

tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

# --- Tab 1: 庫存管理 ---
with tab1:
    st.header("實時產品庫存 (包含預警)")
    if products:
        df_inv = pd.DataFrame(products)[["產品名稱", "現貨庫存"]]
        df_inv["預警門檻"] = 50
        # 恢復紅字預警
        st.dataframe(
            df_inv.style.apply(lambda x: ['background-color: #ffcccc' if val < 50 else '' for val in x], subset=['現貨庫存'], axis=1),
            use_container_width=True
        )
        # 圖表放在下面
        st.markdown("---")
        st.subheader("📊 庫存佔比分佈圖")
        fig1, ax1 = plt.subplots(figsize=(10, 4))
        ax1.bar(df_inv["產品名稱"], df_inv["現貨庫存"], color='skyblue')
        plt.xticks(rotation=45)
        st.pyplot(fig1)

# --- Tab 2: 營運看板 ---
with tab2:
    st.header("📉 財務與銷售分析")
    if products and orders:
        df_p = pd.DataFrame(products)
        df_o = pd.DataFrame(orders)
        
        # 1. 核心指標卡片
        c1, c2, c3 = st.columns(3)
        total_sales = df_o['Total_USD'].sum()
        real_profit = sum(sales_stats.get(p['產品名稱'], 0) * p['毛利'] for p in products)
        c1.metric("總銷售額", f"${total_sales:,.2f}")
        c2.metric("累積真實利潤", f"${real_profit:,.2f}")
        c3.metric("實時毛利率", f"{(real_profit/total_sales*100 if total_sales>0 else 0):.1f}%")

        st.markdown("---")
        # 2. 恢復產品明細（成本、利潤、利潤率）
        st.subheader("💵 產品獲利明細 (成本與毛利)")
        st.dataframe(
            df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]].style.format({
                "售價": "${:.2f}", "成本": "${:.2f}", "毛利": "${:.2f}", "毛利率": "{:.1f}%"
            }).background_gradient(subset=["毛利率"], cmap="RdYlGn"),
            use_container_width=True
        )

        # 3. 銷量排行榜 (緊跟在明細下面)
        st.subheader("🏆 產品銷量排行榜")
        df_sales = pd.DataFrame([{"產品名稱": k, "賣出數量": v} for k, v in sales_stats.items()]).sort_values(by="賣出數量", ascending=False)
        st.table(df_sales)

        st.markdown("---")
        # 4. 物流與訂單區 (上方增加豎形圖)
        st.subheader("📊 產品銷售統計 (豎形圖)")
        if not df_sales.empty:
            fig2, ax2 = plt.subplots(figsize=(10, 4))
            ax2.bar(df_sales["產品名稱"], df_sales["賣出數量"], color='green')
            st.pyplot(fig2)
            
        st.subheader("🚚 物流訂單追蹤")
        st.dataframe(df_o, use_container_width=True)

with tab3:
    st.header("🔍 文案合規")
    st.write("模組正常運作中")
