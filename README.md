# treadmilio_sound_server

Runs on a remote device with a soundcard output to enable the [TreamdillIO
system](https://github.com/kemerelab/TreadmillIO)
to control the playback of sound on network-connected remotes. The YAML configuration of the  main 
TreadmillIO process needs to know the network name and ALSA configuration of this system.
See the `network_sound_unit_test.yaml` example config file for formatting hints.

### Dependencies
The package has fewer dependencies than the main TreadmillIO system. It depends on
  + `zmq`
  + `numpy` (used for buffers)
  + `setproctitle` (used to aid in process tracking)
  + `pyalsaaudio` (which in turns requires `libasound` for alsa support)

With the exception of `libasound`, these an all be installed by `pip`, though
the `zmq` and `numpy` packages are also available as `python3-zmq` and `python3-numpy`
debian packages. One goal of this package is to make installation on a Raspberry Pi
as simple as possible. With a [HiFiBerry MiniAMP](https://www.hifiberry.com/docs/data-sheets/datasheet-miniamp/),
the Pi 3 and Pi 4 can playback stereo 96 kHz or even 192 kHz sampled audio well
above 20 kHz, which is valuable for stimuli for animals such as mice with ultrasonic
hearing. **Note that the code is not optimized for low latency!** This network sound client
is intended to construct soundscapes in a documented, repeatable, configurable way.

### Installation

The package can be installed directly from Github using: 
```  
/usr/bin/pip3 install git+https://github.com/kemerelab/treadmillio_sound_server.git
```

To run as a system service, create a file like `/lib/systemd/system/treadmillio_sound_server_service.service` that has the content
```
[Unit]
Description=TreadmillIO_Sound_Serviec
After=network.target

[Service]
ExecStart=/home/kemerelab/.local/bin/treadmillio-start-sound-server
Restart=always
User=kemerelab

[Install]
WantedBy=multi-user.target
```
Then run `sudo systemctl enable treadmillio_sound_server_service.service`. For testing, you can
instead run `sudo systemctl start treadmillio_sound_server_service.service`.
