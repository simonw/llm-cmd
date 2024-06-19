import click
import llm
import subprocess

from prompt_toolkit.shortcuts import prompt
from prompt_toolkit.lexers import PygmentsLexer
from pygments.lexers.shell import BashLexer


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
    @click.option("--key", help="API key to use")
    def cmd(args, model, system, key):
        """Generate and execute commands in your shell"""
        from llm.cli import get_default_model, logs_on, logs_db_path

        prompt = " ".join(args)

        model_id = model or get_default_model()

        model_obj = llm.get_model(model_id)
        if model_obj.needs_key:
            model_obj.key = llm.get_key(key, model_obj.needs_key, model_obj.key_env_var)

        result = model_obj.prompt(prompt, system=system or SYSTEM_PROMPT)

        output = interactive_exec(str(result))
        print(output)

        if logs_on():
            import sqlite_utils
            from llm.migrations import migrate

            log_path = logs_db_path()
            (log_path.parent).mkdir(parents=True, exist_ok=True)
            db = sqlite_utils.Database(log_path)
            migrate(db)
            _log_cmd(db, model_id, result, output, prompt)


def interactive_exec(command) -> str:
    try:
        if "\n" in command:
            print("Multiline command - Meta-Enter or Esc Enter to execute")
            edited_command = prompt(
                "> ", default=command, lexer=PygmentsLexer(BashLexer), multiline=True
            )
        else:
            edited_command = prompt(
                "> ", default=command, lexer=PygmentsLexer(BashLexer)
            )
    except KeyboardInterrupt:
        return "Aborted!"

    try:
        output = subprocess.check_output(
            edited_command, shell=True, stderr=subprocess.STDOUT
        )
        return output.decode()
    except subprocess.CalledProcessError as e:
        return f"Command failed with error (exit status {e.returncode}): {e.output.decode()}"


def _log_cmd(db, model_id, result, output, prompt):
    failed = "Command failed with error" in output
    canceled = output == "Aborted!"
    db["cmds"].insert(
        {
            "model": model_id,
            "prompt": prompt,
            "cmd": str(result),
            "output": output,
            "failed": failed,
            "canceled": canceled,
        },
        ignore=True,
    )
