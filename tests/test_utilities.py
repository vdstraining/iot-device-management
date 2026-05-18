import os
import tempfile
from pathlib import Path

from utilities import DEFAULT_COMMANDS, DEFAULT_COMMANDS_PATH, load_default_commands, save_default_commands


def test_load_missing_file_returns_empty_list():
    tf = tempfile.NamedTemporaryFile(delete=False)
    path = tf.name
    tf.close()
    try:
        os.remove(path)
    except OSError:
        pass

    assert load_default_commands(path) == []


def test_load_invalid_json_returns_empty_list():
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
        tf.write("not a json")
        path = tf.name

    try:
        assert load_default_commands(path) == []
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def test_save_and_load_round_trip_persists_commands():
    commands = [
        {"name": "T1", "payload": {"a": 1}},
        {"name": "T2", "payload": {"b": 2}},
    ]

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
        path = tf.name

    try:
        save_default_commands(path, commands)
        loaded = load_default_commands(path)
        assert loaded == commands
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def test_load_default_commands_skips_invalid_items():
    invalid_items = [
        {"name": "Valid", "payload": {"a": 1}},
        "not-a-dict",
        {"name": "MissingPayload"},
        {"payload": {"a": 2}},
    ]

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as tf:
        tf.write(str(invalid_items).replace("'", '"'))
        path = tf.name

    try:
        loaded = load_default_commands(path)
        assert loaded == [{"name": "Valid", "payload": {"a": 1}}]
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def test_default_commands_constant_matches_default_file():
    file_path = Path(DEFAULT_COMMANDS_PATH)
    assert file_path.exists(), f"Expected default commands file at {DEFAULT_COMMANDS_PATH}"
    loaded = load_default_commands(DEFAULT_COMMANDS_PATH)
    assert loaded == DEFAULT_COMMANDS

