# from app import TorcpItemDBObj, TorcpItemCallbackObj, initDatabase
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "torcp2"))
from torcp.torcp import Torcp
from rcpconfig import readConfig, loadJsonConfig, CONFIG
import argparse
import re
from loguru import logger



def extractIMDbFromTag(tagstr):
    tagList = []
    if tagstr:
        tagList = tagstr.split(',')
    imdbtag = next((x for x in tagList if x.startswith('tt')), '')
    return imdbtag


def parseSiteId(siteidStr, torimdb):
    site = ''
    siteid = ''
    m = re.search(r'(\w+)[_-](\d+)(_(tt\d+))?', siteidStr, re.I)
    if m:
        site = m[1]
        siteid = m[2]
        if not torimdb and m[4]:
            torimdb = m[4]
    return site, siteid, torimdb


def tryint(instr):
    try:
        string_int = int(instr)
    except ValueError:
        string_int = 0
    return string_int


def getSiteIdDirName(pathStr, savepath):
    npath = os.path.normpath(pathStr.strip())
    siteIdFolder = os.path.basename(os.path.normpath(savepath))
    relativePath = os.path.relpath(npath, savepath)
    l = relativePath.split(os.path.sep)
    torRootFolder = os.path.join(savepath, l[0]) if len(l) > 0 else npath
    return torRootFolder, siteIdFolder

# def runTorcpMove(sourceDir, targetDir, torimdb=None, tmdbcatidstr=None):
#     if sourceDir:
#         if not os.path.exists(sourceDir):
#             logger.warning('File/Dir not exists: ' + sourceDir)
#             return "", '', None
#         # torimdb = extractIMDbFromTag(tortag)
#         # rootdir, site_id_imdb = getSiteIdDirName(sourceDir, savepath)

#         # site, siteid, torimdb = parseSiteId(site_id_imdb, imdbstr)
#         # if insertHashDir:
#         #     targetDir = os.path.join(CONFIG.linkDir, torhash)
#         # else:
#         #     targetDir = CONFIG.linkDir
#         argv = [sourceDir, "-d", targetDir, "-s",
#                 "--torcpdb-url", CONFIG.torcpdb_url,
#                 CONFIG.bracket,
#                 "-e", "srt",
#                 "--extract-bdmv",
#                 "--tmdb-origin-name"]
#         if CONFIG.areadir:
#             argv += [CONFIG.areadir]
#         if CONFIG.genre:
#             argv += ["--genre", CONFIG.genre]
#         if CONFIG.bracket == '--emby-bracket':
#             argv += ["--filename-emby-bracket"]
#         if torimdb:
#             argv += ["--imdbid", torimdb]
#         if tmdbcatidstr:
#             argv += ["--tmdbid", tmdbcatidstr]
#         argv += ["--move-run"]

#         # print(argv)
#         eo = app.TorcpItemCallbackObj()
#         o = Torcp()
#         o.main(argv, eo)
#         return eo.targetDir, eo.tmdbTitle, eo.tmdbParser
#     return '', '', None


import requests
def myheader():
    headers = {}
    if CONFIG.torll_apikey:
        headers = {
            'User-Agent': 'python/request:torcp',
            'X-API-Key': CONFIG.torll_apikey
        }
    else:
        logger.error('api-key not set.')
    return headers

def query_torll_dlinfo(qbid):
    try:
        json_data = {
            'qbid': qbid
        }
        response = requests.get(
            CONFIG.torll_url+ "/api/getdlinfo", 
            headers=myheader(),
            json=json_data
        )
        # response.raise_for_status()  # 如果响应状态码不是200，抛出异常
        return response.json()
    except requests.RequestException as e:
        print(f"查询失败: {str(e)}")
        raise

def post_item_torcped(json_data):
    try:
        response = requests.post(
            CONFIG.torll_url+ "/api/ontorcped", 
            headers=myheader(),
            json=json_data
        )
        # response.raise_for_status()  # 如果响应状态码不是200，抛出异常
        return response.json()
    except requests.RequestException as e:
        print(f"查询失败: {str(e)}")
        raise


class TorcpCallbackClient:
    def __init__(self, torimdb, torhash, torsize, relocatedir, tordownload_qbid):
        self.torimdb = torimdb
        self.torhash = torhash
        self.torsize = torsize
        self.relocatedir = relocatedir
        self.tordownload_qbid = tordownload_qbid

    def onOneItemTorcped(self, targetDir, mediaName, tmdbIdStr, tmdbCat, tmdbTitle, tmdbobj=None):
        # logger.info("%s %s %s %s " % (targetDir, mediaName, tmdbIdStr, tmdbCat))
        json_data = {
            'qbid': self.tordownload_qbid,
            'torhash' : self.torhash,
            'relocate_dir': self.relocatedir,
            'target_dir' : targetDir,
            'media_name' : mediaName,
            'tmdb_id' : tmdbIdStr,
            'tmdb_cat' : tmdbCat,
            'tmdb_title' : tmdbTitle
        }
        post_item_torcped(json_data)
        self.tmdbParser = tmdbobj


