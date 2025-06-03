from llm.plugins import load_plugins, pm


def test_plugin_is_installed():
    load_plugins()
    names = [mod.__name__ for mod in pm.get_plugins()]
    assert "llm_cmd" in names
