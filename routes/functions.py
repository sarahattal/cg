import json
from polyglot.detect import Detector
import pandas as pd


def check_json_format(reqBody):
    if reqBody==None:

        return json.dumps({"message": "Json form is empty"})   
    else:
        if not ('id' in reqBody ):
            return json.dumps({"message": "id key is missing"})
        else:
            user_id = str(reqBody['id'])
            if (user_id == ""):
                return json.dumps({"message": "id is missing"})
            
            else:
                return json.dumps({"message":True,"id":user_id})

def check_values_request(reqBody,file):
    if not ('id' in reqBody):
        return json.dumps({"message": "id key is missing"})
    else:
        user_id = reqBody.get("id")
        if (user_id == ""):
            return json.dumps({"message": "id is missing"})
        else:
            if file.filename == "":
                return json.dumps({"message": "No file is selected"})
            else:
                file = file.filename
                extension = file.rsplit('.', 1)[1].lower()
                print(extension)
                if(extension == "csv" or extension == "json" ):
                    return json.dumps({"message": True})
            


def detect_language(text):
    detector = Detector(text) 
    return json.dumps(detector.language.code)


def createJsonFile(training_examples):
    training_data = {'rasa_nlu_data': {"common_examples": training_examples,
                                       "regex_features": [],
                                       "lookup_tables": [],
                                       "entity_synonyms": []
                                       }}
    json_train = json.dumps(training_data,ensure_ascii=False)
    with open("train_file.json", "w") as jsonfile:
        jsonfile.write(json_train)
    return json_train

