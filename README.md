# rcp.py 
* 在 qbit 下载完成后的脚本中，调用本 rcp.py,
* rcp.py 向 torll 请求所需要的信息，然后本地执行 torcp 刮削硬链
* 完成后向 torll 报告入库


## 安装
* rcp.py 需要依赖 sibling 目录中的 torcp2
```sh
git clone https://github.com/ccf-2012/rcp.git
git clone https://github.com/ccf-2012/torcp2.git

```
* 安装依赖
```sh
cd rcp
pip install -r requirements.txt
```

## 从 torll 服务端下载配置
* 首先建立一个 `rcpconfig.ini` 文件，内容如下：
* 其中 torll 和 torcpdb 服务的配置项，需要手工设置：
```ini
[TORLL]
torll_url = http://127.0.0.1:5006
torll_apikey = something

[TORCP]
torcpdb_url = http://127.0.0.1:5009
torcpdb_apikey = somethin_anything

[QBIT]
qb_name = local  # 这里的名字与 torll 中设置对应
```

* 在作好上述设置后，其它的设置，可以通过 `rcp.py --get-config` 获取
```sh
python3 rcp.py --get-config
```
* 没有报错的话，检查 `rcpconfig.ini` 文件内容


## 由 torll 设置种子下载完成后运行命令
* torll 的 qbittorrent 设置中，对远程的下载器进行设置
* 检查其设置的参数，特别是运行程序的路径是否正确
* 比如 torll 会设置远程 qbit 的种子下载完成后命令为：
```sh
sh rcp.sh "%I"
```
* 多数情况需要手工设置其中的绝对路径，比如改成：
```sh
sh /share/CACHEDEV1_DATA/Download/rcp/rcp.sh "%I"
```
* 而其中的 rcp.sh 内容需要手工编写，也应当对应绝对路径，以及python环境，如：
```
#!/bin/bash
/bin/bash -c ". /etc/profile.d/python3.bash; exec python3 /share/CACHEDEV1_DATA/Download/rcp/rcp.py -I $1 >>/share/CACHEDEV1_DATA/Download/rcp2.log 2>>/share/CACHEDEV1_DATA/Download/rcp2e.log"
```

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
> 这样的调用方式下，不需要连接下载器，也不需要 `qbittorrent-api` 依赖

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

