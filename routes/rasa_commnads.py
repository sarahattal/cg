import requests
import shutil
import json
from config import (
    RASA_ADDRESS,
    PATH_TO_TRAIN,
    PATH_TO_MODEL,
    MODEL_LOCATION,
    PATH_TO_PARSE
)

def trainModel(language,training_examples,port):
    
    file=language
    ext='.yml'
    file="".join([file, ext])
    print(file)
    config_file=""
    with open(file, 'r') as f:

        config_file = f.read()
        print(config_file)
    
    url=RASA_ADDRESS+port+PATH_TO_TRAIN
    print(url)

    print(MODEL_LOCATION+"nlu-20201020-135808.tar.gz")

    payload = {
        "nlu": training_examples,
        "config": config_file
    }

    x = requests.post(url, json=payload)
    model_name = x.headers.get('filename')
    from_loc=MODEL_LOCATION+model_name
    to_loc=MODEL_LOCATION+str(port)+".tar.gz"
    shutil.move(from_loc,to_loc)
    print(to_loc)

    url2 = RASA_ADDRESS+port+PATH_TO_MODEL
    payload2 = {
        "model_file": to_loc
    }
    z = requests.put(url2, json=payload2)
    return "Done"


def parseModel(port,text):

    url=RASA_ADDRESS+str(port)+PATH_TO_PARSE

    payload = {
        "text":text,
    }
    x = requests.post(url, json=payload)
    x = json.loads(x.text)
    intent = x['intent']['name']
    confidence = x['intent']['confidence']
    return json.dumps( {"message": text, "intent": intent, "confidence": confidence})

       

