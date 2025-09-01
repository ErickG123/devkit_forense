import typer

from cli.commands.network import network_app
from cli.commands.browser import browser_app
from cli.commands.email import email_app
from cli.commands.utils import utils_app
from cli.commands.describe import describe_app

app = typer.Typer()

app.add_typer(network_app, name="network", help="Ferramentas para análise e operações em redes")
app.add_typer(browser_app, name="browser", help="Ferramentas para coleta e análise de dados de navegadores")
app.add_typer(email_app, name="email", help="Ferramentas para análise e manipulação de dados de e-mail")
app.add_typer(utils_app, name="utils", help="Funções utilitárias de apoio ao sistema")
app.add_typer(describe_app, name="describe", help="Explicações detalhadas sobre as funcionalidades disponíveis")

if __name__ == "__main__":
    app()
