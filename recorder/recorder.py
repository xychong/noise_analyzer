import pyaudio
import wave
import audioop
from collections import deque
import os
from os import path
from pathlib import Path
import time
from datetime import datetime
import pytz
import math
import sqlite3

# based on https://github.com/jeysonmc/python-google-speech-scripts/blob/master/stt_google.py
# Values of environment variables can be adjusted on balenaCloud under "Device Variables"

# explicitly specifying path and filename of database in shared volume and store the path in environment variable "DB_PATH"
DB_PATH = os.getenv("DB_PATH", "/data/sound_app/sound_app.db")

# FYI: Database schema below, only one table
# CREATE TABLE wav_file(my_rowid INTEGER PRIMARY KEY, timestamp_created TEXT, timestamp_evaluated TEXT, timestamp_deleted TEXT, interpreter_class TEXT, interpreter_certainty INT,
#   interpreter_class2 TEXT, interpreter_certainty2 INT, system_notes TEXT, user_description TEXT, user_notes TEXT, 
#   timestamp_uploaded TEXT, current_status TEXT, filename TEXT, threshold INT, avg_intensity REAL, classify_duration TEXT, 
#   user_class TEXT, timestamp_ready TEXT, remote_filename TEXT, upload_msg TEXT, certainty_threshold INT, t3 TEXT, t4 TEXT, n1 INT, n2 INT,
#   interpreter_class_id INT, interpreter_class2_id INT, user_class_id INT);

# explicitly specifying path to location for saving WAV files in shared volume and store the path in environment variable "WAV_PATH"
WAV_FILE_PATH = os.getenv("WAV_PATH", "/data/sound_app/") 

# explicitly specifying total size limit in bytes of stored WAV files before warning and store the value in environment variable "WAV_FILE_LIMIT"
wf = os.getenv("WAV_FILE_LIMIT", "6000000000") 
if wf.isnumeric():
    WAV_FILE_LIMIT = int(wf)
else:
    WAV_FILE_LIMIT = 6000000000

# obtain first seven chars of device UUID
UUID = os.environ.get('RESIN_DEVICE_UUID')[:7] 

# Microphone stream config.
CHUNK = 1024  # read 1024 samples each time from mic
FORMAT = pyaudio.paInt16 # signed 16-bit binary string to store sound data; each sample is 2 bytes
CHANNELS = 1 
RATE = 44100 # sampling rate, i.e. number of samples per second
th = os.getenv("WAV_REC_THRESHOLD", "2000")  # The threshold intensity that defines silence
                                             # and noise signal (an int. lower than THRESHOLD is silence).
                                             # based on peak ampltude in each chunk of audio data
if th.isnumeric():
    THRESHOLD = int(th)
else:
    THRESHOLD = 2000

SILENCE_LIMIT = 1  # Silence limit in seconds. The max ammount of seconds where
                   # only silence is recorded. When this time passes the
                   # recording is saved and evaluated.

PREV_AUDIO = 0.5  # Previous audio (in seconds) to prepend. When noise
                  # is detected, how much of previously recorded audio is
                  # prepended. This helps to prevent chopping the beggining
                  # of the sound.

# explicitly specifying which physical input to record from and store the result in environment variable "INPUT_INDEX"
idx = os.getenv("INPUT_INDEX", "x")  
if idx.isnumeric():
    INPUT_INDEX = int(idx)
else:
    INPUT_INDEX = 'x'

MAX_FILE_LENGTH = 4 # Number of seconds until a new file is started while reording

file_count = 0 # counter for how many files created in this session.

# get WAV file of recorded audio and write into database
def append_db(filename):
    """
    Writes record to database for new sound file recording
    """
    
    now = datetime.now(pytz.timezone('Asia/Singapore'))

    if not(path.exists(DB_PATH)):
        print("Database not found. Sleeping 5 seconds awaiting db copy.")
        time.sleep(5)
        
    try:
        conn = sqlite3.connect(DB_PATH) # creating a Connection object that represents the database
    except Error as e:
        print("Error connecting to database: ", e)

    cur = conn.cursor() # create a Cursor object
    # Create table
    sql = """INSERT INTO 'wav_file'('filename', 'timestamp_created', 'current_status', 'threshold')
        VALUES(?, ?, ?, ?);"""
    # Data being inserted
    data_tuple = (filename, now.replace(tzinfo=None), 'created', THRESHOLD)
    try:
        cur.execute(sql, data_tuple)
        conn.commit() # Save (commit) the changes
    except Exception as e:
        print("Error inserting into database: ", e)

