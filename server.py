#!/bin/bash
'''
  Author: Girik Malik
  gmalik@ccs.neu.edu
  http://www.ccs.neu.edu/~gmalik/

  The code assumes your videos to be in a directory, segregated in different sub-directories based on the conditions. 
  It then randomly generates a number that can be used to append to the video url for rendering the video on a webpage.
  The dictionary 'experiments' describes the structure of experiments, that remains fixed for all participants, wherein
  everyone gets to see the same condition at the same trial, but a different video chosen randomly from that condition.

  There is also separate support for catch trials.

  Within the consent function, where the sessions are set, there can be a check to see if the participant has done the experiment already. 
  The experiment is limited to be run only on computers using a chrome browser due to unsupported video rendering types in firefox.

  The code generates a separate csv file for every user's responses, with the same name as the unique code given to them
  at the end of the experiment. The code can be pasted on MTurk or any other website to confirm the completion of experiment. 

  The server expects the hit to have the following structure:
    yoursite.com/?workerId=something&hitId=something&assignmentId=something
  This can however be changed or turned off in the consent function. 
  Please ensure that you remove the subsequent use of these variables from the code as well
'''
from flask import Flask, render_template, request, redirect, url_for, make_response, session
import csv
import numpy as np
import random
import time
import datetime
import os
import hashlib

app = Flask(__name__)
app.secret_key = str(os.getenv("secret_key"))

# @app.route("/")
# def hello():
#   return render_template("index.html")
MAX_EXP = 72 # maximum number of experiments to show
MAX_WARMUP = 12 # maximum number of warmup trials to show before starting the final experiment
REST = 10 # maximum number of experiments to show before showing a rest screen with progress bar

# experiments = {0: "64_15_0", 1: "64_1_0", 2: "64_15_1", 3: "128_26_1", 4: "128_26_1", 5: "64_6_0", 6: "64_15_0", 7: "128_1_1", 8: "128_26_1", 9: "128_26_0", 10: "64_15_0", 11: "128_26_1", 12: "64_1_1", 13: "128_26_1", 14: "128_26_0", 15: "128_26_0", 16: "64_15_1", 17: "64_15_1", 18: "64_6_1", 19: "128_26_0", 20: "64_15_1", 21: "128_1_0", 22: "128_1_1", 23: "64_15_0", 24: "128_26_1", 25: "64_15_0", 26: "128_26_0", 27: "128_26_0", 28: "128_26_0", 29: "64_15_0", 30: "64_1_0", 31: "64_15_1", 32: "64_15_0", 33: "64_15_0", 34: "128_26_1", 35: "128_26_0", 36: "128_26_0", 37: "128_26_0", 38: "64_15_1", 39: "128_26_0", 40: "64_1_1", 41: "64_15_1", 42: "64_15_1", 43: "128_26_1", 44: "64_15_1", 45: "64_15_1", 46: "64_15_0", 47: "128_26_1", 48: "64_15_0", 49: "64_15_1", 50: "128_26_0", 51: "64_15_0", 52: "128_26_1", 53: "64_15_1", 54: "128_26_1", 55: "128_26_0", 56: "64_15_0", 57: "64_15_1", 58: "128_26_1", 59: "64_6_0", 60: "128_26_0", 61: "128_26_0", 62: "128_26_1", 63: "128_1_0", 64: "64_6_1", 65: "64_15_0", 66: "128_26_1", 67: "64_15_1", 68: "64_15_0", 69: "64_15_0", 70: "64_15_1", 71: "128_26_1"}
experiments = {0: "64_15_1", 1: "64_26_1", 2: "64_26_1", 3: "64_15_0", 4: "64_26_1", 5: "64_1_0", 6: "128_15_1", 7: "64_26_0", 8: "128_15_0", 9: "64_15_0", 10: "64_26_1", 11: "64_1_1", 12: "128_15_1", 13: "128_15_1", 14: "128_15_1", 15: "64_26_0", 16: "128_15_0", 17: "128_1_0", 18: "64_26_1", 19: "64_15_1", 20: "64_15_0", 21: "64_26_0", 22: "128_15_0", 23: "64_6_1", 24: "128_15_0", 25: "64_15_0", 26: "64_15_1", 27: "128_15_1", 28: "128_15_1", 29: "64_6_0", 30: "64_15_0", 31: "128_15_1", 32: "64_26_0", 33: "64_15_1", 34: "128_15_1", 35: "128_1_1", 36: "64_26_0", 37: "64_26_0", 38: "64_26_1", 39: "128_15_0", 40: "128_15_0", 41: "64_1_1", 42: "64_15_0", 43: "64_15_0", 44: "64_26_1", 45: "64_15_0", 46: "64_26_1", 47: "64_6_0", 48: "64_26_0", 49: "64_26_0", 50: "128_15_1", 51: "128_15_1", 52: "64_15_1", 53: "128_1_0", 54: "128_15_0", 55: "128_15_0", 56: "64_26_1", 57: "128_15_0", 58: "64_15_1", 59: "64_6_1", 60: "64_15_1", 61: "64_26_1", 62: "128_15_0", 63: "64_15_0", 64: "64_26_0", 65: "128_1_1", 66: "64_15_1", 67: "64_15_0", 68: "64_26_0", 69: "64_15_1", 70: "64_15_1", 71: "64_1_0"}
catch_dists = ['1', '6']

