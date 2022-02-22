import os

import click
from tabulate import tabulate

from flamingo.main import cli
from flamingo.api import FlamingoAPI, _parse_buildpack_name
from flamingo.tools import TABLE_STYLE, _describe, _block, _success, run, _err


@cli.group()
def buildpack():
    """Manages build packs"""


@buildpack.command("list")
def buildpack_list():
    """List buildpacks."""
    bp_info = {}
    for bp in FlamingoAPI.list_buildpacks():
        name = bp['name']
        bp_info[f"{name}"] = [name, bp['runtime'], bp['target']]

    sorted_info = dict(sorted(bp_info.items())).values()
    click.echo(tabulate(sorted_info, headers=["Name", "Runtime", "Target"], tablefmt=TABLE_STYLE))


@buildpack.command("info")
@click.option('--name', '-n', type=str, required=True, help="Build pack name")
def buildpack_info(name):
    """Detail buildpack."""

    bp_info = _parse_buildpack_name(name=name)
    if not bp_info:
        return

    _describe([
        ('NAME', bp_info['name']),
        ('RUNTIME', bp_info['runtime']),
        ('TARGET', bp_info['target']),

    ])

    build_commands = bp_info['post_build_commands']
    _block(header='POST BUILD COMMANDS', content='\n'.join(build_commands))

    build_args = bp_info['build_args']
    db_info = [
        f"{key}: {value}"
        for key, value in build_args.items()
    ]
    _block(header='BUILD ARGS', content='\n'.join(db_info))


@buildpack.command("download")
@click.option('--name', '-n', type=str, required=True, help="Build pack name")
def buildpack_download(name):
    """Set application's build dependencies."""

    _buildpack_info = _parse_buildpack_name(name=name)
    if not _buildpack_info:
        return

    destination = os.getcwd()
    _, err = run('gsutil', 'cp', _buildpack_info['dockerfile_url'], destination)

    if 'completed' in err:
        _success(f"Successfully downloaded {name}'s files to {destination}")
    else:
        _err(err)
