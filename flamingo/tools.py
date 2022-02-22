# UTILS
import subprocess

import click
from tabulate import tabulate


TABLE_STYLE = "fancy_grid"


def run(*commands):
    with subprocess.Popen(commands, stdout=subprocess.PIPE, stderr=subprocess.PIPE) as sp:
        out, err = sp.communicate()
        return out.decode(), err.decode()


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
