from flask import Flask, request, jsonify, make_response
import psycopg2
import numpy as np
from psycopg2.extras import RealDictCursor
from io import TextIOWrapper
import csv
import pandas as pd
import requests
import shutil
import bcrypt
import json
import jsonschema
from jsonschema import validate
import paramiko
import re
import random
import subprocess
from polyglot.detect import Detector


app = Flask(__name__)

host = "itbot.chc2ffunjdw0.us-east-1.rds.amazonaws.com"
port = "5432"  # default postgres port
dbname = "CXG"
user = "ubilityai"
pw = "ubility#07"

db_conn = psycopg2.connect(
    host=host, port=port, database=dbname, user=user, password=pw)
cursor = db_conn.cursor()


def validateJson1(jsonData):

    dataSchema = {
    "type": "object",
                "required": [
                    "id", "data"
                ],
        "properties": {
                    "id": {
                        "type": "integer"
                    },
                  
                        "properties": {
                            "data": {
                                "type": "array",

                                "items": {
                                    "type": "object",
                                    "required": [
                                        "intent", "texts"
                                    ],

                                    "properties": {
                                        "intent": {
                                            "type": "string"
                                        },
                                        "texts": {
                                            "type": "array"
                                        }
                                    }
                                }
                            }
                        }
                    
                }
        }
        
    try:
        validate(instance=jsonData, schema=dataSchema)
    except jsonschema.exceptions.ValidationError as err:
        return False
    return True

@app.route("/api/appendData",methods=['POST'])
def ff():
    reqBody = request.get_json()
    if (reqBody==None):
        return updateDataFromFile()
    else:
        return updateData()


@app.route("/api/newData",methods=['POST'])
def ff1():
    reqBody = request.get_json()
    if (reqBody==None):
        return addDataFromFile()
    else:
        return addData()


# @app.route("/api/appendData2", methods=['POST'])
def updateData():
    reqBody = request.get_json()
    isValid = validateJson1(reqBody)
    if isValid:
        user_id = reqBody['id']
        data = reqBody['data']
        for element in data:
            if not ('intent' in element and 'texts' in element):
                return json.dumps("intent or texts key is missing"), 400
            else:
                if json.loads(check_user(user_id))['message'] == "user not exists":
                    return json.dumps("user doesn't exists"),400
                else:
                    texts = element['texts']
                    intent = element['intent']
                    for text in range(len(texts)):
                        language=str(detect_language(texts[text])).replace('"','')
                        data_to_insert = json.dumps(
                            {"intent": intent, "text": texts[text]},ensure_ascii=False)
                        try:
                            cursor.execute("INSERT INTO data (user_id, language,data) VALUES (%s, %s, %s)", (
                                user_id, language, data_to_insert))
                            db_conn.commit()
                            status=200
                            return_message = "Successfully inserted"
                            # return json.dumps({"message":"Successfully inserted"}),200
                        except psycopg2.Error as e:
                            print(e)
                            status=500
                            return_message = "Server error"
                            # return json.dumps({"message":"Server error"}),500
                        except psycopg2.InterfaceError as exc:
                            print(exc.message)
                            psycopg2.connect(host=host, port=port,
                                            database=dbname, user=user, password=pw)
                            status=500
                            return_message = "Reconnected"
            
        return json.dumps({"message":return_message}),status
            
    else:
        return json.dumps("the JSON data is invalid must be id and data array or check value type of each key")



# @app.route("/api/appendDataFromFile", methods=['POST'])
def updateDataFromFile():

    if not ('id' in request.values ):
        return json.dumps({"message": "id key is missing"}), 400
    else:
        user_id = request.values.get("id")
        if (user_id == ""):
            return json.dumps({"message": "id is missing"}), 400
        else:
            if request.files['file'].filename == "":
                return json.dumps({"message": "No file is selected"}), 400
            else:
                if json.loads(check_user(user_id))['message'] == "user not exists":
                    return json.dumps("user doesn't exists"),400
                else:
                    file = request.files['file'].filename
                    extension = file.rsplit('.', 1)[1].lower()
                    if(extension == "csv"):
                        return from_csv_to_db(file, user_id, 'Level 1', 'description')
                    if (extension == "json"):
                        return from_json_to_db(file, user_id)
                    else:
                        return json.dumps({"message": "enter valid file json or csv"}), 400




