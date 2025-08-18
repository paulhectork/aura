import click

from split import Split


@click.group()
def cli():
    """
    command line interface for aura
    """


@cli.command()
def envelope():
    """
    command line interface for aura.envelope
    """


@cli.command()
@click.option(
    "-t", "--trackname",
    type=click.STRING,
    required=True,
    help="path of the input track"
)
@click.option(
    "-o", "--output",
    type=click.STRING,
    required=True,
    help="path of the output folder"
)
@click.option(
    "-l", "--length",
    type=click.FloatRange(min=0),
    required=True,
    help="length of output chunks (in seconds)"
)
@click.option(
    "-d", "--dev",
    type=click.FLOAT,
    default=0,
    help="length standard deviation, in seconds (defaults to 0)"
)
@click.option(
    "-n", "--nchunks",
    type=click.INT,
    help="number of samples to generate (if None, tracklength / length)"
)
@click.option(
    "-c", "--nchannels",
    type=click.Choice([1,2]),
    default=None,
    help="number of channels in output tracks (1=mono, 2=stereo). if None, same as number of channels in input track"
)
def split(
    trackname,
    output,
    length,
    dev,
    nchunks,
    nchannels
):
    """
    command line interface for aura.split: generate `nchunks` random chunks of `length` seconds (+/- `dev` standard deviation) from track `trackname` and write them to `output`
    """
    Split(
        trackname=trackname,
        output=output,
        length=length,
        dev=dev,
        nchunks=nchunks,
        nchannels=nchannels
    ).pipeline()


@cli.command()
def splice():
    """
    command line interface for aura.splice
    """


if __name__ == "__main__":
    cli()