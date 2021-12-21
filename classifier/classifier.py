import tflite_runtime.interpreter as tflite
import glob
import os
from os import path
import librosa
import numpy as np
import sqlite3
import time
from datetime import datetime, timedelta

DB_FILE = os.getenv("DB_PATH", "/data/sound_app/sound_app.db")  # path and filename of database
WAV_PATH = os.getenv("WAV_PATH", "/data/sound_app/") # folder with wav files
MODEL_FILE = os.getenv("MODEL_FILE", "/data/sound_app/mobilenet_v2_sound_classification_qat_edgetpu.tflite") # path and filename  with model file
LABEL_FILE = os.getenv("LABEL_FILE", "/data/sound_app/class_labels.txt") #path and filename of associated model class names
AUTO_DELETE = os.getenv("AUTO_DELETE", "false") #if equal to true, files above the threshold will automatically be deleted 
ct = os.getenv("CERTAINTY_THRESHOLD", "70") # minimum value to consider prediction to be acceptable
if ct.isnumeric():
    CERTAINTY_THRESHOLD = int(ct)
else:
    CERTAINTY_THRESHOLD = 70

# Load labels from a file
sound_names = [line.rstrip('\n') for line in open(LABEL_FILE)]
print("Loaded {0} labels for model.".format(len(sound_names)))

# just extract the features
def extract_features_only(filename):
    features = np.empty((224,224,3)) # MobileNetV2 input size
    X, sample_rate = librosa.load(filename, 44100)
    #mel_spect = librosa.feature.melspectrogram(y=X, sr=sample_rate, n_fft = 2048, hop_length = 788, n_mels=224, fmin=20)
    duration = librosa.get_duration(X)/2
    print("Duration: {0}".format((duration)))
    hop_len = round(44100/(224/duration))
    print("Hop Length: {0}".format(hop_len))
    num_features = (sample_rate/hop_len) * duration
    print("Number of Features: {0}".format(num_features))
    if num_features > 224:
        hop_len += 1
        print("New Hop Length: {0}".format(hop_len))
    if num_features < 224:
        hop_len -=1
        print("New Hop Length: {0}".format(hop_len))
    mel_spect = librosa.feature.melspectrogram(y=X, sr=sample_rate, n_fft = 2048, hop_length = hop_len, n_mels=224, fmin=20)
    log_mel_spect = librosa.power_to_db(mel_spect, ref=np.max)
    features = np.repeat(log_mel_spect[:,:, np.newaxis], 3, axis =2)
    return features


# Specify a TensorFlow Lite delegate for the Edge TPU.
# Then, whenever the interpreter encounters a graph node
# that's compiled for the Edge TPU, it sends that operation
# to the Edge TPU instead of the CPU

try:
    interpreter = tflite.Interpreter(model_path=MODEL_FILE, experimental_delegates=[tflite.load_delegate('libedgetpu.so.1')])
except ValueError:
    print("Interpreter error. Is Edge TPU plugged in?")
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
interpreter.allocate_tensors()
#print("== Input details ==")
#print("shape:", input_details[0]['shape'])
#print("type:", input_details[0]['dtype'])
#print("\n== Output details ==")
#print("shape:", output_details[0]['shape'])
#print("type:", output_details[0]['dtype'])

try:
    conn = sqlite3.connect(DB_FILE)
except Error as e:
    print("Error connecting to database: ", e)

conn.row_factory = sqlite3.Row
cur = conn.cursor()
top_certainty = 0
second_certainty = 0
sleep_msg = 1