@ app.route("/api/newData2", methods=['POST'])
def addData():
    reqBody = request.get_json()
    isValid = validateJson1(reqBody)
    if isValid:
        user_id = reqBody['id']
        data = reqBody['data']

        if json.loads(check_user(user_id))['message'] == "user not exists":
            return json.dumps("user doesn't exists")
        else:
            delete_query='Delete from data where user_id = %s '
            cursor.execute(delete_query,(user_id,))
            for element in data:
                if not ('intent' in element and 'texts' in element):
                    return json.dumps("intent or texts key is missing"), 400
                else:
                    texts = element['texts']
                    intent = element['intent']
                    for text in range(len(texts)):
                        language=detect_language(texts[text]).replace('"','')
                        data_to_insert = json.dumps(
                            {"intent": intent, "text": texts[text]},ensure_ascii=False)
                        try:
                            cursor.execute('INSERT INTO data(user_id,language,data) VALUES (%s,%s,%s)', (
                                user_id, language, data_to_insert))
                            db_conn.commit()
                            return_message="Successfully inserted"
                            status=200
                        except psycopg2.Error as e:
                            print(e)
                            return_message="Server error"
                            status=500
                        except psycopg2.InterfaceError as exc:
                            print(exc.message)
                            psycopg2.connect(host=host, port=port,database=dbname, user=user, password=pw)
                            return_message="Reconnected"
                            status=500
            return json.dumps({"message":return_message}),status

    else:
        return json.dumps("the JSON data is invalid must be username and data array"),400


@app.route("/api/newDataFromFile", methods=['POST'])
def addDataFromFile():

    if not ('id' in request.values):
        return json.dumps({"message": "id key is missing"}), 400
    else:
        user_id = request.values.get("id")
        
        if (user_id == ""):
            return json.dumps({"message": "id is missing"}), 400
        else:
            if request.files['file'].filename == "":
                return json.dumps({"message": "No file is selected"}), 400
            else:
                file = request.files['file'].filename
                extension = file.rsplit('.', 1)[1].lower()
                if(extension == "csv"):
                    if json.loads(check_user(user_id))['message'] == "user not exists":
                        return json.dumps("user doesn't exists")
                    else:
                        print(json.loads(delete_from_user(user_id))['message'])
                        return from_csv_to_db(file, user_id, 'Level 1', 'description')
                if (extension == "json"):
                    if json.loads(check_user(user_id))['message'] == "user not exists":
                        return json.dumps("user doesn't exists")
                    else:
                        delete_from_user(user_id)
                        return from_json_to_db(file, user_id)
                else:
                    return json.dumps({"message": "enter valid file json or csv"}), 400

@ app.route("/api/updateById", methods=['PUT'])
def updateByid():
    reqBody = request.get_json()
    if not ('id' in reqBody and 'data' in reqBody):
                return json.dumps("id or data  key is missing"), 400
    else:
        user_id = reqBody['id']
        if json.loads(check_user(user_id))['message'] == "user not exists":
            return json.dumps("user doesn't exists"),400
        else:
            data = reqBody['data']
            not_exists=[]
            for i in range(len(data)):
                intent = data[i]['intent']
                text = data[i]['text']
                data_id = data[i]['id']
                
                language=detect_language(text).replace('"','')
                print(language)

                data_to_insert = json.dumps({"intent": intent,"text": text},ensure_ascii=False)
                print(data_to_insert)
                try:
                    sql_update_query = 'Update data set data=%s , language=%s where  data_id=%s and user_id=%s '
                    cursor.execute(sql_update_query,
                                    (data_to_insert,language,data_id,user_id))
                    rowcount = cursor.rowcount
                    if (rowcount == 0):
                        str1 = " "
                        not_exists.append(str(data_id))
                        str1 = str1.join(not_exists)
                        print(str1)
                        return_message = "id " + str1+" doesn't exists"
                        status=400
                    else:
                        db_conn.commit()
                        return_message="Successfully Updated"
                        status=200
                except psycopg2.Error as e:
                    print(e)
                    return_message="Server error"
                    status=500
                except psycopg2.InterfaceError as exc:
                    print(exc.message)
                    psycopg2.connect(host=host, port=port,database=dbname, user=user, password=pw)
                    return_message="Reconnected"
                    status=500

            return json.dumps({"message":return_message}),status

