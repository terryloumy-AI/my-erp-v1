import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import os
import numpy as np
from datetime import datetime, timedelta

# 頁面配置
st.set_page_config(page_title="A's 大健康 ERP 1.0", layout="wide")

# --- 🎯 終極修正：強制載入 A 的字體檔 ---
def load_custom_font():
    font_file = "font.ttc.otf"
    if os.path.exists(font_file):
        try:
            fe = fm.FontEntry(fname=font_file, name='MyCustomFont')
            fm.fontManager.ttflist.insert(0, fe)
            plt.rcParams['font.family'] = fe.name
            plt.rcParams['axes.unicode_minus'] = False
        except:
            pass
    plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'sans-serif']

load_custom_font()

# --- 核心數據生成功能 (直接內建在主程式) ---
def force_init_data():
    products = ["NMN", "薑黃素", "藍莓素", "葉黃素", "深海魚油", "睡眠丸", "益生菌", "Q10", "尿適通", "血淨"]
    
    # 1. 生成庫存數據
    inv_data = {
        "產品名稱": products,
        "現貨庫存": np.random.randint(20, 150, len(products)),
        "在途貨物": np.random.randint(10, 100, len(products)),
        "預警門檻": [50] * len(products)
    }
    pd.DataFrame(inv_data).to_csv("inventory.csv", index=False)
    
    # 2. 生成銷售數據
    sales_list = []
    start_date = datetime.now() - timedelta(days=90)
    for i in range(200):
        date = start_date + timedelta(days=np.random.randint(0, 90))
        sales_list.append({
            "日期": date.strftime("%Y-%m-%d"),
            "產品名稱": np.random.choice(products),
            "數量": np.random.randint(1, 10),
            "金額": np.random.randint(100, 1000)
        })
    pd.DataFrame(sales_list).to_csv("all_orders_90days.csv", index=False)
    return "✅ 數據初始化成功！"

# --- 側邊欄 ---
if st.sidebar.button("📦 重新初始化數據"):
    msg = force_init_data()
    st.sidebar.success(msg)
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.info("💡 提示：若圖表未出現，請先按上方按鈕。")

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
except Exception as e:
    st.error(f"庫存數據讀取異常: {e}")

st.markdown("---")

# --- 分區二：銷售報表 ---
st.header("📈 銷售分析 (90天週期)")
if os.path.exists("all_orders_90days.csv"):
    try:
        sales_df = pd.read_csv("all_orders_90days.csv")
        sales_df['月份'] = pd.to_datetime(sales_df['日期']).dt.strftime('%m月')
        
        month_list = sorted(sales_df['月份'].unique())
        target_month = st.selectbox("選擇查看月份", month_list)
        
        month_data = sales_df[sales_df['月份'] == target_month]
        chart_data = month_data.groupby("產品名稱")["數量"].sum().sort_values()
        
        fig, ax = plt.subplots(figsize=(10, 6))
        chart_data.plot(kind='barh', ax=ax, color='#4CAF50')
        ax.set_ylabel("")
        ax.set_xlabel("銷售數量")
        plt.tight_layout()
        st.pyplot(fig)
    except Exception as e:
        st.error(f"圖表生成失敗: {e}")
else:
    st.info("📊 銷售數據檔案尚未生成，請點擊左側「重新初始化數據」。")
