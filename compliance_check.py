import re

class ComplianceChecker:
    def __init__(self):
        # 1. 違規關鍵字清單 (中英雙語)
        self.forbidden_words = [
            "根治", "治療", "治癒", "癌症", "糖尿病", "消炎", "藥到病除", "療效",
            "Cure", "Treat", "Heal", "Cancer", "Diabetes", "Anti-inflammatory", "Medical effect"
        ]
        
        # 2. 誇大不實字眼
        self.sensitive_words = [
            "100%", "百分之百", "保證", "立即見效", "全球第一", "最強",
            "Guaranteed", "Instant results", "No.1", "Best", "Breakthrough"
        ]

    def scan(self, text):
        found_red = [w for w in self.forbidden_words if re.search(w, text, re.IGNORECASE)]
        found_yellow = [w for w in self.sensitive_words if re.search(w, text, re.IGNORECASE)]
        return found_red, found_yellow

# 測試用 (點擊執行可以看結果)
if __name__ == "__main__":
    checker = ComplianceChecker()
    test_text = "這款 NMN 產品能根治失眠，100%保證有效，是全球最強的 Cancer 剋星。"
    red, yellow = checker.scan(test_text)
    print(f"嚴重違規: {red}")
    print(f"建議修改: {yellow}")