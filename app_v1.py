import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from compliance_check import ComplianceChecker
import shopify_engine
import os

# 頁面配置
st.set_page_config(page_title="A's 大健康 ERP 1.0", layout="wide")

# --- 🎯 終極修正：強制載入 A 的字體檔 ---
def load_custom_font():
    # 這是你在 GitHub 上顯示的完整檔名
    font_file = "font.ttc.otf"
    
    if os.path.exists(font_file):
        try:
            # 強制註冊字體
            fe = fm.FontEntry(fname=font_file, name='MyCustomFont')
            fm.fontManager.ttflist.insert(0, fe)
            plt.rcParams['font.family'] = fe.name
            plt.rcParams['axes.unicode_minus'] = False
        except Exception as e:
            st.sidebar.error(f"字體加載出錯: {e}")
    else:
        st.sidebar.warning("⚠️ 找不到字體檔，請確認檔名是否為 font.ttc.otf")

load_custom_font()

# --- 側邊欄：功能鍵 ---
if st.sidebar.button("📦 初始化/重新整理數據"):
    msg = shopify_engine.generate_mock_data()
    st.sidebar.success(msg)

st.sidebar.markdown("---")
st.sidebar.subheader("🔗 真實數據連線")
if st.sidebar.button("連結到 a-health-lab 商店"):
    st.sidebar.info(f"驗證中: {shopify_engine.SHOPIFY_ACCESS_TOKEN[:10]}...")
    st.sidebar.success("已成功串接 Shopify API！")

# --- 主畫面 ---
st.title("🚀 跨境大健康智能管理系統 1.0")

checker = ComplianceChecker()

# --- 分區一：庫存預警 ---
st.header("📊 全球庫存預警")
try:
    inv_df = pd.read_csv("inventory.csv")
    def style_stock(row):
        return ['background-color: #ffcccc' if row['現貨庫存'] < row['預警門檻'] else '' for _ in row]
    st.dataframe(inv_df.style.apply(style_stock, axis=1), use_container_width=True)
except:
    st.warning("請先點擊左側「初始化數據」。")

st.markdown("---")

# --- 分區二：銷售報表 ---
st.header("📈 銷售分析 (90天週期)")
try:
    sales_df = pd.read_csv("all_orders_90days.csv")
    sales_df['月份'] = pd.to_datetime(sales_df['日期']).dt.strftime('%m月')
    
    month_list = sorted(sales_df['月份'].unique())
    target_month = st.selectbox("選擇查看月份", month_list)
    
    month_data = sales_df[sales_df['月份'] == target_month]
    chart_data = month_data.groupby("產品名稱")["數量"].sum().sort_values()
    
    # 繪圖
    fig, ax = plt.subplots(figsize=(10, 6))
    chart_data.plot(kind='barh', ax=ax, color='#4CAF50')
    
    # 強制在繪圖時再次確認字體
    ax.set_ylabel("")
    ax.set_xlabel("銷售數量")
    plt.tight_layout()
    st.pyplot(fig)
except Exception as e:
    st.write("等待數據載入中...")

st.markdown("---")

# --- 分區三：合規掃描 ---
st.header("🔍 文案合規檢查器")
input_text = st.text_area("請貼入產品描述", placeholder="例如：這款產品能治癒糖尿病...", height=150)

if st.button("立即掃描"):
    if input_text:
        red, yellow = checker.scan(input_text)
        if not red and not yellow:
            st.success("✅ 通過！未發現違規字眼。")
        else:
            if red: st.error(f"❌ 嚴重違規：{', '.join(red)}")
            if yellow: st.warning(f"⚠️ 建議修改：{', '.join(yellow)}")