@ app.route("/api/deleteById", methods=['DELETE'])
def deleteById():
    return_message = ""
    reqBody = request.get_json()
    not_exists = []
    if not ('id' in reqBody and 'ids' in reqBody):
                return json.dumps("id or language or ids key is missing"), 400
    else:
        username = reqBody['id']
        ids = reqBody['ids']
        if json.loads(check_user(username))['message'] == "user not exists":
            return json.dumps("user doesn't exists")
        else:
            for i in range(len(ids)):
                data_id = ids[i]
                s = 'DELETE FROM data WHERE data_id=%s and user_id=%s'
                try:
                    cursor.execute(s, (data_id, username))
                    db_conn.commit()
                    rowcount = cursor.rowcount
                    if (rowcount == 0):
                        str1 = " "
                        not_exists.append((str(data_id)))
                        str1 = str1.join(not_exists)
                        print(str1)
                        return_message = "id " + str1+" doesn't exists"
                        status=400
                    else:
                        db_conn.commit()
                        return_message="Successfully deleted"
                        status=200

                except psycopg2.Error as e:
                    print(e)
                    return_message="Server error Not deleted"
                    status=500
                
            return json.dumps({"message":return_message}),status

def from_csv_to_db(filename, user_id, intent_column, description):

    return_message = ""
    csv_data_df = pd.read_csv(filename)
    c = csv_data_df.dropna(subset=[intent_column], inplace=True)
    levels = list(csv_data_df[intent_column].unique())
    for intent in levels:
        df = csv_data_df.loc[csv_data_df[intent_column] == intent]
        texts = df[description]
        for text in texts:
            language=detect_language(text).replace('"','')
            data_to_insert = json.dumps({"intent": intent, "text": text},ensure_ascii=False)
            try:
                cursor.execute('INSERT INTO data(user_id,language,data) VALUES (%s,%s,%s)', (
                    user_id, language, data_to_insert))
                db_conn.commit()
                status=200
                return_message = "Successfully inserted"
                # return json.dumps({"message":"Successfully inserted"}),200
            except psycopg2.Error as e:
                print(e)
                status=500
                return_message = "Server error"
            except psycopg2.InterfaceError as exc:
                print(exc.message)
                psycopg2.connect(host=host, port=port,database=dbname, user=user, password=pw)
                db_conn.commit()
                status=500
                return_message = "Reconnected"

    return json.dumps({"message": return_message}),status

def from_json_to_db(filename, user_id):

    with open(filename) as json_file:
        data = json.load(json_file)
        data = data['data']
        for element in data:
            if not ('intent' in element and 'texts' in element):
                return json.dumps("intent or texts key is missing"), 400
            else:
                texts = element['texts']
                intent = element['intent']
                for text in range(len(texts)):
                    language=detect_language(texts[text]).replace('"','')
                    data_to_insert = json.dumps(
                        {"intent": intent, "text": texts[text]},ensure_ascii=False)
                    try:
                        cursor.execute('INSERT INTO data(user_id,language,data) VALUES (%s,%s,%s)', (
                            user_id, language, data_to_insert))
                        db_conn.commit()
                        status=200
                        return_message = "Successfully inserted"
                        # return json.dumps({"message":"Successfully inserted"}),200
                    except psycopg2.Error as e:
                        print(e)
                        status=500
                        return_message = "Server error"
                    except psycopg2.InterfaceError as exc:
                        print(exc.message)
                        psycopg2.connect(host=host, port=port,database=dbname, user=user, password=pw)
                        db_conn.commit()
                        status=500
                        return_message = "Reconnected"
    
        return json.dumps({"message": return_message}),status

def check_user(user_id):
    cursor = db_conn.cursor(cursor_factory=RealDictCursor)
    try:
        select_query = 'Select client_id from client where client_id = %s '
        cursor.execute(select_query, (user_id,))
        rowcount = cursor.rowcount
        if (rowcount == 0):
            return json.dumps({"message": "user not exists"})
        else:
            select_query = 'select * from client where client_id = %s'
            cursor.execute(select_query, (user_id,))
            return json.dumps({"message": "user exists", "user": cursor.fetchone()})

    except psycopg2.Error as e:
        print(e)
        return json.dumps({"message": "Server error"})
    except psycopg2.InterfaceError as exc:
        print(exc.message)
        psycopg2.connect(host=host, port=port,database=dbname, user=user, password=pw)
        db_conn.commit()
        return json.dumps({"message": "Reconnection .."})


