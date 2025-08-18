import click

from split import Split
from splice import Splice
from utils.constants import NO_SILENCE

class IntOrStrType(click.ParamType):
    name = "int or str"

    def convert(self, value, param, ctx):
        try:
            return int(value)
        except ValueError:
            try:
                return str(value)
            except ValueError:
                self.fail("{value!r} could not be converted to 'int' or 'str'", param, ctx)
INT_OR_STR = IntOrStrType()

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
    "-t", "--trackpath",
    type=click.STRING,
    required=True,
    help="path of the input track"
)
@click.option(
    "-o", "--outpath",
    type=click.STRING,
    required=True,
    help="path to the output folder"
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
@click.option(
    '-w', "--overwrite",
    type=click.BOOL,
    is_flag=True,
    default=False,
    help="overwrite contents of output directory. if not used, will raise an error if the output dir exists"
)
def split(
    trackpath,
    outpath,
    length,
    dev,
    nchunks,
    nchannels,
    overwrite
):
    """
    command line interface for aura.split: generate `nchunks` random chunks of `length` seconds (+/- `dev` standard deviation) from track `trackpath` and write them to `output`
    """
    Split(
        trackpath=trackpath,
        outpath=outpath,
        length=length,
        dev=dev,
        nchunks=nchunks,
        nchannels=nchannels,
        overwrite=overwrite
    ).pipeline()


@cli.command()
@click.option(
    "-t", "--trackspath",
    type=click.STRING,
    required=True,
    help="path to input directory. all `.wav` files in the directory (non-recrusvively) will be loaded as chunks to be used in the final track"
)
@click.option(
    "-o", "--outpath",
    type=click.STRING,
    required=True,
    help="path to the output file"
)
@click.option(
    "-l", "--length",
    type=click.INT,
    required=True,
    help="length of output track in seconds"
)
@click.option(
    "-i", '--nimpulses',
    type=INT_OR_STR,
    required=True,
    default= NO_SILENCE,
    help="number of impulses (an impulse is a trigger to add a chunk to the output track). either '<int>' (use a defined number of impulses) or 'no-silence' (fill the track with chunks until the length is over)"
)
@click.option(
    "-e", "--envelope",
    type=click.STRING,
    default=None,
    help="evelope(s) to process the chunks. accepted value are 'random' (to use randomly generated envelopes), '<path to envelope file>' (to use user-defined envelopes)"
)
@click.option(
    "-c", "--nchannels",
    type=click.Choice([1,2]),
    default=2,
    help="number of channels in the output track (1=mono, 2=stereo)"
)
@click.option(
    "-w", "--width",
    type=click.FloatRange(0,1),
    default=1,
    help=r"streo width (no effect if 'nchannels==1'): if '1', tracks will be panned to 100% left/right, if '0.3', tracks will be panned to 30% of left/right"
)
@click.option(
    "-m", "--mode",
    type=click.Choice([2,3,"range"]),
    default=2,
    help="how to place the chunks in stereo space (no effect if 'nchannels==1'). if 'mode=2', chunks will be hard-panned (placed either on the left or right channel) ; if 'mode==3', chunks will be placed in left, right and center of stereo space ; if 'range', chunks will be placed randomly in the stereo space."
)
@click.option(
    "-p", "--pattern",
    type=click.STRING,
    help="path to a pattern-track that will be added repeatedly to the output."
)
@click.option(
    "-r", "--repeat",
    type=click.FLOAT,
    help="interval in seconds at which to repeat 'pattern'. must be shorter than 'pattern''s length"
)
def splice(
    trackspath,
    outpath,
    length,
    nimpulses,
    envelope,
    nchannels,
    width,
    mode,
    pattern,
    repeat
):
    """
    command line interface for aura.splice: generate a track from
    """
    Splice(
        trackspath=trackspath,
        outpath=outpath,
        length=length,
        nimpulses=nimpulses,
        envelope=envelope,
        nchannels=nchannels,
        width=width,
        mode=mode,
        pattern=pattern,
        repeat=repeat
    )


if __name__ == "__main__":
    cli()