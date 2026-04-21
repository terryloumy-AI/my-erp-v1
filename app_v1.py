import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import shopify_engine

st.set_page_config(page_title="A's 大健康 ERP 1.2", layout="wide")

# --- 側邊欄控制 ---
st.sidebar.title("⚙️ 系統設定")
if st.sidebar.button("🔄 同步 Shopify 最新數據"):
    st.cache_data.clear()
    st.rerun()

st.title("🚀 跨境大健康智能管理系統 1.2")

# 載入數據
inv_data = shopify_engine.get_real_inventory()
order_data = shopify_engine.get_orders_and_profit()

# 建立分頁
tab1, tab2, tab3 = st.tabs(["📊 庫存監控", "💰 訂單與利潤", "🔍 文案合規"])

# --- Tab 1: 庫存監控 ---
with tab1:
    st.header("實時庫存狀態")
    if inv_data:
        df_inv = pd.DataFrame(inv_data)
        st.dataframe(df_inv.style.apply(lambda x: ['background-color: #ffcccc' if val < 50 else '' for val in x], subset=['現貨庫存'], axis=1), use_container_width=True)
    else:
        st.warning("請先連結 Shopify API")

# --- Tab 2: 訂單與利潤 (你的新需求) ---
with tab2:
    st.header("營運與物流看板")
    if order_data:
        df_orders = pd.DataFrame(order_data)
        
        # 數據摘要卡片
        col1, col2, col3 = st.columns(3)
        col1.metric("總銷售額", f"${df_orders['總金額'].sum():,.0f}")
        col2.metric("預估總毛利", f"${df_orders['預估毛利'].sum():,.0f}", delta="40% Margin")
        col3.metric("待處理訂單", len(df_orders[df_orders['物流狀態'] == "🟡 待處理"]))

        st.markdown("---")
        
        # 訂單明細表格
        st.subheader("📋 最近訂單追蹤")
        st.dataframe(df_orders, use_container_width=True)
        
        # 物流狀態圖表
        st.subheader("🚚 物流進度分析")
        status_counts = df_orders['物流狀態'].value_counts()
        fig, ax = plt.subplots()
        ax.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', startangle=90, colors=['#4CAF50', '#FFC107', '#2196F3'])
        st.pyplot(fig)
    else:
        st.info("尚無訂單數據，請在 Shopify 下個測試單試試看！")

# --- Tab 3: 文案檢查 ---
with tab3:
    st.header("🔍 文案合規檢查")
    input_text = st.text_area("貼入產品描述", height=150)
    if st.button("檢查文案"):
        if "治癒" in input_text or "療效" in input_text:
            st.error("發現醫療敏感字眼")
        else:
            st.success("通過")
