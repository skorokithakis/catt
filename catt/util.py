import click


def warning(msg):
    click.secho("Warning: ", fg="red", nl=False, err=True)
    click.echo(msg, err=True)
