import requests
import re
import os
import time
from colorama import Fore, init

init(autoreset=True)

def auto_liquidate(target_domain):
    input_file = 'in'
    output_file = 'out'
    exclude_file = 'exclude.txt'

    # 1. 第一步：自动抓取情报 (带重试机制和伪装)
    print(f"[*] 正在从 crt.sh 实时清算 {target_domain} 的情报...")
    url = f"https://crt.sh/?q=%.{target_domain}&output=json"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json'
    }

    try:
        # 增加到 60 秒超时，因为大型查询真的很慢
        response = requests.get(url, headers=headers, timeout=60) 
        
        if response.status_code == 200:
            with open(input_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
            print(f"{Fore.GREEN}[+] 情报已完整入库 (in)")
        elif response.status_code == 503:
            print(f"{Fore.YELLOW}[!] 服务器 503 罢工（通常是查询量太大导致超时）。")
            print(f"{Fore.CYAN}[💡] 建议：过 10 秒再试，或者手动在浏览器访问该链接并另存为 'in'。")
            return
        else:
            print(f"{Fore.RED}[-] 接口返回错误码: {response.status_code}")
            return

    except requests.exceptions.Timeout:
        print(f"{Fore.RED}[!] 请求超时！服务器响应太慢了。")
        return
    except Exception as e:
        print(f"{Fore.RED}[!] 抓取过程发生未知错误: {e}")
        return

    # 2. 第二步：启动地毯式提炼 (正则逻辑)
    print(f"[*] 正在启动地毯式提炼...")
    try:
        if not os.path.exists(input_file):
            return

        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 匹配域名格式
        domain_pattern = r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}'
        raw_matches = re.findall(domain_pattern, content)

        # 加载黑名单
        excluded = set()
        if os.path.exists(exclude_file):
            with open(exclude_file, 'r', encoding='utf-8') as f:
                excluded = {line.strip().lower() for line in f if line.strip()}

        domains = set()
        for s in raw_matches:
            s = s.strip().lower().lstrip('.')
            # 逻辑清算：必须以目标域名结尾，防止 milsons 这种词中包含的情况
            if s.endswith('.' + target_domain) and '*' not in s and s not in excluded:
                domains.add(s)

        with open(output_file, 'w', encoding='utf-8') as f:
            for d in sorted(domains):
                f.write(d + '\n')
        
        print(f"{Fore.GREEN}[🏆] 清算完成！得到唯一合规域名: {len(domains)} 个")

    except Exception as e:
        print(f"{Fore.RED}[!] 提炼过程出错: {e}")

if __name__ == "__main__":
    # --- 你在这里改域名就行 ---
    auto_liquidate('tines.com')