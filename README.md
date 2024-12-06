# rcp.py 
* 在 qbit 下载完成后的脚本中，调用本 rcp.py,
* rcp.py 向 torll 请求所需要的信息，然后本地执行 torcp 刮削硬链
* 完成后向 torll 报告入库


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

## 对应 qbit 中的设置
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

* 为方便，加了qbfunc.py，可以如下调用：
```sh
python rcp.py -I "%I"
```


