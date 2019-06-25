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
    print('Next printing the incoming JSON')
    print(json.dumps(req, indent=4))
    
    # Next, we have to (1) extract the parameters needed from the incoming request -> (2) query the Open Weather API ->
    # -> (3) construct the response -> (4) Send response to Dialogflow
    #res = makeResponse(req)    
    #res = json.dumps(res, indent=4)

    #r = make_response(res) # Setup the response in the right format for our Webhook response in the format that Dialogflow understand
    #r.headers['Content-Type'] = 'application/json' # Content type required by the Dialogflow end
 
    return make_response(jsonify(makeResponse(req))) # Debugging, return sample from https://www.pragnakalp.com/dialogflow-fulfillment-webhook-tutorial/

    #return r



def makeResponse(req):
    # Obtaining parameters from Dialogflow request
    print('makeResponse function')
    result = req.get("queryResult")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    date = parameters.get("date")
    
    # Format Dialogflow date variable to do comparison with OpenWeatherMap JSON date format
    dateString = str(date)  
    dateString = dateString.replace("T", " ")
    dateString = dateString.split("+")[0]


    print('printing city=', city) # For debugging
    print('printing date=', date) # For debugging

    # Call to Open Weather API and get response
    #r=requests.get('http://api.openweathermap.org/data/2.5/forecast?q='+city+'&appid=35918c9922e8cac62623e7a20694eecb') #Test1
    r=requests.get('https://api.openweathermap.org/data/2.5/forecast?q='+city+',us&appid=35918c9922e8cac62623e7a20694eecb') #Test2
    json_object = r.json()
    print ('printing json openweathermap object') # Debugging
    print (json_object) # Debugging

    weather=json_object['list']
    for i in range(0,30): # It should be len(weather):
        if dateString in weather[i]['dt_txt']:
            condition= weather[i]['weather'][0]['description']
            print ('printing condition', condition) # For debugging
            break
    speech = "The forecast for "+city+" for "+date+" is "+condition # generate speech responses for my Dialogflow agent
    print ('printing the speech') # For debugging
    print (speech) # For debugging
    
    return {'fulfillmentText': speech}

    '''
    return {
    "speech": speech,
    "displayText": speech,
    "source": "apiai-weather-webhook"
    }
    '''



if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=False, port=port, host='0.0.0.0')

















