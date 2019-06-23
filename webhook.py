import json # Parses JSN into a Python dictionary or list. 
import os 
import requests

# Flask is a micro web framework written in Python. It is classified as a microframework because it does not require particular tools or libraries. 
from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)

@app.route('/webhook', methods=['POST']) # A decorator (@ symbol) that tells Flask should trigger our function, instead of just running the body of our function directly. By default, Flack route responds to GET requests. This can be altered by providing methods argument to route() decorator.
def webhook(): # method app.route decorators create

    # Parses the incoming JSON request data and print
    req = request.get_json(silent=True, force=True)
    print('Next printing the incoming JSON')
    print(json.dumps(req, indent=4))
    
    # Next, we have to (1) extract the parameters needed from the incoming request -> (2) query the Open Weather API ->
    # -> (3) construct the response -> (4) Send response to Dialogflow
    res = makeResponse(req)    
    res = json.dumps(res, indent=4)

    r = make_response(res) # Setup the response in the right format for our Webhook response in the format that Dialogflow understand
    r.headers['Content-Type'] = 'application/json' # Content type required by the Dialogflow end
    return r

def makeResponse(req):
    # Obtaining parameters from Dialogflow request
    print('makeResponse function')
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    date = parameters.get("date")
    print('city=', city) # For debugging
    print('date=', date) # For debugging

    # Call to Open Weather API and get response
    #r=requests.get('http://api.openweathermap.org/data/2.5/forecast?q='+city+'&appid=35918c9922e8cac62623e7a20694eecb') #Test1
    r=requests.get('https://api.openweathermap.org/data/2.5/forecast?q='+city+',us&appid=35918c9922e8cac62623e7a20694eecb') #Test2
    json_object = r.json()
    weather=json_object['list']
    for i in len(weather):
        if date in weather[i]['dt_txt']:
            condition= weather[i]['weather'][0]['description']
            break
    speech = "The forecast for"+city+"for "+date+" is "+condition # generate speech responses for my Dialogflow agent
    return {
    "speech": speech,
    "displayText": speech,
    "source": "apiai-weather-webhook"  # ?????
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=False, port=port, host='0.0.0.0')

















