# aura

`aura` is an (au)dio (ra)ndomizer and splitter. what it does in a nutshell is:

- `split`: take an input track and split it into randomly selected chunks
- `splice`: take an array of input chunks and fill a track with them in stereo space
- `envelope`: generate and write envelopes that can be used in `splice`

`aura` provides simple tools tailored to do exactly what i want them to do. `aura` is made for (harsh) noise (wall) and weird sounds. to hear exemples, check out [this](./data/splice_500i_60s.wav).

---

## TODO

`aura` is functionnal but here are upcoming functionnalities i want to add:

- `splice`: implement `--pattern` and `--pattern-repeat` (define a chunk that will be appended to the output track at a regular interval)
- `splice`: add `chaos`, a chaos factor in range 0..1 that would make things weirder: i.e., randomly reverse tracks, concentrate them in certain time intervals...

--- 

## about

the idea for `aura` dates back to 6-7 years when i was obsessively into harsh noise wall and wanted to make walls by randomly splitting and rearranging source sounds. like a lot of my noise ideas, [Sven K](https://svenkay.com/)'s work was an inspiration. in particular:
- the magnificent [Malheurr](https://weworshipthevoid.bandcamp.com/album/v15d-purge-fluids-causerie-sur-le-temps) which has always sounded like randomized black metal to me
- [D. Kreitzer & J. Erdős](https://weworshipthevoid.bandcamp.com/album/v16d-organised-sound-infinitary-combinatorics-of-a-finite-set) which literally asks for an aura-like tool to play the album.

since those 6-7 years, i also started coding quite a bit, and wanted both to get back into "fun" (non-professionnal) and "creative" (small scale) coding. i also wanted to learn more about python sound processing (which is too mathy for me), numpy (which i doubt i learned anything), oop, cli ui and library design.

---

## install

i use `uv`, so commands describe `uv` usage, but you can use the good old pip and python tools as well :)

```sh
git clone git@github.com:paulhectork/aura.git
cd aura
uv sync
```

--- 

## usage

`aura` is meant to be used as a command line interface, though it could be easily used as a Python library as well. all parameters are given through CLI arguments and options.

an input track example can be found [here](https://github.com/paulhectork/aura/blob/main/data/inputs/hn_1min_mono.wav).

### `split`

split a track randonly into chunks of predefined length, and save those chunks to an array

outputted chunks can be found [here](https://github.com/paulhectork/aura/tree/main/data/chunks).

```bash
# usage
uv run main.py split [OPTIONS] <./path/to/input/track>

# a full command looks like this
uv run main.py split \
    </path/to/input/track> \
    --outpath   </path/to/output/directory> \
    --length    <float: length of output chunks in seconds> \
    --dev       <float: standard deviation from length in seconds> \
    --nchunks   <int: number of chunts to generate> \
    --nchannels <1|2: stereo or mono>

# view help for the full docs
uv run main.py split --help
```

### `splice`

`splice` *splices* -- that is to say, collates -- chunks in a single track by randomly positionning them in time and in stereo space.

a track made out of the above chunks can be found [here](https://github.com/paulhectork/aura/blob/main/data/splice_500i_60s.wav).

```bash
# basic usage
uv run main.py splice [OPTIONS] /path/to/chunks/directory

# a full command looks like this
uv run main.py splice \
    </path/to/chunk/directory> \
    --outpath   </path/to/output/file> \
    --length    <float: output length in seconds> \
    --nimpulses <int: number of impulses per minute (equivalent to BPM)> \
    --nchannels  <1|2: stereo or mono> \
    --lines     <int: number of pan positions on which to place sound> \
    --width     <float: stereo width, in range 0..1>
    --envelope  <"random" or path to envelope file: envelope to apply> \
    --crackle   <flag: add crackle through numpy dtype conversions>

# view help for the full docs
uv run main.py splice --helo
```

### `envelope`

`envelope` is very simple: it generates and writes to file a certain amount of ADSR sound envelopes.

some envelopes can be found [here](https://github.com/paulhectork/aura/blob/main/data/envs.txt).

```bash
# basic usage
uv run main.py envelope <n>

# full command example: generate 100 envelopes
uv run main.py envelope 100 -o </path/to/output/envelope/file.json>

# view help
uv run main.py envelope --help
```

---

## license

GNU GPL v3
