# split with -n
$UV split "$ROOT_DIR/data/inputs/hn_1min_mono.wav" -o /tmp/chunks -n 1000 --length 1 --dev 0.9 --nchannels 1 -W

# split without -n (nosilence mode)
$UV split "$ROOT_DIR/data/inputs/hn_1min_mono.wav" -o /tmp/chunks --length 1 --dev 0.9 --nchannels 1 -W

# split with --nchannels 2 (stereo)
$UV split "$ROOT_DIR/data/inputs/hn_1min_mono.wav" -o /tmp/chunks --length 1 --nchannels 2 --dev 0.9 --nchannels 1 -W

# splice
$UV splice /tmp/chunks --length 60 --nchannels 2 --nimpulses 500 --width 1 --envelope random --outpath /tmp/test.wav -W

# splice without --nchannels (taken from input chunks)
$UV splice /tmp/chunks --length 60 --nimpulses 500 --width 1 --envelope random --outpath /tmp/test.wav -W

# splice with --nlines
$UV splice /tmp/chunks --length 60 --nimpulses 500 --nlines 10 --width 1 --envelope random --outpath /tmp/test.wav -W