path_to_videos = "Enter base path to your videos directory"



@app.route("/")
def consent():
  try:
    session.pop('assignmentId')
    session.pop('consent')
    session.pop('hitId')
    session.pop('right')
    session.pop('warmuptrial')
    session.pop('workerId')
    session.pop('wrong')
    session.pop('unique_string')
    session.pop('exp')
    session.pop('browser')
    session.pop('version')
    session.pop('platform')
    session.pop('uas')
  except:
    print("New user")

  
  browser = request.user_agent.browser
  version = request.user_agent.version and int(request.user_agent.version.split('.')[0])
  platform = request.user_agent.platform
  uas = request.user_agent.string

  if browser not in ['chrome', 'Chrome']:
    # return "We do not support "+browser+". Please use Chrome browser to continue this experiment."
    return render_template("browser_err.html", browser=browser)

  # print("Browser: ", browser)
  # print("Version: ", version)
  # print("Platform: ", platform)
  # print("UAS: ", uas)

  mobile_devices = ["android", "iphone", "blackberry", "BlackBerry", "None", None]

  if platform in mobile_devices:
    print("Browser: ", browser)
    print("Version: ", version)
    print("Platform: ", platform)
    print("UAS: ", uas)
    not_supported="Mobile devices are not supported. <br>Please use a computer with latest web browser to perform this experiment."
    # return not_supported
    return render_template("mobile_err.html")

  # get workerId, assignmentId and hitId from the url and parse them into the url and session
  try:
    workerId = request.args["workerId"]
  except:
    not_set="Your Mturk credentials are missing. Please go back to the portal and click on the right link."
    # return not_set
    return render_template("mturk_err.html")

  try:
    assignmentId = request.args["assignmentId"]
  except:
    not_set="Your Mturk credentials are missing. Please go back to the portal and click on the right link."
    # return not_set
    return render_template("mturk_err.html")

  try:
    hitId = request.args["hitId"]
  except:
    not_set="Your Mturk credentials are missing. Please go back to the portal and click on the right link."
    # return not_set
    return render_template("mturk_err.html")

  # write the variables received from Mturk into sessinon
  session["workerId"] = workerId
  session["assignmentId"] = assignmentId
  session["hitId"] = hitId
  # save the device properties
  session["browser"] = browser
  session["version"] = version
  session["platform"] = platform
  session["uas"] = uas
  return render_template("consent.html", workerId=workerId, assignmentId=assignmentId, hitId=hitId)


@app.route("/warmup", methods=["GET", "POST"])
def warmup():
  if request.method == "GET":
    return redirect(url_for('error'))
  userdata = dict(request.form)
  print(userdata)
  warmuptrial=int(userdata["warmuptrial"]) # what number on trial is this
  if warmuptrial==0:
    if userdata["consent"]=="disagree":
      return redirect(url_for('decline'))
    else:
      session["consent"] = "agree"
    text="Let's get you acquainted with our task."
  else:
    text="Here is another video for you to judge."

  
  right=int(userdata["r"])
  wrong=int(userdata["w"])

  with open('data/warmup_trial_videos.csv') as csv_file:
    data = csv.reader(csv_file, delimiter=',')
    first_line = True
    videos = []
    for row in data:
      if not first_line:
        videos.append({
          "video_url": row[0],
          "label": row[1]
        })
      else:
        first_line = False
    print(videos[warmuptrial])
    return render_template("warmup.html", videos=[videos[warmuptrial]], warmuptrial=warmuptrial, r=right, w=wrong, text=text)


