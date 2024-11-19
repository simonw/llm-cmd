import os
import pytest
from unittest.mock import patch, MagicMock
from llm_cmd import interactive_exec

@pytest.fixture
def mock_subprocess_run():
    with patch('subprocess.run') as mock_run:
        yield mock_run

@pytest.fixture
def mock_subprocess_check_output():
    with patch('subprocess.check_output') as mock_check:
        yield mock_check

@pytest.fixture
def mock_prompt_session():
    with patch('llm_cmd.PromptSession') as MockSession:
        session = MagicMock()
        MockSession.return_value = session
        session.prompt.return_value = "test command"
        yield session

def test_history_saving_with_flag(mock_subprocess_run, mock_subprocess_check_output, mock_prompt_session, monkeypatch, capsys):
    # Test with --save-history flag
    monkeypatch.setenv('HISTFILE', '/tmp/test_history')
    mock_subprocess_run.return_value.returncode = 0
    mock_subprocess_run.return_value.stderr = ""
    mock_subprocess_run.return_value.stdout = ""
    
    mock_subprocess_check_output.return_value = b""
    interactive_exec("test command", save_history=True)
    
    # Verify history command was called
    mock_subprocess_run.assert_called_once()
    assert 'history -s' in mock_subprocess_run.call_args[0][0][2]

def test_history_saving_with_env_var(mock_subprocess_run, mock_subprocess_check_output, mock_prompt_session, monkeypatch, capsys):
    # Test with environment variable
    monkeypatch.setenv('HISTFILE', '/tmp/test_history')
    monkeypatch.setenv('LLM_CMD_SAVE_HISTORY', '1')
    mock_subprocess_run.return_value.returncode = 0
    mock_subprocess_check_output.return_value = b""
    
    interactive_exec("test command", save_history=False)
    
    # Verify history command was called due to env var
    mock_subprocess_run.assert_called_once()
    assert 'history -s' in mock_subprocess_run.call_args[0][0][2]

def test_no_history_saving(mock_subprocess_run, mock_subprocess_check_output, mock_prompt_session, monkeypatch, capsys):
    # Test with no history saving enabled
    monkeypatch.delenv('LLM_CMD_SAVE_HISTORY', raising=False)
    
    interactive_exec("test command", save_history=False)
    
    # Verify history command was not called
    mock_subprocess_run.assert_not_called()

def test_history_saving_failure(mock_subprocess_run, mock_subprocess_check_output, mock_prompt_session, monkeypatch, capsys):
    # Test history saving with no HISTFILE set
    monkeypatch.delenv('HISTFILE', raising=False)
    
    interactive_exec("test command", save_history=True)
    
    # Verify warning was printed and history command was not called
    captured = capsys.readouterr()
    assert "Warning: $HISTFILE environment variable not set or not exported" in captured.out
    assert "History saving is disabled" in captured.out
    mock_subprocess_run.assert_not_called()

    # Test history saving failure scenario
    monkeypatch.setenv('HISTFILE', '/tmp/test_history')
    mock_subprocess_run.return_value.returncode = 1
    mock_subprocess_run.return_value.stderr = "Permission denied"
    mock_subprocess_run.return_value.stdout = ""
    
    interactive_exec("test command", save_history=True)
    
    # Verify error messages were printed
    captured = capsys.readouterr()
    assert "Warning: Failed to save command to history" in captured.out
    assert "Permission denied" in captured.out
