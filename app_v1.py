import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import shopify_engine

st.set_page_config(page_title="A's 大健康 ERP 1.6.1", layout="wide")

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

st.title("🚀 跨境大健康智能管理系統 1.6.1")

tab1, tab2, tab3 = st.tabs(["📦 庫存管理", "💰 營運看板", "🔍 文案合規"])

# --- Tab 1: 庫存管理 ---
with tab1:
    st.header("實時產品庫存 (包含預警)")
    if products:
        df_inv = pd.DataFrame(products)[["產品名稱", "現貨庫存"]]
        df_inv["預警門檻"] = 50
        st.dataframe(
            df_inv.style.apply(lambda x: ['background-color: #ffcccc' if val < 50 else '' for val in x], subset=['現貨庫存'], axis=1),
            use_container_width=True
        )
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

# --- Tab 3: 文案合規 (修正無法輸入的問題) ---
with tab3:
    st.header("🔍 廣告文案合規掃描")
    st.info("請在下方輸入產品描述，系統將自動偵測是否存在「療效宣稱」等違規風險字眼。")
    
    # 這裡恢復了輸入框
    user_text = st.text_area("請輸入文案內容（例如 NMN 或 葉黃素 的介紹）...", height=200, placeholder="在此輸入文字...")
    
    if st.button("🚀 開始安全掃描"):
        if user_text:
            # 這是大健康產品最容易違規的字眼
            danger_words = ["治癒", "療效", "根治", "副作用", "抗癌", "百病", "藥到病除"]
            found = [w for w in danger_words if w in user_text]
            
            if found:
                st.error(f"❌ 掃描失敗！發現違規字眼：{', '.join(found)}")
                st.warning("建議：健康食品不能宣稱療效，請將上述字眼修改為「調節生理機能」或「健康維持」。")
            else:
                st.success("✅ 掃描完成：未發現明顯違規字眼，文案看起來很安全。")
        else:
            st.warning("請先輸入一些文字再進行掃描喔！")
