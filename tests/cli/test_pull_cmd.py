"""Tests for the pull CLI command."""
# tests/cli/test_pull_cmd.py

# Unit under test:
import dem.cli.main as main

# Test framework
from typer.testing import CliRunner
from unittest.mock import patch, MagicMock, call

from rich.console import Console
import io
from dem.core.tool_images import ToolImages

## Global test variables

# In order to test stdout and stderr separately, the stderr can't be mixed into the stdout.
runner = CliRunner(mix_stderr=False)

def test_dev_env_not_available_in_org():
    # Test setup
    mock_platform = MagicMock()
    mock_catalog = MagicMock()
    mock_platform.dev_env_catalogs.catalogs = [mock_catalog]
    mock_catalog.get_dev_env_by_name.return_value = None
    main.platform = mock_platform

    # Run unit under test
    runner_result = runner.invoke(main.typer_cli, ["pull", "not existing env"], color=True)

    # Check expectations
    mock_catalog.get_dev_env_by_name.assert_called_once_with("not existing env")

    assert 0 == runner_result.exit_code

    console = Console(file=io.StringIO())
    console.print("[red]Error: The input Development Environment is not available for the organization.[/]")
    assert console.file.getvalue() == runner_result.stderr

def test_dev_env_already_installed():
    # Test setup
    mock_platform = MagicMock()
    mock_catalog = MagicMock()
    mock_platform.dev_env_catalogs.catalogs = [mock_catalog]
    main.platform = mock_platform

    mock_catalog_dev_env = MagicMock()
    mock_tools = MagicMock()
    mock_catalog.get_dev_env_by_name.return_value = mock_catalog_dev_env

    mock_local_dev_env = MagicMock()
    mock_local_dev_env.name = "test_env"
    mock_platform.get_dev_env_by_name.return_value = mock_local_dev_env

    # Set the same tools for both the catalog and the local instance
    mock_catalog_dev_env.tools = mock_tools
    mock_local_dev_env.tools = mock_tools

    def stub_check_image_availability(*args, **kwargs):
        image_statuses = []
        for tool in mock_local_dev_env.tools:
            tool["image_status"] = ToolImages.LOCAL_AND_REGISTRY
            image_statuses.append(ToolImages.LOCAL_AND_REGISTRY)
        return image_statuses
    mock_local_dev_env.check_image_availability.side_effect = stub_check_image_availability

    test_env_name =  "test_env"

    # Run unit under test
    runner_result = runner.invoke(main.typer_cli, ["pull", test_env_name], color=True)

    # Check expectations
    assert 0 == runner_result.exit_code

    mock_catalog.get_dev_env_by_name.assert_called_once_with(test_env_name)

    mock_platform.get_dev_env_by_name.assert_called_once_with(mock_catalog_dev_env.name)
    mock_platform.install_dev_env.assert_called_once_with(mock_local_dev_env)
    mock_local_dev_env.check_image_availability.assert_called_once_with(mock_platform.tool_images, 
                                                                         update_tool_image_store=True)

    console = Console(file=io.StringIO())
    console.print("The [yellow]test_env[/] Development Environment is ready!")
    assert console.file.getvalue() == runner_result.stdout

def test_dev_env_installed_but_different():
    # Test setup
    mock_platform = MagicMock()
    mock_catalog = MagicMock()
    mock_platform.dev_env_catalogs.catalogs = [mock_catalog]
    main.platform = mock_platform

    mock_catalog_dev_env = MagicMock()
    mock_tools = MagicMock()
    mock_catalog_dev_env.tools = mock_tools
    mock_catalog.get_dev_env_by_name.return_value = mock_catalog_dev_env

    mock_local_dev_env = MagicMock()
    mock_local_dev_env.name = "test_env"
    mock_platform.get_dev_env_by_name.return_value = mock_local_dev_env

    def stub_check_image_availability(*args, **kwargs):
        image_statuses = []
        for tool in mock_local_dev_env.tools:
            tool["image_status"] = ToolImages.LOCAL_AND_REGISTRY
            image_statuses.append(ToolImages.LOCAL_AND_REGISTRY)
        return image_statuses
    mock_local_dev_env.check_image_availability.side_effect = stub_check_image_availability

    test_env_name =  "test_env"

    # Run unit under test
    runner_result = runner.invoke(main.typer_cli, ["pull", test_env_name], color=True)

    # Check expectations
    assert 0 == runner_result.exit_code
    assert mock_local_dev_env.tools is mock_catalog_dev_env.tools

    mock_catalog.get_dev_env_by_name.assert_called_once_with(test_env_name)

    mock_platform.get_dev_env_by_name.assert_called_once_with(mock_catalog_dev_env.name)
    mock_platform.flush_descriptors.assert_called_once()
    mock_platform.install_dev_env.assert_called_once_with(mock_local_dev_env)
    mock_local_dev_env.check_image_availability.assert_called_once_with(mock_platform.tool_images, 
                                                                         update_tool_image_store=True)

    console = Console(file=io.StringIO())
    console.print("The [yellow]test_env[/] Development Environment is ready!")
    assert console.file.getvalue() == runner_result.stdout

