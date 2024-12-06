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

def loadJsonConfig(cfgFile, json_data):
    config = configparser.ConfigParser()
    config.read(cfgFile)
    if 'qb_host' in json_data:
        CONFIG.qbServer = json_data.get('qb_host')
        config.set('QBIT', 'server_ip', CONFIG.qbServer)
    if 'qb_port' in json_data:
        CONFIG.qbPort = json_data.get('qb_port')
        config.set('QBIT', 'port', CONFIG.qbPort)
    if 'qb_user' in json_data:
        CONFIG.qbUser = json_data.get('qb_user')
        config.set('QBIT', 'user', CONFIG.qbUser)
    if 'qb_pass' in json_data:
        CONFIG.qbPass = json_data.get('qb_pass')
        config.set('QBIT', 'pass', CONFIG.qbPass)
    if 'docker_from' in json_data:
        CONFIG.dockerFrom = json_data.get('docker_from')
        config.set('QBIT', 'dockerFrom', CONFIG.dockerFrom)
    if 'docker_to' in json_data:
        CONFIG.dockerTo = json_data.get('docker_to')
        config.set('QBIT', 'dockerTo', CONFIG.dockerTo)
    if 'link_dir' in json_data:
        CONFIG.linkDir = json_data.get('link_dir')
        config.set('TORCP', 'linkdir', CONFIG.linkDir)
    if 'bracket' in json_data:
        CONFIG.bracket = json_data.get('bracket')
        config.set('TORCP', 'bracket', CONFIG.bracket)
    if 'areadir' in json_data:
        CONFIG.areadir = json_data.get('areadir')
        config.set('TORCP', 'areadir', CONFIG.areadir)
    if 'genre' in json_data:
        CONFIG.genre = json_data.get('genre')
        config.set('TORCP', 'genre', CONFIG.genre)
    if 'genre_with_area' in json_data:
        CONFIG.genreWithArea = json_data.get('genre_with_area')
        config.set('TORCP', 'genre_with_area', CONFIG.genreWithArea)
    if 'symbolink' in json_data:
        CONFIG.symbolink = json_data.get('symbolink')
        config.set('TORCP', 'symbolink', CONFIG.symbolink)
    if 'extra_param' in json_data:
        CONFIG.extraParam = json_data.get('extra_param')
        config.set('TORCP', 'extra', CONFIG.extraParam)
    if 'insert_hash_dir' in json_data:
        CONFIG.insertHashDir = json_data.get('insert_hash_dir')
        config.set('TORCP', 'insert_hash_dir', CONFIG.insertHashDir)
    # TODO:
    if 'category_dir_list' in json_data:
        category_dir_list = json_data.get('category_dir_list')
        CONFIG.categoryDirList = category_dir_list.split(',')

    with open(cfgFile, 'w') as f:
        config.write(f)


