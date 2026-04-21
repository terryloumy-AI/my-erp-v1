import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import shopify_engine # 確保這行有在，才能讀取你的 shopify_engine.py

# 頁面配置
st.set_page_config(page_title="A's 大健康 ERP 1.1", layout="wide")

# --- 🚀 基礎設定：防止亂碼 ---
plt.rcdefaults()
plt.rcParams['font.sans-serif'] = ['Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# --- 內建合規檢查邏輯 ---
class InternalComplianceChecker:
    def __init__(self):
        self.red_flags = ["治癒", "療效", "癌症", "糖尿病", "降血壓", "處方"]
        self.yellow_flags = ["最強", "100%", "立即見效", "神藥"]

    def scan(self, text):
        found_red = [word for word in self.red_flags if word in text]
        found_yellow = [word for word in self.yellow_flags if word in text]
        return found_red, found_yellow

# --- 核心數據載入邏輯 ---
def load_all_data():
    # 嘗試從 shopify_engine 抓取真實數據
    real_data = shopify_engine.get_real_inventory()
    
    if real_data:
        df = pd.DataFrame(real_data)
        source_msg = "🟢 狀態：已成功連結 Shopify 真實數據"
        is_real = True
    else:
        # 如果 API 沒連上，顯示模擬數據，確保畫面不崩潰
        mock_data = {
            "產品名稱": ["NMN 18000 (模擬)", "高純度薑黃素 (模擬)", "護眼藍莓素 (模擬)"],
            "Product_ID": ["Demo01", "Demo02", "Demo03"],
            "現貨庫存": [64, 25, 90],
            "在途貨物": [30, 0, 15],
            "預警門檻": [50, 50, 50]
        }
        df = pd.DataFrame(mock_data)
        source_msg = "🟡 狀態：連線失敗或無產品 (目前為演示模式)"
        is_real = False
    return df, source_msg, is_real

# --- 側邊欄控制 ---
st.sidebar.title("⚙️ 系統設定")
if st.sidebar.button("🔄 同步 Shopify 最新數據"):
    st.cache_data.clear() # 清除舊的暫存數據
    st.rerun()

st.title("🚀 跨境大健康智能管理系統 1.1")

# 執行數據抓取
df, data_status, is_real = load_all_data()
st.sidebar.info(data_status)

# --- 區塊一：全球庫存預警 ---
st.header("📊 實時庫存監控")
def style_stock(row):
    # 如果庫存低於預警門檻，整行顯示紅色
    return ['background-color: #ffcccc' if row['現貨庫存'] < row['預警門檻'] else '' for _ in row]

# 顯示表格
st.dataframe(df[["產品名稱", "現貨庫存", "在途貨物", "預警門檻"]].style.apply(style_stock, axis=1), use_container_width=True)
st.caption("💡 說明：紅色背景代表現貨低於 50 瓶，系統自動發出補貨預警。")

st.markdown("---")

# --- 區塊二：銷售趨勢 (目前用庫存量做圖表展示) ---
st.header("📈 庫存分佈分析")
col1, col2 = st.columns([1, 2])

with col1:
    st.write("### 產品清單")
    st.table(df[["產品名稱", "現貨庫存"]])

with col2:
    st.write("### 庫存水位圖")
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        # 繪製橫向條形圖
        ax.barh(df["產品名稱"], df["現貨庫存"], color='#4CAF50')
        ax.invert_yaxis() # 讓第一個產品排在最上面
        ax.set_xlabel("Current Inventory Level")
        plt.tight_layout()
        st.pyplot(fig)
    except Exception:
        st.error("圖表生成異常，請檢查字體設定。")

st.markdown("---")

# --- 區塊三：文案合規檢查器 (放在最下方) ---
st.header("🔍 文案合規檢查器")
st.info("💡 專為大健康產業設計，自動偵測醫療過度承諾字眼，降低澳門及跨境法規風險。")

checker = InternalComplianceChecker()
input_text = st.text_area("請在此貼入產品描述文案", placeholder="例如：這款 NMN 能治癒癌症...", height=150)

if st.button("🔍 執行合規掃描"):
    if input_text:
        red, yellow = checker.scan(input_text)
        if not red and not yellow:
            st.success("✅ 檢查通過！未發現明顯違規風險。")
        else:
            if red:
                st.error(f"❌ **嚴重違規 (涉及醫療療效)**：{', '.join(red)}")
                st.caption("建議：修改為「調節生理機能」或「促進新陳代謝」。")
            if yellow:
                st.warning(f"⚠️ **建議修改 (誇大用語)**：{', '.join(yellow)}")
    else:
        st.info("請輸入文字後再執行掃描。")

# --- 頁尾 API 狀態 ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔗 API 連結資訊")
st.sidebar.text(f"商店網址: \na-health-lab.myshopify.com")
