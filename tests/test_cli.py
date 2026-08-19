from typer.testing import CliRunner
from search_cli.cli import app

runner = CliRunner()


def test_cli_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "search-cli version" in result.stdout


def test_cli_auth_status_unauthenticated():
    result = runner.invoke(app, ["auth", "status"])
    assert result.exit_code == 0
    assert "Not authenticated" in result.stdout or "Authenticated" in result.stdout


def test_cli_config_commands(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    
    # Set default site
    res_set = runner.invoke(app, ["config", "set", "default_site", "sc-domain:test.com"])
    assert res_set.exit_code == 0
    assert "Set 'default_site'" in res_set.stdout

    # Get default site
    res_get = runner.invoke(app, ["config", "get", "default_site"])
    assert res_get.exit_code == 0
    assert "sc-domain:test.com" in res_get.stdout

    # List config
    res_list = runner.invoke(app, ["config", "list"])
    assert res_list.exit_code == 0
    assert "sc-domain:test.com" in res_list.stdout


def test_cli_query_missing_site(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    result = runner.invoke(app, ["query"])
    assert result.exit_code == 1
    assert "No site URL specified" in result.stderr or "No site URL specified" in result.stdout


def test_cli_guide():
    result = runner.invoke(app, ["guide"])
    assert result.exit_code == 0
    assert "Search CLI - AI Agent & User Guide" in result.stdout


def test_cli_guide_json():
    import json
    result = runner.invoke(app, ["guide", "--json"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["title"] == "SearchCLI_Agent_Specification"
    assert "query" in data["commands"]

