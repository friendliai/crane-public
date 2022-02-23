import typer

app = typer.Typer()

@app.callback('example_plugin')
def check_cmd_group():
    """Example plugin."""

@app.command("first_command")
def _first_command():
    """Example command."""
