# treadmilio_sound_server

Runs on a remote device with a soundcard output to enable the [TreamdillIO
system](https://github.com/kemerelab/TreadmillIO)
to control the playback of sound on network-connected remotes. The YAML configuration of the  main 
TreadmillIO process needs to know the network name and ALSA configuration of this system.
See the `network_sound_unit_test.yaml` example config file for formatting hints.
