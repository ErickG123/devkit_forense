import typer

from cli.commands.network import network_app
from cli.commands.browser import browser_app
from cli.commands.email import email_app
from cli.commands.utils import utils_app
from cli.commands.describe import describe_app

app = typer.Typer()

app.add_typer(network_app, name="network")
app.add_typer(browser_app, name="browser")
app.add_typer(email_app, name="email")
app.add_typer(utils_app, name="utils")
app.add_typer(describe_app)

if __name__ == "__main__":
    app()
