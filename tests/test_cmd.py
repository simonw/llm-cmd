from llm.plugins import load_plugins, pm
import click


def test_plugin_is_installed():
    load_plugins()
    names = [mod.__name__ for mod in pm.get_plugins()]
    assert "llm_cmd" in names

def test_print_only_flag():
    load_plugins()

    cli = click.Group()
    pm.hook.register_commands(cli=cli)
    cmd = cli.commands['cmd']
    assert any(opt.name == "print_only" for opt in cmd.params)