def delete_from_user(user_id):
    try:
        select_query = 'Delete from data where user_id = %s '
        cursor.execute(select_query, (user_id,))
        rowcount = cursor.rowcount
        if (rowcount == 0):
            return json.dumps({"message": "user not exists"})
        else:

            return json.dumps({"message": "data deleted "})

    except psycopg2.Error as e:
        print(e)
        return json.dumps({"message": "Server error"})
    except psycopg2.InterfaceError as exc:
            print(exc.message)
            psycopg2.connect(host=host, port=port,database=dbname, user=user, password=pw)
            db_conn.commit()
            return json.dumps({"message": "Reconnection .."})

@app.route("/api/createUser", methods=['POST'])
def createUser():

    reqBody = request.get_json()
    if not ('clientName' in reqBody and 'languages' in reqBody):
        return json.dumps("client Name or language key is missing"), 400
    else:
        clientName = reqBody['clientName']
        languages = reqBody['languages']
        
        if (clientName == "" or languages == ""):
            return json.dumps("client Name or languages is missing"), 400
        else:
            if json.loads(check_user2(clientName))['message'] == "user exists":
                return json.dumps("user exists")
            else:
                try:
                    query = "Insert into client (client_name) values (%s)"
                    cursor.execute(query, (clientName,))
                    db_conn.commit()
                    for language in languages:

                        port = random.randint(10000, 12000)
                        select_ports = 'select port from languages'
                        cursor.execute(select_ports)
                        ports = cursor.fetchall()
                        while not (port in ports):
                            port = random.randint(10000, 12000)
                            ports.append(port)
                    #ansible // hon badi ello 5od l port w language as arguments to rasa w sha8elon there
                        val='No'
                        while val != 'Yes':
                            val = subprocess.check_call("./create.sh  {} {}".format(port,language),shell=True)
                            print(val)
                        
                        #get last inserted id and insert into langaues table this user_id 
                        cursor.execute("INSERT INTO public.languages(client_id, language, port) VALUES ((Select currval(pg_get_serial_sequence('client','client_id' ))), %s, %s)",(language,port))
                        db_conn.commit()
            
                    return json.dumps({"message":"Client successfully created"  }),200

                except psycopg2.Error as e:
                        print(e)
                        return json.dumps({"message":"Error in creating client"}), 400

@ app.route("/api/trainModel", methods=['POST'])
def trainModel():
    reqBody = request.get_json()
    if not ('id' in reqBody ):
        return json.dumps("id  key is missing"), 400
    else:
        user_id = reqBody['id']
        if (user_id == "" ):
            return json.dumps("id is missing"), 400
        else:
            user=json.loads(check_user(user_id))
            if user['message'] == "No user":
                return json.dumps("user doesn't exists")
            else:
                languages=[]
                training_examples=[]
                try:
                    query = 'SELECT DISTINCT language FROM data where user_id = %s '
                    cursor.execute(query, (user_id,))
                    languages = cursor.fetchall()
                    print(languages)
                    languages = [item for sublist in languages for item in sublist]
                    print(languages)
                    for language in languages:
                        print(language)
   
                        get_training_data_per_lan="Select data from data where user_id=%s and language=%s"
                        cursor.execute(get_training_data_per_lan, (user_id,language))
                        training_examples=cursor.fetchall()
                        training_examples = [item for sublist in training_examples for item in sublist]
                        print(training_examples)
                        cjson = createJsonFile(training_examples)
                        print(cjson)
                        file=language
                        ext='.yml'
                        file="".join([file, ext])
                        print(file)
                        with open(file, 'r') as f:
                            config_file = f.read()
                            print(config_file)
                        print(language)
                        get_port_per_lan="Select port from languages where client_id=%s and language=%s"
                        cursor.execute(get_port_per_lan, (user_id,language))
                        port=cursor.fetchone()[0]
                        print(port)

                        address='http://0.0.0.0:'
                        port=str(port)
                        path='/model/train'
                        url=address+port+path
                        print(url)
                        payload = {
                            "nlu": cjson,
                            "config": config_file
                        }
                        x = requests.post(url, json=payload)

                        print(x.headers)
                        print(x.headers.get('filename'))

                        model_name = x.headers.get('filename')
        

                        shutil.move("/home/sarahattal/models/models/"+model_name,
                                                        "/home/sarahattal/models/models/"+str(port)+".tar.gz")
                        model_path = "/home/sarahattal/models/models/"+str(port)+".tar.gz"
                        print(model_path)

                        path2="/model"
                        url2 = address+port+path2
                        payload2 = {
                            "model_file": model_path
                        }
                        z = requests.put(url2, json=payload2)
                        

                    return "Done"


                except psycopg2.Error as e:
                    print(e)
                    return json.dumps({"message":"Server error"}),500
                    
                

