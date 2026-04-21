import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import shopify_engine

st.set_page_config(page_title="A's 大健康 ERP 1.3", layout="wide")

# --- 側邊欄控制 ---
st.sidebar.title("⚙️ 系統控制")
if st.sidebar.button("🔄 刷新即時數據"):
    st.cache_data.clear()
    st.rerun()

# 載入數據
inv_data = shopify_engine.get_real_inventory()
order_data = shopify_engine.get_orders_and_profit()

# --- 計算全局平均毛利率 ---
avg_margin = 0
if inv_data:
    df_inv = pd.DataFrame(inv_data)
    avg_margin = df_inv["毛利率 (Margin %)"].mean()

st.sidebar.markdown("---")
st.sidebar.metric("📊 全球平均毛利率", f"{avg_margin:.1f}%")
st.sidebar.success(f"API 連結: {st.secrets['SHOP_URL']}")

st.title("🚀 跨境大健康智能管理系統 1.3")

# 建立分頁
tab1, tab2, tab3 = st.tabs(["💰 產品毛利明細", "📉 營運財務看板", "🔍 文案合規檢查"])

with tab1:
    st.header("💵 產品獲利能力分析 (每款產品)")
    if inv_data:
        # 整理表格，只顯示與錢有關的
        df_profit = pd.DataFrame(inv_data)
        display_cols = ["產品名稱", "售價 (USD)", "成本 (USD)", "毛利 (Profit)", "毛利率 (Margin %)", "現貨庫存"]
        
        # 格式化顯示：毛利率加上 %
        st.dataframe(
            df_profit[display_cols].style.format({
                "售價 (USD)": "{:.2f}",
                "成本 (USD)": "{:.2f}",
                "毛利 (Profit)": "{:.2f}",
                "毛利率 (Margin %)": "{:.1f}%"
            }).background_gradient(subset=["毛利率 (Margin %)"], cmap="RdYlGn"),
            use_container_width=True
        )
        st.caption("💡 說明：表格已按毛利率進行顏色深淺標註，綠色越深代表獲利能力越強。")
    else:
        st.warning("無法抓取產品數據")

with tab2:
    st.header("📊 總體營運看板")
    if order_data:
        df_orders = pd.DataFrame(order_data)
        col_m1, col_m2, col_m3 = st.columns(3)
        total_sales = df_orders['Total_USD'].sum()
        # 根據平均毛利率計算總利潤
        est_total_profit = total_sales * (avg_margin / 100)
        
        col_m1.metric("總銷售額", f"${total_sales:,.2f}")
        col_m2.metric("預估總利潤", f"${est_total_profit:,.2f}", delta=f"基於平均 {avg_margin:.1f}% 毛利")
        col_m3.metric("總訂單數", f"{len(df_orders)} 筆")
        
        st.markdown("---")
        st.subheader("📋 訂單狀態追蹤")
        st.table(df_orders)
    else:
        st.info("尚無訂單數據")

with tab3:
    st.header("🔍 文案合規檢查")
    user_text = st.text_area("請輸入產品描述內容...", height=150)
    if st.button("開始檢查"):
        risky_words = ["治癒", "療效", "根治", "抗癌", "副作用"]
        matches = [w for w in risky_words if w in user_text]
        if matches: st.error(f"❌ 發現危險字眼：{', '.join(matches)}")
        else: st.success("✅ 合規檢查通過")
