import re
import requests
from collections import OrderedDict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

tv_urls = [
    "https://qu.ax/vUBde.txt",
    "https://m3u.ibert.me/fmml_ipv6.m3u",
    "https://raw.githubusercontent.com/Guovin/iptv-api/refs/heads/gd/output/result.m3u",
    "https://raw.githubusercontent.com/zwc456baby/iptv_alive/master/live.m3u",
    "https://raw.githubusercontent.com/BurningC4/Chinese-IPTV/master/TV-IPV4.m3u",
    "https://raw.githubusercontent.com/Wirili/IPTV/refs/heads/main/live.m3u",
    "https://raw.githubusercontent.com/wwb521/live/refs/heads/main/tv.m3u",
    "https://raw.githubusercontent.com/Kimentanm/aptv/master/m3u/iptv.m3u",
    "https://live.zbds.top/tv/iptv4.m3u",
    "https://live.zbds.top/tv/iptv6.m3u",
    "https://raw.githubusercontent.com/wind005/TVlive/refs/heads/main/m3u/%E6%B9%96%E5%8D%97%E7%A7%BB%E5%8A%A8.m3u",
    "https://raw.githubusercontent.com/hanhan8127/TVBox/refs/heads/main/live.txt",
    "https://raw.githubusercontent.com/hujingguang/ChinaIPTV/main/cnTV_AutoUpdate.m3u8",
    "https://raw.githubusercontent.com/suxuang/myIPTV/refs/heads/main/ipv4.m3u",
    "https://raw.githubusercontent.com/suxuang/myIPTV/refs/heads/main/ipv6.m3u",
    "https://raw.githubusercontent.com/Free-TV/IPTV/master/playlist.m3u8",
    "",
]

