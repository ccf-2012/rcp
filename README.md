# rcp.py 
* 在 qbit 下载完成后的脚本中，调用本 rcp.py,
* rcp.py 向 torll 请求所需要的信息，然后本地执行 torcp 刮削硬链
* 完成后向 torll 报告入库


## 安装
* rcp.py 需要依赖邻目录中的 torcp2
```sh
git clone https://github.com/ccf-2012/rcp.git
git clone https://github.com/ccf-2012/torcp2.git
```

  
* 安装依赖
```sh
cd rcp
pip install -r requirements.txt
```
* 或通过 rye 进行依赖管理
* install rye: https://rye.astral.sh/guide/installation/
```sh
cd rcp
rye init 
rye sync
python -m ensurepip
python -m pip install -r requirements.txt
```

## torll 与 torcpdb 服务端
* 服务端需要安装 torll 与 torcpdb


### torll
* 安装依赖
```sh
cd torll
rye init 
rye sync
python -m ensurepip
python -m pip install -r requirements.txt
```
* 生成初始密码
```sh 
screen 
# 生成初始密码
python app.py -G
# 记下生成的用户名和密码，在 config.ini 中可手工修改
```
* 在 config.ini 中加一行：
```ini
client_api_key = something
```
* 启动 torll
```
python app.py
```

### torcpdb

* 编写一个 `config.ini`
```ini
[TMDB]
tmdb_api_key = _your_tmdb_api_key_  # 配置 TMDb 的 api key
tmdb_lang = zh-CN

[AUTH]
user = ccf          # 登陆 torcpdb 的用户名 / 密码
pass = something
client_api_key = something  # 供 torll 用的 api key
```
* 启动 torcpdb
```sh
screen 
python app.py 
```

## 使用
### 检查配置
1. 记录下 torcpdb 的 apikey 和 torll 的 apikey
2. 检查 torll 中配置的 torcpdb 的 apikey 是否正确
3. 检查 rcp 中配置的 torll, torcpdb 的 apikey 是否正确

### torll 中的设置
1. 设置-torcp设置，各项参数设置
2. 设置-qbittorrent设置，添加 qbit，注意名称应与 rcp 中 rcpconfig.ini 中名字对应
3. 站点-站点设置，添加站点
4. RSS-RSS任务，设置RSS （rssconfig.json）

### 远程 rcp 机器上配置
*  在作好上述设置后，在远程机器上的rcp目录中可进行配置

```sh
cd rcp
rye init 
rye sync
python -m ensurepip
python -m pip install -r requirements.txt
```

* 编写 rcpconfig.ini 其中以下分别 torll 和 torcpdb 服务的配置项，需要手工设置：
```ini
[TORLL]
torll_url = http://127.0.0.1:5006
torll_apikey = something

[TORCP]
torcpdb_url = http://127.0.0.1:5009
torcpdb_apikey = somethin_anything

[QBIT]
qbitname = qb51  # 这里的名字与 torll 中设置对应
```

* 通过 `rcp.py --get-config` 获取参数
```sh
cd /root/rcp
python rcp.py --get-config
```

## 检查远程 rcp 配置
1. qbittorent 的运行命令
2. rcp.sh 的内容
3. rcpconfig.ini 中各参数

## usage
```
python rcp.py -h
usage: rcp.py [-h] [-F FULL_PATH] [-I INFO_HASH] [-D SAVE_PATH] [-T TRACKER] [-L CATEGORY] [-G TAGS] [-Z SIZE] [--hash-dir] [--tmdbcatid TMDBCATID]
              [--auto-resume-delete] [-C CONFIG]

wrapper to TORCP to save log in sqlite db.

options:
  -h, --help            show this help message and exit
  -F FULL_PATH, --full-path FULL_PATH
                        full torrent save path.
  -I INFO_HASH, --info-hash INFO_HASH
                        info hash of the torrent.
  -D SAVE_PATH, --save-path SAVE_PATH
                        qbittorrent save path.
  -T TRACKER, --tracker TRACKER
                        torrent tracker.
  -L CATEGORY, --category CATEGORY
                        category of the torrent.
  -G TAGS, --tags TAGS  tags of the torrent.
  -Z SIZE, --size SIZE  size of the torrent.
  --hash-dir            create hash dir.
  --tmdbcatid TMDBCATID
                        specify TMDb as tv-12345/m-12345.
  --auto-resume-delete  try to resume paused torrent when disk space available.
  -C CONFIG, --config CONFIG
                        config file.
```

## qbit 中的设置
* 在 qbit 完成后执行脚本，可以输出以下参数：
```
%N：Torrent 名称
%L：分类
%G：标签（以逗号分隔）
%F：内容路径（与多文件 torrent 的根目录相同）
%R：根目录（第一个 torrent 的子目录路径）
%D：保存路径
%C：文件数
%Z：Torrent 大小（字节）
%T：当前 tracker
%I: 信息哈希值 v1
%J：信息哈希值 v2
%K: Torrent ID
```

* 调用 rcp.py 可以使用如下命令行：
```sh
python rcp.py -F "%F" -I "%I" -D "%D" -L "%L" -G "%G" -Z "%Z" --hash-dir
```

* 为方便，加了qbfunc.py，通过 qbittorrent-api 获取信息，可以如下调用：
```sh
python rcp.py -I "%I"
```

## rcpconfig.ini
* 需要一个配置文件，内容包括：
```ini
[TORLL]
torll_url = http://127.0.0.1:5006
torll_apikey = something

[TORCP]
linkdir = /volume1/video/downloads/emby
bracket = --plex-bracket
symbolink =
genre = 动画,纪录,真人秀,脱口秀,音乐会
mbrootdir = /volume1/video/downloads/emby
notifyplex = True
areadir = --sep-area5
torcpdb_url = http://127.0.0.1:5009
torcpdb_apikey = somethin_anything

[CATEGORY_DIR]
未完结 = 未完结
特摄 = 特摄
综艺 = 综艺

[AUTO_CATEGORY]
未完结 = S\d+E\d+|第\d+.*集
特摄 = 特摄

[QBIT]
server_ip = 192.168.5.6
port = 15190
user = admin
pass = Setup194
apirun = True
dockerfrom = /downloads
dockerto = /volume1/video/downloads
auto_delete = False
```

