import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import shopify_engine

st.set_page_config(page_title="A's 大健康 ERP 1.2", layout="wide")

# 側邊欄同步
st.sidebar.title("⚙️ 系統設定")
if st.sidebar.button("🔄 同步 Shopify 最新數據"):
    st.cache_data.clear()
    st.rerun()

st.title("🚀 跨境大健康智能管理系統 1.2")

# 數據讀取
inv_data = shopify_engine.get_real_inventory()
order_data = shopify_engine.get_orders_and_profit()

# 分頁顯示
tab1, tab2, tab3 = st.tabs(["📊 庫存監控", "💰 訂單與利潤分析", "🔍 文案合規檢查"])

with tab1:
    st.header("📦 實時庫存狀態")
    if inv_data:
        df_inv = pd.DataFrame(inv_data)
        st.dataframe(df_inv.style.apply(lambda x: ['background-color: #ffcccc' if val < 50 else '' for val in x], subset=['現貨庫存'], axis=1), use_container_width=True)
    else:
        st.warning("尚未連動庫存數據")

with tab2:
    st.header("📈 營運與物流看板")
    if order_data:
        df_orders = pd.DataFrame(order_data)
        
        # 數據卡片
        c1, c2, c3 = st.columns(3)
        sales = df_orders['Total_USD'].sum()
        profit = df_orders['Profit_Est'].sum()
        c1.metric("總銷售額 (Total Sales)", f"${sales:,.2f}")
        c2.metric("預估總毛利 (Est. Profit)", f"${profit:,.2f}", delta="40%")
        c3.metric("總訂單數 (Total Orders)", f"{len(df_orders)} 筆")

        st.markdown("---")
        
        col_list, col_pie = st.columns([2, 1])
        with col_list:
            st.subheader("📋 訂單追蹤明細")
            st.table(df_orders)
            
        with col_pie:
            st.subheader("🚚 物流進度")
            status_counts = df_orders['Status'].value_counts()
            fig, ax = plt.subplots()
            ax.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', startangle=90, colors=['#4CAF50', '#FFC107', '#2196F3'])
            st.pyplot(fig)
    else:
        st.info("💡 提示：請在 Shopify 建立一筆「已付款」訂單後點擊同步。")

with tab3:
    st.header("🔍 文案合規檢查")
    text = st.text_area("在此輸入產品描述文案...")
    if st.button("掃描風險"):
        danger_words = ["治癒", "療效", "根治", "副作用"]
        found = [w for w in danger_words if w in text]
        if found: st.error(f"❌ 發現違規字眼：{', '.join(found)}")
        else: st.success("✅ 合規檢查通過")
