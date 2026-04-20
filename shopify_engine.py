import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta

# --- 1. 配置區 (這是你的鑰匙) ---
SHOPIFY_ACCESS_TOKEN = "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"
SHOP_URL = "a-health-lab.myshopify.com"

# --- 2. 真實數據抓取功能 ---
def fetch_real_shopify_data():
    """從真實 Shopify 抓取產品與庫存"""
    headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}
    # 這是抓取產品清單的 API 地址
    url = f"https://{SHOP_URL}/admin/api/2024-01/products.json"
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            products = response.json().get('products', [])
            data = []
            for p in products:
                # 抓取第一個規格的庫存
                variant = p['variants'][0]
                data.append({
                    "產品名稱": p['title'],
                    "現貨庫存": variant.get('inventory_quantity', 0),
                    "在途貨物": 0,
                    "預警門檻": 50
                })
            df = pd.DataFrame(data)
            # 如果抓到資料，就寫入 inventory.csv 供 app.py 讀取
            if not df.empty:
                df.to_csv("inventory.csv", index=False)
                return f"✅ 成功！已從 Shopify 抓取 {len(data)} 款真實產品。"
            return "⚠️ 商店內似乎還沒有產品。"
        else:
            return f"❌ 連結失敗，錯誤代碼：{response.status_code}"
    except Exception as e:
        return f"❌ 發生錯誤: {str(e)}"

# --- 3. 模擬數據生成功能 (保留備用) ---
def generate_mock_data():
    """當你想看 NMN 等產品效果時使用的模擬功能"""
    products = [
        "NMN", "薑黃素", "藍莓素", "葉黃素", "深海魚油", 
        "睡眠丸", "益生菌", "Q10", "尿適通", "血淨", 
        "肝淨", "腦活素", "兒童助長素", "蟲草皇", "靈芝皇", 
        "健腰益生菌", "膠原蛋白丸", "牛樟芝", "海狗丸", "私密淨"
    ]
    inv_data = {
        "產品名稱": products,
        "現貨庫存": np.random.randint(10, 150, size=len(products)),
        "在途貨物": np.random.randint(0, 100, size=len(products)),
        "預警門檻": [50] * len(products)
    }
    pd.DataFrame(inv_data).to_csv("inventory.csv", index=False)
    
    # 生成模擬銷售
    sales_list = []
    start_date = datetime.now() - timedelta(days=90)
    for _ in range(200):
        p = np.random.choice(products)
        qty = np.random.randint(1, 5)
        date = start_date + timedelta(days=np.random.randint(0, 90))
        sub = np.random.choice(["無", "30天", "90天"], p=[0.7, 0.2, 0.1])
        sales_list.append([p, qty, date.strftime("%Y-%m-%d"), sub])
    pd.DataFrame(sales_list, columns=["產品名稱", "數量", "日期", "訂閱週期"]).to_csv("all_orders_90days.csv", index=False)
    return "✅ 模擬數據初始化成功！"

if __name__ == "__main__":
    # 預設執行模擬數據
    print(generate_mock_data())