import configparser
import os

class configData():
    # apikey
    torcpdb_url = 'http://127.0.0.1:5009'
    torcpdb_apikey = ''
    torll_url = 'http://127.0.0.1:5006'
    torll_apikey = ''
    # qbit
    qbitname = 'this'
    host = '127.0.0.1'
    port = ''
    username = ''
    password = ''
    docker_from = ''
    docker_to = ''
    link_dir = ''
    auto_delete = False
    free_disk_margin = 5
    run_torcp_by_api = False
    add_pause = False
    default = True
    islocal = True
    # TORCP
    bracket = ''
    areadir = ''
    genre = ''
    genre_with_area = ''
    symbolink = ''
    extra_param = ''         # config.ini only
    insert_hash_dir = False
    categoryDirList = []    # config.ini only
    autoCategory = []       # config.ini only

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
        CONFIG.link_dir = config['TORCP'].get('link_dir', '')
        CONFIG.bracket = config['TORCP'].get('bracket', '')
        # if not CONFIG.bracket.startswith('--'):
        #     CONFIG.bracket = '--' + CONFIG.bracket
        # CONFIG.tmdbLang = config['TORCP'].get('tmdb_lang', 'en-US')
        # CONFIG.lang = config['TORCP'].get('lang', 'cn,ja,ko')
        CONFIG.areadir = config['TORCP'].get('areadir', '')
        CONFIG.genre = config['TORCP'].get('genre', '')
        CONFIG.genre_with_area = config['TORCP'].get('genre_with_area', '')
        CONFIG.symbolink = config['TORCP'].get('symbolink', '')
        CONFIG.extra_param = config['TORCP'].get('extra_param', '')
        CONFIG.insert_hash_dir = config['TORCP'].getboolean('insert_hash_dir', False)
        CONFIG.torcpdb_url = config['TORCP'].get('torcpdb_url', 'http://127.0.0.1:5009')
        CONFIG.torcpdb_apikey = config['TORCP'].get('torcpdb_apikey', '')

    if 'QBIT' in config:
        CONFIG.qbitname = config['QBIT'].get('qbitname', 'this')
        CONFIG.host = config['QBIT'].get('host', '127.0.0.1')
        CONFIG.port = config['QBIT'].get('port', '')
        CONFIG.username = config['QBIT'].get('username', '')
        CONFIG.password = config['QBIT'].get('password', '')

        # CONFIG.apiRunProgram = config['QBIT'].get('apirun', 'False')
        CONFIG.docker_from = config['QBIT'].get('docker_from', '')
        CONFIG.docker_to = config['QBIT'].get('docker_to', '')

        CONFIG.dryrun = config['QBIT'].getboolean('dryrun', False)
        CONFIG.add_pause = config['QBIT'].getboolean('add_pause', False)
        CONFIG.auto_delete = config['QBIT'].getboolean('auto_delete', False)
        CONFIG.default = config['QBIT'].getboolean('default', True)
        CONFIG.islocal = config['QBIT'].getboolean('islocal', True)
        CONFIG.run_torcp_by_api = config['QBIT'].getboolean('run_torcp_by_api', False)

        CONFIG.rcpshfile = os.path.join(os.path.dirname(__file__), 'rcp.sh')
        CONFIG.free_disk_margin = config['QBIT'].getint('free_disk_margin', 5)

def loadJsonConfig(cfgFile, json_data):
    config = configparser.ConfigParser()
    config.read(cfgFile)
    if not config.has_section('QBIT'):
        config.add_section('QBIT')
    if not config.has_section('TORCP'):
        config.add_section('TORCP')
    if 'qbitname' in json_data:
        CONFIG.qbitname = json_data.get('qbitname')
        config.set('QBIT', 'qbitname', CONFIG.qbitname)
    if 'host' in json_data:
        CONFIG.host = json_data.get('host')
        config.set('QBIT', 'host', CONFIG.host)
    if 'port' in json_data:
        CONFIG.port = str(json_data.get('port'))
        config.set('QBIT', 'port', CONFIG.port)
    if 'username' in json_data:
        CONFIG.username = json_data.get('username')
        config.set('QBIT', 'username', CONFIG.username)
    if 'password' in json_data:
        CONFIG.password = json_data.get('password')
        config.set('QBIT', 'password', CONFIG.password)
    if 'docker_from' in json_data:
        CONFIG.docker_from = json_data.get('docker_from')
        config.set('QBIT', 'docker_from', CONFIG.docker_from)
    if 'docker_to' in json_data:
        CONFIG.docker_to = json_data.get('docker_to')
        config.set('QBIT', 'docker_to', CONFIG.docker_to)
    if 'link_dir' in json_data:
        CONFIG.link_dir = json_data.get('link_dir')
        config.set('TORCP', 'link_dir', CONFIG.link_dir)
    if 'auto_delete' in json_data:
        CONFIG.auto_delete = json_data.get('auto_delete')
        config.set('QBIT', 'auto_delete', str(CONFIG.auto_delete))
    if 'islocal' in json_data:
        CONFIG.islocal = json_data.get('islocal')
        config.set('QBIT', 'islocal', str(CONFIG.islocal))
    if 'default' in json_data:
        CONFIG.default = json_data.get('default')
        config.set('QBIT', 'default', str(CONFIG.default))
    if 'add_pause' in json_data:
        CONFIG.add_pause = json_data.get('add_pause')
        config.set('QBIT', 'add_pause', str(CONFIG.add_pause))
    if 'disk_free_margin' in json_data:
        CONFIG.disk_free_margin = str(json_data.get('disk_free_margin'))
        config.set('QBIT', 'disk_free_margin', CONFIG.disk_free_margin)
    if 'run_torcp_by_api' in json_data:
        CONFIG.run_torcp_by_api = json_data.get('run_torcp_by_api')
        config.set('QBIT', 'run_torcp_by_api', str(CONFIG.run_torcp_by_api))

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
        CONFIG.genre_with_area = json_data.get('genre_with_area')
        config.set('TORCP', 'genre_with_area', CONFIG.genre_with_area)
    if 'symbolink' in json_data:
        CONFIG.symbolink = json_data.get('symbolink')
        config.set('TORCP', 'symbolink', CONFIG.symbolink)
    if 'extra_param' in json_data:
        CONFIG.extra_param = json_data.get('extra_param')
        config.set('TORCP', 'extra_param', CONFIG.extra_param)
    if 'insert_hash_dir' in json_data:
        CONFIG.insert_hash_dir = json_data.get('insert_hash_dir')
        config.set('TORCP', 'insert_hash_dir', str(CONFIG.insert_hash_dir))
    # TODO:
    if 'category_dir_list' in json_data:
        category_dir_list = json_data.get('category_dir_list')
        CONFIG.categoryDirList = category_dir_list.split(',')

    with open(cfgFile, 'w') as f:
        config.write(f)


