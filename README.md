# aura

`aura` is an (au)dio (ra)ndomizer and splitter. what it does in a nutshell is:

- `split`: take an input track and split it into randomly selected chunks
- `splice`: take an array of input chunks and fill a track with them in stereo space
- `envelope`: generate and write envelopes that can be used in `splice`

`aura` provides simple tools tailored to do exactly what i want them to do. `aura` is made for (harsh) noise (wall) and weird sounds. to hear exemples, check out [this](./data/splice_500i_60s.wav).

--- 

## about

the idea for `aura` dates back to 6-7 years when i was obsessively into harsh noise wall and wanted to make walls by randomly splitting and rearranging source sounds. like a lot of my noise ideas, [Sven K](https://svenkay.com/)'s work was an inspiration. in particular:
- the magnificent [Malheurr](https://weworshipthevoid.bandcamp.com/album/v15d-purge-fluids-causerie-sur-le-temps) which has always sounded like randomized black metal to me
- [D. Kreitzer & J. Erdős](https://weworshipthevoid.bandcamp.com/album/v16d-organised-sound-infinitary-combinatorics-of-a-finite-set) which literally asks for an aura-like tool to play the album.

since those 6-7 years, i also started coding quite a bit, and wanted both to get back into "fun" (non-professionnal) and "creative" (small scale) coding. i also wanted to learn more about python sound processing (which is too mathy for me), numpy (which i doubt i learned anything), OOP, CLI UI and designing a library.

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

an input track example can be found [here](https://github.com/paulhectork/aura/blob/main/data/inputs/hn_1min_mono.wav).

### `split`

split a track randonly into chunks of predefined length, and save those chunks to an array

outputted chunks can be found [here](https://github.com/paulhectork/aura/tree/main/data/chunks).

```bash
uv run main.py split [OPTIONS] ./path/to/input/track
```

```
  command line interface for aura.split: generate `nchunks` random chunks of
  `length` seconds (+/- `dev` standard deviation) from track `trackpath` and
  write them to `output`

Options:
  -o, --outpath TEXT        path to the output file or directory  [required]
  -l, --length FLOAT RANGE  length of output chunks (in seconds)  [x>=0;
                            required]
  -d, --dev FLOAT           length of standard deviation, in seconds (defaults
                            to 0)
  -n, --nchunks INTEGER     number of samples to generate (if None,
                            tracklength / length)
  -c, --nchannels [1|2]     number of channels in output tracks (1=mono,
                            2=stereo). if None, same as number of channels in
                            input track
  -W, --overwrite           overwrite contents of output. if not used, will
                            raise an error if the output dir or file exists
                            (default=False)
```

### `splice`

`splice` *splices* -- that is to say, collates -- chunks in a single track by randomly positionning them in time and in stereo space.

a track made out of the above chunks can be found [here](https://github.com/paulhectork/aura/blob/main/data/splice_500i_60s.wav).

```bash
uv run main.py splice [OPTIONS] ./path/to/chunks/directory
```

```
  command line interface for aura.splice: generate a track of `length` seconds
  by playing chunks in `trackspath` randomly `nimpulses` times and write it to
  `outpath`. it is possible to apply envelopes to the tracks, place them in
  stereo space, add a repeating pattern...

Options:
  -l, --length INTEGER        length of output track in seconds  [required]
  -i, --nimpulses INT OR STR  number of impulses per minute (an impulse is a
                              trigger to add a chunk to the output track).
                              either '<int>' (use a defined number of
                              impulses) or 'no-silence' (fill the track with
                              chunks until the length is over)  [required]
  -e, --envelope TEXT         evelope(s) to process the chunks. accepted value
                              are 'random' (to use randomly generated
                              envelopes), '<path to envelope file>' (to use
                              user-defined envelopes). If not provided, no
                              envelope will be applied to the chunks.
  -c, --nchannels [1|2]       number of channels in the output track (1=mono,
                              2=stereo)
  -w, --width FLOAT RANGE     streo width (no effect if 'nchannels==1'): if
                              '1', tracks will be panned to 100% left/right,
                              if '0.3', tracks will be panned to 30% of
                              left/right  [0<=x<=1]
  -L, --lines INTEGER         number of 'lines', or pan-positions on which to
                              place sound in stereo. if lines=10, sound will
                              be distributed accross 10 lines panned evenly
                              from L to R (-1,-0.9,...,0.9,1). output will be
                              converted back to stereo. useless if
                              nchannels==1
  -p, --pattern TEXT          path to a pattern-track that will be added
                              repeatedly to the output.
  -r, --repeat FLOAT          interval in seconds at which to repeat
                              'pattern'. must be shorter than 'pattern''s
                              length
  --crackle                   add extra clipping'n'crackling to the generated
                              track (done by messing with type conversion when
                              applying width)
  -W, --overwrite             overwrite contents of output. if not used, will
                              raise an error if the output dir or file exists
                              (default=False)
  -o, --outpath TEXT          path to the output file or directory  [required]
  --help                      Show this message and exit.

```

### `envelope`

`envelope` is very simple: it generates and writes to file a certain amount of ADSR sound envelopes.

```bash
uv run main.py <n>
```

some envelopes can be found [here](https://github.com/paulhectork/aura/blob/main/data/envs.txt).

```
  generate `n` random envelopes and write them to `outpath`

Options:
  -W, --overwrite     overwrite contents of output. if not used, will raise an
                      error if the output dir or file exists (default=False)
  -o, --outpath TEXT  path to the output file or directory  [required]
```

---

## license

GNU GPL v3
