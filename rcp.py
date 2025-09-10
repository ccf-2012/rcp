# -*- coding: utf-8 -*-
import argparse
from collections import defaultdict
import configparser
import json
import os
import sys
import urllib.request
import urllib.error
import logging
import re

# 设置日志记录
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 从torcp.py借鉴的视频文件扩展名列表
VIDEO_EXTS = ['.mkv', '.mp4', '.ts', '.m2ts', '.mov', '.avi', '.wmv', '.strm', '.ass', '.srt']

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    if not os.path.exists(config_path):
        logging.error(f"配置文件 {config_path} 不存在。请参考 config.ini.template 创建。")
        sys.exit(1)
    
    config = configparser.ConfigParser()
    config.read(config_path)
    
    try:
        torll_config = config['torll']
        emby_config = config['emby']
        
        return {
            'url': torll_config['url'],
            'api_key': torll_config['api_key'],
            'root_path': emby_config['root_path'],
            'qbitname': torll_config['qbitname'],
        }
    except KeyError as e:
        logging.error(f"配置文件中缺少必要的键: {e}")
        sys.exit(1)

def get_media_info(config, torhash, dl_uuid, tor_path, torname=None):
    """向torll3 API发送请求获取媒体信息"""
    headers = {
        'X-API-Key': config['api_key'],
        'Content-Type': 'application/json'
    }
    payload = {
        'qbitname': config['qbitname'],
        'torhash': torhash,
        'dl_uuid': dl_uuid,
        'torname': torname,
        'tor_path': tor_path,
    }
    
    logging.info(f"向 {config['url']} 发送请求...")
    
    # 使用 urllib.request 替代 requests
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(config['url'], data=data, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            # 检查响应状态码
            if not (200 <= response.status < 300):
                logging.error(f"请求torll API失败，状态码: {response.status}")
                logging.error(f"响应内容: {response.read().decode('utf-8')}")
                sys.exit(1)
            
            logging.info("成功获取API响应。")
            # 读取并解析JSON响应
            response_body = response.read().decode('utf-8')
            return json.loads(response_body)
            
    except urllib.error.HTTPError as e:
        # HTTPError 能够提供响应体
        logging.error(f"请求torll API时发生HTTP错误: {e}")
        try:
            # 尝试读取错误响应体
            error_content = e.read().decode('utf-8')
            logging.error(f"响应内容: {error_content}")
        except Exception as read_error:
            logging.error(f"读取错误响应体失败: {read_error}")
        sys.exit(1)
    except urllib.error.URLError as e:
        # URLError 通常是网络层面的问题 (e.g., 无法连接)
        logging.error(f"请求torll API时发生URL错误: {e.reason}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"处理请求时发生未知错误: {e}")
        sys.exit(1)

def find_media_files(source_path):
    """在源路径中查找媒体文件"""
    media_files = []
    for root, _, files in os.walk(source_path):
        for file in files:
            if os.path.splitext(file)[1].lower() in VIDEO_EXTS:
                media_files.append(os.path.join(root, file))
    return media_files

def create_hard_link(src, dst):
    """创建硬链接，如果目标已存在则跳过"""
    try:
        if os.path.exists(dst):
            logging.warning(f"目标文件已存在，跳过链接: {dst}")
            return
        os.link(src, dst)
        logging.info(f"成功链接: {src} -> {dst}")
    except OSError as e:
        logging.error(f"创建硬链接失败: {e}")
    except Exception as e:
        logging.error(f"发生未知错误: {e}")

def generate_movie_links(target_dir, media_files, media_info):
    """
    根据媒体信息，为电影文件（包括关联字幕）生成并创建硬链接。
    处理文件名过长和多文件冲突的问题。
    """
    if not media_files:
        logging.warning(f"未找到任何媒体文件进行链接。")
        return

    # 按文件名（不含后缀）对文件进行分组，以处理字幕等关联文件
    file_groups = defaultdict(list)
    for f in media_files:
        base_name = os.path.splitext(os.path.basename(f))[0]
        file_groups[base_name].append(f)

    # 遍历每个文件组
    for i, (base_name, files_in_group) in enumerate(file_groups.items()):
        file_prefix = f"{media_info['tmdb_title']} ({media_info['tmdb_year']}) {media_info['emby_bracket']}"
        
        # 确定这组文件最长的后缀名，用于更准确地计算长度
        longest_ext = ""
        if files_in_group:
            longest_ext = max((os.path.splitext(f)[1] for f in files_in_group), key=len)

        # 检查加上原始文件名后的潜在长度
        potential_dst_base = f"{file_prefix} - {base_name}"
        potential_dst_file = os.path.join(target_dir, f"{potential_dst_base}{longest_ext}")
        
        final_dst_base = ""
        # 通常文件名限制是255字节，这里用250作为安全阈值
        if len(potential_dst_file.encode('utf-8')) > 250:
            logging.warning(f"目标文件名过长，将进行截断处理: {potential_dst_file}")
            # 如果过长，则不使用原始文件名。
            # 当存在多个文件组(如cd1,cd2)时，添加索引(-1, -2, ...)来防止冲突。
            index_suffix = f" - {i + 1}" if len(file_groups) > 1 else ""
            final_dst_base = f"{file_prefix.strip()}{index_suffix}"
        else:
            final_dst_base = potential_dst_base
        
        # 为组内的每个文件创建硬链接
        for src_file in files_in_group:
            _, file_ext = os.path.splitext(src_file)
            dst_file = os.path.join(target_dir, f"{final_dst_base}{file_ext}")
            create_hard_link(src_file, dst_file)

def process_movie(config, media_info, tor_path):
    """处理电影类别"""
    emby_root = config['root_path']
    
    emby_dir = media_info['emby_dir']
    target_dir = os.path.join(emby_root, emby_dir)
    
    logging.info(f"创建电影目录: {target_dir}")
    os.makedirs(target_dir, exist_ok=True)
    
    media_files = []
    if os.path.isfile(tor_path):
        if os.path.splitext(tor_path)[1].lower() in VIDEO_EXTS:
            media_files.append(tor_path)
    elif os.path.isdir(tor_path):
        media_files = find_media_files(tor_path)

    if not media_files:
        logging.warning(f"在 {tor_path} 中未找到媒体文件。")
        return

    generate_movie_links(target_dir, media_files, media_info)

def process_tv(config, media_info, tor_path):
    """处理电视剧类别"""
    emby_root = config['root_path']
    
    # 构建目标目录
    emby_dir = media_info['emby_dir']
    target_dir = os.path.join(emby_root, emby_dir)

    
    logging.info(f"创建电视剧目录: {target_dir}")
    os.makedirs(target_dir, exist_ok=True)

    # 如果是单文件
    if os.path.isfile(tor_path):
        logging.info(f"检测到单文件 torrent，按单文件模式处理: {tor_path}")
        media_files = []
        if os.path.splitext(tor_path)[1].lower() in VIDEO_EXTS:
            media_files.append(tor_path)
        
        if not media_files:
            logging.warning(f"文件 {tor_path} 不是支持的媒体文件类型。")
            return
            
        season_str = media_info.get('season')
        if not season_str:
            logging.error("API未返回季号 (season)，无法处理。")
            return
            
        season_target_dir = os.path.join(target_dir, season_str)
        os.makedirs(season_target_dir, exist_ok=True)
        
        for src_file in media_files:
            dst_file = os.path.join(season_target_dir, os.path.basename(src_file))
            create_hard_link(src_file, dst_file)
        return

    # --- 如果是目录 ---

    # 检查是否存在分季目录 (如 S01, Season 01)
    season_pattern = re.compile(r'S(\d+)|Season[\s._]*(\d+)', re.IGNORECASE)
    
    subdirs = [d for d in os.listdir(tor_path) if os.path.isdir(os.path.join(tor_path, d))]
    season_folders = {}
    for subdir in subdirs:
        match = season_pattern.match(subdir)
        if match:
            season_num = int(match.group(1) or match.group(2))
            season_folders[season_num] = os.path.join(tor_path, subdir)

    if season_folders:
        # 情况A: 存在分季目录
        logging.info("检测到分季目录，将进行递归链接。")
        for season_num, season_path in season_folders.items():
            # 格式化季号目录，例如 "Season 01"
            season_dir_name = f"Season {season_num:02d}"
            season_target_dir = os.path.join(target_dir, season_dir_name)
            os.makedirs(season_target_dir, exist_ok=True)
            media_files = find_media_files(season_path)
            for src_file in media_files:
                dst_file = os.path.join(season_target_dir, os.path.basename(src_file))
                create_hard_link(src_file, dst_file)
    else:
        # 情况B: 媒体文件直接放在根目录
        logging.info("未检测到分季目录，将根据API返回的季号创建目录。")
        media_files = find_media_files(tor_path)
        if not media_files:
            logging.warning(f"在 {tor_path} 中未找到媒体文件。")
            return
            
        season_str = media_info.get('season')
        if not season_str:
            logging.error("API未返回季号 (season)，无法处理。")
            return
            
        season_target_dir = os.path.join(target_dir, season_str)
        os.makedirs(season_target_dir, exist_ok=True)
        
        for src_file in media_files:
            dst_file = os.path.join(season_target_dir, os.path.basename(src_file))
            create_hard_link(src_file, dst_file)


def main():
    logging.info(f"--- rcp.py 启动 ---")
    
    # 优先从命令行参数获取
    parser = argparse.ArgumentParser(description="RCP - Remote Torrent Copy. 从torll获取信息并整理媒体文件。")
    parser.add_argument("tor_path", nargs='?', default=None, help="种子的本地文件路径。")
    parser.add_argument("--torhash", "-t", help="种子的HASH值。")
    parser.add_argument("--torname", "-n", help="种子名称。")
    parser.add_argument("--dl_uuid", "-u", help="下载器任务的UUID (可选)。")
    
    args = parser.parse_args()

    tor_path = args.tor_path
    torhash = args.torhash
    dl_uuid = args.dl_uuid
    torname = args.torname

    # 如果命令行参数未提供，则从环境变量获取
    if not all([tor_path, torhash]):
        logging.info("部分或全部主要参数（路径、哈希）未通过命令行提供，尝试从环境变量加载。")
        tor_path = os.environ.get('RCP_TOR_PATH')
        torhash = os.environ.get('RCP_TOR_HASH')
        dl_uuid = os.environ.get('RCP_DL_UUID')
        torname = os.environ.get('RCP_TOR_NAME')
        
        logging.info(f"从环境变量加载的值: Path={tor_path}, Hash={torhash}, UUID={dl_uuid}, Name={torname}")


    # 检查最终是否获取到必要的参数
    if not tor_path or not torhash:
        logging.error("错误：必须通过命令行参数或环境变量提供 tor_path 和 torhash。")
        parser.print_help()
        sys.exit(1)

    config = load_config()
    
    media_info = get_media_info(config, torhash, dl_uuid, tor_path, torname)
    # print(json.dumps(media_info, indent=2, ensure_ascii=False))    
    if not media_info or 'tmdb_cat' not in media_info:
        logging.error("获取的媒体信息无效或不完整。")
        sys.exit(1)
        
    tmdb_cat = media_info['tmdb_cat']

    tor_full_path = tor_path 
    # 如果是目录，且API返回了torpath，且当前路径未包含torpath，则拼接路径
    if os.path.isdir(tor_path) and media_info.get('torpath') and not tor_path.endswith(media_info['torpath']):
        tor_full_path = os.path.join(tor_path, media_info['torpath'])
    logging.info(f"最终处理路径: {tor_full_path}")

    if tmdb_cat == 'movie':
        process_movie(config, media_info, tor_full_path)
    elif tmdb_cat == 'tv':
        process_tv(config, media_info, tor_full_path)
    else:
        logging.error(f"不支持的媒体类别: {tmdb_cat}")
        sys.exit(1)
        
    logging.info("处理完成。")

if __name__ == "__main__":
    main()
