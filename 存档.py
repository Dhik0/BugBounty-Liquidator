import json
import os

def extract_domains(input_file, output_file, exclude_file='exclude.txt'):
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found.")
        return

    # 读取排除列表
    excludes = set()
    if os.path.exists(exclude_file):
        with open(exclude_file, 'r', encoding='utf-8') as f:
            excludes = {line.strip().lower() for line in f if line.strip()}
        print(f"[*] 已加载 {len(excludes)} 个排除域名。")

    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        domains = set()
        for entry in data:
            common_name = entry.get("common_name", "")
            if common_name:
                # 处理可能存在的多行或逗号分隔的情况
                raw_names = common_name.replace(',', '\n').split('\n')
                for name in raw_names:
                    name = name.strip().lower()
                    # 过滤掉通配符域名
                    if name and not name.startswith('*'):
                        # 检查是否在排除列表中
                        if name not in excludes:
                            domains.add(name)
        
        # 排序后写入文件
        sorted_domains = sorted(list(domains))
        with open(output_file, 'w', encoding='utf-8') as f:
            for domain in sorted_domains:
                f.write(domain + '\n')
        
        print(f"Successfully extracted {len(sorted_domains)} unique domains to {output_file}")

    except json.JSONDecodeError:
        print(f"Error: Failed to decode JSON from {input_file}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    extract_domains('bestbuy.txt', 'targets.txt', 'exclude.txt')
