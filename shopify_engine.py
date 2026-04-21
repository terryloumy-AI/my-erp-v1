import requests
import streamlit as st

# 從 Secrets 讀取密鑰
SHOPIFY_ACCESS_TOKEN = st.secrets["SHOPIFY_ACCESS_TOKEN"]
SHOP_URL = st.secrets["SHOP_URL"]
API_VERSION = "2024-04"

def get_real_inventory():
    """抓取產品庫存、成本與毛利"""
    # 1. 抓取產品基本資訊
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/products.json"
    headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            products = response.json().get('products', [])
            product_list = []
            
            for p in products:
                variant = p['variants'][0]
                price = float(variant.get('price', 0))
                # 取得 Shopify 內的成本欄位 (需透過 inventory_item 接口，這裡簡化邏輯供演示)
                # 註：真實環境中，Shopify API 的成本存放在 inventory_items 中
                # 為了讓你立刻看到效果，我們嘗試抓取，若無則預設一個比例
                cost = float(variant.get('compare_at_price', 0)) if variant.get('compare_at_price') else price * 0.6
                
                profit = price - cost
                margin = (profit / price) * 100 if price > 0 else 0
                
                product_list.append({
                    "產品名稱": p['title'],
                    "售價 (USD)": price,
                    "成本 (USD)": cost,
                    "毛利 (Profit)": profit,
                    "毛利率 (Margin %)": margin,
                    "現貨庫存": variant.get('inventory_quantity', 0),
                    "預警門檻": 50
                })
            return product_list
        return None
    except: return None

def get_orders_and_profit():
    """抓取訂單概況"""
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/orders.json?status=any"
    headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            orders = response.json().get('orders', [])
            order_data = []
            for o in orders:
                f_status = o.get('fulfillment_status')
                status_label = "Shipped" if f_status == 'fulfilled' else "Pending"
                
                order_data.append({
                    "Order_ID": o.get('name'),
                    "Total_USD": float(o.get('total_price', 0)),
                    "Status": status_label
                })
            return order_data
        return None
    except: return None
