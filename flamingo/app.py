import click
from tabulate import tabulate

from flamingo.main import cli
from flamingo.api import FlamingoAPI, _parse_app_name
from flamingo.tools import TABLE_STYLE, _describe, _block, _success


@cli.group()
def app():
    """Manages services."""


@app.command("list")
def app_list():
    """List applications."""
    app_info = {}
    for app in FlamingoAPI.list_apps():
        name, env, endpoint = app['name'], app['environment']['name'], app['endpoint']
        app_info[f"{name}-{env}"] = [name, env, endpoint]

    sorted_info = dict(sorted(app_info.items())).values()
    click.echo(tabulate(sorted_info, headers=["Name", "Environment", "Endpoint"], tablefmt=TABLE_STYLE))


@app.command("info")
@click.option('--application', '-a', type=str, required=True, help="Full application name (e.g. harry-potter-api-prd)")
def app_info(application):
    """Detail application."""

    app_info = _parse_app_name(application=application)
    if not app_info:
        return

    _describe([
        ('NAME', app_info['name']),
        ('ENVIRONMENT', app_info['environment']['name']),
        ('REGION', app_info['region']),
        ('ENDPOINT', app_info['endpoint']),
        ('REPOSITORY', app_info['repository']['name']),
        ('ACCESS', "Private" if app_info['build']['is_authenticated'] else "Public"),
    ])

    build = app_info['build']
    build_info = [
        f"Build Pack: {build['build_pack_name']}",
        f"Deploy Branch: {build['deploy_branch']}",
        f"Deploy Tag: {build['deploy_tag']}",
        f"OS Dependencies: {' '.join(build['os_dependencies'])}",
        f"RAM: {build['memory']}MB",
        f"CPU: {build['cpu']} cores",
        f"Auto-scale: {build['min_instances']} - {build['max_instances']}",
        f"Timeout: {build['timeout']}s",
        f"Project: {build['project']['id']}",
    ]
    _block(header='BUILD', content='\n'.join(build_info))

    database = app_info['database']
    db_info = [
        f"Instance: {database['instance']}",
        f"Name: {database['name']}",
        f"User: {database['user']}",
        f"Engine: {database['version']}",
        f"Region: {database['region']}",
        f"Project: {database['project']['id']}",
        f"Env Var: {database['env_var']}",
    ]
    _block(header='DATABASE', content='\n'.join(db_info))

    bucket = app_info['bucket']
    bucket_info = [
        f"Name: {bucket['name']}",
        f"Region: {bucket['region']}",
        f"Project: {bucket['project']['id']}",
        f"Env Var: {bucket['env_var']}",
    ]
    _block(header='BUCKET', content='\n'.join(bucket_info))


@app.command("apply")
@click.option('--application', '-a', type=str, required=True, help="Full application name (e.g. harry-potter-api-prd)")
def app_apply(application):
    """Apply application's configuration."""

    app_info = _parse_app_name(application=application)
    if not app_info:
        return

    data = FlamingoAPI.apply_app(app_id=app_info['id'])
    _success(f"Successfully applied {app_info['name']}-{app_info['environment']['name']}'s configuration.")
    click.echo(f"Cloud Build trigger {data['trigger_id']} has been updated")
