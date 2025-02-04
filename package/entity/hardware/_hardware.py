#!/ustreamReceiver/bin/env python
import datetime
import os
import time

import numpy as np
import pycnbi.utils.q_common as qc
from pycnbi import logger

from ..edata.variables import Variables


class HardwareAdditionalMethods:
    """
    HardwareAdditionalMethods controls heavy recording function in a separate thread
    """
    def record(self):
        """
        Continue recording data until the record stop button is pressed, the recorded data
        are firstly saved in a buffer which will be saved to a csv file when recording finishes.
        TODO: Save data to file during recording
        """
        timestamp = time.strftime('%Y%m%d-%H%M%S', time.localtime())
        # start recording
        logger.info('\n>> Recording started (PID %d).' % os.getpid())
        tm = qc.Timer(autoreset=True)
        next_sec = 1
        while self.is_recording_running:

            self.streamReceiver.acquire("recorder using")

            if self.streamReceiver.get_buflen() > next_sec:
                # print("\nbuffer length: ",self.streamReceiver.get_buflen())
                duration = str(datetime.timedelta(seconds=int(self.streamReceiver.get_buflen())))
                logger.info('RECORDING %s' % duration)
                # logger.info('\nLSL clock: %s' % self.streamReceiver.get_lsl_clock())
                # logger.info('Server timestamp = %s' % self.streamReceiver.get_server_clock())
                # logger.info('offset {}'.format(self.streamReceiver.get_lsl_clock() - self.streamReceiver.get_server_clock()))
                # # self.lsl_time_list.append(self.streamReceiver.get_lsl_clock())
                # self.server_time_list.append(self.streamReceiver.get_server_clock())
                # self.offset_time_list.append(self.streamReceiver.get_lsl_offset())
                next_sec += 1

            self.streamReceiver.set_window_size(self.MRCP_window_size)
            self.current_window, self.current_time_stamps = self.streamReceiver.get_window()
            tm.sleep_atleast(0.001)


        buffers, times = self.streamReceiver.get_buffer()
        signals = buffers
        events = None

        data = {'signals': signals, 'timestamps': times, 'events': events,
                'sample_rate': self.streamReceiver.get_sample_rate(), 'channels': self.streamReceiver.get_num_channels(),
                'ch_names': self.streamReceiver.get_channel_names(), 'lsl_time_offset': self.streamReceiver.lsl_time_offset}
        logger.info('Saving raw data ...')

        self.write_recorded_data_to_csv(data)
        temp_lsl_list = self.lsl_time_list.copy()
        temp_lsl_list.insert(0,0)
        temp_lsl_list.pop()
        # print("lsl clock", self.lsl_time_list)
        # print('temp lsl list', temp_lsl_list)
        # print(np.subtract(self.lsl_time_list, temp_lsl_list))
        # print("timestamp len before flush", len(self.streamReceiver.timestamps[0]))
        # print("buffer len before flushing: ", len(self.streamReceiver.buffers[0]))
        self.streamReceiver.flush_buffer()
        print("timestamp len after flush", len(self.streamReceiver.timestamps[0]))
        print("buffer len after flushing: ", len(self.streamReceiver.buffers[0]))


    def write_recorded_data_to_csv(self, data):
        """
        Write buffer to Run1/raw_eeg.csv
        """
        eeg_file = self.eeg_file_path
        logger.info(eeg_file)
        raw_data_with_time_stamps = np.c_[data['timestamps'], data['signals']]
        with open(eeg_file, 'w') as f:
            np.savetxt(eeg_file, raw_data_with_time_stamps, delimiter=',', fmt='%.5f', header = '')

        logger.info('Saved to %s\n' % eeg_file)

    def write_timestamps_to_csv(self):
        """
        Write timestamps to Run1/event.csv
        """
        eeg_timestamp_file = Variables.get_raw_eeg_timestamp_file_path()
        logger.info(eeg_timestamp_file)
        # pdb.set_trace()
        time_stamps = np.c_[self.lsl_time_list, self.server_time_list, self.offset_time_list]
        with open(eeg_timestamp_file, 'w') as f:
            np.savetxt(eeg_timestamp_file, time_stamps, delimiter=',', fmt='%.5f', header = '')


