# rcp.py - 自动化媒体库整理工具

这是一个 Python 脚本，旨在与 qBittorrent 和 torll2 服务集成，实现下载完成后自动整理媒体文件到 Emby/Jellyfin 媒体库。

## 核心功能

- **自动触发**: 在 qBittorrent 下载完成后自动执行。
- **智能识别**: 调用 `torll2` API 获取下载内容的详细媒体信息（如电影、电视剧、标题、年份等）。
- **创建硬链接**: 根据识别出的媒体信息，在你的媒体库目录中创建结构化的目录和硬链接，避免重复占用磁盘空间。
- **支持电影和电视剧**: 能够正确处理电影和电视剧，并将它们归入不同的目录结构。

## 工作流程

1.  **qBittorrent** 下载完成一个任务。
2.  qBittorrent 调用 `rcp.sh` 脚本，并将种子路径、HASH等信息作为参数传递。
3.  `rcp.sh` 脚本执行 `rcp.py`。
4.  `rcp.py` 读取 `config.ini` 配置，并携带种子信息请求 `torll` API。
5.  `torll` API 返回刮削好的媒体信息 (TMDB/TVDB 信息)。
6.  `rcp.py` 根据返回的信息，在 `config.ini` 中指定的媒体库根目录 (`root_path`) 下创建硬链接。

## 环境要求

- Python 3.10+ (脚本内建 `urllib`，无需安装 `requests`)

## 安装与配置

### 1. 克隆项目

```sh
git clone https://github.com/ccf-2012/rcp.git
cd rcp
```

### 2. 配置 `config.ini`

复制模板文件 `config.ini.template` 并重命名为 `config.ini`，然后根据你的环境修改内容。

```ini
[torll]
# torll 服务的 URL 地址
url = http://127.0.0.1:6006/api/v1/torcp/info
# torll 服务的 API Key
api_key = your_secret_api_key
# 你在 torll 中设置的 qBittorrent 客户端名称
qbitname = qb10

[emby]
# Emby/Jellyfin 媒体库的根目录
# 注意：运行 rcp.py 的主机需要有对该目录的写入权限
root_path = /path/to/your/media/library
```

## 使用方法

### 1. 创建 `rcp.sh` 包装脚本

为了确保 `rcp.py` 在正确的目录下执行，并能记录日志，建议创建一个 `rcp.sh` 脚本来调用它。

在项目目录下创建 `rcp.sh` 文件，内容如下：

```sh
#!/bin/bash
# 脚本所在的绝对路径
# !!! 修改为你项目实际的绝对路径 !!!
cd /path/to/your/rcp

# 使用你的 Python 解释器路径执行 rcp.py
# 日志会输出到 rcp.log 和 rcp2e.log 文件中
/usr/bin/python rcp.py "$1" -t "$2" -u "$3" -n "$4" >> rcp.log 2>> rcp2e.log
```

**注意:**
- 将 `cd /path/to/your/rcp` 中的路径修改为 `rcp.py` 所在的 **绝对路径**。
- 将 `/usr/bin/python` 修改为你环境中 Python 3 的实际路径 (可以通过 `which python` 或 `which python3` 查看)。
- 确保脚本有执行权限: `chmod +x rcp.sh`。

### 2. 配置 qBittorrent

打开 qBittorrent 的 `设置` -> `下载` -> `种子下载完成时运行外部程序`，填入以下命令：

```sh
/path/to/your/rcp/rcp.sh "%F" "%I" "%L" "%N"
```

- 将 `/path/to/your/rcp/rcp.sh` 替换为 `rcp.sh` 脚本的 **绝对路径**。
- 参数说明:
    - `%F`: 下载的文件/目录的完整路径
    - `%I`: 种子 HASH
    - `%L`: 种子分类
    - `%N`: 种子名称

### (备选) 解决中文参数乱码问题

少数系统在通过命令行传递中文名时可能会出现编码错误。如果遇到此问题，可以改用环境变量来传递参数。

修改 `rcp.sh` 如下:

```sh
#!/bin/bash
# 将从 qBittorrent 接收到的参数导出为环境变量
export RCP_TOR_PATH="$1"
export RCP_TOR_HASH="$2"
export RCP_DL_UUID="$3"
export RCP_TOR_NAME="$4"

# !!! 修改为你项目实际的绝对路径 !!!
cd /path/to/your/rcp

# 执行 Python 脚本，脚本内部会自动读取环境变量
/usr/bin/python rcp.py >> rcp.log 2>> rcp2e.log
```
`rcp.py` 脚本被设计为优先使用命令行参数，如果参数不完整，则会自动尝试从环境变量中读取，无需修改 Python 代码。

## 日志

脚本的运行日志和错误日志会分别记录在 `rcp.py` 同目录下的 `rcp.log` 和 `rcp2e.log` 文件中。如果整理失败，请检查这两个文件以定位问题。