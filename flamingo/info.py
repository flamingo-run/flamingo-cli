from flamingo.main import cli
from flamingo.api import FlamingoAPI
from flamingo.tools import _describe


@cli.command("info")
def info():
    """Information about the CLI."""

    _info = FlamingoAPI.info()
    _describe([
        ('EMAIL', _info['email']),
        ('ENDPOINT', _info['endpoint']),
    ])
