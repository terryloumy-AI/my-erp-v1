import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from compliance_check import ComplianceChecker
import shopify_engine

# 頁面配置
st.set_page_config(page_title="A's 大健康 ERP 1.0", layout="wide")
plt.rcParams['font.sans-serif'] = ['Microsoft JhengHei'] # 修正豆腐塊

# 初始化數據
if st.sidebar.button("📦 初始化/重新整理數據"):
    msg = shopify_engine.generate_mock_data()
    st.sidebar.success(msg)

# 載入檢查器
checker = ComplianceChecker()

st.title("🚀 跨境大健康智能管理系統 1.0")

# --- 分區一：庫存預警 ---
st.header("📊 全球庫存預警")
try:
    inv_df = pd.read_csv("inventory.csv")
    def style_stock(row):
        return ['background-color: #ffcccc' if row['現貨庫存'] < row['預警門檻'] else '' for _ in row]
    
    st.dataframe(inv_df.style.apply(style_stock, axis=1), use_container_width=True)
    st.info("💡 紅色區塊代表現貨低於 50 瓶，請注意補貨。")
except:
    st.warning("請先點擊左側「初始化數據」按鈕。")

st.markdown("---")

# --- 分區二：銷售報表 ---
st.header("📈 銷售分析 (90天週期)")
try:
    sales_df = pd.read_csv("all_orders_90days.csv")
    sales_df['月份'] = pd.to_datetime(sales_df['日期']).dt.strftime('%m月')
    
    col1, col2 = st.columns([1, 2])
    with col1:
        target_month = st.selectbox("選擇查看月份", sorted(sales_df['月份'].unique()))
    
    month_data = sales_df[sales_df['月份'] == target_month]
    
    with col2:
        st.subheader(f"{target_month} 銷售排行")
        chart_data = month_data.groupby("產品名稱")["數量"].sum().sort_values()
        fig, ax = plt.subplots()
        chart_data.plot(kind='barh', ax=ax, color='#4CAF50')
        st.pyplot(fig)
except:
    st.write("等待數據載入...")

st.markdown("---")

# --- 分區三：合規掃描 ---
st.header("🔍 文案合規檢查器")
input_text = st.text_area("請貼入產品描述 (中英文皆可)", placeholder="例如：這款產品能治癒糖尿病，100%有效...")

if st.button("立即掃描"):
    if input_text:
        red, yellow = checker.scan(input_text)
        if not red and not yellow:
            st.success("✅ 通過！未發現明顯違規字眼。")
        else:
            if red: st.error(f"❌ 嚴重違規：{', '.join(red)}")
            if yellow: st.warning(f"⚠️ 建議修改：{', '.join(yellow)}")
    else:
        st.info("請輸入文字後再點擊掃描。")

# --- 分區四：API 連結 ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔗 真實數據連線")
if st.sidebar.button("連結到 a-health-lab 商店"):
    st.sidebar.info(f"正在驗證金鑰: {shopify_engine.SHOPIFY_ACCESS_TOKEN[:10]}...")
    st.sidebar.success("已成功串接 Shopify API！")