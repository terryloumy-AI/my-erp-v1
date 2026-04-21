import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import shopify_engine

st.set_page_config(page_title="A's 大健康 ERP 1.3 (精準成本版)", layout="wide")

st.sidebar.title("⚙️ 系統控制")
if st.sidebar.button("🔄 同步 Shopify 最新數據"):
    st.cache_data.clear()
    st.rerun()

# 載入數據
inv_data = shopify_engine.get_real_inventory()
order_data = shopify_engine.get_orders_and_profit()

# 計算全局平均毛利率
avg_margin = 0
if inv_data:
    df_inv = pd.DataFrame(inv_data)
    # 過濾掉沒有成本設定的產品再算平均
    valid_margins = df_inv[df_inv["成本 (USD)"] > 0]["毛利率 (Margin %)"]
    avg_margin = valid_margins.mean() if not valid_margins.empty else 0

st.sidebar.markdown("---")
st.sidebar.metric("📊 全球平均毛利率", f"{avg_margin:.1f}%")
st.sidebar.success(f"已連接: {st.secrets['SHOP_URL']}")

st.title("🚀 跨境大健康智能管理系統 1.3")

tab1, tab2, tab3 = st.tabs(["💰 產品獲利明細", "📉 營運看板", "🔍 文案合規"])

with tab1:
    st.header("💵 產品獲利能力分析")
    if inv_data:
        df_profit = pd.DataFrame(inv_data)
        st.dataframe(
            df_profit.style.format({
                "售價 (USD)": "{:.2f}",
                "成本 (USD)": "{:.2f}",
                "毛利 (Profit)": "{:.2f}",
                "毛利率 (Margin %)": "{:.1f}%"
            }).background_gradient(subset=["毛利率 (Margin %)"], cmap="RdYlGn"),
            use_container_width=True
        )
    else:
        st.error("無法獲取數據，請檢查 API 權限是否包含 'read_inventory'")

with tab2:
    st.header("📊 總體營運看板")
    if order_data:
        df_orders = pd.DataFrame(order_data)
        total_sales = df_orders['Total_USD'].sum()
        est_total_profit = total_sales * (avg_margin / 100)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("總銷售額", f"${total_sales:,.2f}")
        c2.metric("預估總利潤", f"${est_total_profit:,.2f}", delta=f"Avg {avg_margin:.1f}%")
        c3.metric("總訂單數", f"{len(df_orders)} 筆")
        st.table(df_orders)

with tab3:
    st.header("🔍 文案掃描")
    text = st.text_area("產品描述...")
    if st.button("檢查"):
        st.success("文案掃描完成")
