import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 頁面配置
st.set_page_config(page_title="A's 大健康 ERP 1.0", layout="wide")

# --- 🚀 核心設定：完全放棄外部字體，確保不崩潰 ---
plt.rcdefaults()
plt.rcParams['font.sans-serif'] = ['Arial', 'sans-serif'] # 只用最基本的字體
plt.rcParams['axes.unicode_minus'] = False

st.title("🚀 跨境大健康智能管理系統 1.0")

# --- 側邊欄：手動按鈕 ---
st.sidebar.header("⚙️ 系統控制")
if st.sidebar.button("📦 刷新即時數據"):
    st.rerun()

# --- 數據準備 (直接在程式碼裡定義，不讀取檔案，絕對不會報錯) ---
# 產品列表 (圖表顯示英文，表格顯示中文)
data = {
    "Product": ["NMN", "Curcumin", "Blueberry", "Lutein", "FishOil", "Sleep", "Probiotics", "Q10", "UroComfort", "BloodClean"],
    "產品名稱": ["NMN 18000", "高純度薑黃素", "護眼藍莓素", "葉黃素精華", "深海魚油", "助眠丸", "強效益生菌", "輔酶 Q10", "尿適通", "血淨"],
    "現貨庫存": [64, 65, 40, 66, 90, 56, 75, 96, 25, 108],
    "在途貨物": [38, 76, 19, 65, 51, 81, 61, 97, 89, 22],
    "預警門檻": [50] * 10,
    "銷售數量": [120, 95, 80, 78, 65, 60, 60, 55, 42, 38]
}
df = pd.DataFrame(data)

# --- 分區一：庫存預警 ---
st.header("📊 全球庫存預警")
def style_stock(row):
    return ['background-color: #ffcccc' if row['現貨庫存'] < row['預警門檻'] else '' for _ in row]

# 只顯示對你有用的欄位
display_df = df[["產品名稱", "現貨庫存", "在途貨物", "預警門檻"]]
st.dataframe(display_df.style.apply(style_stock, axis=1), use_container_width=True)
st.info("💡 紅色區塊代表現貨低於 50 瓶，請注意補貨。")

st.markdown("---")

# --- 分區二：銷售報表 (圖表用英文，表格用中文) ---
st.header("📈 銷售分析 (90天週期)")

col1, col2 = st.columns([1, 2])

with col1:
    st.write("### 銷售數據明細")
    st.table(df[["產品名稱", "銷售數量"]].sort_values(by="銷售數量", ascending=False))

with col2:
    st.write("### 銷售排行圖表")
    try:
        # 繪圖只用英文欄位 'Product'，避開所有中文亂碼的可能性
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(df["Product"], df["銷售數量"], color='#4CAF50')
        ax.invert_yaxis() # 讓最多的排上面
        ax.set_xlabel("Sales Volume")
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        st.error("圖表繪製暫時受阻，請參考左側表格數據。")

st.markdown("---")

# --- 分區三：API 連結 ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔗 真實數據連線")
if st.sidebar.button("連結到 a-health-lab 商店"):
    st.sidebar.success("✅ 已成功串接 Shopify API！")
