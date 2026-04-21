import requests
import streamlit as st

SHOPIFY_ACCESS_TOKEN = st.secrets["SHOPIFY_ACCESS_TOKEN"]
SHOP_URL = st.secrets["SHOP_URL"]
API_VERSION = "2024-04"

def get_real_inventory():
    """精準抓取產品、庫存及真實成本"""
    headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}
    
    try:
        # 1. 抓取產品基本資訊
        p_url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/products.json"
        p_res = requests.get(p_url, headers=headers, timeout=10)
        
        if p_res.status_code == 200:
            products = p_res.json().get('products', [])
            product_list = []
            
            for p in products:
                variant = p['variants'][0]
                inventory_item_id = variant.get('inventory_item_id')
                price = float(variant.get('price', 0))
                
                # 2. 精準抓取該品項的真實成本 (Cost per item)
                cost = 0.0
                if inventory_item_id:
                    c_url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/inventory_items/{inventory_item_id}.json"
                    c_res = requests.get(c_url, headers=headers, timeout=5)
                    if c_res.status_code == 200:
                        cost_str = c_res.json().get('inventory_item', {}).get('cost')
                        cost = float(cost_str) if cost_str else 0.0
                
                # 如果 API 沒設定成本，則回退到 0，避免誤導
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
    except:
        return None

def get_orders_and_profit():
    """抓取訂單概況"""
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/orders.json?status=any"
    headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            orders = response.json().get('orders', [])
            return [{"Order_ID": o.get('name'), "Total_USD": float(o.get('total_price', 0)), "Status": "Shipped" if o.get('fulfillment_status') == 'fulfilled' else "Pending"} for o in orders]
        return None
    except:
        return None
