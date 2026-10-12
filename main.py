import functools
from typing import Callable

import click
from numpy import common_type

from src.gen import Gen
from src.split import Split
from src.splice import Splice, NO_SILENCE
from src.envelope import random_envs_to_file

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


def common_options(func:Callable) -> Callable:
    """
    adds options shared by several commands:
    `-W --overwrite` checks whether or not you can overwrite output data.
    `-o --out` defines an output path for the data
    `-l --length` defines the length of output track(s)
    """
    @click.option(
        '-W', "--overwrite",
        type=click.BOOL,
        is_flag=True,
        default=False,
        help="overwrite contents of output. if not used, will raise an error if the output dir or file exists (default=False)"
    )
    @click.option(
        "-o", "--outpath",
        type=click.STRING,
        required=True,
        help="path to the output file or directory"
    )
    @click.option(
        "-l", "--length",
        type=click.FLOAT,
        required=True,
        help="length of output track(s) in seconds"
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def common_options_arr(func: Callable) -> Callable:
    """
    add common options for commands that generate an array of tracks (`gen`, `split`)
    - `-n --nchunks` defines the number of chunks to generate
    - `-d --dev` defines a standard deviation from length, in seconds
    """
    @click.option(
        "-d", "--dev",
        type=click.FLOAT,
        default=0,
        help="length of standard deviation, in seconds (defaults to 0)"
    )
    @click.option(
        "-n", "--nchunks",
        type=click.INT,
        help="number of samples to generate (if None, tracklength / length)"
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


def nchannel_options(func: Callable) -> Callable:
    @click.option(
        "-c", "--nchannels",
        type=click.Choice([1,2]),
        default=None,
        help="number of channels in output track(s) (1=mono, 2=stereo)"
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper


@click.group()
def cli():
    """
    command line interface for aura
    """


@cli.command()
@click.argument(
    "n_env",
    type=click.INT,
    required=True
)
@common_options
def envelope(
    n_env: int,
    outpath: str,
    overwrite: bool
):
    """
    generate `n_env` random envelopes and write them to `outpath`
    """
    random_envs_to_file(n_env, outpath, overwrite)


@cli.command()
@click.argument(
    "trackpath",
    type=click.STRING,
    required=True
)
@common_options_arr
@common_options
@nchannel_options
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
@click.argument(
    "trackspath",
    type=click.STRING,
    required=True,
)
@click.option(
    "-i", '--nimpulses',
    type=INT_OR_STR,
    required=True,
    default= NO_SILENCE,
    help="number of impulses per minute (an impulse is a trigger to add a chunk to the output track). either '<int>' (use a defined number of impulses) or 'no-silence' (fill the track with chunks until the length is over)"
)
@click.option(
    "-e", "--envelope",
    type=click.STRING,
    default=None,
    help="evelope(s) to process the chunks. accepted value are 'random' (to use randomly generated envelopes), '<path to envelope file>' (to use user-defined envelopes). If not provided, no envelope will be applied to the chunks."
)
@click.option(
    "-w", "--width",
    type=click.FloatRange(0,1),
    default=1.,
    help=r"streo width (no effect if 'nchannels==1'): if '1', tracks will be panned to 100% left/right, if '0.3', tracks will be panned to 30% of left/right"
)
@click.option(
    "-L", "--nlines",
    type=click.INT,
    default=2,
    help="number of 'lines', or pan-positions on which to place sound in stereo. if nlines=10, sound will be distributed accross 10 lines panned evenly from L to R (-1,-0.9,...,0.9,1). output will be converted back to stereo. useless if nchannels==1"
)
@click.option(
    "-p", "--pattern",
    type=click.STRING,
    help="path to a pattern-track that will be added repeatedly to the output."
)
@click.option(
    "-r", "--repeat",
    type=click.FLOAT,
    default=10,
    help="interval in seconds at which to repeat 'pattern'. must be shorter than 'pattern''s length"
)
@click.option(
    "--crackle",
    type=click.BOOL,
    is_flag=True,
    default=False,
    help="add extra clipping'n'crackling to the generated track (done by messing with type conversion when applying width)"
)
@click.option(
    "-v", "--visualize",
    type=click.BOOL,
    is_flag=True,
    default=False,
    help="display a visualization of the generated track"
)
@common_options
@nchannel_options
def splice(
    trackspath,
    outpath,
    length,
    nimpulses,
    envelope,
    nchannels,
    width,
    nlines,
    pattern,
    repeat,
    overwrite,
    crackle,
    visualize
):
    """
    command line interface for aura.splice: generate a track of `length` seconds by playing chunks in `trackspath` randomly `nimpulses` times and write it to `outpath`. it is possible to apply envelopes to the tracks, place them in stereo space, add a repeating pattern...
    """
    Splice(
        trackspath=trackspath,
        outpath=outpath,
        length=length,
        nimpulses=nimpulses,
        envelope=envelope,
        nchannels=nchannels,
        width=width,
        nlines=nlines,
        pattern=pattern,
        repeat=repeat,
        overwrite=overwrite,
        crackle=crackle,
        visualize=visualize
    ).pipeline()


@cli.command
@click.argument(
    "soundtype",
    type=click.Choice(Gen.allowed_soundtypes),
)
@click.option(
    "-f", "--freq",
    type=click.STRING,
    help="frequency or frequency range of sound. must match 'd(:d)?', with 'd' a positive integer"
)
@click.option(
    "-v", "--visualize",
    type=click.BOOL,
    is_flag=True,
    default=False,
    help="display a visualization of the generated track"
)
@click.option(
    "-S", "--sine-to-noise",
    type=click.FLOAT,
    help="if soundtype is 'random', ratio of sine chunks as compared to noise chunks. in range 0..1 (0=generate no sine, 1=generate only sines, 0.5=generate as many sines as noises)"
)
@common_options_arr
@common_options
def gen(
    soundtype,
    nchunks,
    length,
    freq,
    outpath,
    sine_to_noise,
    dev=0,
    overwrite=False,
    visualize=False,
):
    Gen(
        soundtype=soundtype,
        nchunks=nchunks,
        length=length,
        freq=freq,
        outpath=outpath,
        dev=dev,
        sine_to_noise=sine_to_noise,
        overwrite=overwrite,
        visualize=visualize
    ).pipeline()


if __name__ == "__main__":
    cli()