while True:
    try:
        cur.execute("SELECT my_rowid, filename FROM wav_file WHERE current_status='created'")
        recs = cur.fetchall()
    except Exception as e:
        print("[ERROR] %s".format(e))
    if len(recs) > 0:
        print("Found {0} unevaluated file(s).".format(len(recs)))
        sleep_msg = 1
    for row in recs:
        print("Evaluating file {0}{1} (id {2})".format(WAV_PATH, row[1], row[0]))
        # do eval here
        # load audio file and extract features
        if path.exists(WAV_PATH + row[1]):
            predict_x = extract_features_only(WAV_PATH + row[1])
            predict_x = np.expand_dims(predict_x, axis=0)
            interpreter.set_tensor(input_details[0]['index'], predict_x.astype(np.uint8))
            #input_details = interpreter.get_input_details()[0] # for one input data
            #tensor_index = input_details['index'] # tensor index in the interpreter
            #input_tensor = interpreter.tensor(tensor_index)()[0]
            #input_tensor[:, :] = predict_x
            start_time = datetime.now()
            interpreter.invoke()
            end_time = datetime.now()
            duration = str(end_time - start_time)
            print("Interpreter duration: ", duration)
            #tflite_model_predictions = interpreter.get_tensor(output_details[0]['index'])
            output_details = interpreter.get_output_details()[0] # for one output data
            tflite_model_predictions = interpreter.get_tensor(output_details['index']) # obtains output tensor in numpy array
            #tflite_model_predictions = np.argmax(tflite_model_predictions) # obtain most probable output
            #print(tflite_model_predictions[0])
            # get the indices of the top 2 predictions, invert into descending order
            ind = np.argpartition(tflite_model_predictions[0], -2)[-2:]
            ind[np.argsort(tflite_model_predictions[0][ind])]
            ind = ind[::-1]
            top_certainty = int(tflite_model_predictions[0,ind[0]] * 100)
            second_certainty = int(tflite_model_predictions[0,ind[1]] * 100)
            print("Top guess: ", sound_names[ind[0]], " (",top_certainty,"%)")
            print("2nd guess: ", sound_names[ind[1]], " (",second_certainty,"%)")

            if top_certainty >= CERTAINTY_THRESHOLD:
                if AUTO_DELETE == "true":
                    print("Top guess above threshold, updating database and deleting sound file.")
                    sql = """UPDATE wav_file SET timestamp_evaluated='{0}',
                          timestamp_deleted='{1}',
                          interpreter_class='{2}',
                          interpreter_certainty={3},
                          interpreter_class2='{4}',
                          interpreter_certainty2={5},
                          current_status='deleted',
                          interpreter_class_id={6},
                          interpreter_class2_id={7},
                          certainty_threshold={8},
                          classify_duration='{9}'
                          WHERE my_rowid = {10}""".format(str(start_time), str(datetime.now()), sound_names[ind[0]], top_certainty, sound_names[ind[1]], second_certainty, ind[0], ind[1], CERTAINTY_THRESHOLD, duration, row[0])
                    # Delete file
                    os.remove(WAV_PATH + row[1])
                else:
                    print("Top guess above threshold, updating database, auto-delete OFF.")
                    sql = """UPDATE wav_file SET timestamp_evaluated='{0}',
                          interpreter_class='{1}',
                          interpreter_certainty={2},
                          interpreter_class2='{3}',
                          interpreter_certainty2={4},
                          current_status='evaluated',
                          interpreter_class_id={5},
                          interpreter_class2_id={6},
                          certainty_threshold={7},
                          classify_duration='{8}'
                          WHERE my_rowid = {9}""".format(str(start_time), sound_names[ind[0]], top_certainty, sound_names[ind[1]], second_certainty, ind[0], ind[1], CERTAINTY_THRESHOLD, duration, row[0])

            else:
                print("Top guess below threshold, saving file for further review.")

                sql = """UPDATE wav_file SET timestamp_evaluated='{0}',
                     interpreter_class='{1}',
                     interpreter_certainty={2},
                     interpreter_class2='{3}',
                     interpreter_certainty2={4},
                     current_status='evaluated',
                     interpreter_class_id={5},
                     interpreter_class2_id={6},
                     certainty_threshold={7},
                     classify_duration='{8}'
                     WHERE my_rowid = {9}""".format(time.strftime('%Y-%m-%d %H:%M:%S'), sound_names[ind[0]], top_certainty, sound_names[ind[1]], second_certainty, ind[0], ind[1], CERTAINTY_THRESHOLD, duration, row[0])

        else:
            print("Wav file not found, continuing to next file...")
            sql = "UPDATE wav_file SET current_status='missing' WHERE my_rowid = {0}".format(row[0])

        conn.execute(sql)
        conn.commit()

    cur.close()
    cur = conn.cursor()
    if sleep_msg == 1:
        print("No unevaluated files left in the queue, waiting...")
        sleep_msg = 0
    time.sleep(2)