# def findDownloadItem(torcat):
#     with app.app.app_context():
#         dlitem = app.db.session.query(app.TorDownload).filter_by(
#             qbid=torcat).first()
#         return dlitem

def runTorcp(torpath, torhash, torsize, torcat, savepath, abbrevTracker, insertHashDir, tmdbcatidstr=None, tortag=''):
    if (CONFIG.docker_from != CONFIG.docker_to):
        if torpath.startswith(CONFIG.docker_from) and savepath.startswith(CONFIG.docker_from):
            torpath = torpath.replace(
                CONFIG.docker_from, CONFIG.docker_to, 1)
            savepath = savepath.replace(
                CONFIG.docker_from, CONFIG.docker_to, 1)

    if not CONFIG.link_dir.strip():
        logger.warning('config not set: link dir ')
        return 401
    if not CONFIG.torcpdb_url.strip():
        logger.warning('config not set: torcpdb_url')
        return 401

    if torpath and torhash:
        if not os.path.exists(torpath):
            logger.warning('File/Dir not exists: ' + torpath)
            return 402
        # TODO: get site, infolink from TorDownload
        rootdir, site_id_imdb = getSiteIdDirName(torpath, savepath)
        site, siteid, torimdb = parseSiteId(site_id_imdb, '')
        if not site:
            site = abbrevTracker
        if insertHashDir:
            targetDir = os.path.join(CONFIG.link_dir, torhash)
        else:
            targetDir = CONFIG.link_dir

        # 由 tortag 在categoryDirList和TorDownload.auto_cat中找是否配置了自动分类
        extitle = ''
        autocatdir = ''
        if tortag:
            torlist = [z.strip() for z in tortag.split(',')]
            matchTagList = [z for z in torlist if z in [g[0] for g in CONFIG.categoryDirList]]
            if len(matchTagList) > 0:
                autocatdir = matchTagList[0]
        tordownload_qbid = torcat
        if tordownload_qbid:
            # remote query /api/getdlinfo
            json_data = query_torll_dlinfo(tordownload_qbid)
            if json_data:
                if 'qbid' in json_data:
                    qbid = json_data['qbid']
                if 'auto_cat' in json_data:
                    autocatdir = json_data['auto_cat']
                if 'extitle' in json_data:
                    extitle = json_data['extitle']
                if 'imdb_id' in json_data:
                    imdb_id = json_data['imdb_id']
                    if imdb_id and imdb_id.startswith('tt'):
                        torimdb = imdb_id
        else:
            logger.error('no qbid set in torrent category.')
            
        # 根据 autocatdir 找 此分类 是否配置了 重定位的 位置
        relocated = False
        relocatedir = ''
        catDirTup = next((g for g in CONFIG.categoryDirList if autocatdir == g[0]), ("", ""))
        if catDirTup[1] != '' :
            relocatedir = catDirTup[1].strip()
            # if catdir.startswith('/'):
            #   意味着放弃前面所有设置的路径，直接放到指定目录，尚未知会有什么问题
            targetDir = os.path.join(targetDir, relocatedir)
            relocated = True
    
        logger.info(f"torpath: {torpath}, torsize: {torsize}, targetDir: {targetDir}, relocated: {relocated}")

        argv = [rootdir, "-d", targetDir, "-s",
                "--torcpdb-url", CONFIG.torcpdb_url,
                "--torcpdb-apikey", CONFIG.torcpdb_apikey,
                # "--make-log",
                "-e", "srt",
                "--extract-bdmv",
                "--origin-name"]
                # "--tmdb-origin-name"]
        if CONFIG.bracket:
            argv += [CONFIG.bracket]
        # 2024.11 开始，改用 --sep-area5
        # if CONFIG.lang:
        #     argv += ["--lang", CONFIG.lang]
        if CONFIG.areadir:
            argv += [CONFIG.areadir]
        if CONFIG.genre:
            argv += ["--genre", CONFIG.genre]
        if CONFIG.genre_with_area:
            argv += ["--genre-with-area", CONFIG.genre_with_area]
        if torimdb:
            argv += ["--imdbid", torimdb]
        if tmdbcatidstr:
            argv += ["--tmdbid", tmdbcatidstr]
        if extitle:
            argv += ["--extitle", extitle]

        if CONFIG.extra_param:
            exparamList = [item.strip() for item in CONFIG.extra_param.split(',')]
            argv += exparamList

        #TODO  如果前面已经匹配到了重定向位置规则，则不加--add-year-dir
        if relocated and ('--add-year-dir' in argv):
            argv.remove('--add-year-dir')        

        # logger.debug(argv)
        if not torsize:
            torsize = '0'
        eo = TorcpCallbackClient(
                torimdb=torimdb, 
                torhash=torhash.strip(), 
                torsize=tryint(torsize.strip()), 
                relocatedir=relocatedir, 
                tordownload_qbid=tordownload_qbid)
        o = Torcp()
        o.main(argv, eo)

        return 200
    return 401