@ app.route("/api/getClassification", methods=['POST'])
def getClassification():
    reqBody = request.get_json()
    classifications = []
    messages = reqBody['message']
    
    if not ('id' in reqBody ):
        return json.dumps("id  key is missing"), 400
    else:
        user_id = reqBody['id']
       

        if (user_id == ""):
            return json.dumps("id or language is missing"), 400
        else:
            if json.loads(check_user(user_id))['message'] == "No user":
                return json.dumps("user doesn't exists")
            else:

                for i in range(len(messages)):
                    language=detect_language(messages[i]).replace('"','')
                    get_port_per_lan="Select port from languages where client_id=%s and language=%s"

                    try:
                        cursor.execute(get_port_per_lan, (user_id,language))
                        port=cursor.fetchone()[0]
                        print(port)
                    except:
                        print("error")
                    
                    address='http://0.0.0.0:'
               
                    path='/model/parse'
                    url=address+port+path

                    payload = {
                        "text": messages[i],
                    }
                    x = requests.post(url, json=payload)
                    x = json.loads(x.text)
                    intent = x['intent']['name']
                    confidence = x['intent']['confidence']
                    classifications.append(
                        {"message": messages[i], "intent": intent, "confidence": confidence})

                return json.dumps(classifications)

@ app.route("/api/getClassificationFromFile", methods=['POST'])
def getClassificationFromFile():
    
    if not ('id' in request.values and 'language' in request.values):
        return json.dumps({"message": "id or language key is missing"}), 400
    else:
        user_id = request.values.get("id")
        language = request.values.get("language")
        
        if (language == "" or user_id == ""):
            return json.dumps({"message": "id or language is missing"}), 400
        else:
            if request.files['file'].filename == "":
                return json.dumps({"message": "No file is selected"}), 400
            else:
                file = request.files['file'].filename
                with open(file) as json_file:
                    data = json.load(json_file)
                    messages = data['messages']

                    port = json.loads(check_user(user_id,language))['user']['port']
                    print(port)
                    classifications = []
                    
                    address='http://0.0.0.0:'
                    port=str(port)
                    path='/model/parse'
                    url=address+port+path
                    print(url)

                    for i in range(len(messages)):
                      
                        payload = {
                            "text": messages[i],
                            }
                        x = requests.post(url, json=payload)
                        x = json.loads(x.text)
                        intent = x['intent']['name']
                        confidence = x['intent']['confidence']

                        classifications.append(
                            {"message": messages[i], "intent": intent, "confidence": confidence})

                    return json.dumps(classifications)


@app.route("/api/getUserInfo",methods=['POST'])
def getUserInfo():
    reqBody = request.get_json()
    
    if 'id' in reqBody:
        user_id = reqBody['id']
        
        user=json.loads(check_user(user_id,))
        if user['message'] == "user not exists":
            return json.dumps("user doesn't exists")
        else:
            return json.dumps(user['user'])
         
    if 'username' in reqBody:
        username = reqBody['username']
       
        user=json.loads(check_user2(username,))
        if user['message'] == "user not exists":
            return json.dumps("user doesn't exists")
        else:
            return json.dumps(user['user'])

    else:
        return json.dumps("id or language is missing"), 400

#ansible
@app.route("/api/service",methods=['POST'])
def service():
    reqBody = request.get_json()

    if not ('id' in reqBody and 'language' in reqBody and 'status' in reqBody):
                return json.dumps("id or language or status to update key is missing"), 400
    else:
        user_id = reqBody['id']
        status=reqBody['status']
        user=json.loads(check_user(user_id))
        if user['message'] == "user not exists":
            return json.dumps("user doesn't exists"),400
        else:
            if (status =="stop" or status=="start" or status=="restart"):
                get_ports="Select port from languages where client_id=%s"
                try:
                        cursor.execute(get_ports, (user_id))
                        ports=cursor.fetchall()
                        ports_list = [item for sublist in ports for item in sublist]

                        for port in ports_list:
                            val = subprocess.check_call("systemctl --user {} nlp@{}".format(status,port),shell=True)
                            ##if (val='No') need to be checket with annsible output 
                            return json.dumps({"message":"status: "+status+" is done" })
                except psycopg2.Error as e:
                    print(e)
                    return json.dumps({"message": "Server error"})
                except psycopg2.InterfaceError as exc:
                        print(exc.message)
                        psycopg2.connect(host=host, port=port,database=dbname, user=user, password=pw)
                        db_conn.commit()
                        return json.dumps({"message": "Reconnection .."})
            else:
                return json.dumps({"message":"status: must be stop or start or restart" })

                
              #  val = subprocess.check_call("systemctl --user stop nlp@'%s'" % port, shell=True)



