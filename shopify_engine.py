import requests

# --- ⚠️ 填寫區 ⚠️ ---
# 1. 點擊「顯示權杖一次」後，把那串 shpat_... 貼在下面
SHOPIFY_ACCESS_TOKEN = "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" 

# 2. 你的商店網址 (根據你的截圖確認為此網址)
SHOP_URL = "a-health-lab.myshopify.com"

API_VERSION = "2024-01"

def get_real_inventory():
    """從 Shopify API 抓取真實庫存數據"""
    url = f"https://{SHOP_URL}/admin/api/{API_VERSION}/products.json"
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN,
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            products = response.json().get('products', [])
            if not products:
                return None
                
            inv_list = []
            for p in products:
                if 'variants' in p and len(p['variants']) > 0:
                    variant = p['variants'][0]
                    inv_list.append({
                        "產品名稱": p['title'],
                        "Product_ID": str(p['id']),
                        "現貨庫存": variant.get('inventory_quantity', 0),
                        "在途貨物": 0,
                        "預警門檻": 50
                    })
            return inv_list
        else:
            return None
    except Exception:
        return None
