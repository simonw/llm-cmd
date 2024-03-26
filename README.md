# llm-cmd

[![PyPI](https://img.shields.io/pypi/v/llm-cmd.svg)](https://pypi.org/project/llm-cmd/)
[![Changelog](https://img.shields.io/github/v/release/simonw/llm-cmd?include_prereleases&label=changelog)](https://github.com/simonw/llm-cmd/releases)
[![Tests](https://github.com/simonw/llm-cmd/actions/workflows/test.yml/badge.svg)](https://github.com/simonw/llm-cmd/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/simonw/llm-cmd/blob/main/LICENSE)

Use LLM to generate and execute commands in your shell

## Installation

Install this plugin in the same environment as [LLM](https://llm.datasette.io/).
```bash
llm install llm-cmd
```
## Usage

This command could be **very dangerous**. Do not use this unless you are confident you understand what it does and are sure you could spot if it is likely to do something dangerous.

Run `llm cmd` like this:

```bash
llm cmd undo last git commit
```
It will use your [default model](https://llm.datasette.io/en/stable/setup.html#setting-a-custom-default-model) to generate the corresponding shell command.

This will then be displayed in your terminal ready for you to edit it, or hit `<enter>` to execute the prompt.

If the command doesnt't look right, hit `Ctrl+C` to cancel.

## The system prompt

This is the prompt used by this tool:

> Return only the command to be executed as a raw string, no string delimiters
wrapping it, no yapping, no markdown, no fenced code blocks, what you return
will be passed to subprocess.check_output() directly.
>
> For example, if the user asks: undo last git commit
>
> You return only: git reset --soft HEAD~1

## Development

To set up this plugin locally, first checkout the code. Then create a new virtual environment:
```bash
cd llm-cmd
python3 -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
llm install -e '.[test]'
```
To run the tests:
```bash
pytest
```
