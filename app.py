import json
import os
from flask import Flask, Response, request, render_template, redirect, url_for
import requests
import urllib
app = Flask(__name__)

client_id = os.environ['CLIENT_ID']
client_secret = os.environ['CLIENT_SECRET']
host_url = os.environ['HOST_URL']

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/codes", methods=['GET'])
def codes():
    username = request.args['state']
    code = request.args['code']
    url = "https://id.twitch.tv/oauth2/token"
    headers = {"Content-Type" : "application/x-www-form-urlencoded"}
    data = {
        "client_id" : client_id,
        "client_secret" : client_secret,
        "code" : code,
        "grant_type" : "authorization_code",
        "redirect_uri" : host_url + "results"
    }
    r = requests.post(url, data=data, headers=headers)
    access_token = json.loads(r.text)['access_token']
    refresh_token = json.loads(r.text)['refresh_token']

    url = "https://api.twitch.tv/helix/users?login=" + username
    headers = {
        "Authorization" : "Bearer " + access_token,
        "Client-Id" : client_id
        }
    r = requests.get(url, headers=headers)
    broadcaster_id = json.loads(r.text)['data'][0]['id']
    return render_template('codes.html', access_token=access_token, refresh_token=refresh_token, broadcaster_id=broadcaster_id)

@app.route("/authorize", methods=['POST'])
def authorize():
    username = request.form['username']
    url = "https://id.twitch.tv/oauth2/authorize?"
    params = {
        "response_type" : "code",
        "client_id" : client_id,
        "redirect_uri" : host_url + "codes",
        "scope" : "moderator:read:followers",
        "state" : username
        }
    return redirect(url + urllib.parse.urlencode(params))

@app.route("/subscribe", methods=['POST'])
def subscribe():
    url = "https://api.twitch.tv/helix/eventsub/subscriptions"
    headers = {
        "Content-Type" : "application/json",
        "Authorization" : "Bearer " + request.json['access_token'],
        "Client-Id" : client_id
    }
    data = {
        "type" : request.json['type'],
        "version" : request.json['version'],
        "condition" : {
            "broadcaster_user_id" : request.json['condition']['broadcaster_user_id'],
            "moderator_user_id" : request.json['condition']['moderator_user_id']
        },
        "transport" : {
            "method" : request.json['transport']['method'],
            "session_id" : request.json['transport']['session_id']
        }
    }
    r = requests.post(url, data=json.dumps(data), headers=headers)
    return Response(r.text, status=r.status_code, mimetype='application/json')


@app.route("/refresh", methods=['POST'])
def refresh():
    url = "https://id.twitch.tv/oauth2/token"
    headers = {
        "Content-Type" : "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type" : "refresh_token",
        "refresh_token" : request.json['refresh_token'],
        "client_id" : client_id,
        "client_secret" : client_secret
    }
    r = requests.post(url, data=data, headers=headers)
    return Response(r.text, status=r.status_code, mimetype='application/json')
