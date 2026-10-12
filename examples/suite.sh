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

# gen
$UV gen sine --length 1 --nchunks 1000 -o /tmp/gen/ -W -f 100:5000 -d 0.9

# gen: random noise
$UV gen random-noise --length 1 --dev 0.2 --nchunks 1000 -o /tmp/gen/ -W

# gen: random noise + sine
$UV gen random --length 0.5 --dev 0.2 --nchunks 1000 -o /tmp/gen/ -W --freq 2000:10000 --sine-to-noise 0.05

# splice with gen
$UV splice ./data_dev/gen_sine/ -o /tmp/splice_sine.wav --length 60 --nimpulses 60 --width 1 --nlines 5 --nchannels 2 -W

