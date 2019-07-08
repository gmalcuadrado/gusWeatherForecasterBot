import json # Parses JSN into a Python dictionary or list. 
import os 
import requests

# Flask is a lightweight Python framework for web applications that provides the basics for URL routing and page rendering. 
from flask import Flask, jsonify
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)

@app.route('/webhook', methods=['GET', 'POST']) # A decorator (@ symbol) that tells Flask should trigger our function, instead of just running the body of our function directly. By default, Flack route responds to GET requests. This can be altered by providing methods argument to route() decorator.
def webhook(): # method app.route decorators create

    # Parses the incoming JSON request data and print
    req = request.get_json(silent=True, force=True)
    # print('Next printing the incoming JSON') # For debugging
    # print(json.dumps(req, indent=4)) # For debugging
 
    return make_response(jsonify(makeResponse(req))) # Debugging, return sample from https://www.pragnakalp.com/dialogflow-fulfillment-webhook-tutorial/


def makeResponse(req):
    # Obtaining parameters from Dialogflow request
    
    result = req.get("queryResult")
    parameters = result.get("parameters")
    city = parameters.get("geo-city") # For debugging
    date = parameters.get("date") # For debugging
    
    #print('printing city=', city) # For debugging
    #print('printing date=', date) # For debugging

    # Format Dialogflow date variable to do comparison with OpenWeatherMap JSON date format
    dateTimeFormated = str(date)  
    dateTimeFormated = dateTimeFormated.replace("T", " ")
    dateTimeFormated = dateTimeFormated.split("+")[0]
    justDate = dateTimeFormated.split("+")[0]

    print('printing date time formatted as weathermap=', dateTimeFormated) # For debugging
    print('printing just date=', justDate) # For debugging


    # Call to Open Weather API and get response
    r=requests.get('https://api.openweathermap.org/data/2.5/forecast?q='+city+',us&appid=35918c9922e8cac62623e7a20694eecb')
    json_object = r.json()
    #print ('printing json openweathermap object') # Debugging
    #print (json_object) # Debugging

    weather=json_object['list']
    for i in range(0,30): # It should be something like len(weather):, not working
        if dateTimeFormated in weather[i]['dt_txt']:
            condition= weather[i]['weather'][0]['description']
            print ('printing condition', condition) # For debugging
            break
        # elif condition for date/time not found in weathermap, provide a forecast based just on date.
        # Found use case where forecast for today was offering a time which was not in JSON openweathermap response
        elif justDate in weather[i]['dt_txt']:
            condition= weather[i]['weather'][0]['description']
            print ('printing condition', condition) # For debugging
            break

        else:
            condition="City or date-time not found in WeatherMap"

            # Pending else if value is not found, print back on Dialogflow

            
    speech = "The forecast for "+city+" at "+dateTimeFormated+" is "+condition # generate speech responses for my Dialogflow agent
    
    # print ('printing the speech') # For debugging
    # print (speech) # For debugging
    
    return {'fulfillmentText': speech}


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=False, port=port, host='0.0.0.0')

















