# Import all the necessary files!
import os
import tensorflow as tf
from tensorflow.keras import layers
from tensorflow.keras import Model
from flask import Flask, request
import cv2,json
import numpy as np
from flask_cors import CORS
from tensorflow.python.keras.backend import set_session
from tensorflow.keras.models import Sequential
import base64
from datetime import datetime

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
# graph = tf.get_default_graph()
graph = tf.compat.v1.get_default_graph()

app = Flask(__name__)
CORS(app)
# sess = tf.Session()
sess = tf.compat.v1.Session()
set_session(sess)

model = tf.keras.models.load_model('model/facenet_keras.h5',compile=False)
#model.summary()

def img_to_encoding(path, model):
  img1 = cv2.imread(path, 1)
  img = img1[...,::-1]
  dim = (160, 160)
  # resize image
  if(img.shape != (160, 160, 3)):
    img = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
  x_train = np.array([img])
  embedding = model.predict(x_train)
  #print("embedding",embedding)
  return embedding

database = {}

# TO BE ADDED--Take username from frontend and call this fn
def verify(image_path, identity, database, model):
  
    encoding = img_to_encoding(image_path, model)
    dist = np.linalg.norm(encoding-database[identity])
    # print(dist)
    if dist<5:
        print("It's " + str(identity) + ", Welcome!")
        match = True
    else:
        print("It's not " + str(identity) + ", Invalid user")
        match = False
    return dist, match

@app.route('/register', methods=['POST'])
def register():
    try:
        username = request.get_json()['username']
        img_data = request.get_json()['image64']
        with open('images/'+username+'.jpg', "wb") as fh:
            fh.write(base64.b64decode(img_data[22:]))
        path = 'images/'+username+'.jpg'

        # global sess
        # global graph
        # with graph.as_default():
        #     set_session(sess)
        #     database[username] = img_to_encoding(path, model) 
        database[username] = img_to_encoding(path, model)
        # Print entries in the database
        # for (name, db_enc) in database.items():
        #     print("name--",name)    
        return json.dumps({"status": 200})
    except:
        return json.dumps({"status": 500})


def who_is_it(image_path, database, model):
    # print(image_path)
    encoding = img_to_encoding(image_path, model)
    min_dist = 1000
    # Loop over the database dictionary's names and encodings.
    for (name, db_enc) in database.items():
        dist = np.linalg.norm(encoding-db_enc)
        # Print entries in the database with distance
        # print("name--",name,"distance--",dist)
        if dist<min_dist:
            min_dist = dist
            identity = name
    # if min_dist > 5:
    #     print("Not in the database.")
    # else:
    #     print ("it's " + str(identity) + ", the distance is " + str(min_dist))
    return min_dist, identity

@app.route('/verify', methods=['POST'])
def change():
    img_data = request.get_json()['image64']
    img_name = str(int(datetime.timestamp(datetime.now())))
    with open('images/'+img_name+'.jpg', "wb") as fh:
        fh.write(base64.b64decode(img_data[22:]))
    path = 'images/'+img_name+'.jpg'
    # global sess
    # global graph
    # with graph.as_default():
    #     set_session(sess)
    #     min_dist, identity = who_is_it(path, database, model)
    min_dist, identity = who_is_it(path, database, model)
    os.remove(path)
    if min_dist < 5:
        return json.dumps({"identity": str(identity)})
    return json.dumps({"identity": 0})    
    

@app.route('/')
def index():
    return 'Hello World'

if __name__ == "__main__":
    app.run(debug=True)