import click

from flamingo.main import cli
from flamingo.api import FlamingoAPI, _parse_app_name
from flamingo.tools import _success, _bold


@cli.group()
def env():
    """Manages service's environment variables."""


@env.command("get")
@click.option('--application', '-a', type=str, required=True, help="Full application name (e.g. harry-potter-api-prd)")
def env_get(application):
    """List application's environment variables."""

    app_info = _parse_app_name(application=application)
    if not app_info:
        return

    user_envs = []
    implicit_envs = []
    shared_envs = []
    for env_info in FlamingoAPI.list_envs(app_id=app_info['id']):
        key, value = env_info['key'], env_info['value']

        if env_info['source'] == 'user':
            user_envs.append(f"{key}={value}")
        elif env_info['source'] == 'shared':
            shared_envs.append(f"{key}={value}")
        else:
            implicit_envs.append(f"{key}={value}")

    click.echo(_bold("\nEnvironment Variables provided by user"))
    for user_env in sorted(user_envs):
        click.echo(user_env)

    if not user_envs:
        click.echo("--NONE--")

    click.echo(_bold("\nEnvironment Variables inherited from Env/Buildpack"))
    for shared_env in sorted(shared_envs):
        click.echo(shared_env)

    if not shared_envs:
        click.echo("--NONE--")

    click.echo(_bold("\nEnvironment Variables generated by Flamingo"))
    for implicit_env in sorted(implicit_envs):
        click.echo(implicit_env)

    if not implicit_envs:
        click.echo("--NONE--")


@env.command("set")
@click.option('--application', '-a', type=str, required=True, help="Full application name (e.g. harry-potter-api-prd)")
@click.option('--env', '-e', 'env_', type=str, multiple=True)
def env_set(application, env_):
    """Add application's environment variables."""

    app_info = _parse_app_name(application=application)
    if not app_info:
        return

    key_values = {}
    for env_var in env_:
        key, value = env_var.split('=', 1)
        key_values[key] = value

    FlamingoAPI.set_envs(app_id=app_info['id'], key_values=key_values)
    _success(f"Successfully added {len(env_)} env vars to {app_info['name']}-{app_info['environment']['name']}.")


@env.command("unset")
@click.option('--application', '-a', type=str, required=True, help="Full application name (e.g. harry-potter-api-prd)")
@click.option('--env', '-e', 'env_', type=str, multiple=True)
def env_unset(application, env_):
    """Remove application's environment variables."""

    app_info = _parse_app_name(application=application)
    if not app_info:
        return

    FlamingoAPI.unset_envs(app_id=app_info['id'], keys=env_)
    _success(f"Successfully removed {len(env_)} env vars from {app_info['name']}-{app_info['environment']['name']}.")