@app.route("/submitwarmup", methods=["GET", "POST"])
def submitwarmup():
  if request.method == "GET":
    return redirect(url_for('error'))
  elif request.method == "POST":
    userdata = dict(request.form)
    print(userdata)
    video = userdata["video_url"]
    warmuptrial = int(userdata["warmuptrial"])
    right = int(userdata["r"])
    wrong = int(userdata["w"])
    label = int(userdata["label"])
    response = int(userdata["response"])
    
    if len(video) < 2 and len(response) > 1 :
      return "Please submit valid data."
    
    if response == label:
      res="Correct"
      # the user got this trial right
      right+=1
    else:
      res="Incorrect"
      wrong+=1

    # if writing warmup trials to csv file, write here. 
    # also move the md5 hash generation string from setcookie to here if writing to the same file, or generate on the fly
    

    warmuptrial+=1

    # update the session variables here
    session["warmuptrial"] = warmuptrial
    session["right"] = right
    session["wrong"] = wrong

    if warmuptrial == MAX_WARMUP:
      # "Warmup Complete." #redirect user to main trial
      return redirect(url_for('beginexp', res=res, r=right, w=wrong), code=307)
    return render_template("warmup_result.html", res=res, warmuptrial=warmuptrial, r=right, w=wrong)
    
    
    # ip_addr = request.remote_addr
    # timestamp = datetime.datetime.now()
    # with open('data/outputs_videos.csv', mode='a') as csv_file:
      # data = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
      # data.writerow([video, response, userid, exp, ip_addr, timestamp])
  # return "Thank you!"
  # return redirect(url_for('wait', userid=userid, exp=exp), code=307)

@app.route("/beginexp", methods=["GET", "POST"])
def beginexp():
  # function to route the user to setcookies and then begins experiments
  if request.method == "GET":
    print("got GET")
    return redirect(url_for('error'))
  res=request.args['res']
  r=request.args['r']
  w=request.args['w']
  return render_template("begin_exp.html", res=res)


@app.route("/setcookie", methods=["GET", "POST"])
def setcookie():
  if request.method == "GET":
    return redirect(url_for('error'))
  userdata = dict(request.form)
  
  

  # resp.set_cookie('userID', user)
  # userid = "u1"
  # userid = session["name"]
  exp = 0      # setup the initial experiment number
  # set the unique string for the experiment based on the workerId, assignmentId and hitId from the session
  added_string = session["workerId"]+session["assignmentId"]+session["hitId"]
  unique_string = hashlib.md5(added_string.encode()).hexdigest()
  session["unique_string"] = unique_string
  session["exp"] = exp
  print(session)

  # res = make_response("Setting a cookie")
  # res = make_response(render_template('readcookie.html'))
  # res.set_cookie('userid', 'u2', max_age=60*60*24*365*2, domain='129.10.127.229')
  # print(("Setting cookie"))
  return redirect(url_for('experiment', exp=exp), code=307)
  

@app.route("/experiment", methods=["GET", "POST"])
def experiment():
  # prevent people from hard refreshing the page
  if request.method == "GET":
    return redirect(url_for('error'))
  # userdata = dict(request.form)
  # if userdata["consent"]=="disagree":
  #   return redirect(url_for('decline'))

  # userid = request.cookies.get('userid')
  # userid = request.args['userid']
  # userid = session["name"]
  exp = int(request.args['exp'])
  # userid = 'default'
  # print("USERID: ", userid)

  # do some authentication checking here
  # like what is the session consent 
  # if the user took warmup trial or not
  # if there is an imposed right or wrong/reliability score that needs to be used

  

  start_time=time.time()

  # with open('data/tasks_videos.csv') as csv_file:
  #   data = csv.reader(csv_file, delimiter=',')
  #   first_line = True
  #   videos = []
  #   for row in data:
  #     if not first_line:
  #       videos.append({
  #         "video_url": row[0]
  #       })
  #     else:
  #       first_line = False
  #   # print(random.sample(videos, 1))
  # # return render_template("index.html", videos=videos)
  # create the path to video dynamically here
  if experiments[exp].split('_')[1] in catch_dists:
    # it is a catch trial
    end_range=499
  else:
    end_range=999
  video_path=path_to_videos+experiments[exp]+'/'+experiments[exp].split('_')[-1]+'_output_video_'+str(random.randint(0, end_range))+'.mp4'
  videos = []
  videos.append({"video_url": video_path})
  print(videos)
  return render_template("index.html", videos=random.sample(videos, 1), exp=exp, st=start_time)

