import requests
import time
import urllib3
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import Fore, init

# 禁用 SSL 警告（有些大厂内网证书不合规，跳过警告防止刷屏）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
init(autoreset=True)

# ==================== 【关键配置】 ====================
H1_USERNAME = "dhiko_"  # 你的用户名
H1_EMAIL = f"{H1_USERNAME}@wearehackerone.com"
MAX_THREADS = 15        # 线程数，建议 10-20，太快容易被封 IP
# =====================================================

# 探测任务清单：路径 -> 关键命中特征
TARGET_TASKS = {
    "/xmlrpc.php": "system.multicall",
    "/.env": "DB_PASSWORD",
    "/.git/config": "repositoryformatversion",
    "/actuator/env": "activeProfiles",
    "/.vscode/sftp.json": "password"
}

def scan_site(domain):
    domain = domain.strip().lower()
    if not domain: return []
    
    # 统一格式化为 https
    base_url = f"https://{domain}" if not domain.startswith('http') else domain
    base_url = base_url.rstrip('/')
    
    headers = {
        'User-Agent': f'Research-Scanner/2.0 ({H1_EMAIL})',
        'X-HackerOne-Research': H1_USERNAME,
        'Accept': '*/*'
    }
    
    found_vulns = []
    
    for path, feature in TARGET_TASKS.items():
        target = f"{base_url}{path}"
        try:
            # 这里的 time.sleep 是单线程内的微型延迟，避免瞬间并发过高
            time.sleep(0.1) 
            
            # 使用 GET 探测（XML-RPC 依然用 POST，但大部分敏感文件是 GET）
            if "xmlrpc" in path:
                payload = """<methodCall><methodName>system.listMethods</methodName><params></params></methodCall>"""
                resp = requests.post(target, data=payload, headers=headers, timeout=8, verify=False)
            else:
                resp = requests.get(target, headers=headers, timeout=8, verify=False, allow_redirects=False)

            # 判定逻辑：状态码 200 且 包含特征字符
            if resp.status_code == 200 and feature in resp.text:
                print(f"{Fore.RED}[🔥] 命中！路径: {target} | 特征: {feature}")
                found_vulns.append(target)
                
        except Exception:
            pass
            
    return found_vulns, domain

if __name__ == "__main__":
    input_file = 'out' 
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            domains = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"{Fore.RED}[-] 错误：找不到目标文件 '{input_file}'")
        exit()

    total = len(domains)
    print(f"{Fore.CYAN}>>> 启动清算 2.0：目标 {total} 个 | 监控 {len(TARGET_TASKS)} 个高危路径 <<<\n")

    all_vulnerable = []
    
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_to_domain = {executor.submit(scan_site, d): d for d in domains}
        
        count = 0
        for future in as_completed(future_to_domain):
            count += 1
            vulns, domain = future.result()
            
            if vulns:
                all_vulnerable.extend(vulns)
            
            # 进度显示：每处理 10 个打印一次，防止刷屏太快
            if count % 10 == 0 or count == total:
                print(f"{Fore.WHITE}[进度 {count}/{total}] 正在清算: {domain}")

    # --- 战果结算 ---
    print(f"\n{Fore.CYAN}{'='*50}")
    if all_vulnerable:
        with open('vulnerable_found.txt', 'a', encoding='utf-8') as f:
            for v in all_vulnerable:
                f.write(v + '\n')
        print(f"{Fore.GREEN}[🏆] 清算大捷！捕获 {len(all_vulnerable)} 个高危漏洞，已存入 vulnerable_found.txt")
    else:
        print(f"{Fore.YELLOW}[-] 这波目标依然很硬，建议换一批资产或增加探测路径。")
    print(f"{Fore.CYAN}{'='*50}")