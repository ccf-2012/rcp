
import qbittorrentapi
import myconfig
import urllib.parse
import time
import shutil
from humanbytes import HumanBytes

from loguru import logger

DISK_SPACE_MARGIN = (myconfig.CONFIG.freeDiskMargin * 2**30)  # 2G before disk full


def getTorrentFirstTracker(torrent):
    noneTracker = {"url": "", "msg": ""}
    firstTracker = next(
        (tracker for tracker in torrent.trackers if tracker['status'] > 0), noneTracker)
    return firstTracker

def abbrevTracker(trackerstr):
    hostnameList = urllib.parse.urlparse(trackerstr).netloc.split('.')
    if len(hostnameList) == 2:
        abbrev = hostnameList[0]
    elif len(hostnameList) == 3:
        abbrev = hostnameList[1]
    else:
        abbrev = ''
    return abbrev

def validQbitConfig():
    if (not myconfig.CONFIG.qbServer) or (not myconfig.CONFIG.qbPort):
        logger.error('检查 qBittorrent 配置')
        return False
    return True


def getTorrentByHash(torhash):
    if not validQbitConfig():
        return '', '', '', '', '', '', ''
    
    qbClient = qbittorrentapi.Client(
        host=myconfig.CONFIG.qbServer, port=myconfig.CONFIG.qbPort, username=myconfig.CONFIG.qbUser, password=myconfig.CONFIG.qbPass)

    try:
        qbClient.auth_log_in()
    except:
        return '', '', '', '', '', '', ''

    torlist = qbClient.torrents_info(torrent_hashes=torhash, limit=3)
    if len(torlist) <= 0:
        logger.warning('Torrent hash NOT found.')
        return '', '', '', '', '', '', ''
    torrent = torlist[0]
    tracker = getTorrentFirstTracker(torrent)

    taglist = torrent.tags
    # taglist = torrent.tags.split(',')
    # tag1 = taglist[0] if len(taglist)>0 else ''
    return torrent.content_path, torrent.hash, str(torrent.size), torrent.category, torrent.save_path, abbrevTracker(tracker["url"]), taglist


def getAutoRunProgram():
    qbClient = qbittorrentapi.Client(
        host=myconfig.CONFIG.qbServer, port=myconfig.CONFIG.qbPort, username=myconfig.CONFIG.qbUser, password=myconfig.CONFIG.qbPass)

    try:
        qbClient.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        print(e)
        return False
    except:
        return False

    if not qbClient:
        return False

    prefs = qbClient.app_preferences()
    autoprog = prefs["autorun_program"]
    return autoprog



def setAutoRunProgram(prog):
    qbClient = qbittorrentapi.Client(
        host=myconfig.CONFIG.qbServer, port=myconfig.CONFIG.qbPort, username=myconfig.CONFIG.qbUser, password=myconfig.CONFIG.qbPass)

    try:
        qbClient.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        print(e)
        return False
    except:
        return False

    if not qbClient:
        return False

    qbClient.app_set_preferences(prefs={"autorun_enabled": True, "autorun_program": prog})
    return True


def check_and_remove_category(qbClient, category):
    # 获取所有的 给定的 category 的 torrents
    category_torrents = qbClient.torrents_info(category=category)

    # 如果该类别下没有 torrent
    if not category_torrents:
        # logger.info(f"No torrents found in category '{category}', removing the category.")
        # 删除该类别
        qbClient.torrents_remove_categories(category)
    else:
        logger.warning(f"Found {len(category_torrents)} torrents in category '{category}'.")

def check_and_remove_tags(qbClient, tags):
    # 获取所有的 给定的 category 的 torrents
    # for tag in tags:
    tag_torrents = qbClient.torrents_info(tag=tags)
    # 如果该tag下没有 torrent
    if not tag_torrents:
        # logger.info(f"No torrents found in tag '{tag}', removing the category.")
        # 删除该类别
        qbClient.torrents_remove_tags(tags)

def qbDeleteTorrentA(tor_hash):
    if not validQbitConfig():
        return
    
    qbClient = qbittorrentapi.Client(
        host=myconfig.CONFIG.qbServer, port=myconfig.CONFIG.qbPort, username=myconfig.CONFIG.qbUser, password=myconfig.CONFIG.qbPass)
    qbDeleteTorrent(qbClient, tor_hash)

