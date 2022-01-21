#!/bin/bash

sleep 2

# Copy model and labels to shared volume - overwrites existing
cp /usr/src/app/mobilenet_v2_sound_classification_qat_edgetpu.tflite /data/sound_app/mobilenet_v2_sound_classification_qat_edgetpu.tflite
cp /usr/src/app/mobilenet_v2_sound_classification_float_qat_edgetpu.tflite /data/sound_app/mobilenet_v2_sound_classification_float_qat_edgetpu.tflite
cp /usr/src/app/mobilenet_v2_sound_classification_ptq_edgetpu.tflite /data/sound_app/mobilenet_v2_sound_classification_ptq_edgetpu.tflite
cp /usr/src/app/mobilenet_v2_sound_classification_float_ptq_edgetpu.tflite /data/sound_app/mobilenet_v2_sound_classification_float_ptq_edgetpu.tflite
cp /usr/src/app/class_labels.txt /data/sound_app/class_labels.txt

# Start the classifier
python3 classifier.py