def listen_for_speech(threshold=THRESHOLD):
    """
    Listens to microphone, extracts phrases from it and saves as wav file
    to be analyzed by the classifier. a "phrase" is sound
    surrounded by silence (according to threshold). num_phrases controls
    how many phrases to process before finishing the listening process
    (-1 for infinite).
    """
    global file_count, INPUT_INDEX

    #Open stream
    p = pyaudio.PyAudio()
    if INPUT_INDEX == "x": # Get default input device
        INPUT_INDEX = p.get_default_input_device_info()["index"]
    print("Using audio input index {0}.".format(INPUT_INDEX))
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input_device_index=INPUT_INDEX,
                    input=True,
                    frames_per_buffer=CHUNK)

    print("Listening to audio input...")
    audio2send = [] # list containing chunks of audio data
    cur_data = ''  # current chunk of audio data
    rel = RATE/CHUNK 
    slid_win = deque(maxlen=int(SILENCE_LIMIT * rel)+1) # number of chunks to make up silence (44)
    #print("slid_win length: ", len(slid_win)) (0)
    #Prepend audio from 0.5 seconds before noise was detected
    prev_audio = deque(maxlen=int(PREV_AUDIO * rel)+1) # number of chunks to make up prev audio (22)
    #print("prev_audio length: ", len(prev_audio)) (0)
    started = False 
    #n = num_phrases 
    response = [] 
    file_split = 0 

    while (1):
        cur_data = stream.read(CHUNK, exception_on_overflow = False) # read one chunk of data (1024 samples)
        # audioop.avg returns average over all samples in one chunk
        slid_win.append(math.sqrt(abs(audioop.avg(cur_data, 4)))) # obtain intensity values of audio chunk
        #print("slid_win length: ", len(slid_win))
        #print("sum x > threshold: ", sum([x > THRESHOLD for x in slid_win]))
        if(sum([x > THRESHOLD for x in slid_win]) > 0 and file_split == 0): # check if intensity of chunk exceeds silence threshold
            if(not started):
                print("Starting file recording...")
                started = True
            audio2send.append(cur_data) # append 1 chunk of data each time
            # total_num_of_samples = sampling_rate * number_of_seconds 
            # num_of_chunks = total_num_of_samples / chunk_size
            #print("audio2send length: ", len(audio2send)) # number of chunks 
            #print("seconds: ", len(audio2send)/rel) # duration of audio
            if len(audio2send)/rel >= (MAX_FILE_LENGTH - PREV_AUDIO): # split file once duration of audio > 3.5s; max duration is 4s (got max 0.5s of prev audio)
                file_split = 1
        elif (started is True): # silence detected in one chunk after recording has started
            print("Finished recording.")
            # The limit was reached, finish capture
            filename = save_speech(list(prev_audio) + audio2send, p) # save audio data into WAV file
            print("Saving file {0}, length {1}s.".format(filename, round(len(audio2send)/rel)))
            # Add file info to db so classifier can evaluate it
            append_db(filename) # append database with audio data in WAV file 
            
            # Reset all settings
            started = False
            slid_win = deque(maxlen=int(SILENCE_LIMIT * rel)+1)
            prev_audio = deque(maxlen=int(PREV_AUDIO * rel)+1)
            audio2send = []
            #print(SILENCE_LIMIT)
            #print(PREV_AUDIO)
            #print(n)
            #n -= 1
            file_split = 0

            file_count += 1 
            if file_count % 10 == 0:
                # every ten files that are created, check wav file space usage
                print("{0} files created so far.".format(str(file_count)))
                root_directory = Path('WAV_FILE_PATH')
                wav_space = sum(f.stat().st_size for f in root_directory.glob('*.wav') if f.is_file()) # calculate size of all WAV files generated
                if wav_space > WAV_FILE_LIMIT:
                    print("Warning: wav files are utilizing more drive space than the specified limit!")
                    #TODO: Create a more useful warning
            print("Listening ...")
        else: # silence detected but recording hasn't started
            prev_audio.append(cur_data) # prepend previous audio to current chunk; do this for each chunk 
            #print("prev_audio length: ", len(prev_audio))

    print("Finished.")
    stream.close() # stop stream
    p.terminate() # close PyAudio

    #return response


def save_speech(data, p):
    """ Saves mic data to WAV file. Returns filename of saved
        file """

    now = datetime.now(pytz.timezone('Asia/Singapore'))
    filename = str(now.replace(tzinfo=None))
    # writes data to WAV file
    data = b''.join(data) # perform join on a byte string since data is in bytes
    wf = wave.open(WAV_FILE_PATH + filename + '.wav', 'wb')
    wf.setnchannels(1) # set number of channels
    wf.setsampwidth(p.get_sample_size(pyaudio.paInt16)) # set sample width to 2 bytes
    wf.setframerate(RATE) # set frame rate to be sampling rate
    wf.writeframes(data) # write data into wav file
    wf.close()
    return filename + '.wav'

# Interpreter inserts this at the top of the module when run as the main program
if(__name__ == '__main__'):
    listen_for_speech()  # listen to mic.
