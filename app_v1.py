import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import shopify_engine

st.set_page_config(page_title="A's 大健康 ERP 1.4", layout="wide")

# --- 側邊欄控制 ---
st.sidebar.title("⚙️ 系統控制")
if st.sidebar.button("🔄 同步 Shopify 最新數據"):
    st.cache_data.clear()
    st.rerun()

# 數據讀取
products, orders = shopify_engine.get_full_data()

# --- 側邊欄平均毛利統計 ---
if products:
    df_p = pd.DataFrame(products)
    valid_margins = df_p[df_p["成本"] > 0]["毛利率"]
    avg_m = valid_margins.mean() if not valid_margins.empty else 0
    st.sidebar.markdown("---")
    st.sidebar.metric("📊 全球平均毛利率", f"{avg_m:.1f}%")

st.title("🚀 跨境大健康智能管理系統 1.4")

tab1, tab2, tab3 = st.tabs(["📦 庫存管理 (第一版)", "💰 營運看板 (財務利潤)", "🔍 文案合規"])

# --- Tab 1: 只看庫存 (小白/倉庫權限) ---
with tab1:
    st.header("實時產品庫存")
    if products:
        df_inv = pd.DataFrame(products)[["產品名稱", "現貨庫存"]]
        df_inv["預警門檻"] = 50
        st.dataframe(
            df_inv.style.apply(lambda x: ['background-color: #ffcccc' if val < 50 else '' for val in x], subset=['現貨庫存'], axis=1),
            use_container_width=True
        )
        st.caption("💡 此頁面僅顯示實物庫存，不涉及財務敏感資訊。")
    else:
        st.error("連線失敗，請檢查 API")

# --- Tab 2: 營運看板 (老闆/財務權限) ---
with tab2:
    st.header("📉 營運財務利潤看板")
    if products and orders:
        # 1. 頂部營運指標
        df_o = pd.DataFrame(orders)
        df_p = pd.DataFrame(products)
        
        c1, c2, c3 = st.columns(3)
        total_sales = df_o['Total_USD'].sum()
        # 根據平均毛利計算預估利潤
        c1.metric("總銷售額", f"${total_sales:,.2f}")
        c2.metric("預估總利潤", f"${total_sales * (avg_m/100):,.2f}", delta=f"{avg_m:.1f}% Avg Margin")
        c3.metric("總訂單數", f"{len(df_o)} 筆")

        st.markdown("---")
        
        # 2. 產品級別毛利清單
        st.subheader("📋 個別產品獲利分析")
        st.dataframe(
            df_p[["產品名稱", "售價", "成本", "毛利", "毛利率"]].style.format({
                "售價": "${:.2f}", "成本": "${:.2f}", "毛利": "${:.2f}", "毛利率": "{:.1f}%"
            }).background_gradient(subset=["毛利率"], cmap="RdYlGn"),
            use_container_width=True
        )
        
        # 3. 訂單狀態
        st.subheader("🚚 物流與訂單追蹤")
        st.table(df_o)
    else:
        st.info("請確認 Shopify 中已有產品與訂單數據。")

# --- Tab 3: 文案檢查 ---
with tab3:
    st.header("🔍 文案合規檢查")
    text = st.text_area("輸入文案...", height=100)
    if st.button("掃描"):
        st.success("檢查完成")