# import subprocess
# def callAfterRcpShellScript(torhash):
#     scriptcmd = os.path.join(os.path.dirname(__file__), 'after_rcp.sh')
#     if not os.path.exists(scriptcmd):
#         # nothing to run, nothing to say
#         return
#     logger.info(f'call shell script: {scriptcmd}')
#     r = subprocess.call(['sh', scriptcmd, torhash])
#     if r > 0:
#         logger.warning(f'return value: {r}')
#     else:
#         logger.info(f'return value: {r}')

from qbitconfig import QbitConfig
from qbfunc import QbitClient
def torcpByHash(torhash):
    if torhash:
        qbconfig = QbitConfig(
            qbitname=CONFIG.qbitname,
            host=CONFIG.host,
            port=CONFIG.port,
            username=CONFIG.username,
            password=CONFIG.password,
            docker_from=CONFIG.docker_from,
            docker_to=CONFIG.docker_to,
            link_dir=CONFIG.link_dir,
            auto_delete=CONFIG.auto_delete,
            islocal = CONFIG.islocal,
            default=CONFIG.default
        )
        qbclient = QbitClient(qbconfig)
        torinfo = qbclient.get_torrent_by_hash(torhash)
        if not torinfo:
            logger.error('qbit not connected.')
            return 404
        
        logger.info(f'调用 torcp: {torinfo.content_path}')
        r = runTorcp(
                torpath=torinfo.content_path, 
                torhash=torinfo.hash, 
                torsize=torinfo.size, 
                torcat=torinfo.category, 
                savepath=torinfo.save_path, 
                abbrevTracker=torinfo.tracker_name, 
                insertHashDir=CONFIG.insert_hash_dir,
                tmdbcatidstr=None,
                tortag=torinfo.tags)
        return r
    else:
        print("set -I arg")
        return 403


def getTorllConfig():
    try:
        json_data = {
            'qbitname': CONFIG.qbitname
        }
        response = requests.get(
            CONFIG.torll_url+ "/api/getconfig", 
            headers=myheader(),
            json=json_data)
        response.raise_for_status()  # 如果响应状态码不是200，抛出异常
        data = response.json()  # 假设这是解析 JSON 数据的代码
        print("Server returned JSON data:", data)  # 插入打印语句
        loadJsonConfig(ARGS.config, data)
        return 
    except requests.RequestException as e:
        print(f"查询失败: {str(e)}")
        raise    

def loadArgs():
    parser = argparse.ArgumentParser(
        description='wrapper to TORCP to save log in sqlite db.')
    parser.add_argument('-F', '--full-path', help='full torrent save path.')
    parser.add_argument('-I', '--info-hash', help='info hash of the torrent.')
    parser.add_argument('-D', '--save-path', help='qbittorrent save path.')
    parser.add_argument('-T', '--tracker', help='torrent tracker.')
    parser.add_argument('-L', '--category', help='category of the torrent.')
    parser.add_argument('-G', '--tags', help='tags of the torrent.')
    parser.add_argument('-Z', '--size', help='size of the torrent.')
    parser.add_argument('--hash-dir', action='store_true', help='create hash dir.') 
    parser.add_argument('--tmdbcatid', help='specify TMDb as tv-12345/m-12345.')
    parser.add_argument('--auto-resume-delete', action='store_true', help='try to resume paused torrent when disk space available.') 
    parser.add_argument('-C', '--config', help='config file.')
    parser.add_argument('--get-config', action='store_true', help='get config from torll server.') 

    global ARGS
    ARGS = parser.parse_args()
    if not ARGS.config:
        ARGS.config = os.path.join(os.path.dirname(__file__), 'rcpconfig.ini')


def main():
    loadArgs()
    # app.initDatabase()
    readConfig(ARGS.config)
    if ARGS.get_config:
        getTorllConfig()
        return
    if ARGS.full_path and ARGS.save_path:
        runTorcp(torpath=ARGS.full_path, 
                 torhash=ARGS.info_hash, 
                 torsize=ARGS.size,
                 torcat=ARGS.category,
                 savepath=ARGS.save_path,
                 insertHashDir=ARGS.hash_dir, 
                 tmdbcatidstr=ARGS.tmdbcatid,
                 tortag=ARGS.tags)
    else:
        torcpByHash(ARGS.info_hash)
        # callAfterRcpShellScript(ARGS.info_hash)
    # if ARGS.auto_resume_delete:
    #     qbfunc.autoResumeDelete(delete_to_free=True)

if __name__ == '__main__':
    logger.remove()
    formatstr = "{time:YYYY-MM-DD HH:mm:ss} | <level>{level: <8}</level> | - <level>{message}</level>"
    logger.add(sys.stdout, format=formatstr)
    main()
