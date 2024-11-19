import click
import llm
import os
import subprocess
from prompt_toolkit import PromptSession
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.patch_stdout import patch_stdout
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
    @click.option("--save-history", is_flag=True, help="Save commands to shell history")
    def cmd(args, model, system, key, save_history):
        """Generate and execute commands in your shell"""
        from llm.cli import get_default_model
        prompt = " ".join(args)
        model_id = model or get_default_model()
        model_obj = llm.get_model(model_id)
        if model_obj.needs_key:
            model_obj.key = llm.get_key(key, model_obj.needs_key, model_obj.key_env_var)
        result = model_obj.prompt(prompt, system=system or SYSTEM_PROMPT)
        interactive_exec(str(result), save_history)

def interactive_exec(command, save_history):
    # Check if history saving is enabled via flag or env var
    save_to_history = save_history or os.environ.get('LLM_CMD_SAVE_HISTORY')
    session = PromptSession(lexer=PygmentsLexer(BashLexer))
    with patch_stdout():
        if '\n' in command:
            print("Multiline command - Meta-Enter or Esc Enter to execute")
            edited_command = session.prompt("> ", default=command, multiline=True)
        else:
            edited_command = session.prompt("> ", default=command)
    try:
        # Execute the command first
        output = subprocess.check_output(
            edited_command, shell=True, stderr=subprocess.STDOUT
        )
        print(output.decode())
        
        # Only save successful commands to history
        if save_to_history:
            histfile = os.environ.get('HISTFILE')
            if not histfile:
                print("Warning: $HISTFILE environment variable not set or not exported")
                print("History saving is disabled. Please ensure HISTFILE is exported in your shell config")
            else:
                # Add to bash history and append to history file
                escaped_cmd = edited_command.replace('"', '\\"')
                history_result = subprocess.run(
                    ['bash', '-c', f'history -s "{escaped_cmd}" && history -a'],
                    capture_output=True,
                    text=True,
                    check=False
                )
                if history_result.returncode != 0:
                    print("Warning: Failed to save command to shell history")
    except subprocess.CalledProcessError as e:
        error_msg = e.output.decode() if e.output else "No error output available"
        print(f"Command failed with error (exit status {e.returncode}): {error_msg}")
