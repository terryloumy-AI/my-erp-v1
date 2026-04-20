import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np
from datetime import datetime, timedelta

# 頁面配置
st.set_page_config(page_title="A's 大健康 ERP 1.0", layout="wide")

# --- 🚀 終極安全字體設定：完全清空自定義設定 ---
plt.rcdefaults() # 恢復所有預設值
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# --- 數據生成功能 ---
def force_init_data():
    # 圖表標籤全英文，確保不崩潰
    products_en = ["NMN", "Curcumin", "Blueberry", "Lutein", "FishOil", "Sleep", "Probiotics", "Q10", "UroComfort", "BloodClean"]
    products_cn = ["NMN", "薑黃素", "藍莓素", "葉黃素", "深海魚油", "睡眠丸", "益生菌", "Q10", "尿適通", "血淨"]
    
    inv_data = {
        "Product": products_en,
        "Name_CN": products_cn,
        "Stock": np.random.randint(20, 150, len(products_en)),
        "Incoming": np.random.randint(10, 100, len(products_en)),
        "Threshold": [50] * len(products_en)
    }
    pd.DataFrame(inv_data).to_csv("inventory.csv", index=False)
    
    sales_list = []
    start_date = datetime.now() - timedelta(days=90)
    for i in range(200):
        date = start_date + timedelta(days=np.random.randint(0, 90))
        sales_list.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Product": np.random.choice(products_en),
            "Qty": np.random.randint(1, 10)
        })
    pd.DataFrame(sales_list).to_csv("all_orders_90days.csv", index=False)
    return "✅ 數據初始化成功！"

# --- 側邊欄 ---
if st.sidebar.button("📦 重新初始化數據"):
    force_init_data()
    st.rerun()

# --- 主畫面 ---
st.title("🚀 跨境大健康智能管理系統 1.0")

# --- 分區一：庫存預警 (表格顯示中文沒問題) ---
st.header("📊 全球庫存預警")
if not os.path.exists("inventory.csv"):
    force_init_data()

try:
    inv_df = pd.read_csv("inventory.csv")
    def style_stock(row):
        return ['background-color: #ffcccc' if row['Stock'] < row['Threshold'] else '' for _ in row]
    # 這裡表格顯示還是可以用中文
    st.dataframe(inv_df.style.apply(style_stock, axis=1), use_container_width=True)
except Exception as e:
    st.error(f"數據顯示異常: {e}")

st.markdown("---")

# --- 分區二：銷售報表 (圖表絕對安全版) ---
st.header("📈 銷售分析 (90天週期)")
if os.path.exists("all_orders_90days.csv"):
    try:
        sales_df = pd.read_csv("all_orders_90days.csv")
        sales_df['Date'] = pd.to_datetime(sales_df['Date'])
        sales_df['Month'] = sales_df['Date'].dt.strftime('%m') + " Month"
        
        target_month = st.selectbox("Select Month", sorted(sales_df['Month'].unique()))
        month_data = sales_df[sales_df['Month'] == target_month]
        
        chart_data = month_data.groupby("Product")["Qty"].sum().sort_values()
        
        # 繪圖保護層
        fig, ax = plt.subplots(figsize=(10, 6))
        chart_data.plot(kind='barh', ax=ax, color='#4CAF50')
        ax.set_title(f"Sales Ranking - {target_month}")
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        # 如果還是出錯，最後一招：直接顯示表格數據，不畫圖
        st.error("圖表生成受阻，改為數據顯示：")
        st.table(chart_data)
else:
    st.info("請點擊左側初始化數據。")