@app.route("/api/deleteUser", methods=['DELETE'])
def delete():
    reqBody = request.get_json()
    if not ('id' in reqBody and 'language' in reqBody):
        return json.dumps("id or language key is missing"), 400
    else:
        user_id = reqBody['id']
        language = reqBody['language']

        if (user_id == "" or language == ""):
            return json.dumps("id or language is missing"), 400
        else:
            user=json.loads(check_user(user_id,language))
            if user['message'] == "No user":
                return json.dumps("user doesn't exists")
            else:
                port=user['user']['port']
                #ansible
                val = subprocess.check_call("systemctl --user stop nlp@'%s'" % port, shell=True)
                model_path = "/home/sarah/Desktop/models/models/"+str(port)+".tar.gz"
                val = subprocess.check_call("rm -r '%s'" % model_path, shell=True)

                try:
                    sql_delete_query = 'Delete from "user" where user_id = %s and language=%s'
                    cursor.execute(sql_delete_query, (user_id,language ))
                    db_conn.commit()
                    rowcount = cursor.rowcount
                    if (rowcount==0):
                        return_message="id doesn't exists"
                    else:
                        return_message="Successfully deleted"
                        status=200

                except psycopg2.Error as e:
                        print(e)
                        status=500
                        return_message = "Server error"
                except psycopg2.InterfaceError as exc:
                        print(exc.message)
                        psycopg2.connect(host=host, port=port,database=dbname, user=user, password=pw)
                        db_conn.commit()
                        status=500
                        return_message = "Reconnected"
    
            return json.dumps({"message": return_message}),status
                



def check_user2(clientName):
    cursor = db_conn.cursor(cursor_factory=RealDictCursor)
    try:
        select_query = 'Select client_name from client where client_name = %s '
        cursor.execute(select_query, (clientName, ))
        rowcount = cursor.rowcount
        if (rowcount == 0):
            return json.dumps({"message": "user not exists"})
        else:
            select_query = 'select * from "client" where client_name = %s'
            cursor.execute(select_query, (clientName,))
            return json.dumps({"message": "user exists", "user": cursor.fetchone()})

    except psycopg2.Error as e:
        print(e)
        return json.dumps({"message": "Server error"})

def detect_language(text):
    detector = Detector(text) 
    return json.dumps(detector.language.code)
    

@app.route("/hello", methods=['POST'])
def hello():
    user_id=33
    language='en'
    
    
    get_training_data_per_lan="Select data from data where user_id=%s and language=%s"
    cursor.execute(get_training_data_per_lan, (user_id,language))
    training_examples=cursor.fetchall()
    training_examples = [item for sublist in training_examples for item in sublist]
    print(training_examples)
    cjson = createJsonFile(training_examples)
    print(cjson)
    file=language
    ext='.yml'
    file="".join([file, ext])
    print(file)
    with open(file, 'r') as f:
        config_file = f.read()
        print(config_file)
    print(language)
    get_port_per_lan="Select port from languages where client_id=%s and language=%s"
    cursor.execute(get_port_per_lan, (user_id,language))
    port=cursor.fetchone()[0]
    print(port)

    address='http://0.0.0.0:'
    port=str(port)
    path='/model/train'
    url=address+port+path
    print(url)
    payload = {
        "nlu": cjson,
        "config": config_file
    }
    x = requests.post(url, json=payload)

    print(x.headers)
    print(x.headers.get('filename'))
    model_name = x.headers.get('filename')
    shutil.move("/home/sarahattal/models/models/"+model_name,
                                    "/home/sarahattal/models/models/"+str(port)+".tar.gz")
    model_path = "/home/sarahattal/models/models/"+str(port)+".tar.gz"
    print(model_path)

    path2="/model"
    url2 = address+port+path2
    payload2 = {
        "model_file": model_path
    }
    z = requests.put(url2, json=payload2)
                        

    return "Done"



if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