@patch("dem.cli.command.pull_cmd.DevEnv")
def test_dev_env_new_install(mock_DevEnv: MagicMock):
    # Test setup
    mock_platform = MagicMock()
    mock_catalog = MagicMock()
    mock_platform.dev_env_catalogs.catalogs = [mock_catalog]
    main.platform = mock_platform

    mock_catalog_dev_env = MagicMock()
    mock_tools = MagicMock()
    mock_catalog_dev_env.tools = mock_tools
    mock_catalog.get_dev_env_by_name.return_value = mock_catalog_dev_env
    mock_platform.get_dev_env_by_name.return_value = None

    mock_local_dev_env = MagicMock()
    mock_DevEnv.return_value = mock_local_dev_env
    
    def stub_check_image_availability(*args, **kwargs):
        image_statuses = []
        for tool in mock_local_dev_env.tools:
            tool["image_status"] = ToolImages.LOCAL_AND_REGISTRY
            image_statuses.append(ToolImages.LOCAL_AND_REGISTRY)
        return image_statuses
    mock_local_dev_env.check_image_availability.side_effect = stub_check_image_availability
    test_env_name =  "test_env"
    mock_local_dev_env.name = test_env_name
    mock_platform.local_dev_envs = []

    # Run unit under test
    runner_result = runner.invoke(main.typer_cli, ["pull", test_env_name], color=True)

    # Check expectations
    assert 0 == runner_result.exit_code
    assert mock_local_dev_env in mock_platform.local_dev_envs

    mock_catalog.get_dev_env_by_name.assert_called_once_with(test_env_name)
    mock_platform.get_dev_env_by_name.assert_called_once_with(mock_catalog_dev_env.name)
    mock_DevEnv.assert_called_once_with(dev_env_to_copy=mock_catalog_dev_env)
    mock_platform.flush_descriptors.assert_called_once()
    mock_platform.install_dev_env.assert_called_once_with(mock_local_dev_env)
    mock_local_dev_env.check_image_availability.assert_called_once_with(mock_platform.tool_images, 
                                                                         update_tool_image_store=True)

    console = Console(file=io.StringIO())
    console.print("The [yellow]" + test_env_name + "[/] Development Environment is ready!")
    assert console.file.getvalue() == runner_result.stdout

@patch("dem.cli.command.pull_cmd.stderr.print")
@patch("dem.cli.command.pull_cmd.create_dev_env")
def test_execute_install_failed(mock_create_dev_env: MagicMock,
                                mock_stderr_print: MagicMock):
    # Test setup
    mock_platform = MagicMock()
    main.platform = mock_platform

    mock_catalog = MagicMock()
    mock_platform.dev_env_catalogs.catalogs = [mock_catalog]

    mock_catalog_dev_env = MagicMock()
    mock_catalog.get_dev_env_by_name.return_value = mock_catalog_dev_env
    mock_platform.get_dev_env_by_name.return_value = None

    mock_local_dev_env = MagicMock()
    mock_platform.get_dev_env_by_name.return_value = mock_local_dev_env
    mock_create_dev_env.return_value = mock_local_dev_env

    mock_local_dev_env.check_image_availability.return_value = [ToolImages.LOCAL_ONLY]
    test_env_name =  "test_env"

    mock_tools = MagicMock()
    mock_local_dev_env.tools = mock_tools

    # Run unit under test
    runner_result = runner.invoke(main.typer_cli, ["pull", test_env_name], color=True)

    # Check expectations
    assert 0 == runner_result.exit_code

    mock_catalog.get_dev_env_by_name(test_env_name)
    mock_platform.get_dev_env_by_name.assert_called_once_with(mock_catalog_dev_env.name)
    mock_create_dev_env.assert_called_once_with(mock_local_dev_env, mock_catalog_dev_env, 
                                                         mock_platform)
    mock_local_dev_env.check_image_availability.assert_called_once_with(mock_platform.tool_images, 
                                                                         update_tool_image_store=True)
    mock_platform.install_dev_env.assert_called_once_with(mock_local_dev_env)
    mock_stderr_print.assert_called_once_with("The installation failed.")

@patch("dem.cli.command.pull_cmd.stderr.print")
def test_execute_no_catalogs(mock_stderr_print: MagicMock):
    # Test setup
    mock_platform = MagicMock()
    mock_platform.dev_env_catalogs.catalogs = []
    main.platform = mock_platform

    test_env_name =  "test_env"

    # Run unit under test
    runner_result = runner.invoke(main.typer_cli, ["pull", test_env_name], color=True)

    # Check expectations
    assert 0 == runner_result.exit_code

    mock_stderr_print.assert_called_once_with("[red]Error: No Development Environment Catalogs are available to pull the image from![/]")

@patch("dem.cli.command.pull_cmd.stderr.print")
def test_execute_dev_env_not_available_in_catalog(mock_stderr_print: MagicMock):
    # Test setup
    mock_platform = MagicMock()
    mock_catalog = MagicMock()
    mock_catalog.get_dev_env_by_name.return_value = None
    mock_platform.dev_env_catalogs.catalogs = [mock_catalog]
    main.platform = mock_platform

    test_env_name =  "test_env"

    # Run unit under test
    runner_result = runner.invoke(main.typer_cli, ["pull", test_env_name], color=True)

    # Check expectations
    assert 0 == runner_result.exit_code

    mock_catalog.get_dev_env_by_name.assert_called_once_with(test_env_name)
    mock_stderr_print.assert_called_once_with("[red]Error: The input Development Environment is not available for the organization.[/]")