def qbDeleteTorrent(qbClient, tor_hash):
    if not validQbitConfig():
        return
    try:
        torrent = qbClient.torrents_info(torrent_hashes=tor_hash)[0]
        qbClient.torrents_delete(True, torrent_hashes=tor_hash)
        check_and_remove_category(qbClient, torrent.category)
        # check_and_remove_tags(qbClient, torrent.tags)
    except Exception as ex:
        logger.error(f'There was an error during client.torrents_delete: {tor_hash}, {ex}')

def psutilGetFreeSpace():
    total, used, free = shutil.disk_usage("/")
    return free


def qbGetFreeSpace():
    if not validQbitConfig():
        return -1
    qbClient = qbittorrentapi.Client(
        host=myconfig.CONFIG.qbServer, port=myconfig.CONFIG.qbPort, username=myconfig.CONFIG.qbUser, password=myconfig.CONFIG.qbPass)

    try:
        qbClient.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        logger.error('检查 qBittorrent 配置')
        print(e)
        return -1

    if not qbClient:
        return -1

    try:
        r = qbClient.sync_maindata(rid=0)
        return r['server_state']['free_space_on_disk']
    except Exception:
        logger.error('Error getting qBittorrent main data.')
        return -1

def getFreeSpace():
    free = qbGetFreeSpace()
    if free < -1:
        # TODO: 无法从qb取得硬盘空间时，先允许下载？
        logger.warning('Can\'t get free space from qbittorrent, assume 100G to make it start')
        free = 100 * 2**30
    return free

def autoResumeDelete(delete_to_free):
    size_storage_space = getFreeSpace()

    qbClient = qbittorrentapi.Client(
        host=myconfig.CONFIG.qbServer, port=myconfig.CONFIG.qbPort, username=myconfig.CONFIG.qbUser, password=myconfig.CONFIG.qbPass)
    try:
        torrents = qbClient.torrents_info()
    except:
        logger.debug('  !! Fail to load torrent list.')
        # client.disconnect()
        return -1
    total_count = len(torrents)
    count = 0
    paused_torrents = [x for x in torrents if (x['state'] in ['pausedDL', 'pausedUP'])]
    paused_count = len(paused_torrents)
    if paused_count > 0: 
        logger.info(f'Resume torrents: {paused_count} paused / {total_count}  total.')
        
    for torrent in paused_torrents:
        torrents = qbClient.torrents_info()
        enough_space = freeTorrentSpace(
            qbClient, torrents, torrent['total_size'], size_storage_space, delete_to_free)
        if enough_space:
            torrent.resume()
            logger.info(f' resume:  {count} {torrent["name"]} {HumanBytes.format(torrent["total_size"])}.')
            size_storage_space -= torrent['total_size']
            count += 1
            time.sleep(3)
    return count


def freeTorrentSpace(client, torrents, torsize, size_storage_space, delete_to_free):
    size_new_torrent = torsize

    # for all Downloading torrents in qbit, calculate bytes left to download
    size_left_to_complete = 0
    uncompleted_torrents = [x for x in torrents if (x['state'] in ['downloading', 'stalledDL', 'queuedDL']) ]
    # uncompleted_torrents = [x for x in torrents if x['progress'] < 1]
    for torrent in uncompleted_torrents:
        size_left_to_complete += torrent['amount_left']
        # size_left_to_complete += (torrent['total_size'] - torrent['downloaded'])
    remain_space = size_storage_space - size_left_to_complete
    logger.info(f'   >> (hdd_free) {HumanBytes.format(size_storage_space)} - (uncomplete) {HumanBytes.format(size_left_to_complete)} - '
                f'(new_tor) {HumanBytes.format(size_new_torrent)} = {HumanBytes.format(remain_space - size_new_torrent)}.')
    if (remain_space - size_new_torrent) > (myconfig.CONFIG.freeDiskMargin * 2**30):
        # enough space to add the new torrent
        logger.info(
            f'   => Enough space : ({HumanBytes.format(size_new_torrent)} / {HumanBytes.format(remain_space)}).')
        return True

    if not delete_to_free:
        return False
    
    # Sort completed torrents by seeding time
    completed_torrents = sorted(
        [x for x in torrents if x['progress'] == 1],
        key=lambda t: t['seeding_time'],
        reverse=True
    )
    logger.info(
        f'   -- {len(completed_torrents)} finished / {len(torrents)} total torrents.')

    # Loop through completed torrents and delete until there is enough space
    torrents_to_del = []
    space_to_del = 0
    for tor_complete in completed_torrents:
        torrents_to_del.append(tor_complete)
        space_to_del += tor_complete['downloaded']
        logger.info(
            f'   >> {tor_complete["name"]} : {HumanBytes.format(tor_complete["downloaded"])} ')
        logger.info(f'   :: (hdd_free) {HumanBytes.format(size_storage_space)} + (assume_del) {HumanBytes.format(space_to_del)} '
                    f'- (uncomplete) {HumanBytes.format(size_left_to_complete)} '
                    f'- (new_tor) {HumanBytes.format(size_new_torrent)} '
                    f'= {HumanBytes.format(size_storage_space + space_to_del - size_left_to_complete - size_new_torrent)}')
        if (size_storage_space + space_to_del - size_left_to_complete - size_new_torrent) > (myconfig.CONFIG.freeDiskMargin * 2**30):
            for tor_to_del in torrents_to_del:
                logger.warning(
                    f'   Deleting: {tor_to_del["name"]} to free {HumanBytes.format(tor_to_del["downloaded"])}.')
                qbDeleteTorrent(client, tor_to_del['hash'])
                time.sleep(3)
            return True
    remain_space = size_storage_space + space_to_del - size_left_to_complete
    logger.warning(f' not enough for download, remain_space ={HumanBytes.format(remain_space)} ')
    # logger.info('   !!! not enough: %s + %s - %s = %s.' % (convert_size(size_storage_space), convert_size(space_to_del), convert_size(
    #     size_left_to_complete), convert_size(remain_space)))

    return False

