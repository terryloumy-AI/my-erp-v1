import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import numpy as np
from datetime import datetime, timedelta

# 頁面配置
st.set_page_config(page_title="A's 大健康 ERP 1.0", layout="wide")

# --- 🚀 修正：放棄損毀檔案，使用系統內建方案 ---
def set_safe_font():
    # 這裡我們不再讀取 font.ttc.otf，改用 Linux 內建字體
    # 如果是雲端環境，通常會自動尋找替代字體
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False

set_safe_font()

# --- 數據生成功能 ---
def force_init_data():
    # 為了防止亂碼，圖表標籤我們暫時改用英文/拼音縮寫
    # 這樣你的 1.3M 目標才不會被「方塊」擋住
    products_en = ["NMN", "Curcumin", "Blueberry", "Lutein", "FishOil", "Sleep", "Probiotics", "Q10", "UroComfort", "BloodClean"]
    products_cn = ["NMN", "薑黃素", "藍莓素", "葉黃素", "深海魚油", "睡眠丸", "益生菌", "Q10", "尿適通", "血淨"]
    
    # 1. 生成庫存數據 (表格顯示中文沒問題)
    inv_data = {
        "產品名稱": products_cn,
        "現貨庫存": np.random.randint(20, 150, len(products_cn)),
        "在途貨物": np.random.randint(10, 100, len(products_cn)),
        "預警門檻": [50] * len(products_cn)
    }
    pd.DataFrame(inv_data).to_csv("inventory.csv", index=False)
    
    # 2. 生成銷售數據 (圖表使用英文避免崩潰)
    sales_list = []
    start_date = datetime.now() - timedelta(days=90)
    for i in range(200):
        date = start_date + timedelta(days=np.random.randint(0, 90))
        sales_list.append({
            "日期": date.strftime("%Y-%m-%d"),
            "產品名稱": np.random.choice(products_en),
            "數量": np.random.randint(1, 10)
        })
    pd.DataFrame(sales_list).to_csv("all_orders_90days.csv", index=False)
    return "✅ 數據初始化成功！"

# --- 側邊欄 ---
st.sidebar.button("📦 重新初始化數據", on_click=force_init_data)

# --- 主畫面 ---
st.title("🚀 跨境大健康智能管理系統 1.0")

# --- 分區一：庫存預警 ---
st.header("📊 全球庫存預警")
if not os.path.exists("inventory.csv"):
    force_init_data()

try:
    inv_df = pd.read_csv("inventory.csv")
    def style_stock(row):
        return ['background-color: #ffcccc' if row['現貨庫存'] < row['預警門檻'] else '' for _ in row]
    st.dataframe(inv_df.style.apply(style_stock, axis=1), use_container_width=True)
except:
    st.warning("請按左側「初始化」按鈕。")

st.markdown("---")

# --- 分區二：銷售報表 ---
st.header("📈 銷售分析 (90天週期)")
if os.path.exists("all_orders_90days.csv"):
    try:
        sales_df = pd.read_csv("all_orders_90days.csv")
        sales_df['日期'] = pd.to_datetime(sales_df['日期'])
        sales_df['月份'] = sales_df['日期'].dt.strftime('%m月')
        
        target_month = st.selectbox("選擇查看月份", sorted(sales_df['月份'].unique()))
        month_data = sales_df[sales_df['月份'] == target_month]
        
        chart_data = month_data.groupby("產品名稱")["數量"].sum().sort_values()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        chart_data.plot(kind='barh', ax=ax, color='#4CAF50')
        ax.set_title(f"{target_month} Sales Rank")
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        st.error(f"圖表顯示異常: {e}")
else:
    st.info("請點擊左側初始化。")
