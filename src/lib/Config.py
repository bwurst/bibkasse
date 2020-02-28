import json, os

def config(section = None):
    CONFIG = 'daten/config.json'
    if not os.path.exists(CONFIG):
        raise RuntimeError('Die Config-Datei existiert nicht!')
    
    configfile = open(CONFIG, 'r')
    conf = json.load(configfile)
    if section:
        return conf[section]
    else:
        return conf
