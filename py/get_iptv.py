import requests
import pandas as pd
import re
import os
from typing import List, Dict, Optional

urls = [
    "https://qu.ax/vUBde.txt",
    "http://live.nctv.top/x.txt",
    "https://aktv.space/live.m3u",
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

ipv4_pattern = re.compile(r'^http://(\d{1,3}\.){3}\d{1,3}')
ipv6_pattern = re.compile(r'^http://\[([a-fA-F0-9:]+)\]')

def fetch_streams_from_url(url: str) -> Optional[str]:
    """从指定URL获取流内容"""
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

def fetch_all_streams() -> str:
    """从所有URL获取流内容并合并"""
    all_streams = []
    for url in urls:
        if content := fetch_streams_from_url(url):
            all_streams.append(content)
        else:
            print(f"跳过来源: {url}")
    return "\n".join(all_streams)

def parse_m3u(content: str) -> List[Dict[str, str]]:
    """解析M3U格式内容，提取节目信息和分组"""
    streams = []
    current_program = None
    group_title = "未分组"  # 默认分组

    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#EXTINF"):
            # 提取tvg-name
            if match := re.search(r'tvg-name="([^"]+)"', line):
                current_program = match.group(1).strip()
            # 提取group-title
            if match := re.search(r'group-title="([^"]+)"', line):
                group_title = match.group(1).strip()
        elif line and line.startswith("http"):
            if current_program:
                streams.append({
                    "program_name": current_program,
                    "stream_url": line,
                    "group_title": group_title
                })
                current_program = None
                group_title = "未分组"  # 重置为默认值
    return streams

def parse_txt(content: str) -> List[Dict[str, str]]:
    """解析TXT格式内容，支持带分组信息"""
    streams = []
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
            
        # 支持两种格式：
        # 1. 节目名称,URL
        # 2. 节目名称,URL,分组名称
        if match := re.match(r"(.+?),\s*(http.+?)(?:,\s*(.+))?$", line):
            program = match.group(1).strip()
            url = match.group(2).strip()
            group = match.group(3).strip() if match.group(3) else "未分组"
            
            streams.append({
                "program_name": program,
                "stream_url": url,
                "group_title": group
            })
    return streams

def organize_streams(content: str) -> pd.DataFrame:
    """整理流数据并去重"""
    parser = parse_m3u if content.startswith("#EXTM3U") else parse_txt
    df = pd.DataFrame(parser(content))
    df = df.drop_duplicates(subset=['program_name', 'stream_url'])
    return df

def save_to_txt(df: pd.DataFrame, filename: str = "lib/iptv.txt") -> None:
    """保存为TXT格式，按IPv4/IPv6分类"""
    ipv4 = []
    ipv6 = []

    for _, row in df.iterrows():
        line = f"{row['program_name']},{row['stream_url']}"
        if row['group_title'] != "未分组":
            line += f",{row['group_title']}"
            
        if ipv4_pattern.match(row['stream_url']):
            ipv4.append(line)
        elif ipv6_pattern.match(row['stream_url']):
            ipv6.append(line)

    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("# IPv4 Streams\n" + "\n".join(ipv4))
        f.write("\n\n# IPv6 Streams\n" + "\n".join(ipv6))
    print(f"文本文件已保存: {os.path.abspath(filename)}")

def save_to_m3u(df: pd.DataFrame, filename: str = "lib/iptv.m3u") -> None:
    """保存为M3U格式，包含分组信息"""
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("#EXTM3U\n")
        for _, row in df.iterrows():
            f.write(f'#EXTINF:-1 tvg-name="{row["program_name"]}" group-title="{row["group_title"]}",{row["program_name"]}\n')
            f.write(f"{row['stream_url']}\n")
    print(f"M3U文件已保存: {os.path.abspath(filename)}")

if __name__ == "__main__":
    print("开始抓取所有源...")
    if content := fetch_all_streams():
        print("整理源数据中...")
        df = organize_streams(content)
        save_to_txt(df)
        save_to_m3u(df)
    else:
        print("未能获取有效数据")