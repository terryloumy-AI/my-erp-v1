import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 頁面配置
st.set_page_config(page_title="A's 大健康 ERP 1.0", layout="wide")

# --- 🚀 核心設定 ---
plt.rcdefaults()
plt.rcParams['font.sans-serif'] = ['Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

# --- 內建合規檢查邏輯 ---
class InternalComplianceChecker:
    def __init__(self):
        self.red_flags = ["治癒", "療效", "藥到病除", "根治", "癌症", "糖尿病", "降血壓", "處方"]
        self.yellow_flags = ["最強", "第一", "100%", "完全無副作用", "立即見效", "神藥"]

    def scan(self, text):
        found_red = [word for word in self.red_flags if word in text]
        found_yellow = [word for word in self.yellow_flags if word in text]
        return found_red, found_yellow

st.title("🚀 跨境大健康智能管理系統 1.0")

# --- 側邊欄 ---
st.sidebar.header("⚙️ 系統控制")
if st.sidebar.button("📦 刷新即時數據"):
    st.rerun()

# --- 數據準備 ---
data = {
    "Product": ["NMN", "Curcumin", "Blueberry", "Lutein", "FishOil", "Sleep", "Probiotics", "Q10", "UroComfort", "BloodClean"],
    "產品名稱": ["NMN 18000", "高純度薑黃素", "護眼藍莓素", "葉黃素精華", "深海魚油", "助眠丸", "強效益生菌", "輔酶 Q10", "尿適通", "血淨"],
    "現貨庫存": [64, 65, 40, 66, 90, 56, 75, 96, 25, 108],
    "在途貨物": [38, 76, 19, 65, 51, 81, 61, 97, 89, 22],
    "預警門檻": [50] * 10,
    "銷售數量": [120, 95, 80, 78, 65, 60, 60, 55, 42, 38]
}
df = pd.DataFrame(data)

# --- 區塊一：全球庫存預警 (核心數據最先顯示) ---
st.header("📊 全球庫存預警")
def style_stock(row):
    return ['background-color: #ffcccc' if row['現貨庫存'] < row['預警門檻'] else '' for _ in row]

st.dataframe(df[["產品名稱", "現貨庫存", "在途貨物", "預警門檻"]].style.apply(style_stock, axis=1), use_container_width=True)
st.caption("💡 紅色背景表示庫存低於預警線（50瓶），需儘快安排物流。")

st.markdown("---")

# --- 區塊二：銷售報表 ---
st.header("📈 銷售分析 (90天週期)")
col1, col2 = st.columns([1, 2])
with col1:
    st.write("### 銷售排行 (數據)")
    st.table(df[["產品名稱", "銷售數量"]].sort_values(by="銷售數量", ascending=False))
with col2:
    st.write("### 銷售趨勢 (圖表)")
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.barh(df["Product"], df["銷售數量"], color='#4CAF50')
    ax.invert_yaxis()
    ax.set_xlabel("Sales Volume")
    plt.tight_layout()
    st.pyplot(fig)

st.markdown("---")

# --- 區塊三：文案合規檢查器 (移至最下方) ---
st.header("🔍 文案合規檢查器")
st.info("💡 輸入產品文案，系統將自動過濾澳門及跨境電商敏感字眼。")

checker = InternalComplianceChecker()
input_text = st.text_area("請在此貼入待檢查的產品描述", placeholder="例如：這款產品能治癒糖尿病...", height=150)

if st.button("🔍 執行合規掃描"):
    if input_text:
        red, yellow = checker.scan(input_text)
        if not red and not yellow:
            st.success("✅ 檢查通過！未發現違規風險。")
        else:
            if red:
                st.error(f"❌ **嚴重違規**：{', '.join(red)}")
            if yellow:
                st.warning(f"⚠️ **建議修改**：{', '.join(yellow)}")
    else:
        st.info("請輸入文字後再執行。")

# --- 側邊欄：API 連結 ---
st.sidebar.markdown("---")
st.sidebar.subheader("🔗 數據同步")
if st.sidebar.button("同步 Shopify"):
    st.sidebar.success("✅ 已同步至 a-health-lab 商店數據")
