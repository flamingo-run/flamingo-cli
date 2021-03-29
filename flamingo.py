import os
import subprocess
import sys

import click
import requests
from requests import HTTPError
from tabulate import tabulate


TABLE_STYLE = "fancy_grid"


@click.group()
@click.version_option()
def cli():
    """Welcome to Flamingo 🦩 CLI

    Command Line Interface for interacting with services
    managed by your Flamingo server

    You can start by checking your current setup, type:
    flamingo info
    """


@cli.command("info")
def info():
    """Information about the CLI."""

    info = FlamingoAPI.info()
    _describe([
        ('EMAIL', info['email']),
        ('ENDPOINT', info['endpoint']),
    ])


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
    for env_info in FlamingoAPI.list_envs(app_id=app_info['id']):
        key, value = env_info['key'], env_info['value']

        if env_info['source'] == 'user':
            user_envs.append(f"{key}={value}")
        else:
            implicit_envs.append(f"{key}={value}")

    click.echo(_bold("\nEnvironment Variables provided by user"))
    for user_env in sorted(user_envs):
        click.echo(user_env)

    click.echo(_bold("\nEnvironment Variables generated by Flamingo"))
    for implicit_env in sorted(implicit_envs):
        click.echo(implicit_env)


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


# UTILS

def run(*commands):
    sp = subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = sp.communicate()
    return out.decode(), err.decode()


def _parse_app_name(application):
    try:
        name, environment = application.rsplit('-', 1)
    except ValueError:
        _err(f"Application name must be in the format <name>-<env>, not {application}")
        return

    apps = FlamingoAPI.get_app(name=name, environment=environment)

    if len(apps) > 1:
        _err("Duplicated apps found!!")
        return

    if len(apps) == 0:
        _warn(f"No app named {name} in the environment {environment}")
        return

    return apps[0]


def _bold(txt):
    return click.style(txt, bold=True)


def _success(txt):
    click.echo(
        click.style(txt, fg='blue'),
    )


def _err(txt):
    click.echo(
        click.style(txt, fg='red'),
        err=True,
    )


def _warn(txt):
    click.echo(
        click.style(txt, fg='yellow'),
        err=True,
    )


def _describe(items):
    for key, value in items:
        click.echo(f"{_bold(key)}: {value}")


def _block(header, content):
    click.echo(tabulate([[content]], headers=[_bold(header)], tablefmt=TABLE_STYLE))


# API CLIENT

if 'FLAMINGO_URL' not in os.environ:
    sys.exit(f"Environment variable 'FLAMINGO_URL' must be set with the Flamingo server endpoint")


class FlamingoAPI:
    API = os.environ['FLAMINGO_URL']

    @classmethod
    def list_apps(cls):
        return cls._list(endpoint='/apps')

    @classmethod
    def get_app(cls, name, environment):
        apps = list(cls._list(endpoint='/apps', name=name, environment_name=environment))
        return apps

    @classmethod
    def update_app(cls, app_id, data):
        return cls._patch(endpoint=f'/apps/{app_id}', data=data)

    @classmethod
    def list_envs(cls, app_id):
        return cls._detail(endpoint=f'/apps/{app_id}/vars')['results']

    @classmethod
    def set_envs(cls, app_id, key_values):
        return cls._post(endpoint=f'/apps/{app_id}/vars', data=key_values)

    @classmethod
    def unset_envs(cls, app_id, keys):
        return cls._delete(endpoint=f'/apps/{app_id}/vars', data=keys)

    @classmethod
    def apply_app(cls, app_id):
        return cls._post(endpoint=f'/apps/{app_id}/apply')

    @classmethod
    def info(cls):
        out, err = run('gcloud', 'auth', 'list')

        email = None
        for row in out.splitlines():
            if row.startswith('*'):
                email = row.split(' ')[-1].strip()
                break

        return {
            'email': email,
            'endpoint': cls.API,
        }

    @classmethod
    def _headers(cls, url):
        stream = os.popen('gcloud auth print-identity-token')
        output = stream.read().strip()
        return {'Authorization': f"Bearer {output}"}

    @classmethod
    def _detail(cls, endpoint, **kwargs):
        url = f"{cls.API}{endpoint}"
        response = requests.get(url=url, params=kwargs, headers=cls._headers(url=url))
        response.raise_for_status()
        return response.json()

    @classmethod
    def _list(cls, endpoint, **kwargs):
        page = 1
        while True:
            try:
                results = cls._detail(endpoint=endpoint, page=page, **kwargs)['results']
                yield from results
                page += 1
            except HTTPError as e:
                if e.response.status_code == 404:
                    break
                raise

    @classmethod
    def _post(cls, endpoint, data=None):
        url = f"{cls.API}{endpoint}"
        response = requests.post(url=url, json=data, headers=cls._headers(url=url))
        response.raise_for_status()
        return response.json()

    @classmethod
    def _patch(cls, endpoint, data):
        url = f"{cls.API}{endpoint}"
        response = requests.patch(url=url, json=data, headers=cls._headers(url=url))
        response.raise_for_status()
        return response.json()

    @classmethod
    def _delete(cls, endpoint, data=None):
        url = f"{cls.API}{endpoint}"
        response = requests.delete(url=url, json=data, headers=cls._headers(url=url))
        response.raise_for_status()
        return response.json()
