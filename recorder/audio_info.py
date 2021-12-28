import pyaudio
import pytz
import json
from datetime import datetime

# instantiate PyAudio
audio = pyaudio.PyAudio()

now = datetime.now(pytz.timezone('Asia/Singapore'))
outp ="Audio Information as of {0}\n\n".format(now.replace(tzinfo=None))

# obtain list of device index and name of devices
outp = outp + "----------------------record device list---------------------\n"
info = audio.get_host_api_info_by_index(0)
numdevices = info.get('deviceCount')
for i in range(0, numdevices):
        if (audio.get_device_info_by_host_api_device_index(0, i).get('maxInputChannels')) > 0:
            outp = outp + "Input Device index {0} - {1}\n".format(i, audio.get_device_info_by_host_api_device_index(0, i).get('name'))

outp = outp + "-------------------------------------------------------------\n"

outp = outp + "   \n"

outp = outp + "------------------default input device --------------------- \n"
info = audio.get_default_input_device_info()
# convert python object into a json string
# ". " is the item separator
# " = " is the key separator
outp = outp + json.dumps(info, indent=4, separators=(". ", " = ")) + "\n"

print(outp)
audio_info_file = open("/data/sound_app/audio_info.txt", "w")
audio_info_file.writelines(outp)
audio_info_file.close()
