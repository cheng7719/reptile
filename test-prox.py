import requests

def test_proxy(proxy):
    """
    測試單個代理伺服器是否可用。
    """
    url = "https://httpbin.org/ip"  # 測試代理用的目標網站
    proxies = {
        "http": f"http://{proxy}",
        "https": f"http://{proxy}"
    }
    try:
        print(f"正在測試代理: {proxy}")
        response = requests.get(url, proxies=proxies, timeout=5)
        response.raise_for_status()
        print("代理有效，返回的 IP 為:", response.json())
        return True
    except requests.exceptions.RequestException as e:
        print(f"代理無效: {e}")
        return False

if __name__ == "__main__":
    # 測試用代理，從 Free Proxy List 複製
    proxy = "3.70.191.255:8090"  # 替換為您的代理
    test_proxy(proxy)
