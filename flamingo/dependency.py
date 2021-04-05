import click

from flamingo.main import cli
from flamingo.api import FlamingoAPI, _parse_app_name
from flamingo.tools import _success, _warn


@cli.group()
def dependency():
    """Manages service's or build pack's OS depencdencies"""


@dependency.command("set")
@click.option('--application', '-a', type=str, required=True, help="Full application name (e.g. harry-potter-api-prd)")
@click.option('--dependency', '-d', '_dependency', type=str, multiple=True)
def dependency_set(application, _dependency):
    """Set application's build dependencies."""

    app_info = _parse_app_name(application=application)
    if not app_info:
        return

    data = app_info.copy()
    data['build']['os_dependencies'] = _dependency

    FlamingoAPI.update_app(app_id=app_info['id'], data=data)
    _success(f"Successfully updated {app_info['name']}-{app_info['environment']['name']}'s OS dependencies.")


@dependency.command("add")
@click.option('--application', '-a', type=str, required=True, help="Full application name (e.g. harry-potter-api-prd)")
@click.option('--dependency', '-d', '_dependency', type=str, multiple=True)
def dependency_add(application, _dependency):
    """Set application's build dependencies."""

    app_info = _parse_app_name(application=application)
    if not app_info:
        return

    data = app_info.copy()
    data['build']['os_dependencies'].extend(_dependency)

    FlamingoAPI.update_app(app_id=app_info['id'], data=data)
    _success(f"Successfully added more {app_info['name']}-{app_info['environment']['name']}'s OS dependencies.")


@dependency.command("remove")
@click.option('--application', '-a', type=str, required=True, help="Full application name (e.g. harry-potter-api-prd)")
@click.option('--dependency', '-d', '_dependency', type=str, multiple=True)
def dependency_remove(application, _dependency):
    """Set application's build dependencies."""

    app_info = _parse_app_name(application=application)
    if not app_info:
        return

    data = app_info.copy()
    existing_dependencies = data['build']['os_dependencies']

    missing = []
    for to_remove in _dependency:
        if to_remove not in existing_dependencies:
            missing.append(to_remove)
        else:
            existing_dependencies.remove(to_remove)

    data['build']['os_dependencies'] = existing_dependencies

    FlamingoAPI.update_app(app_id=app_info['id'], data=data)

    app_full_name = f"{app_info['name']}-{app_info['environment']['name']}"
    if len(missing) != len(_dependency):
        _success(f"Successfully removed {app_full_name}'s OS dependencies.")
    if missing:
        missing_str = ' | '.join(missing)
        _warn(f"Some OS dependencies ({missing_str}) were not found in {app_full_name}.")
