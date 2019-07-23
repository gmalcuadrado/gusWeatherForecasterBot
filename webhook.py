import json # Parses JSON into a Python dictionary or list. 
import os
import requests
import pandas as pd
import boto3 # Amazon Web Services (AWS) SDK for Python. When I try to import it, ModuleNotFoundError: No module named 'boto3' and Python app does not work
import botocore
from botocore.exceptions import ClientError
import logging


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
    
    # Depending on parameter obtained, we solve GSM or Weather question
    if parameters.get("geo-city"):
        return make_response(jsonify(makeWeatherResponse(req))) # Debugging, return sample from https://www.pragnakalp.com/dialogflow-fulfillment-webhook-tutorial/

    elif parameters.get("amount"):
        return make_response(jsonify(makeWriteGsmResponse(req)))

    else:
        return make_response(jsonify(makeReadGsmResponse(req)))



def makeWriteGsmResponse(req):

    print()
    print("makeWriteGsmResponse function")
    print()


    # Obtaining parameters from Dialogflow request    
    result = req.get("queryResult")
    parameters = result.get("parameters")
    leaveDayRequestStr = parameters.get("amount")
    
    print('printing leaveDay =', leaveDayRequestStr) # For debugging


    # Conneting to Bucket
    s3 = boto3.client('s3')
    s3Resource=boto3.resource('s3')

    response = s3.list_buckets()
    print()
    print("S3 bucket response: ", response)
    print()

    # CONNECT TO AMAZON S3 FILES
    bucket = "whochatbot"
    pathFileReadName = "GSM-Export/wernerj-Data.csv"
    pathFileWriteName = "GSM-Import"
    FileWriteName = "leaveRequest.csv"


    s3ReadConnObj = s3.get_object(Bucket= bucket, Key= pathFileReadName)
    #s3WriteConnObj = s3.get_object(Bucket= bucket, Key= pathFileWriteName) # File does not exist anymore!


    print()
    print("S3 read connection object: ", s3ReadConnObj)
    print()

    '''
    # DOWNLOAD FILE

    # The file disappeard this nigh!
    try:
        #s3.download_file('your_bucket','k.png','/Users/username/Desktop/k.png')
        s3.download_fileobj('whochatbot','wernerj.csv','c:/temp/python/wernerj.csv')

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "404":
            print("The object does not exist.")
        else:
            raise

    '''

    # IMPORT CSV TO PANDA DATAFRAME

    df = pd.read_csv(s3ReadConnObj['Body']) # 'Body' is a key word
    print(df) # For debugging


    # EXTRACT RELEVANT INFO FROM DATAFRAME

    remainingLeaveDayStr=df.RemainingLeave.to_string().split()[1]
    gsmName=df.GSMName.to_string().split(None, 1)[1]

    print() # For debugging
    print("Remaining days = ", remainingLeaveDayStr)
    print("GSM Name = ", gsmName)
    print() # For debugging


    # Generate response
    try:
        # This cast is to avoid passing non number value like ) #TODO: Improve this 
        leaveDayRequestInt=int(leaveDayRequestStr)
        remainingLeaveDayInt=int(remainingLeaveDayStr)
        print("leaveDayRequestInt = ", leaveDayRequestInt)
        print("remainingLeaveDayInt = ", remainingLeaveDayInt)
        print() # For debugging

        if (remainingLeaveDayInt>=leaveDayRequestInt):
            print("....insert line on CSV......")

            # UPDATE LEAVE DAY VALUE TO LOCAL FILE

            pathFile='c:\\temp\\python\\leaveREquest.csv' # TO CHANGE PATH ON HEROKU


            with open(pathFile, 'w') as f:
                f.write(leaveDayRequestStr)
                f.close
            
            # UPLOAD THE FILE
            try:
                s3Resource.Object(bucket,'GSM-Import/leaveRequest.csv').upload_file(Filename=pathFile)
            except botocore.exceptions.ClientError as e:           
                print("Error saving the file")


            # generate speech responses for my Dialogflow agent, parameter must be string
            speech = "Dear "+gsmName+"; I have sent a leave request for "+leaveDayRequestStr+" days"
            print(speech)
        else:
            speech = "Dear "+gsmName+"; you do not have enough days available ("+remainingLeaveDayStr+") for your request of "+leaveDayRequestStr+" days"
            print(speech)


        
    except ValueError:
        print("leaveDayRequestInt is not an integer = ", leaveDayRequestInt)
        print()
        speech = "Sorry, there was an issue :S "
        print(speech)







def makeReadGsmResponse(req):
    
    print()
    print("makeReadGsmResponse function")
    print()


    # CONNECT TO S3 BUCKET AND GET DATAFRAME
    
    # Conneting to Bucket
    s3 = boto3.client('s3') 
    response = s3.list_buckets()
    #print()
    #print("S3 bucket response: ", response)
    #print()

    # Getting CSV file object from Bucket
    bucket = "whochatbot"
    file_name = "GSM-Export/wernerj-Data.csv"
    s3ConnReadObj = s3.get_object(Bucket= bucket, Key= file_name)
    print()
    #print("S3 connection object: ", s3ConnReadObj)
    print()

    # Import CSV on Pandas dataframe
    df = pd.read_csv(s3ConnReadObj['Body']) # 'Body' is a key word

    print(df) # For debugging

    # EXTRACT INFO AND GENERATE RESPONSE 

    # Get the days for the StaffNumber passed
    remainingLeaveDayString=df.RemainingLeave.to_string().split()[1]
    usedLeaveDayIntString=df.UsedLeave.to_string().split()[1]
    gsmName=df.GSMName.to_string().split(None, 1)[1]
    
    print() # For debugging
    #print("remainingLeaveDayString = ", remainingLeaveDayString) # For debugging
    #print("usedLeaveDayIntString = ", usedLeaveDayIntString)
    print("GSM Name = ", gsmName)
    print() # For debugging
    
 
    # Generate response
    try:
        # This cast is to avoid passing non number value like ) #TODO: Improve this 
        remainingLeaveDayInt=int(remainingLeaveDayString)              
        print("remainingLeaveDayInt = ", remainingLeaveDayInt)

        # generate speech responses for my Dialogflow agent, parameter must be string
        speech = "My dear "+gsmName+", you have consumed "+usedLeaveDayIntString+", so you have "+remainingLeaveDayString+" days available"
    
    except ValueError:
        print("remainingLeaveDayInt is not an integer = ", remainingLeaveDayInt)
        print()
        speech = "Sorry, I did not find data on GSM :S "

  
    # Return speech to DialogFlow
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
    
    # Return speech to DialogFlow
    return {'fulfillmentText': speech}





if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=False, port=port, host='0.0.0.0')

















