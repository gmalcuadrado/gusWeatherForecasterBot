import json # Parses JSN into a Python dictionary or list. 
import os 
import requests

# Flask is a micro web framework written in Python. It is classified as a microframework because it does not require particular tools or libraries. 
from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)

@app.route('/webhook', methods=['POST']) # A decorator (@ symbol) that tells Flask should trigger our function. By default, Flack route responds to GET requests. This can be altered by providing methods argument to route() decorator.
def webhook():
    req = request.get_json(silent=True, force=True)
    print(json.dumps(req, indent=4))
    
    res = makeResponse(req)
    
    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r

def makeResponse(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    date = parameters.get("date")
    r=requests.get('http://api.openweathermap.org/data/2.5/forecast?q='+city+'&appid=35918c9922e8cac62623e7a20694eecb')
    json_object = r.json()
    weather=json_object['list']
    for i in len(weather):
        if date in weather[i]['dt_txt']:
            condition= weather[i]['weather'][0]['description']
            break
    speech = "The forecast for"+city+"for "+date+" is "+condition
    return {
    "speech": speech,
    "displayText": speech,
    "source": "apiai-weather-webhook"
    }

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    print("Starting app on port %d" % port)
    app.run(debug=False, port=port, host='0.0.0.0')

















