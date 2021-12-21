# AI Monitoring at the Edge for Smart Nation Deployment
A project that aims to identify sources of noise pollution in schools using the Google Coral Development Board.

The Google Coral Development Board (Coral Dev Board) comes with a built-in microphone that can be used to listen for noises above a certain intensity threshold. The noises are saved as WAV files before audio features (e.g Log-Mel Spectrogram) are extracted. A Tensorflow Lite model that runs on the Edge TPU takes in these audio features as input and outputs the predicted sound classes.

# Files

**sound_edgetpu.tflite** - Tensorflow model in the classifier folder trained on sounds belonging to either of the following 5 sound classes: ambience, footsteps, horn, music and shout. This model has been converted to Tensorflow Lite, quantized and compiled for the Edge TPU. The input and output tensors are uint8 to prevent any latencies caused by data format conversions. The entire model executes on the Edge TPU.

**class_labels.txt** - Text file comprising of 5 labels - ambience, footsteps, horn, music and shout.

# Services

**recorder** - Continuously listens through the microphone and records audio files in 4 second chunks if they are above a certain volume threshold.

**classifier** - Searches for newly recorded WAV files and anaylzes them using the TFLite model. If they are not a reasonable match, they are saved for later analysis.

**webserver** - Express webserver that runs on port 80; allows users to view the classification results and listen to the recorded WAV files.

Browse to the device's IP (or public URL if enabled) to access the web UI. Links at the bottom of this UI provide device information, data export and github repository.

# Device Variables 
Helps to customize the behavior of the application:

**recorder**

`WAV_REC_THRESHOLD` - minimum intensity of audio reaching mic that triggers a recording start (default is 2000)

`INPUT_INDEX` - index of physical audio input to use for recording (default is to use the board's default input) - You can see the audio details in the "recorder" log window when the container starts, or via the "device info" link at the bottom of the application's web page.

`FAN_SPEED` - (Coral Dev board only) set a value in rpm (average range is 2000 - 8000) to run the board fan at a constant speed. Without this set, the fan is supposed to run automatically at 65 C. (Note that any fan noise will be picked up by the on-board microphone and cause significantly less accurate predictions by the classifier)

`WAV_FILE_LIMIT` - total size of all wav files saved to disk in bytes before a warning is issued (default is 6000000000)

**classifier**

`LABEL_FILE` - path and filename of text file with ordered list of classes for associated model (default is `/data/sound_app/labels.txt`)

`MODEL_FILE` - path and filename of Edge TPU model file. (default is `/data/sound_app/sound_edgetpu.tflite`)

`CERTAINTY_THRESHOLD` - minimum percentage value of top guess to be considered a valid guess (default is 70)

`AUTO_DELETE` - files with a prediction certainty above the `CERTAINTY_THRESHOLD` will automatically be deleted unless this is set to false. (default is false)

**webserver**

`MASTER_NODE` - full UUID of the master node to upload sound files and data for re-training the model. The "Upload" button will be disabled if this is not set.

`MINIO_ACCESS_KEY` - access key for master node's Minio server, the data store for uploading sound files. 

`MINIO_SECRET_KEY` - secret key for master node's Minio server, the data store for uploading sound files. 

**all**

`WAV_PATH` - path where wav files are recorded (default is `/data/sound_app/`)

`DB_PATH` - path and filename of SQLite database (default is `/data/sound_app/sound_app.db`)

