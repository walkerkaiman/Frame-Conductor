import os
import json
import pytest
from config_manager import ConfigManager

CONFIG_FILE = 'test_config.json'

def setup_function():
    # Remove test config file before each test
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)

def teardown_function():
    # Clean up after each test
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)

def test_loads_default_config_if_no_file():
    cm = ConfigManager(CONFIG_FILE)
    config = cm.load_config()
    assert config['total_frames'] == 1000
    assert config['frame_rate'] == 30
    assert config['universe'] == 999
    assert config['frame_length'] == 512

def test_loads_config_from_file_with_all_fields():
    data = {
        'total_frames': 1234,
        'frame_rate': 60,
        'universe': 123,
        'frame_length': 256
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)
    cm = ConfigManager(CONFIG_FILE)
    config = cm.load_config()
    assert config == data

def test_loads_config_with_missing_fields_uses_defaults():
    data = {'total_frames': 42}
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f)
    cm = ConfigManager(CONFIG_FILE)
    config = cm.load_config()
    assert config['total_frames'] == 42
    assert config['frame_rate'] == 30
    assert config['universe'] == 999
    assert config['frame_length'] == 512

def test_saves_config_with_all_fields():
    cm = ConfigManager(CONFIG_FILE)
    data = {
        'total_frames': 2222,
        'frame_rate': 25,
        'universe': 888,
        'frame_length': 128
    }
    assert cm.save_config(data)
    with open(CONFIG_FILE) as f:
        loaded = json.load(f)
    assert loaded == data

def test_updates_config_when_value_changes():
    cm = ConfigManager(CONFIG_FILE)
    data = cm.load_config()
    data['total_frames'] = 555
    cm.save_config(data)
    config2 = cm.load_config()
    assert config2['total_frames'] == 555

def test_handles_invalid_config_file_gracefully():
    with open(CONFIG_FILE, 'w') as f:
        f.write('{invalid json')
    cm = ConfigManager(CONFIG_FILE)
    config = cm.load_config()
    assert config['total_frames'] == 1000  # default 