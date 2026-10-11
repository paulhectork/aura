#!/usr/bin/env bash

# a list of examples that can also function as a micro-test suite.
# all commands below should function without an error.

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
ROOT_DIR="$SCRIPT_DIR"/..

UV="uv run --directory=${ROOT_DIR} main.py"

# split with `-n` defined
$UV split "$ROOT_DIR"/data/inputs/hn_1min_mono.wav -o /tmp/chunks -n 1000 --length 1 --dev 0.9 --nchannels 1 -W

# split without `-n` (nosilence mode)
$UV split "$ROOT_DIR"/data/inputs/hn_1min_mono.wav -o /tmp/chunks --length 1 --dev 0.9 --nchannels 1 -W

# split with `--nchannels 2` (stereo)
$UV split "$ROOT_DIR"/data/inputs/hn_1min_mono.wav -o /tmp/chunks --length 1 --nchannels 2 --dev 0.9 --nchannels 1 -W

# splice
$UV splice /tmp/chunks --length 60 --nchannels 2 --nimpulses 500 --width 1 --envelope random --outpath /tmp/test.wav -W

# splice without --nchannels (=> nchannels is taken from # of channels in input chunks)
$UV splice /tmp/chunks --length 60 --nimpulses 500 --width 1 --envelope random --outpath /tmp/test.wav -W

# splice with --nlines
$UV splice /tmp/chunks --length 60 --nimpulses 500 --nlines 10 --width 1 --envelope random --outpath /tmp/test.wav -W
