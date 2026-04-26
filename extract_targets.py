import requests
import re
import os
import subprocess
import time
from colorama import Fore, init

# 初始化色彩系统
init(autoreset=True)

def fetch_data(domain):
    """多源情报提取引擎：按优先级轮询，只要有一个活着就出结果"""
    sources = [
        {
            "name": "crt.sh",
            "url": f"https://crt.sh/?q=%.{domain}&output=json",
            "timeout": 45
        },
        {
            "name": "Anubis",
            "url": f"https://jldc.me/anubis/subdomains/{domain}",
            "timeout": 20
        },
        {
            "name": "HackerTarget",
            "url": f"https://api.hackertarget.com/hostsearch/?q={domain}",
            "timeout": 20
        }
    ]

    for source in sources:
        try:
            print(f"[*] 正在尝试节点: {Fore.CYAN}{source['name']}")
            r = requests.get(source['url'], timeout=source['timeout'], headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            if r.status_code == 200 and len(r.text) > 20:
                print(f"{Fore.GREEN}[+] {source['name']} 响应成功！")
                return r.text
            else:
                print(f"{Fore.YELLOW}[!] {source['name']} 返回异常码: {r.status_code}")
        except Exception as e:
            print(f"{Fore.RED}[!] {source['name']} 节点连接超时或崩溃。")
    return None

def auto_liquidate(target_domain):
    # --- 路径与文件配置 ---
    HTTPX_PATH = r'D:\BUG\工具\httpx_1.9.0_windows_386\httpx.exe'
    input_file = 'in'
    output_file = 'out'
    exclude_file = 'exclude.txt'
    alive_file = 'alive.txt'

    # 1. 启动情报搜集
    content = fetch_data(target_domain)
    if not content:
        print(f"{Fore.RED}[X] 致命错误：所有情报源均已 502/超时。请检查网络或稍后重试。")
        return

    with open(input_file, 'w', encoding='utf-8') as f:
        f.write(content)

    # 2. 启动地毯式提炼
    print(f"[*] 正在执行正则提炼与黑名单过滤...")
    try:
        # 更加严谨的域名匹配正则
        domain_pattern = r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}'
        raw_matches = re.findall(domain_pattern, content)

        # 加载黑名单逻辑（这就是你担心的那部分“消失”的代码）
        excluded = set()
        if os.path.exists(exclude_file):
            with open(exclude_file, 'r', encoding='utf-8') as f:
                excluded = {line.strip().lower() for line in f if line.strip()}

        domains = set()
        for s in raw_matches:
            s = s.strip().lower().lstrip('.')
            # 严格后缀匹配逻辑
            if s.endswith('.' + target_domain) and '*' not in s and s not in excluded:
                domains.add(s)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sorted(domains)))
        
        print(f"{Fore.GREEN}[🏆] 提炼完成！当前合规域名总数: {len(domains)}")

    except Exception as e:
        print(f"{Fore.RED}[!] 提炼过程出错: {e}")
        return

    # 3. 启动 httpx 存活探测
    if domains:
        print(f"[*] 正在调用 httpx 进行最终清算...")
        if not os.path.exists(HTTPX_PATH):
            print(f"{Fore.RED}[!] 错误：未在指定路径找到 httpx.exe")
            return

        try:
            # -silent 减少干扰, -sc 状态码, -title 标题, -cl 长度, -t 线程数
            cmd = f'type {output_file} | "{HTTPX_PATH}" -silent -sc -title -cl -t 50 -o {alive_file}'
            subprocess.run(cmd, shell=True)

            if os.path.exists(alive_file):
                with open(alive_file, 'r', encoding='utf-8') as f:
                    alive_count = len(f.readlines())
                print(f"{Fore.GREEN}[🏁] 任务圆满完成！活跃 Web 目标: {alive_count}")
                print(f"{Fore.CYAN}[💡] 最终战果清单: {alive_file}")
        except Exception as e:
            print(f"{Fore.RED}[!] httpx 调度失败: {e}")
    else:
        print(f"{Fore.YELLOW}[!] 无有效资产可供探测。")

if __name__ == "__main__":
    # 使用纯域名测试，不要带 https://
    auto_liquidate('bumble.com')