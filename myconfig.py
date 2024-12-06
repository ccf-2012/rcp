import configparser
import os

class configData():
    torcpdb_url = 'http://127.0.0.1:5009'
    torcpdb_apikey = ''
    torll_url = 'http://127.0.0.1:5006'
    torll_apikey = ''
    qbServer = '127.0.0.1'
    qbPort = ''
    qbUser = ''
    qbPass = ''
    dockerFrom = ''
    dockerTo = ''
    linkDir = ''
    bracket = ''
    tmdbLang = 'en'
    lang = 'cn,ja,ko'
    areadir = ''
    genre = ''
    genreWithArea = ''
    symbolink = ''
    extraParam = ''         # config.ini only
    insertHashDir = False
    categoryDirList = []    # config.ini only
    autoCategory = []       # config.ini only
    freeDiskMargin = 5

CONFIG = configData()


def readConfig(cfgFile):
    config = configparser.ConfigParser()
    config.read(cfgFile)

    if 'TORLL' in config:
        CONFIG.torll_url = config['TORLL'].get('torll_url', 'http://127.0.0.1:5006')
        CONFIG.torll_apikey = config['TORLL'].get('torll_apikey', '')

    if 'CATEGORY_DIR' in config:
        configitems = config.items('CATEGORY_DIR')
        for key, value in configitems:
            CONFIG.categoryDirList.append((key, value))

    if 'AUTO_CATEGORY' in config:
        configitems = config.items('AUTO_CATEGORY')
        for key, value in configitems:
            CONFIG.autoCategory.append((key, value))

    if 'TORCP' in config:
        CONFIG.linkDir = config['TORCP'].get('linkdir', '')
        CONFIG.bracket = config['TORCP'].get('bracket', '')
        # if not CONFIG.bracket.startswith('--'):
        #     CONFIG.bracket = '--' + CONFIG.bracket
        # CONFIG.tmdbLang = config['TORCP'].get('tmdb_lang', 'en-US')
        CONFIG.lang = config['TORCP'].get('lang', 'cn,ja,ko')
        CONFIG.areadir = config['TORCP'].get('areadir', '')
        CONFIG.genre = config['TORCP'].get('genre', '')
        CONFIG.genreWithArea = config['TORCP'].get('genre_with_area', '')
        CONFIG.symbolink = config['TORCP'].get('symbolink', '')
        CONFIG.extraParam = config['TORCP'].get('extra', '')
        CONFIG.insertHashDir = config['TORCP'].getboolean('insert_hash_dir', False)
        CONFIG.torcpdb_url = config['TORCP'].get('torcpdb_url', 'http://127.0.0.1:5009')
        CONFIG.torcpdb_apikey = config['TORCP'].get('torcpdb_apikey', '')

    if 'QBIT' in config:
        CONFIG.qbServer = config['QBIT'].get('server_ip', '127.0.0.1')
        CONFIG.qbPort = config['QBIT'].get('port', '')
        CONFIG.qbUser = config['QBIT'].get('user', '')
        CONFIG.qbPass = config['QBIT'].get('pass', '')

        # CONFIG.apiRunProgram = config['QBIT'].get('apirun', 'False')
        CONFIG.dockerFrom = config['QBIT'].get('dockerFrom', '')
        CONFIG.dockerTo = config['QBIT'].get('dockerTo', '')

        # CONFIG.dryrun = config['QBIT'].getboolean('dryrun', False)
        # CONFIG.addPause = config['QBIT'].getboolean('add_pause', False)
        # CONFIG.autoDelete = config['QBIT'].getboolean('auto_delete', False)

        # CONFIG.rcpshfile = os.path.join(os.path.dirname(__file__), 'rcp.sh')
        # CONFIG.freeDiskMargin = config['QBIT'].getint('free_disk_margin', 5)