def parse_template(template_file):
    template_channels = OrderedDict()
    current_category = None
    with open(template_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                if "#genre#" in line:
                    current_category = line.split(",")[0].strip()
                    template_channels[current_category] = []
                elif current_category:
                    channel_name = line.split(",")[0].strip()
                    template_channels[current_category].append(channel_name)
    return template_channels

def fetch_channels(url):
    channels = OrderedDict()
    try:
        response = requests.get(url, timeout=120)
        response.raise_for_status()
        response.encoding = "utf-8"
        if response.status_code != 200:
            print(f"从 {url} 获取数据失败，状态码: {response.status_code}")
            return None

        lines = response.text.split("\n")
        is_m3u = any("#EXTINF" in line for line in lines[:5])
        current_category = None

        if is_m3u:
            channel_name = ""
            tvg_name = ""
            tvg_logo = ""
            group_title = ""

            for line in lines:
                line = line.strip()

                if line.startswith("#EXTINF"):
                    # 重置变量
                    channel_name = ""
                    tvg_name = ""
                    tvg_logo = ""
                    group_title = ""
                    
                    # 提取 tvg-name - 增强正则表达式兼容性
                    tvg_name_match = re.search(r'tvg-name\s*=\s*"([^"]*)"', line)
                    if tvg_name_match:
                        tvg_name = tvg_name_match.group(1).strip()
                    
                    # 提取 tvg-logo
                    tvg_logo_match = re.search(r'tvg-logo\s*=\s*"([^"]*)"', line)
                    if tvg_logo_match:
                        tvg_logo = tvg_logo_match.group(1).strip()
                    
                    # 提取 group-title
                    group_title_match = re.search(r'group-title\s*=\s*"([^"]*)"', line)
                    if group_title_match:
                        group_title = group_title_match.group(1).strip()
                        current_category = group_title
                    
                    # 增强频道名称提取：多种格式兼容
                    # 方法1: 提取逗号后的内容（标准格式）
                    name_match = re.search(r',\s*(.*)$', line)
                    if name_match:
                        channel_name = name_match.group(1).strip()
                    
                    # 方法2: 如果上述方法失败，尝试提取最后一个引号后的内容
                    if not channel_name:
                        fallback_match = re.search(r'",\s*(.*)$', line)
                        if fallback_match:
                            channel_name = fallback_match.group(1).strip()
                    
                    # 方法3: 如果仍然无法提取，使用tvg-name作为回退[citation:10]
                    if not channel_name and tvg_name:
                        channel_name = tvg_name
                        print(f"警告: 使用tvg-name作为频道名称回退: {tvg_name}")
                    
                    # 最终回退：使用未知频道标识
                    if not channel_name:
                        channel_name = f"Unknown_Channel_{hash(line) % 10000:04d}"
                        print(f"警告: 无法提取频道名称，使用回退: {channel_name}")

                    # 如果没有获取到 group-title，使用默认分类
                    if not group_title and current_category:
                        group_title = current_category

                elif line and not line.startswith("#"):
                    if line and (channel_name or tvg_name):  # 只要有名称或tvg-name就处理
                        # 使用提取的信息构建频道数据
                        final_display_name = channel_name or tvg_name or f"Unknown_{hash(line) % 10000:04d}"
                        
                        channel_data = {
                            'url': line.strip(),
                            'tvg_name': tvg_name or final_display_name,
                            'tvg_logo': tvg_logo,
                            'group_title': group_title or current_category or "Default",
                            'display_name': final_display_name
                        }
                        
                        category_key = group_title or current_category or "Default"
                        if category_key not in channels:
                            channels[category_key] = []
                        channels[category_key].append(channel_data)
                        
                        # 重置变量以备下一个条目
                        channel_name = ""
                        tvg_name = ""
                        tvg_logo = ""
                        group_title = ""

        else:
            # 非 M3U 格式处理 - 同样增强健壮性
            for line in lines:
                line = line.strip()
                if "#genre#" in line:
                    current_category = line.split(",")[0].strip()
                    channels[current_category] = []
                elif current_category and line:
                    parts = line.split(",", 1)
                    if len(parts) == 2:
                        name, url = parts
                        if not name.strip():  # 如果名称为空，使用回退
                            name = f"Unknown_Channel_{hash(line) % 10000:04d}"
                        channel_data = {
                            'url': url.strip(),
                            'tvg_name': name.strip(),
                            'tvg_logo': "",
                            'group_title': current_category,
                            'display_name': name.strip()
                        }
                        channels[current_category].append(channel_data)
                    elif len(parts) == 1 and line:
                        # 处理只有URL没有名称的情况
                        url = line
                        name = f"Unknown_Channel_{hash(line) % 10000:04d}"
                        channel_data = {
                            'url': url.strip(),
                            'tvg_name': name,
                            'tvg_logo': "",
                            'group_title': current_category,
                            'display_name': name
                        }
                        channels[current_category].append(channel_data)

        return channels

    except requests.exceptions.RequestException as e:
        print(f"请求 {url} 时发生错误: {e}")
        return OrderedDict()
    except Exception as e:
        print(f"处理 {url} 时发生未知错误: {str(e)}")
        return OrderedDict()

def match_channels(template_channels, all_channels):
    matched = OrderedDict()
    for category, names in template_channels.items():
        matched[category] = OrderedDict()
        for name in names:
            primary_name = name.split("|")[0].strip()
            matched[category][primary_name] = []
            
            # 在所有频道源中搜索匹配的频道
            for src_category, channels in all_channels.items():
                for channel_data in channels:
                    chan_name = channel_data['display_name']
                    tvg_name = channel_data['tvg_name']
                    
                    # 检查是否匹配模板中的任何名称（用 | 分隔）
                    template_names = [n.strip() for n in name.split("|")]
                    
                    if any(template_name in chan_name or template_name in tvg_name 
                          for template_name in template_names):
                        matched[category][primary_name].append(channel_data)
    
    return matched

def is_ipv6(url):
    return re.match(r"^http:\/\/\[[0-9a-fA-F:]+\]", url) is not None

def generate_outputs(channels, template_channels):

    written_urls = set()
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    with open("lib/iptv.m3u", "w", encoding="utf-8") as m3u, \
         open("lib/iptv.txt", "w", encoding="utf-8") as txt:

        # 写入 M3U 头
        m3u.write("#EXTM3U x-tvg-url=\"\"\n")
        
        total_count = 0
        for category in template_channels:
            if category not in channels:
                continue

            txt.write(f"\n{category},#genre#\n")
            for name in template_channels[category]:
                primary_name = name.split("|")[0].strip()
                channel_data_list = channels[category].get(primary_name, [])

                # URL 去重
                unique_channels = []
                seen_urls = set()
                for channel_data in channel_data_list:
                    url = channel_data['url']
                    if url and url not in seen_urls and url not in written_urls:
                        seen_urls.add(url)
                        unique_channels.append(channel_data)

                if not unique_channels:
                    continue

                # 格式化输出
                total = len(unique_channels)
                for idx, channel_data in enumerate(unique_channels, 1):
                    url = channel_data['url']
                    tvg_name = channel_data['tvg_name']
                    tvg_logo = channel_data['tvg_logo']
                    group_title = channel_data['group_title']
                    
                    # 构建后缀
                    suffix = "$LR•" + ("IPV6" if is_ipv6(url) else "IPV4")
                    if total > 1:
                        suffix += f"•{total}『线路{idx}』"
                    final_url = f"{url}{suffix}"

                    # 写入 M3U 条目
                    logo_attr = f' tvg-logo="{tvg_logo}"' if tvg_logo else ""
                    m3u.write(f'#EXTINF:-1 tvg-id="{tvg_name}" tvg-name="{tvg_name}"{logo_attr} group-title="{group_title}",{primary_name}\n')
                    m3u.write(f"{final_url}\n")
                    
                    # 写入 TXT 条目
                    txt.write(f"{primary_name},{final_url}\n")
                    
                    written_urls.add(url)
                    total_count += 1

    print("=== 频道处理调试信息 ===")
    total_matched_categories = 0
    total_matched_channels = 0
    
    for category in template_channels:
        if category in channels and channels[category]:
            category_count = len(channels[category])
            total_matched_categories += 1
            total_matched_channels += category_count
            print(f"分类 '{category}': 匹配到 {category_count} 个频道")
        else:
            print(f"分类 '{category}': 未匹配到任何频道")
    
    print(f"总计: {total_matched_categories} 个分类匹配成功，{total_matched_channels} 个频道待处理")
    print("========================")
 
def filter_sources(template_file):
    template = parse_template(template_file)
    all_channels = OrderedDict()

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(fetch_channels, url): url for url in tv_urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                result = future.result()
                if result:
                    for cat, chans in result.items():
                        if cat not in all_channels:
                            all_channels[cat] = []
                        all_channels[cat].extend(chans)
            except Exception as e:
                print(f"处理源 {url} 时出错: {str(e)}")

    return match_channels(template, all_channels), template

if __name__ == "__main__":
    matched_channels, template = filter_sources("py/config/iptv.txt")
    generate_outputs(matched_channels, template)