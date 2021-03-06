
from multiprocessing import Process, Pipe, Queue, Event, current_process
import traceback as tb
import logging
import pickle

from setproctitle import setproctitle


from .alsainterface import ALSAPlaybackSystem
from .alsainterface import normalize_output_device


def run_playback_process(device_config, stimuli_config, control_pipe, stop_event, status_queue):
    current_process().name = "treadmillio alsa playback"
    setproctitle(current_process().name)

    status_queue.put(1)
    try: 
        playback_system = ALSAPlaybackSystem(device_config, stimuli_config, control_pipe)
    except Exception as e:
        status_queue.put(-1)
        status_queue.close()
        raise e

    status_queue.put(2)  # Signal that we made to loop startup
    status_queue.close()
    try:
        # cProfile.runctx('playback_system.play()', globals(), locals(), "results.prof") # useful for debugging
        logging.info('Starting ALSA playback loop')
        playback_system.play(stop_event)
    except KeyboardInterrupt:
        logging.debug('Caught KeyboardInterrupt in ALSA playback process')
        playback_system.running = False # I don't think this does anything
    except Exception as e:
        raise e
    
    logging.info('ALSA playback loop returned.')

class SoundStimulusController():
    def __init__(self, device_config, stimuli_config, verbose=0):

        self.valid = False
        # TODO: Handle pipes for multiple audio devices
        # TODO: Error check the YAML file before this to make sure
        #       that sound stimuli specify devices that are in the device list
        #       otherwise, the process will be exit without the main program
        #       realizing it.

        self._playback_process = None
        self._stop_event = Event()

        device_config = normalize_output_device(device_config)

        # Start the ALSA playback and record processes.
        #  - ALSA playback will also load all the sound files!
        _startup_queue = Queue()
        _playback_read_pipe, self.alsa_playback_pipe = Pipe()  # we'll write to p_master from _this_ process and the ALSA process will read from _playback_read_pipe
        self._playback_process = Process(target=run_playback_process, 
                                         args=(device_config, stimuli_config,
                                                _playback_read_pipe, self._stop_event,
                                                _startup_queue))
        self._playback_process.daemon = True
        self._playback_process.start()     # Launch the sound process

        status = _startup_queue.get()
        while(status < 2):
            if (status < 0): # error in launching the playback process!
                _startup_queue.close()
                self._playback_process.join()
                raise(RuntimeError("An error occured in starting the ALSA playback process/object."))
            status = _startup_queue.get()

    def change_gain(self, stim_key, gain):
        if self.alsa_playback_pipe:
            self.alsa_playback_pipe.send_bytes(pickle.dumps({stim_key: gain}))


    def send_stop_event(self):
        logging.info('Raising stop event for ALSA process.')
        self._stop_event.set()

    def __del__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type:
            logging.ERROR('SoundStimulController: exiting because of exception <{}>'.format(
                exc_type.__name__))
            # tb.print_tb(exc_traceback)

        self._stop_event.set()
        logging.info('SoundStimulController waiting for ALSA processes to join. TODO: Handle other than KeyboardInterrupt!')
        # TODO: Do we need to differentiate different signals? If it's not KeyboardInterrupt, we need to tell it to stop:
        #self.alsa_playback_pipe.send_bytes(pickle.dumps({'StopMessage': True}))

        if self._playback_process:
            self._playback_process.join()
