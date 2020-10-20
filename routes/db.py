"""Database client."""
from .log import LOGGER
import psycopg2
from psycopg2.extras import DictCursor
import json
import pandas as pd
from routes.functions import detect_language
import random
import subprocess

from config import (
    LANGUAGES
)
class Database:
    """PostgreSQL Database class."""

    def __init__(
            self,
            DATABASE_HOST,
            DATABASE_USERNAME,
            DATABASE_PASSWORD,
            DATABASE_PORT,
            DATABASE_NAME
        ):
        self.host = DATABASE_HOST
        self.username = DATABASE_USERNAME
        self.password = DATABASE_PASSWORD
        self.port = DATABASE_PORT
        self.dbname = DATABASE_NAME
        self.conn = None

    def connect(self):
        """Connect to a Postgres database."""
        if self.conn is None:
            try:
                self.conn = psycopg2.connect(
                    host=self.host,
                    user=self.username,
                    password=self.password,
                    port=self.port,
                    dbname=self.dbname
                )
            except psycopg2.DatabaseError as e:
            
                LOGGER.error(e)
                raise e
            finally:
                LOGGER.info('Connection opened successfully.')


    def check_user(self,user_id):
        self.connect()
        select_query = 'Select client_id from client where client_id = %s '
        with self.conn.cursor() as cursor:
            try:
                
                cursor.execute(select_query, (user_id,))
                rowcount = cursor.rowcount
                print(rowcount)
                if (rowcount == 0):
                    return json.dumps({"message": "user not exists"})
                else:
                    select_query = 'select * from client where client_id = %s'
                    cursor.execute(select_query, (user_id,))
                    self.conn.commit()
                    cursor.close()
                    return json.dumps({"message": "user exists", "user": cursor.fetchone()})

            except psycopg2.Error as e:
                cursor.close()
                print(e)
                return json.dumps({"message": "Server error"})
            except psycopg2.InterfaceError as exc:
                self.connect()
                cursor = self.conn.cursor()


    def get_data_list(self,user_id):
        self.connect()
        query = 'Select data from data where user_id = %s '
        with self.conn.cursor() as cursor:
            try:
                cursor.execute(query, (user_id,))
                data_list = cursor.fetchall()
                self.conn.commit()
                cursor.close()
                return json.dumps(data_list)         
            except psycopg2.Error as e:
                print(e)
                return json.dumps({"message":"Server error"}),500
            except psycopg2.InterfaceError as exc:
                self.connect()
                cursor = self.conn.cursor()

    def from_csv_to_db(self,filename, user_id, intent_column, description):
        return_message = ""
        status=""
        self.connect()
        csv_data_df = pd.read_csv(filename)
        c = csv_data_df.dropna(subset=[intent_column], inplace=True)
        levels = list(csv_data_df[intent_column].unique())
        for intent in levels:
            df = csv_data_df.loc[csv_data_df[intent_column] == intent]
            texts = df[description]
            for text in texts:
                language=detect_language(text).replace('"','')
                data_to_insert = json.dumps({"intent": intent, "text": text},ensure_ascii=False)
                with self.conn.cursor() as cursor:
                    try:
                        cursor.execute('INSERT INTO data(user_id,language,data) VALUES (%s,%s,%s)', (
                        user_id, language, data_to_insert))
                        self.conn.commit()
                        cursor.close()
                        status=200
                        return_message = "Successfully inserted"
                    except psycopg2.Error as e:
                        print(e)
                        cursor.close()
                        status=500
                        return_message = "Server error"
                    except psycopg2.InterfaceError as exc:
                        self.connect()
                        cursor = self.conn.cursor()


        return json.dumps({"message": return_message}),status
 
    def from_json_to_db(self,data, user_id):
        self.connect()
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
                    with self.conn.cursor() as cursor:
                        try:
                            cursor.execute('INSERT INTO data(user_id,language,data) VALUES (%s,%s,%s)', (
                                user_id, language, data_to_insert))
                            self.conn.commit()
                            cursor.close()
                            status=200
                            return_message = "Successfully inserted"
                        except psycopg2.Error as e:
                            print(e)
                            status=500
                            return_message = "Server error"
                            cursor.close()
                        except psycopg2.InterfaceError as exc:
                            self.connect()
                            cursor = self.conn.cursor()
        return json.dumps({"message": return_message}),status


    def delete_from_user(self,user_id):
        self.connect()
        with self.conn.cursor() as cursor:
            try:
                select_query = 'Delete from data where user_id = %s '
                cursor.execute(select_query, (user_id,))
                rowcount = cursor.rowcount
                if (rowcount == 0):
                    return json.dumps({"message": "user not exists"})
                else:
                    print("deleteing")
                    return json.dumps({"message": "data deleted "})
            except psycopg2.Error as e:
                print(e)
                return json.dumps({"message": "Server error"})
            except psycopg2.InterfaceError as exc:
                self.connect()
                cursor = self.conn.cursor()

    def update_by_id(self,data,user_id):
        self.connect()
        not_exists=[]
        for i in range(len(data)):
            intent = data[i]['intent']
            text = data[i]['text']
            data_id = data[i]['id']
            
            language=detect_language(text).replace('"','')
            data_to_insert = json.dumps({"intent": intent,"text": text},ensure_ascii=False)
            print(data_to_insert)
            with self.conn.cursor() as cursor:
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
                        self.conn.commit()
                        return_message="Successfully Updated"
                        status=200
                except psycopg2.Error as e:
                    print(e)
                    return_message="Server error"
                    status=500
                except psycopg2.InterfaceError as exc:
                    self.connect()
                    cursor = self.conn.cursor()

        return json.dumps({"message":return_message}),status

    def delete_by_id(self,ids,user_id):
        self.connect()
        not_exists = []
        with self.conn.cursor() as cursor:
            for i in range(len(ids)):
                data_id = ids[i]
                s = 'DELETE FROM data WHERE data_id=%s and user_id=%s'
                
                try:
                    cursor.execute(s, (data_id, user_id))
                    self.conn.commit()
                    rowcount = cursor.rowcount
                    if (rowcount == 0):
                        str1 = " "
                        not_exists.append((str(data_id)))
                        str1 = str1.join(not_exists)
                        print(str1)
                        return_message = "id " + str1+" doesn't exists"
                        status=400
                    else:
                        self.conn.commit()
                        return_message="Successfully deleted"
                        status=200

                except psycopg2.Error as e:
                    print(e)
                    return_message="Server error Not deleted"
                    status=500
            
            return json.dumps({"message":return_message}),status

    def check_user_by_name(self,clientName):
        self.connect()
        select_query = 'Select client_name from client where client_name = %s '
        with self.conn.cursor() as cursor:
            try:
                
                cursor.execute(select_query, (clientName,))
                rowcount = cursor.rowcount
                if (rowcount == 0):
                    return json.dumps({"message": "user not exists"})
                else:
                    select_query = 'select * from "client" where client_name = %s'
                    cursor.execute(select_query, (clientName,))
                    self.conn.commit()
                    cursor.close()
                    return json.dumps({"message": "user exists", "user": cursor.fetchone()})

            except psycopg2.Error as e:
                cursor.close()
                print(e)
                return json.dumps({"message": "Server error"})
            except psycopg2.InterfaceError as exc:
                self.connect()
                cursor = self.conn.cursor()

    def get_languages(self,user_id):
        self.connect()
        query = 'SELECT DISTINCT language FROM data where user_id = %s '
        with self.conn.cursor() as cursor:
            try:
                cursor.execute(query, (user_id,))
                languages = cursor.fetchall()
                print(languages)
                languages = [item for sublist in languages for item in sublist]
                return languages
            
            except psycopg2.Error as e:
                cursor.close()
                print(e)
                return json.dumps({"message": "Server error"})
            except psycopg2.InterfaceError as exc:
                self.connect()
                cursor = self.conn.cursor()
        
    def get_training_data_per_lan(self,user_id,language):
        self.connect()
        get_training_data_per_lan_query="Select data from data where user_id=%s and language=%s"
        with self.conn.cursor() as cursor:
            try:
                cursor.execute(get_training_data_per_lan_query, (user_id,language))
                training_examples = cursor.fetchall()
                training_examples = [item for sublist in training_examples for item in sublist]
                return training_examples
            
            except psycopg2.Error as e:
                cursor.close()
                print(e)
                return json.dumps({"message": "Server error"})
            except psycopg2.InterfaceError as exc:
                self.connect()
                cursor = self.conn.cursor()

    def get_port_per_lan(self,user_id,language):
        self.connect()
        get_port_per_lan_query="Select port from languages where client_id=%s and language=%s"
        with self.conn.cursor() as cursor:
            try:
                cursor.execute(get_port_per_lan_query, (user_id,language))
                port=cursor.fetchone()[0]
                print(port)
                return port
            except psycopg2.Error as e:
                cursor.close()
                print(e)
                return json.dumps({"message": "Server error"})
            except psycopg2.InterfaceError as exc:
                self.connect()
                cursor = self.conn.cursor()

    def get_ports(self,user_id):
        self.connect()
        get_ports="Select port from languages where client_id=%s"
        with self.conn.cursor() as cursor:
            try:
                cursor.execute(get_ports, (user_id))
                ports=cursor.fetchall()
                ports_list = [item for sublist in ports for item in sublist]
                return ports_list
            
            except psycopg2.Error as e:
                cursor.close()
                print(e)
                return json.dumps({"message": "Server error"})
            except psycopg2.InterfaceError as exc:
                self.connect()
                cursor = self.conn.cursor()





    def create_user_ports_per_languages(self,clientName):
        self.connect()
        insert_query="Insert into client (client_name) values (%s)"
        with self.conn.cursor() as cursor:
            try:
                cursor.execute(insert_query, (clientName,))
                self.conn.commit()
                for language in LANGUAGES:
                    val='No'
                    while val != 'Yes':
                        port = random.randint(10000, 12000)
                        select_ports = 'select port from languages'
                        cursor.execute(select_ports)
                        ports = cursor.fetchall()
                        while not (port in ports):
                            port = random.randint(10000, 12000)
                            ports.append(port)
                         #check generated port directly from database ma3 l ansible 
                    #ansible // hon badi ello 5od l port w language as arguments to rasa w sha8elon there
                    
                        val = subprocess.check_call("./create.sh  {} {}".format(port,language),shell=True)
                        print(val)

                        #get last inserted id and insert into langaues table this user_id 
                        cursor.execute("INSERT INTO public.languages(client_id, language, port) VALUES ((Select currval(pg_get_serial_sequence('client','client_id' ))), %s, %s)",(language,port))
                        self.conn.commit()
                cursor.close()
                return json.dumps({"message":"Client successfully created"  }),200
            
            except psycopg2.Error as e:
                cursor.close()
                print(e)
                return json.dumps({"message": "Server error"})
            except psycopg2.InterfaceError as exc:
                self.connect()
                cursor = self.conn.cursor()



                