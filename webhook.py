import json # Parses JSON into a Python dictionary or list. 
import os
import requests
import pandas as pd
import boto3 # Amazon Web Services (AWS) SDK for Python. When I try to import it, ModuleNotFoundError: No module named 'boto3' and Python app does not work

# Flask is a lightweight Python framework for web applications that provides the basics for URL routing and page rendering. 
from flask import Flask, jsonify, request, make_response

# Flask app should start in global layout
app = Flask(__name__)

@app.route('/webhook', methods=['GET', 'POST']) # A decorator (@ symbol) that tells Flask should trigger our function, instead of just running the body of our function directly. By default, Flack route responds to GET requests. This can be altered by providing methods argument to route() decorator.
def webhook(): # method app.route decorators create

    # Parses the incoming JSON request data and print
    req = request.get_json(silent=True, force=True)
    # print('Next printing the incoming JSON=') # For debugging
    # print(json.dumps(req, indent=4)) # For debugging
 
    result = req.get("queryResult") # TODO: Repeated req.get, pending to solve this
    parameters = result.get("parameters")
    
    if parameters.get("geo-city"):
        return make_response(jsonify(makeWeatherResponse(req))) # Debugging, return sample from https://www.pragnakalp.com/dialogflow-fulfillment-webhook-tutorial/
    else:
        print("gsm Python function")
        return make_response(jsonify(makeGsmResponse(req)))



def makeGsmResponse(req):
    # GET RESPONSE PARAMETERS: STAFF NUMBER

    result = req.get("queryResult")
    parameters = result.get("parameters")
    staffNumber = parameters.get("numberStaff")
    print("printing staff number: ", staffNumber)

    # CONNECT TO S3 BUCKET AND GET DATAFRAME
    
    # boto3 import does not work, pending to solve.
    bucket = "whochatbot"
    file_name = "whogsm.csv"
    
    s3 = boto3.client('s3') 
    response = s3.list_buckets()
    print("S3 bucket response: ", response)

    # get object and file (key) from bucket
    obj = s3.get_object(Bucket= bucket, Key= file_name) 

    df = pd.read_csv(obj['Body']) # 'Body' is a key word

    print(df)

    result=df.loc[df['StaffID'] == staffNumber].annualLeavePending


    print("the result is: ",result)
    
    '''
    gsmCsv = {'gsmName': ['ABELLA, Mr. Pablo','ABJELINA, Mr. Roy','ABOU-YOUSSEFF, Mr. Emad A.','Aguilar Rico, Mr. Enrique','Aleixandre, Mr. Carlos','Alfeo, Mr. Salvatore'],
        'surname': ['ABELLA','ABJELINA','ABOU-YOUSSEFF','Aguilar Rico','Aleixandre','Alfeo'],
        'name': ['Pablo','Roy','Emad','Enrique','Carlos','Salvatore'],
        'staffId': ['S206700','S206701','S206702','S206703','S206704','S206705'],
        'annualLeaveConsumed': ['11','4','16','21','9','15'],
        'annualLeavePending': ['15','22','10','5','17','11'],
        'effectiveDate': ['31-10-2019','14-10-2019','14-05-2019','31-11-2019','17-12-2019','15-10-2019']
        }

    df = DataFrame (gsmCsv,columns= ['gsmName', 'Surname', 'Name', 'StaffID', 'annualLeaveConsumed', 'annualLeavePending', 'effectiveDate'])
    
    print (df)

    '''


    # ITERATE DATAFRAME SEARCHING STAFF NUMBER AND GET DAYS

    # PREPARE AND RETURN RESPONSE
    
    speech = "Number of days available for "+staffNumber+" are 42 " # generate speech responses for my Dialogflow agent
    return {'fulfillmentText': speech}













def makeWeatherResponse(req):
    # Obtaining parameters from Dialogflow request
    
    result = req.get("queryResult")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    date = parameters.get("date")
    
    # print('printing city=', city) # For debugging
    # print('printing date=', date) # For debugging

    # Format Dialogflow date variable to do comparison with OpenWeatherMap JSON date format
    dateTimeFormated = str(date)  
    dateTimeFormated = dateTimeFormated.replace("T", " ")
    dateTimeFormated = dateTimeFormated.split("+")[0]
    justDate = dateTimeFormated.split(" ")[0]

    # print('printing date time formatted as weathermap=', dateTimeFormated) # For debugging
    # print('printing just date=', justDate) # For debugging 


    # Call to Open Weather API and get response
    r=requests.get('https://api.openweathermap.org/data/2.5/forecast?q='+city+',us&appid=35918c9922e8cac62623e7a20694eecb')
    json_object = r.json()
    # print ('printing json openweathermap object') # Debugging
    # print (json_object) # Debugging

    weather=json_object['list']
    for i in range(0,30): # TODO: It should be something like len(weather):, not working
        if dateTimeFormated in weather[i]['dt_txt']:
            condition= weather[i]['weather'][0]['description']
            #print ('printing condition', condition) # For debugging
            break
        # elif condition for date/time not found in weathermap, provide a forecast based just on date.
        # Found use case where forecast for today was offering a time which was not in JSON openweathermap response
        elif justDate in weather[i]['dt_txt']:
            condition= weather[i]['weather'][0]['description']
            #print ('printing condition', condition) # For debugging
            break

        else:
            condition="...sorry, city or date/time not found in WeatherMap"


            
    speech = "The forecast for "+city+" at "+dateTimeFormated+" is "+condition # generate speech responses for my Dialogflow agent
    
    # print ('printing the speech') # For debugging
    # print (speech) # For debugging
    
    return {'fulfillmentText': speech}


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=False, port=port, host='0.0.0.0')

















