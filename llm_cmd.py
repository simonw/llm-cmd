import click
import llm
import subprocess

from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.styles.pygments import style_from_pygments_cls

try:
    from pygments.lexers.shell import BashLexer
    from pygments.styles import get_style_by_name, get_all_styles
    import pygments.util
except ImportError:
    BashLexer = get_style_by_name = get_all_styles = None


SYSTEM_PROMPT = """
Return only the command to be executed as a raw string, no string delimiters
wrapping it, no yapping, no markdown, no fenced code blocks, what you return
will be passed to subprocess.check_output() directly.

For example, if the user asks: undo last git commit

You return only: git reset --soft HEAD~1
""".strip()


@llm.hookimpl
def register_commands(cli):
    @cli.command()
    @click.argument("args", nargs=-1)
    @click.option("-m", "--model", default=None, help="Specify the model to use")
    @click.option("-s", "--system", help="Custom system prompt")
    @click.option("-H", "--highlight-style", default=None,
                  help="Pygments highlight style, e.g. monokai")
    @click.option("--key", help="API key to use")
    def cmd(args, model, system, key, highlight_style):
        """Generate and execute commands in your shell"""
        from llm.cli import get_default_model

        style = None
        if highlight_style is not None:
            if get_style_by_name is None:
                raise click.ClickException(
                    "Pygments is not installed, cannot use --highlight-style"
                )
            try:
                style = style_from_pygments_cls(get_style_by_name(highlight_style))
            except (ModuleNotFoundError, pygments.util.ClassNotFound):
                raise click.ClickException(
                    f"Style {highlight_style} not found, available styles: "
                    f"{list(get_all_styles())}"
                )

        prompt = " ".join(args)

        model_id = model or get_default_model()

        model_obj = llm.get_model(model_id)
        if model_obj.needs_key:
            model_obj.key = llm.get_key(key, model_obj.needs_key, model_obj.key_env_var)

        result = model_obj.prompt(prompt, system=system or SYSTEM_PROMPT)

        interactive_exec(str(result), style)


def interactive_exec(command, style):
    if style is None:
        kwargs = {}
    else:
        kwargs = {
            "style": style,
            "lexer": PygmentsLexer(BashLexer),
        }
    if '\n' in command:
        print("Multiline command - Meta-Enter or Esc Enter to execute")
        kwargs["multiline"] = True

    edited_command = prompt("> ", default=command, **kwargs)

    try:
        output = subprocess.check_output(
            edited_command, shell=True, stderr=subprocess.STDOUT
        )
        print(output.decode())
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error (exit status {e.returncode}): {e.output.decode()}")
