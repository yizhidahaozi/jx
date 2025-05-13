import requests
import pandas as pd
import re
import os

urls = [
    "https://qu.ax/vUBde.txt",
    "http://live.nctv.top/x.txt",
    "https://json.doube.eu.org/XingHuo.txt",
    "https://raw.githubusercontent.com/zwc456baby/iptv_alive/master/live.txt",
    "https://raw.githubusercontent.com/BurningC4/Chinese-IPTV/master/TV-IPV4.m3u",
    "https://raw.githubusercontent.com/YueChan/Live/refs/heads/main/APTV.m3u",
    "https://raw.githubusercontent.com/Wirili/IPTV/refs/heads/main/live.m3u",
    "https://raw.githubusercontent.com/wwb521/live/refs/heads/main/tv.m3u",
    "https://raw.githubusercontent.com/Kimentanm/aptv/master/m3u/iptv.m3u",
    "https://live.zbds.top/tv/iptv4.txt",
    "https://live.zbds.top/tv/iptv6.txt",
]

# 读取group-title.txt文件
def load_group_reference(filepath="config/iptv.txt"):
    group_reference = {}
    current_group = None
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
                
            if line.endswith(",#genre#"):
                # 新的分组
                current_group = line.split(",")[0]
                group_reference[current_group] = []
            elif current_group and line:
                # 添加到当前分组
                patterns = [p.strip() for p in line.split("|") if p.strip()]
                group_reference[current_group].extend(patterns)
    
    return group_reference

# 加载分组参考
GROUP_REFERENCE = load_group_reference()

ipv4_pattern = re.compile(r'^http://(\d{1,3}\.){3}\d{1,3}')
ipv6_pattern = re.compile(r'^http://\[([a-fA-F0-9:]+)\]')

def fetch_streams_from_url(url):
    print(f"正在爬取网站源: {url}")
    try:
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'
        if response.status_code == 200:
            return response.text
        print(f"从 {url} 获取数据失败，状态码: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"请求 {url} 时发生错误: {e}")
    return None

def fetch_all_streams():
    all_streams = []
    for url in urls:
        if content := fetch_streams_from_url(url):
            all_streams.append(content)
        else:
            print(f"跳过来源: {url}")
    return "\n".join(all_streams)

def get_group_title(program_name):
    """根据节目名称获取对应的group-title，使用正则表达式匹配"""
    for group, patterns in GROUP_REFERENCE.items():
        for pattern in patterns:
            # 使用正则表达式进行匹配
            try:
                if re.search(pattern, program_name, re.IGNORECASE):
                    return group
            except re.error:
                # 如果正则表达式有误，作为普通字符串匹配
                if pattern.lower() in program_name.lower():
                    return group
    return "其他频道"  # 默认分组

def parse_m3u(content):
    streams = []
    current_program = None
    current_group = None
    current_extinf = None

    for line in content.splitlines():
        if line.startswith("#EXTINF"):
            current_extinf = line
            # 尝试从EXTINF行中提取group-title
            if match := re.search(r'group-title="([^"]+)"', line):
                current_group = match.group(1).strip()
            else:
                current_group = None
                
            if match := re.search(r'tvg-name="([^"]+)"', line):
                current_program = match.group(1).strip()
            elif ',' in line:
                current_program = line.split(',')[-1].strip()
        elif line.startswith("http"):
            if current_program:
                # 根据引用文件确定分组，优先使用引用文件的分组
                final_group = get_group_title(current_program)
                
                streams.append({
                    "program_name": current_program,
                    "stream_url": line.strip(),
                    "group_title": final_group,
                    "extinf_line": current_extinf
                })
                current_program = None
                current_group = None
                current_extinf = None

    return streams

def parse_txt(content):
    streams = []
    for line in content.splitlines():
        if match := re.match(r"(.+?),\s*(http.+)", line):
            program_name = match.group(1).strip()
            group_title = get_group_title(program_name)
            streams.append({
                "program_name": program_name,
                "stream_url": match.group(2).strip(),
                "group_title": group_title,
                "extinf_line": None
            })
    return streams

def organize_streams(content):
    parser = parse_m3u if content.startswith("#EXTM3U") else parse_txt
    streams = parser(content)
    
    # 创建DataFrame
    df = pd.DataFrame(streams)
    
    # 去重
    df = df.drop_duplicates(subset=['program_name', 'stream_url'])
    
    # 分组整理
    grouped = df.groupby(['group_title', 'program_name'])['stream_url'].apply(list).reset_index()
    return grouped

def save_to_txt(grouped_streams, filename="lib/iptv.txt"):
    ipv4 = []
    ipv6 = []
    
    # 先按group_title分组
    grouped = grouped_streams.groupby('group_title')
    
    for group_name, group_data in grouped:
        ipv4_group = []
        ipv6_group = []
        
        for _, row in group_data.iterrows():
            program = row['program_name']
            for url in row['stream_url']:
                if ipv4_pattern.match(url):
                    ipv4_group.append(f"{program},{url}")
                elif ipv6_pattern.match(url):
                    ipv6_group.append(f"{program},{url}")
        
        if ipv4_group:
            ipv4.append(f"\n# {group_name}\n" + "\n".join(ipv4_group))
        if ipv6_group:
            ipv6.append(f"\n# {group_name}\n" + "\n".join(ipv6_group))

    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# IPv4 Streams")
        f.write("\n".join(ipv4))
        f.write("\n\n# IPv6 Streams")
        f.write("\n".join(ipv6))
    print(f"文本文件已保存: {os.path.abspath(filename)}")

def save_to_m3u(grouped_streams, filename="lib/iptv.m3u"):
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        
        # 先按group_title分组
        grouped = grouped_streams.groupby('group_title')
        
        for group_name, group_data in grouped:
            # 写入分组标题
            f.write(f'\n#EXTINF:-1 group-title="{group_name}",{group_name}\n#DUMMY\n')
            
            # 写入该分组下的所有频道
            for _, row in group_data.iterrows():
                program = row['program_name']
                for url in row['stream_url']:
                    f.write(f'#EXTINF:-1 group-title="{group_name}" tvg-name="{program}",{program}\n{url}\n')

    print(f"M3U文件已保存: {os.path.abspath(filename)}")

if __name__ == "__main__":
    print("开始抓取所有源...")
    if content := fetch_all_streams():
        print("整理源数据中...")
        organized = organize_streams(content)
        save_to_txt(organized)
        save_to_m3u(organized)
    else:
        print("未能获取有效数据")