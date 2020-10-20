"""Script entry point."""

from flask import Flask
from flask import request
import json


app = Flask(__name__)

from routes.db import Database
from config import (
    DATABASE_HOST,
    DATABASE_USERNAME,
    DATABASE_PASSWORD,
    DATABASE_PORT,
    DATABASE_NAME,
    CSV_COLUMN_DESCRIPTION,
    CSV_COLUMN_INTENT,
    LANGUAGES
)
# Create database class
db = Database(
    DATABASE_HOST,
    DATABASE_USERNAME,
    DATABASE_PASSWORD,
    DATABASE_PORT,
    DATABASE_NAME
)

"""Script entry point."""


from routes.queries import queries
from routes.log import LOGGER
from routes.functions import check_json_format
from routes.functions import check_values_request
from routes.functions import createJsonFile
from routes.rasa_commnads import trainModel


@app.route("/api/getDataset", methods=['POST'])
def get_dataset():
    reqBody = request.get_json()
    check=json.loads(check_json_format(reqBody))
    if check['message'] != True:
        return json.dumps({"message":check['message']}),400
    else:
        user_id=check['id']
        if json.loads(db.check_user(user_id))['message'] == "user not exists":
                return json.dumps("user doesn't exists"),400
        else:
            return db.get_data_list(user_id)
       
@app.route("/api/appendData",methods=['POST'])
def appendData():
    return append("no delete")


@app.route("/api/newData",methods=['POST'])
def newData():
    return append("delete")

def append(delete_data_from_user):
    reqBody = request.get_json()
    #if request json is empty ==> get from file
    if (reqBody==None and 'file' in request.files ):
        file = request.files['file']
        validate=json.loads(check_values_request(request.values,file)) 
        if (validate['message'] !=True):
            return json.dumps({"message":validate['message'] }),400
        else:
            extension = file.filename.rsplit('.', 1)[1].lower()
            user_id = request.values.get("id")
            if json.loads(db.check_user(user_id))['message'] == "user not exists":
                return json.dumps("user doesn't exists"),400
            else:
                if (extension == "csv"):
                    if(delete_data_from_user=="delete"):
                        db.delete_from_user(user_id)
                        return db.from_csv_to_db(file, user_id, CSV_COLUMN_INTENT, CSV_COLUMN_DESCRIPTION)
                    else:
                        return db.from_csv_to_db(file, user_id, CSV_COLUMN_INTENT, CSV_COLUMN_DESCRIPTION)
                if (extension=="json"):
                    with open(file.filename) as json_file:
                        data = json.load(json_file)
                        if(delete_data_from_user=="delete"):
                            db.delete_from_user(user_id)
                            return db.from_json_to_db(data['data'], user_id)
                        else:
                            return db.from_json_to_db(data['data'], user_id)

    else:
        check=json.loads(check_json_format(reqBody))
        if check['message'] != True:
            return json.dumps({"message":check['message']}),400
        else:
            user_id=check['id']
            if json.loads(db.check_user(user_id))['message'] == "user not exists":
                return json.dumps("user doesn't exists"),400
            else:
                user_id = reqBody['id']
                data = reqBody['data']
                if(delete_data_from_user=="delete"):
                    db.delete_from_user(user_id)
                    return db.from_json_to_db(data, user_id)
                else:
                    return db.from_json_to_db(data, user_id)


@app.route("/api/updateById", methods=['PUT'])
def updateByid():
    reqBody = request.get_json()
    if not ('id' in reqBody and 'data' in reqBody):
                return json.dumps("id or data  key is missing"), 400
    else:
        user_id = reqBody['id']
        if json.loads(db.check_user(user_id))['message'] == "user not exists":
            return json.dumps("user doesn't exists"),400
        else:
            data = reqBody['data']
            return db.update_by_id(data,user_id)


@app.route("/api/deleteById", methods=['DELETE'])
def deleteById():
    reqBody = request.get_json()

    if not ('id' in reqBody and 'ids' in reqBody):
                return json.dumps("id or language or ids key is missing"), 400
    else:
        user_id = reqBody['id']
       
        if json.loads(db.check_user(user_id))['message'] == "user not exists":
            return json.dumps("user doesn't exists")
        else:
            ids = reqBody['ids']
            return db.delete_by_id(ids,user_id)

            
@app.route("/api/createUser", methods=['POST'])
def createUser():

    reqBody = request.get_json()
    if not ('clientName' in reqBody ):
        return json.dumps("client Name  key is missing"), 400
    else:
        clientName = reqBody['clientName']
      
        if (clientName == "" ):
            return json.dumps("client Name is missing"), 400
        else:
            if json.loads(db.check_user_by_name(clientName))['message'] == "user exists":
                return json.dumps("user exists")
            else:
                return db.create_user_ports_per_languages(clientName)

@ app.route("/api/trainModel", methods=['POST'])
def trainModelmethod():
    reqBody = request.get_json()
    check=json.loads(check_json_format(reqBody))
    if check['message'] != True:
        return json.dumps({"message":check['message']}),400
    else:
        user_id=check['id']
        user=json.loads(db.check_user(user_id))
        if user['message'] == "No user":
            return json.dumps("user doesn't exists")
        else:
            languages=[]
            training_examples=[]
            languages=db.get_languages(user_id)
            for language in languages:
                print(language)
                training_examples=db.get_training_data_per_lan(user_id,language)
                training_examples = createJsonFile(training_examples)
                print(training_examples)
                port=db.get_port_per_lan(user_id,language)
                
                trainModel(language,training_examples,str(port))
            return "Done"    


                    

              

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
    

    