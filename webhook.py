import json
import os
import requests
import pandas as pd
import boto3
import botocore
from botocore.exceptions import ClientError
import logging
from flask import Flask, jsonify, request, make_response
import datetime


# Flask app should start in global layout
app = Flask(__name__)

@app.route('/webhook', methods=['GET', 'POST']) # A decorator (@ symbol) that tells Flask should trigger our function, instead of just running the body of our function directly. By default, Flack route responds to GET requests. This can be altered by providing methods argument to route() decorator.
def webhook(): # method app.route decorators create

    # Parses the incoming JSON request data and print
    req = request.get_json(silent=True, force=True)
    print()
    print('Next printing the incoming JSON=') # For debugging
    print()
    #print(json.dumps(req, indent=4)) # For debugging
 
    result = req.get("queryResult") # TODO: Repeated req.get, pending to solve this
    parameters = result.get("parameters")
    print()
    print("parameters: ", parameters)
    print()


    
    # Depending on parameter obtained, we solve GSM or Weather question
    if parameters.get("geo-city"):
        return make_response(jsonify(makeWeatherResponse(req))) # Debugging, return sample from https://www.pragnakalp.com/dialogflow-fulfillment-webhook-tutorial/

    elif parameters.get("date"):
        print("date parameter obtained")
        return make_response(jsonify(makeWriteGsmResponse(req)))

    else:
        return make_response(jsonify(makeReadGsmResponse(req)))



def makeWriteGsmResponse(req):

    print()
    print("makeWriteGsmResponse function")
    print()


    # GET PARAMETERS FROM DIALOGFLOW JSON
    result = req.get("queryResult")
    parameters = result.get("parameters")

    # Parameter output {'date': '2019-09-02T12:00:00+02:00', 'duration': {'amount': 15.0, 'unit': 'day'}}

    leaveDayRequestUnformat = parameters.get("duration")
    leaveDateRequestUnformat = parameters.get("date")


    # FORMATTING OUTPUT PARAMETERS

    # Formatting date leave request
    dateTimeFormated = str(leaveDateRequestUnformat)  
    dateTimeFormated = dateTimeFormated.replace("T", " ")
    dateTimeFormated = dateTimeFormated.split("+")[0]
    leaveDateRequestStr = dateTimeFormated.split(" ")[0]
    print("leaveDateRequestStr = ",leaveDateRequestStr)

    
    print()

    # Formatting leave days
    leaveDayRequestStr = json.dumps(leaveDayRequestUnformat) # Convert dictionary object into string
    leaveDayRequestStr = leaveDayRequestStr.split(" ")[1].split(".")[0]
    print("leaveDayRequestStr = ",leaveDayRequestStr)
    print()    

 
    # Conneting AMAZON Bucket
    s3 = boto3.client('s3')
    s3Resource=boto3.resource('s3')

    #response = s3.list_buckets()
    print()
    #print("S3 bucket response: ", response)
    print()


    # CONNECT TO AMAZON S3 FILE TO OBTAIN USER NAME AND CURRENT DAYS AVAILABLE
    bucket = "whochatbot"
    pathFileReadName = "GSM-Export/wernerj-Data.csv"
    pathFileWriteName = "GSM-Import"
    FileWriteName = "leaveRequest.csv"

    s3ReadConnObj = s3.get_object(Bucket= bucket, Key= pathFileReadName)

    print()
    #print("S3 read connection object: ", s3ReadConnObj)
    print()


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


    # CHECKS IF USER IS REQUESTING MORE DAYS THAN AVAILABLE

    try:
        leaveDayRequestInt=int(leaveDayRequestStr)
        remainingLeaveDayInt=int(remainingLeaveDayStr)

        print("leaveDayRequestInt = ", leaveDayRequestInt)
        print("remainingLeaveDayInt = ", remainingLeaveDayInt)
        print() # For debugging

    except Exception:
        print("leaveDayRequestInt = "+leaveDayRequestInt+ " or remainingLeaveDayInt = "+remainingLeaveDayInt+" is not an integer")
        print()
        speech = "Sorry, there was an issue converting parameters to integer"
        return {'fulfillmentText': speech}
        sys.exit(1)
        

    # Generate response
    
    localPathFile='c:\\temp\\python\\wernerj.csv' # TO CHANGE PATH ON HEROKU

    if (remainingLeaveDayInt>=leaveDayRequestInt):

        # Calculating Start Date and End Date 
        startDate=datetime.datetime.strptime(leaveDateRequestStr, '%Y-%m-%d')
        endDate=startDate + datetime.timedelta(days=leaveDayRequestInt)
        startDateStr="{:%d-%b-%Y}".format(startDate)
        endDateStr="{:%d-%b-%Y}".format(endDate)
        
        print("....insert line on CSV......")
        print()

        csvTxtContent="Absence Type,Absence Status,Absence Reason,Start Date,End Date/nAnnual Leave,Planned,Annual Leave - Personal Reasons,"+startDateStr+","+endDateStr


        # Inser line in Amazon file
        with open(localPathFile, 'w') as f:
            f.write(csvTxtContent)
            f.close
            
        # UPLOAD THE FILE
        try:
            s3Resource.Object(bucket,'GSM-Import/wernerj.csv').upload_file(Filename=localPathFile)

        except Exception:           
            print("Error saving the file")
            speech = "Sorry, there was an issue opening Amazon S3 file to make the leave request"
            return {'fulfillmentText': speech}
            sys.exit(1)

        # generate speech responses for my Dialogflow agent, parameter must be string
        speech = "Dear "+gsmName+"; I have sent a leave request to GSM for "+leaveDayRequestStr+" days"

    else:
        speech = "Dear "+gsmName+"; you do not have enough days available ("+remainingLeaveDayStr+") for your request of "+leaveDayRequestStr+" days"

    # Return speech to DialogFlow
    return {'fulfillmentText': speech}



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
        leaveDateRequestInt=int(remainingLeaveDayString)              
        print("leaveDateRequestInt = ", leaveDateRequestInt)

        # generate speech responses for my Dialogflow agent, parameter must be string
        speech = "Dear "+gsmName+"; you have consumed "+usedLeaveDayIntString+" days, so you still have "+remainingLeaveDayString+" days available"
    
    except ValueError:
        print("leaveDateRequestInt is not an integer = ", leaveDateRequestInt)
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

















