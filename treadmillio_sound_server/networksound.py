from contextlib import ExitStack
import zmq
import time
import pickle
import traceback as tb
import logging

from .soundstimulus import SoundStimulusController

class NetworkSoundInterface:
    printStatements = True
    IP_address_text = None # Will use to display IP address

    def __init__(self, context_manager=None):

        # ZMQ server connection for commands. 
        # We use a DEALER/REP architecture for reliability.
        command_socket_port = "7342"
        # Socket to talk to server
        context = zmq.Context()
        self.command_socket = context.socket(zmq.REP)
        logging.info('Binding port 7342 for commands.')
        self.command_socket.bind("tcp://*:%s" % command_socket_port)

        self.poller = zmq.Poller()
        self.poller.register(self.command_socket, zmq.POLLIN)

        self.sound_controller = None
        self.context_manager = context_manager

    def create_sound_controller(self, device_config, stimuli_config):
        if self.sound_controller:
            self.reset_sound()

        if self.context_manager:
            self.sound_controller = self.context_manager.enter_context(SoundStimulusController(device_config, stimuli_config))
        else:
            with ExitStack() as self.context_manager:
                self.sound_controller = self.context_manager.enter_context(SoundStimulusController(device_config, stimuli_config))

    def reset_sound(self):
        if self.sound_controller:
            self.sound_controller.send_stop_event()

            del self.sound_controller
            self.sound_controller = None

    def exit_fun(self):
        logging.debug('Exit called')
        self.reset_sound()
        time.sleep(1)

    def main_message_loop(self):
        should_exit = False
        while not should_exit:
            msg_list = self.poller.poll(timeout=1)
            while msg_list:
                for sock, event in msg_list:
                    if sock==self.command_socket:
                        logging.debug('Got a command message')
                        pickled_msg = self.command_socket.recv() # Command Socket Messages are pickled dictionaries
                        msg = pickle.loads(pickled_msg)
                        logging.debug("Message received: ", msg)
                        if msg['Command'] == 'Reset':
                            self.reset_sound()
                            self.command_socket.send(b"Reset")
                            logging.debug('Sound system reset!')
                        elif msg['Command'] == 'Configure':
                            self.create_sound_controller(msg['DeviceConfig'], msg['Stimuli'])
                            self.command_socket.send(b"Configured")
                            logging.debug('Sound system configured!')
                        elif msg['Command'] == 'SetGain':
                            if self.sound_controller:
                                self.sound_controller.change_gain(msg['Stimulus'], msg['Gain'])
                                self.command_socket.send(b"Gain Set")
                                logging.debug('Gain change: {}:{}'.format(msg['Stimulus'], msg['Gain']))
                            else:
                                self.command_socket.send(b"Error")
                        elif msg['Command'] == 'Exit':
                            self.command_socket.send(b"Exiting")
                            self.exit_fun()
                            should_exit = True
                    else:
                        msg = sock.recv()
                        print(msg)
                msg_list = self.poller.poll(timeout=0) # it seems like the whole point of poller
                                                    # should be to catch all of these, but...

        return

    def __del__(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type:
            logging.critical('NetworkController: exiting because of exception <{}>\n{}'.format(
                exc_type.__name__, tb.format_tb(exc_traceback)))


def start_server():

    # fs, stimulus_buffer = scipy.io.wavfile.read('/home/ckemere/Code/TreadmillIO/ClientSide/Sounds/48kHz/tone_cloud_short.wav')

    # device_config = {
    #     'HWDevice': 'pulse', #'hw:CARD=SoundCard,DEV=0'
    #     'NChannels': 2,
    #     'ChannelLabels': {
    #         'Speaker1': 0,
    #         'Speaker2': 1
    #     },
    #     'FS': fs
    # }

    # stimuli_config = {
    #     'RightEarSound': {
    #         'StimData': stimulus_buffer,
    #         'BaselineGain': 0.0,
    #         'Channel': 1 
    #     }
    # }

    logging.basicConfig(level=logging.INFO)

    with ExitStack() as stack:

        logging.info('Starting network sound server.')
        network_interface = stack.enter_context(NetworkSoundInterface(context_manager=stack))

        # network_interface.create_sound_controller(device_config, stimuli_config)

        network_interface.main_message_loop() # This is an infinite loop

        logging.info('Exiting network sound server.')


if __name__ == '__main__':
    start_server()
