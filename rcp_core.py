# -*- coding: utf-8 -*-
import configparser
import json
import os
import urllib.request
import urllib.error
import logging
import re
from collections import defaultdict
import shutil

# This is the core logic, designed to be imported.

# 从torcp.py借鉴的视频文件扩展名列表
VIDEO_EXTS = ['.mkv', '.mp4', '.ts', '.m2ts', '.mov', '.avi', '.wmv', '.strm', '.ass', '.srt']

def load_config():
    """加载配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
    if not os.path.exists(config_path):
        logging.error(f"配置文件 {config_path} 不存在。请参考 config.ini.template 创建。")
        raise FileNotFoundError(f"Config file not found at {config_path}")
    
    config = configparser.ConfigParser()
    config.read(config_path)
    
    try:
        torll_config = config['torll']
        emby_config = config['emby']
        
        path_mapping = {}
        if 'path_mapping' in config:
            # Sort path_mapping keys by length in descending order to ensure longest prefix match
            # This is important for paths like /downloads and /downloads/movies
            sorted_keys = sorted(config['path_mapping'].keys(), key=len, reverse=True)
            for key in sorted_keys:
                path_mapping[key] = config['path_mapping'][key]
        
        return {
            'url': torll_config['url'],
            'api_key': torll_config['api_key'],
            'root_path': emby_config['root_path'],
            'qbitname': torll_config['qbitname'],
            'path_mapping': path_mapping,
        }
    except KeyError as e:
        logging.error(f"配置文件中缺少必要的键: {e}")
        raise KeyError(f"Missing required key in config: {e}")

def translate_path_to_agent_path(path: str, path_mapping: dict) -> str:
    """
    Translates a path from the main application's perspective to the rcp_agent's perspective
    using the provided path mapping rules.
    """
    for app_path_prefix, agent_path_prefix in path_mapping.items():
        # Ensure that paths are treated as directories for os.path.relpath
        # so that /a matches /a/b but not /abc
        normalized_app_path_prefix = os.path.normpath(app_path_prefix)
        normalized_path = os.path.normpath(path)

        if normalized_path.startswith(normalized_app_path_prefix):
            # Calculate the relative path from the app_path_prefix
            relative_path = os.path.relpath(normalized_path, normalized_app_path_prefix)
            # Join with the agent_path_prefix to get the translated path
            translated_path = os.path.join(agent_path_prefix, relative_path)
            logging.debug(f"Translated path '{path}' to '{translated_path}' using mapping '{app_path_prefix}' -> '{agent_path_prefix}'")
            return translated_path
    logging.debug(f"No path mapping found for path '{path}', returning original path.")
    return path

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
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(config['url'], data=data, headers=headers, method='POST')
    
    try:
        with urllib.request.urlopen(req) as response:
            if not (200 <= response.status < 300):
                error_msg = f"请求torll API失败，状态码: {response.status}, 内容: {response.read().decode('utf-8')}"
                logging.error(error_msg)
                raise ConnectionError(error_msg)
            
            logging.info("成功获取API响应。")
            response_body = response.read().decode('utf-8')
            return json.loads(response_body)
            
    except urllib.error.HTTPError as e:
        error_content = e.read().decode('utf-8', 'ignore')
        error_msg = f"请求torll API时发生HTTP错误: {e}, 内容: {error_content}"
        logging.error(error_msg)
        raise ConnectionError(error_msg) from e
    except urllib.error.URLError as e:
        error_msg = f"请求torll API时发生URL错误: {e.reason}"
        logging.error(error_msg)
        raise ConnectionError(error_msg) from e
    except Exception as e:
        logging.error(f"处理请求时发生未知错误: {e}")
        raise

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

    file_groups = defaultdict(list)
    for f in media_files:
        base_name = os.path.splitext(os.path.basename(f))[0]
        file_groups[base_name].append(f)

    for i, (base_name, files_in_group) in enumerate(file_groups.items()):
        file_prefix = f"{media_info['tmdb_title']} ({media_info['tmdb_year']}) {media_info['emby_bracket']}"
        
        longest_ext = ""
        if files_in_group:
            longest_ext = max((os.path.splitext(f)[1] for f in files_in_group), key=len)

        potential_dst_base = f"{file_prefix} - {base_name}"
        potential_dst_file = os.path.join(target_dir, f"{potential_dst_base}{longest_ext}")
        
        final_dst_base = ""
        if len(potential_dst_file.encode('utf-8')) > 250:
            logging.warning(f"目标文件名过长，将进行截断处理: {potential_dst_file}")
            index_suffix = f" - {i + 1}" if len(file_groups) > 1 else ""
            final_dst_base = f"{file_prefix.strip()}{index_suffix}"
        else:
            final_dst_base = potential_dst_base
        
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
    emby_dir = media_info['emby_dir']
    target_dir = os.path.join(emby_root, emby_dir)
    
    logging.info(f"创建电视剧目录: {target_dir}")
    os.makedirs(target_dir, exist_ok=True)

    media_files = [] # Initialize media_files here

    if os.path.isfile(tor_path):
        logging.info(f"检测到单文件 torrent，按单文件模式处理: {tor_path}")
        if os.path.splitext(tor_path)[1].lower() in VIDEO_EXTS:
            media_files.append(tor_path)
        
        if not media_files:
            logging.warning(f"文件 {tor_path} 不是支持的媒体文件类型。")
            return
            
        season_str = media_info.get('season')
        if not season_str:
            raise ValueError("API未返回季号 (season)，无法处理。")
            
        try:
            season_num = int(season_str)
            season_dir_name = f"Season {season_num:02d}"
        except ValueError:
            season_dir_name = season_str

        season_target_dir = os.path.join(target_dir, season_dir_name)
        os.makedirs(season_target_dir, exist_ok=True)
        
        for src_file in media_files:
            dst_file = os.path.join(season_target_dir, os.path.basename(src_file))
            create_hard_link(src_file, dst_file)
        return

    season_pattern = re.compile(r'S(\d+)|Season[\s._]*(\d+)', re.IGNORECASE)
    
    subdirs = [d for d in os.listdir(tor_path) if os.path.isdir(os.path.join(tor_path, d))]
    season_folders = {}
    for subdir in subdirs:
        match = season_pattern.match(subdir)
        if match:
            season_num = int(match.group(1) or match.group(2))
            season_folders[season_num] = os.path.join(tor_path, subdir)

    if season_folders:
        logging.info("检测到分季目录，将进行递归链接。")
        for season_num, season_path in season_folders.items():
            season_dir_name = f"Season {season_num:02d}"
            season_target_dir = os.path.join(target_dir, season_dir_name)
            os.makedirs(season_target_dir, exist_ok=True)
            media_files = find_media_files(season_path)
            for src_file in media_files:
                dst_file = os.path.join(season_target_dir, os.path.basename(src_file))
                create_hard_link(src_file, dst_file)
    else:
        logging.info("未检测到分季目录，将根据API返回的季号创建目录。")
        media_files = find_media_files(tor_path)
        if not media_files:
            logging.warning(f"在 {tor_path} 中未找到媒体文件。")
            return
            
        season_str = media_info.get('season')
        if not season_str:
            raise ValueError("API未返回季号 (season)，无法处理。")
            
        try:
            season_num = int(season_str)
            season_dir_name = f"Season {season_num:02d}"
        except ValueError:
            season_dir_name = season_str

        season_target_dir = os.path.join(target_dir, season_dir_name)
        os.makedirs(season_target_dir, exist_ok=True)
        
        for src_file in media_files:
            dst_file = os.path.join(season_target_dir, os.path.basename(src_file))
            create_hard_link(src_file, dst_file)

def run_rcp_process(tor_path, torhash, dl_uuid=None, torname=None):
    """
    The main process logic, callable as a function.
    """
    logging.info(f"--- rcp_core process started for hash: {torhash} ---")
    
    if not tor_path or not torhash:
        raise ValueError("错误：必须提供 tor_path 和 torhash。")

    config = load_config()
    
    # Translate tor_path from app's perspective to agent's perspective
    translated_tor_path = translate_path_to_agent_path(tor_path, config.get('path_mapping', {}))
    logging.info(f"Original tor_path: {tor_path}, Translated tor_path: {translated_tor_path}")
    
    media_info = get_media_info(config, torhash, dl_uuid, translated_tor_path, torname)
    
    execute_hardlinking(config, media_info, translated_tor_path)
        
    logging.info("--- rcp_core process finished. ---")


def delete_links(config, rel_path):
    """Safely deletes old hardlinks.
    It constructs the full path from the root_path in config and the relative path.
    """
    if not rel_path:
        logging.warning("No relative path provided for deletion, skipping.")
        return

    root_path = config.get('root_path')
    if not root_path:
        raise ValueError("root_path is not configured in config.ini")

    full_path = os.path.join(root_path, rel_path)
    
    if not os.path.exists(full_path):
        logging.warning(f"Old path does not exist, skipping deletion: {full_path}")
        return

    try:
        if os.path.isdir(full_path):
            logging.info(f"Removing old directory: {full_path}")
            shutil.rmtree(full_path)
        elif os.path.isfile(full_path):
            logging.info(f"Removing old file: {full_path}")
            os.remove(full_path)
        else:
            logging.warning(f"Old path is not a file or directory, cannot delete: {full_path}")
    except Exception as e:
        logging.error(f"Failed to delete old path {full_path}: {e}", exc_info=True)
        # We don't re-raise, as failing to delete old links might not be a critical error

def execute_hardlinking(config, media_info, tor_path):
    """
    Executes the hardlinking process using provided media_info.
    """
    if not media_info or 'tmdb_cat' not in media_info:
        raise ValueError("获取的媒体信息无效或不完整。")
        
    tmdb_cat = media_info['tmdb_cat']

    # The original downloaded content path might be a file or a directory
    # For movies, it could be a single file. For TV shows, it's often a directory.
    # The `torpath` from media_info might specify a sub-path within the download directory.
    tor_full_path = tor_path 
    if os.path.isdir(tor_path) and media_info.get('torpath') and not tor_path.endswith(media_info['torpath']):
        tor_full_path = os.path.join(tor_path, media_info['torpath'])
    
    logging.info(f"最终处理路径: {tor_full_path}")

    if tmdb_cat == 'movie':
        process_movie(config, media_info, tor_full_path)
    elif tmdb_cat == 'tv':
        process_tv(config, media_info, tor_full_path)
    else:
        raise ValueError(f"不支持的媒体类别: {tmdb_cat}")

