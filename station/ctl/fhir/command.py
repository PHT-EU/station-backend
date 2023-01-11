import click

from station.ctl.fhir import manage
from station.ctl.fhir.setup import setup_cli


@click.command(help="Manage FHIR servers associated with the station.")
@click.option("-c", "--command",
              help="The command to execute",
              type=click.Choice(["setup", "start", "stop", "list", "remove"]),
              required=True)
@click.option("-n", "--name", help="The name of the server to run the command against")
@click.pass_context
def fhir(ctx, command, name):
    if command == "setup":
        setup_cli(ctx, name)
    elif command == "start":
        manage.start_server(name)
    elif command == "stop":
        manage.stop_server(name)
    elif command == "remove":
        manage.remove_server(name)
    elif command == "list":
        click.echo("list")
