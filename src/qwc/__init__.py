import logging
from pathlib import Path
from configobj import ConfigObj

path = Path(__file__).parent
config_path = path / 'config.ini'

try:
    config = ConfigObj('config.ini')
    assert config['qwc']
except Exception as e: 
    config = ConfigObj(str(config_path))




