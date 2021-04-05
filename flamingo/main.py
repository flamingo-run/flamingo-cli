import click


@click.group()
@click.version_option()
def cli():
    """Welcome to Flamingo 🦩 CLI

    Command Line Interface for interacting with services
    managed by your Flamingo server

    You can start by checking your current setup, type:
    flamingo info
    """
