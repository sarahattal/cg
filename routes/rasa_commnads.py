import requests
import shutil

from config import (
    RASA_ADDRESS,
    PATH_TO_TRAIN,
    PATH_TO_MODEL
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

    payload = {
        "nlu": training_examples,
        "config": config_file
    }

    x = requests.post(url, json=payload)
    print(x.headers)
    print(x.headers.get('filename'))
    model_name = x.headers.get('filename')
    print(model_name)


    # shutil.move("/home/sarahattal/models/models/"+model_name,
    #                                 "/home/sarahattal/models/models/"+str(port)+".tar.gz")
    # model_path = "/home/sarahattal/models/models/"+str(port)+".tar.gz"
    # print(model_path)

    # url2 = RASA_ADDRESS+port+PATH_TO_MODEL
    # payload2 = {
    #     "model_file": model_path
    # }
    # z = requests.put(url2, json=payload2)

    return "Done"

