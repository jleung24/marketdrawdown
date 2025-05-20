import configparser
import os


def read_config(section: str):
    config = configparser.ConfigParser()
    base_dir = os.path.join( os.path.dirname( __file__ ), '..' )
    config_path  = os.path.abspath(os.path.join(base_dir, "config.ini"))
    config.read(config_path)
    if section not in config.sections():
        raise KeyError(f"Could not find section {section} in config.ini")
    
    return config[section]