def enoughSpaceForTorrent(torsize, size_storage_space, delete_to_free):
    qbClient = qbittorrentapi.Client(
        host=myconfig.CONFIG.qbServer, port=myconfig.CONFIG.qbPort, username=myconfig.CONFIG.qbUser, password=myconfig.CONFIG.qbPass)
    try:
        torrents = qbClient.torrents_info()
    except:
        logger.debug('  !! Fail to load torrent list.')
        # client.disconnect()
        return False
    
    enough_space = freeTorrentSpace(
        qbClient, torrents, torsize, size_storage_space, delete_to_free)

    return enough_space


def addQbitWithTag(downlink, qbTagList, siteIdStr=None, qbCategory='', add_pause=False):
    qbClient = qbittorrentapi.Client(
        host=myconfig.CONFIG.qbServer, port=myconfig.CONFIG.qbPort, username=myconfig.CONFIG.qbUser, password=myconfig.CONFIG.qbPass)

    try:
        qbClient.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        print(e)
        return False

    if not qbClient:
        return False

    try:
        # curr_added_on = time.time()
        if siteIdStr:
            result = qbClient.torrents_add(
                urls=downlink,
                save_path=siteIdStr,
                # download_path=download_location,
                category=qbCategory,
                tags=qbTagList,
                is_paused=add_pause,
                use_auto_torrent_management=False)
        else:
            result = qbClient.torrents_add(
                urls=downlink,
                category=qbCategory,
                tags=qbTagList,
                is_paused=add_pause,
                use_auto_torrent_management=False)
        # breakpoint()
        if 'OK' in result.upper():
            pass
            # print('   >> Torrent added.')
        else:
            logger.error('   >> Torrent not added! something wrong with qb api ...')
    except Exception as e:
        logger.error('   >> Torrent not added! Exception: '+str(e))
        return False

    return True


def addQbitFileWithTag(filecontent, qbTagList, siteIdStr=None, qbCategory='', add_pause=False):
    qbClient = qbittorrentapi.Client(
        host=myconfig.CONFIG.qbServer, port=myconfig.CONFIG.qbPort, username=myconfig.CONFIG.qbUser, password=myconfig.CONFIG.qbPass)

    try:
        qbClient.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        print(e)
        return False

    if not qbClient:
        return False

    try:
        # curr_added_on = time.time()
        if siteIdStr:
            result = qbClient.torrents_add(
                torrent_files=filecontent,
                save_path=siteIdStr,
                # download_path=download_location,
                category=qbCategory,
                tags=qbTagList,
                is_paused=add_pause,
                use_auto_torrent_management=False)
        else:
            result = qbClient.torrents_add(
                torrent_files=filecontent,
                tags=qbTagList,
                category=qbCategory,
                is_paused=add_pause,
                use_auto_torrent_management=False)
        # breakpoint()
        if 'OK' in result.upper():
            pass
            # print('   >> Torrent added.')
        else:
            logger.error('   >> Torrent not added! something wrong with qb api ...')
    except Exception as e:
        logger.error('   >> Torrent not added! Exception: '+str(e))
        return False

    return True



class DownloadEntry:
    def __init__(self):
        super().__init__()
        self.downlink = ''
        self.title = ''
        self.siteid_str = ''
        self.imdb = ''
        self.label = ''
        self.size = 0