@app.route("/submit", methods=["GET", "POST"])
def submit():
  if request.method == "GET":
    return redirect(url_for('error'))
  elif request.method == "POST":
    userdata = dict(request.form)
    print(userdata)
    video = userdata["video_url"]
    exp = userdata["exp"]
    st = float(userdata["st"])
    response = userdata["response"]
    if request.headers.getlist("X-Forwarded-For"):
      ip_addr = request.headers.getlist("X-Forwarded-For")[0]
    else:
      ip_addr = request.remote_addr
    total_time = time.time()-st
    timestamp = datetime.datetime.now()
    if len(video) < 2 and len(response) > 1 :
      return "Please submit valid data."
    # with open('data/outputs_videos.csv', mode='a') as csv_file:
    with open('data/'+session["unique_string"]+'.csv', mode='a') as csv_file:
      data = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
      if int(exp)==0:
        data.writerow(["unique_string","worker_id","assignment_id","hit_id","video_url","response","experiment_number","ip_address","time_taken","submission_timestamp", "correct_during_trial", "incorrect_during_trial", "device_properties"])
      data.writerow([session["unique_string"], session["workerId"], session["assignmentId"], session["hitId"], video, response, exp, ip_addr, total_time, timestamp, session["right"], session["wrong"], str(session["browser"])+" "+str(session["version"])+" "+str(session["platform"])+" "+str(session["uas"])])
  # return "Thank you!"
  return redirect(url_for('wait', exp=exp), code=307)

@app.route("/wait", methods=["GET", "POST"])
def wait():
  if request.method == "GET":
    return redirect(url_for('error'))
  # userid=request.args["userid"]
  exp = request.args["exp"]
  # time.sleep(2)
  # var="u1"
  # print({"Refresh": "3; url="+url_for('experiment',user=var)})
  # return render_template("wait.html"), {"Refresh": "3; url="+url_for('experiment')}
  return render_template("wait.html", exp=exp)
  # time.sleep(2)
  # return redirect(url_for('experiment'), code=307)

@app.route("/gotoexp", methods=["GET", "POST"])
def gotoexp():
  if request.method == "GET":
    redirect(url_for('error'))
  # time.sleep(2)
  userdata = dict(request.form)
  # userid = userdata["userid"]
  exp = int(userdata["exp"]) #convert experiment number from string to int to perform numerical operations on it

  # check here if the user has already completed n stimulus surveys and should be given the code to put on MTurk
  exp+=1
  session["exp"] = exp
  if exp == MAX_EXP:
    return redirect(url_for('complete'), code=307)
  elif exp%REST == 0:
    return redirect(url_for('rest'), code=307)

  return redirect(url_for('experiment', exp=exp), code=307)

@app.route("/complete", methods=["GET", "POST"])
def complete():
  if request.method == "GET":
    return redirect(url_for('error'))
  # return a render_template(complete.html) and pass the unique string as argument
  # return "Your experiment is now complete. Please paste the below code to your Mechanical Turk account to process the payment. Thank you for participating in our study. Please close browser window once you paste the code."
  print(session)
  return render_template("complete.html", unique_string=session["unique_string"])

@app.route("/rest", methods=["GET", "POST"])
def rest():
  if request.method == "GET":
    return redirect(url_for('error'))
  exp=session["exp"]
  max_exp=MAX_EXP

  return render_template("rest.html", exp=exp, max_exp=max_exp, progress=100*(float(exp)/max_exp))

@app.route("/resume_exp", methods=["GET", "POST"])
def resume_exp():
  if request.method == "GET":
    return redirect(url_for('error'))

  # the form on rest.html also returns the exp-1.
  # if taking userdata from there instead of the session,
  # don't forget to increment exp
  exp = session["exp"]

  return redirect(url_for('experiment', exp=exp), code=307)


  
  

@app.route("/error")
def error():
  return "An error occured. Please start from your link again!"

@app.route("/decline")
def decline():
  return "You have declined the HIT. Please close your web browser."

if __name__ == "__main__":
  # app.run()
  app.run(host="0.0.0.0", debug=False)

