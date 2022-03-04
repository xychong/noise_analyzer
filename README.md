# Artificial Intelligence Monitoring at the Edge for Smart Nation Deployment

# About the Project
A project that aims to identify sources of noise pollution in schools using the Google Coral Development Board.

The Google Coral Development Board (Coral Dev Board) uses an attached microphone to listen for noises above a certain intensity threshold. The noises are saved as WAV files before audio features (e.g Log-Mel Spectrogram) are extracted. A Tensorflow Lite model that runs on the Coral Dev Board takes in these audio features as input and outputs the predicted sound classes.

# Models

The following Tensorflow models can be found in the classifier folder. They are trained on sounds belonging to either of the following 5 sound classes: ambience, footsteps, horn, music and shout. 
The models have been converted to Tensorflow Lite, quantized and compiled for the Edge TPU. 
The two types of quantization techniques explored are 1) Quantization Aware Training (QAT) and 2) Post Training Quantization (PTQ).

**mobilenet_v2_sound_classification_qat_edgetpu.tflite [default model]** -  Quantized using QAT; input and output tensors are uint8 to prevent any latencies caused by data format conversions; entire model executes on the Edge TPU

**mobilenet_v2_sound_classification_ptq_edgetpu.tflite** - Quantized using PTQ; input and output tensors are uint8 to prevent any latencies caused by data format conversions; entire model executes on the Edge TPU

**mobilenet_v2_sound_classification_float_qat_edgetpu.tflite**  - Quantized using QAT; input and output tensors are float32 for higher accuracy; some parts of the model executes on the CPU, resulting in latency

**mobilenet_v2_sound_classification_float_ptq_edgetpu.tflite** - Quantized using PTQ; input and output tensors are float32 for higher accuracy; some parts of the model executes on the CPU, resulting in latency

# Labels

**class_labels.txt** - Text file comprising of 5 labels - ambience, footsteps, horn, music and shout.

# Services

**recorder** - Continuously listens through the microphone and records audio files in 4 second chunks if they are above a certain volume threshold.

**classifier** - Searches for newly recorded WAV files and anaylzes them using the TFLite model. If they are not a reasonable match (e.g. low classification accuracy), they are automatically deleted.

**webserver** - Express webserver that runs on port 80; allows users to view the classification results and listen to the recorded WAV files. Classification results can also be exported into a text file.

Browse to the device's IP (or public URL if enabled) to access the web UI. Links at the bottom of this UI provide device information, data export and github repository.

# Device Variables 
Helps to customize the behavior of the application:

**recorder**

`WAV_REC_THRESHOLD` - Minimum intensity of audio reaching microphone that triggers a recording start (default is 2000)

`INPUT_INDEX` - Index of physical audio input to use for recording (default is to use the board's default input) - You can see the audio details in the "recorder" log window when the container starts, or via the "device info" link at the bottom of the application's web page.

`FAN_SPEED` - Set a value in rpm (average range is 2000 - 8000) to run the board fan at a constant speed. Without this set, the fan is supposed to run automatically at 65 C. (Note: any fan noise will be picked up by the on-board microphone and cause significantly less accurate predictions by the classifier)

`WAV_FILE_LIMIT` - Total size of all wav files saved to disk in bytes before a warning is issued (default is 6000000000)

**classifier**

`LABEL_FILE` - Path and filename of text file with ordered list of classes for associated model (default is `/data/sound_app/class_labels.txt`)

`MODEL_FILE` - Path and filename of Edge TPU model file. (default is `/data/sound_app/mobilenet_v2_sound_classification_qat_edgetpu.tflite`)

`CERTAINTY_THRESHOLD` - Minimum percentage value of top guess to be considered a valid guess (default is 50); Top guess < 50% will be automatically deleted

`AUTO_DELETE` - Files with a prediction certainty below the `CERTAINTY_THRESHOLD` will automatically be deleted unless this is set to false (default is true).

**all**

`WAV_PATH` - path where wav files are recorded (default is `/data/sound_app/`)

`DB_PATH` - path and filename of SQLite database (default is `/data/sound_app/sound_app.db`)

# Part 1 of the Project

* This portion shows how we carried out data preprocessing, built and trained the sound classification model as well as quantized and compiled the model for the Edge TPU.
* Click [here](https://github.com/xychong/edgeaimonitoring) to go to Part 1 of the project.
