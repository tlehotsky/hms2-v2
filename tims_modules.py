#!/usr/bin/python
# -*- coding:UTF-8 -*-


#git update 1/27/2021



from datetime import datetime
import datetime as dt
import os, shutil, glob, time, subprocess, re, sys, sqlite3, logging, smtplib
import RPi.GPIO as GPIO
from datetime import timedelta

import wiotp.sdk.application
import cloudant
from cloudant.client import Cloudant
from cloudant.query import Query
from cloudant.result import QueryResult
from cloudant.error import ResultException

#tims_modules



def tic():
	tic=int(time.perf_counter())
	return tic

def rising_callback(channel):
	#trigger event
    print ("rising event was triggered")

def RecFullDateTime():
	#date/time calc
    return time.time()

def RecTime():
	#date/time calc
    return dt.datetime.now().strftime("%H:%M:%S")

def RecDate():
	#date/time calc
    return dt.datetime.now().strftime("%m-%d-%Y")

def get_user_data():
	user_data = {}
	with open("/home/pi/hms/user_data.txt") as f:
		for line in f:
			(field, val) = line.split()
			user_data[field] = val

	# print ("cloudant organization name = ", user_data['cloud_acct_org_name'])
	# print ("cloudant account password = ", user_data['cloud_acct_pword'])
	# print ("cloudant account URL = ", user_data['cloud_act_url'])
	# print ("cloudant account API key = ", user_data['cloud_acct_API_key'])
	# print ("gmail user account name = ",user_data['gmail_user'])
	# print ("gmail user password = ",user_data['gmail_password'])
	# print ("cloudant username = ",user_data['cloud_acct_username'])
	return user_data

def send_html_email(subject,body,gmail_user,gmail_password):

	sent_from = gmail_user
	to = ["tim.lehotsky@wsp.com"]

	email_text = """\
Content-Type: "text/html"
From: %s
To: %s
Subject: %s

%s
	""" % (sent_from, ", ".join(to), subject, body)

	try:
	    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
	    server.ehlo()
	    server.login(gmail_user, gmail_password)
	    server.sendmail(sent_from, to, email_text)
	    server.close()

	    print ("Email sent!")
	    write_to_log('email sent, message body follows')
	    write_to_log(body)
	except:
	    print ("Something went wrong")
	    write_to_Error_log("error sending email, what follows is the message body")
	    write_to_Error_log(body)
	    time.sleep(10)

def send_email(subject,body,gmail_user,gmail_password):


	sent_from = gmail_user
	to = ["tim.lehotsky@wsp.com"]
	#subject = "3 Whoa Update from your SMART house"
	#body = "Hey, whats up?\n\n- You"

	email_text = """\
Content-Type: "text/plain"
From: %s
To: %s
Subject: %s

%s
	""" % (sent_from, ", ".join(to), subject, body)

	try:
	    server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
	    server.ehlo()
	    server.login(gmail_user, gmail_password)
	    server.sendmail(sent_from, to, email_text)
	    server.close()

	    print ("Email sent!")
	    write_to_log('email sent, email body follows')
	    write_to_log(body)
	except:
	    print ("Something went wrong")
	    write_to_Error_log("error sending email, what follows is the message body")
	    write_to_Error_log(body)
	    time.sleep(10)

def write_door_position_to_cloudant(door_name, door_position):
	# ACCOUNT_NAME= cloud_acct_org_name
	# USERNAME =  cloudant_username
	# PASSWORD =  cloud_acct_pword
	# URL= cloud_act_url
	# API_KEY= cloud_acct_API_key
	DATABASE_NAME="door_position"
	#print ("sub to write data to cloudant - SENSOR ID = ", sensor_id, "LOCATION = ", local, "TEMP = ", temp)
	user_data=get_user_data()
	client = Cloudant(user_data['cloud_acct_username'],user_data['cloud_acct_pword'], url = user_data['cloud_act_url'] )
	client.connect()
	my_database = client[DATABASE_NAME]

	json_document = {
	     "n": door_name,
	     "p": door_position,
	     "t": dt.datetime.now().strftime("%H:%M:%S"),
	     "d": dt.datetime.now().strftime("%m-%d-%Y")
	}

	new_document = my_database.create_document(json_document)
	client.disconnect()

def write_to_cloudant(sensor_id, local, temp):
	# ACCOUNT_NAME= cloud_acct_org_name
	# USERNAME =  cloudant_username
	# PASSWORD =  cloud_acct_pword
	# URL= cloud_act_url
	# API_KEY= cloud_acct_API_key
	DATABASE_NAME="temps"
	print ("sub to write data to cloudant - SENSOR ID = ", sensor_id, "LOCATION = ", local, "TEMP = ", temp)
	user_data=get_user_data()
	client = Cloudant(user_data['cloud_acct_username'],user_data['cloud_acct_pword'], url = user_data['cloud_act_url'] )
	
	try:
		client.connect()

	except:
		write_to_Error_log("error connecting to cloudant TEMP database, will sleep for 30 seconds and then try again")
		time.sleep(30)

		try:
			client.connect()

		except:
			write_to_Error_log("2nd error in a row connecting to cloudant TEMP database, will sleep for 5 minute and then skip")
			time.sleep(300)
			return


	my_database = client[DATABASE_NAME]

	json_document = {
	     "s": sensor_id,
	     "l": local,
	     "temp": temp,
	     "t": dt.datetime.now().strftime("%H:%M:%S"),
	     "d":dt.datetime.now().strftime("%m-%d-%Y")
	}
	try:
		new_document = my_database.create_document(json_document)
	except:
		write_to_Error_log("error writting new database document, will wait 30 seconds and try again")
		time.sleep(30)
		try:
			new_document = my_database.create_document(json_document)
		except:
			write_to_Error_log("2nd error in a row writting new database document, will wait 5 minutes and then skip")
			return
	client.disconnect()

def edit_cloudant_system_status_doc(s, v):
	# USERNAME = cloud_acct_username
	# PASSWORD = cloud_acct_pword
	# URL = cloud_act_url
	user_data=get_user_data()
	client = Cloudant(user_data['cloud_acct_username'],user_data['cloud_acct_pword'], url = user_data['cloud_act_url'] )
	#client.connect()

	try:
		client.connect()
	except:
		write_to_Error_log("error connecting to cloudant System Status database, will sleep for 30 seconds and then try again")
		time.sleep(30)
		try:
			client.connect()
		except:
			write_to_Error_log("2nd error in a row connecting to cloudant System Status database, will sleep for 5 minute and then skip")
			time.sleep(300)
			return
	my_database = client["system_status"]
	my_document = my_database[s]
	my_document['v']=v

	my_document['t'] = dt.datetime.now().strftime("%H:%M:%S")
	my_document['d'] = dt.datetime.now().strftime("%m-%d-%Y")
	my_document.save()
	print ('\n\n************** system table updated************\n\n')

def eventPublishCallback():
	print("\nCLOUDANT PUBLISHED\n")
	#

def write_to_iot_platform(orgId, sensor_id, token, temp):
	print ("going to write sensor", sensor_id, "to IBM IoT Watson platform, with the token:", token)

	myConfig = { 
	    "identity": {
	        "orgId": orgId,
	        "typeId": "DS18B20",
	        "deviceId": sensor_id

	    },
	    "auth":{
	        "token": token
	    }
	}
	#client = wiotp.sdk.gateway.GatewayClient(config=myConfig)
	client = wiotp.sdk.device.DeviceClient(config=myConfig)
	try:
		client.connect()
	except:
		write_to_Error_log("error connecting to IBM Watson IoT, waiting 30 seconds then trying again")
		time.sleep(30)

		try:
			client.connect()
		except:
			write_to_Error_log("2nd error in a row connecting to IBM Watson IoT, waiting 5 minutes then skipping")
			time.sleep(300)
			return
	try:
		client.publishEvent(eventId="status", msgFormat="json", data={"Temp":temp}, qos=0, onPublish=eventPublishCallback())

	except:
		write_to_Error_log("error writting to IBM Watson IoT after establishing a connect, waiting 30 seconds then trying again")
		time.sleep(30)

		try:
			client.publishEvent(eventId="status", msgFormat="json", data={"Temp":temp}, qos=0, onPublish=eventPublishCallback())
		except:
			write_to_Error_log("2nd error in a row writting to IBM Watson IoT after successfully connect, waiting 5 minutes then skipping")
			time.sleep(300)
			return

	client.disconnect()	

def write_to_log(text):
	user_data=get_user_data()
	msg=" STATUS Date:"+ str(RecDate()) + " AT TIME: "+ str(RecTime())+": "+ str(text)+str('\n')
	print ("Writting to LOG file:", msg)
	# log_txt_file="/home/pi/hms/" + str(RecDate())+"-HMS-log.txt"
	# f=open(log_txt_file, 'a')
	# f.write(msg)
	# f.close()

	DATABASE_NAME="hms_log" 
	client = Cloudant(user_data['cloud_acct_username'], user_data['cloud_acct_pword'], url = user_data['cloud_act_url'] )

	client.connect()

	my_database = client[DATABASE_NAME]

	json_document = {
	     "d":dt.datetime.now().strftime("%m-%d-%Y"),
	     "t":dt.datetime.now().strftime("%H:%M:%S"),
	     "m":msg
	}
	try:
		new_document = my_database.create_document(json_document)
	except:
		print ('error writing to database')
		time.sleep(30)
		try:
			new_document = my_database.create_document(json_document)
		except:
			return
	client.disconnect()

def write_to_Error_log(text):
	user_data=get_user_data()
	msg="ERROR - Date:"+ str(RecDate()) + " AT TIME: "+ str(RecTime())+": "+ str(text)+str('\n')
	print ("Writting to ERROR LOG file:", msg)
	# log_txt_file="/home/pi/hms/" + str(RecDate())+"-HMS-log.txt"
	# f=open(log_txt_file, 'a')
	# f.write(msg)
	# f.close()

	DATABASE_NAME="hms_log"
	client = Cloudant(user_data['cloud_acct_username'],user_data['cloud_acct_pword'], url = user_data['cloud_act_url'] )

	client.connect()

	my_database = client[DATABASE_NAME]

	json_document = {
	     "d":dt.datetime.now().strftime("%m-%d-%Y"),
	     "t":dt.datetime.now().strftime("%H:%M:%S"),
	     "m":msg
	}
	try:
		new_document = my_database.create_document(json_document)
	except:
		time.sleep(30)
		try:
			new_document = my_database.create_document(json_document)
		except:
			return
	client.disconnect()

	
def read_high_low_day_temp(location):

	#########################################
	###### DATA for EVENING update email ####
	#########################################
	user_data=get_user_data()
	client = Cloudant(user_data['cloud_acct_username'],user_data['cloud_acct_pword'], url = user_data['cloud_act_url'] )
	client.connect()

	my_database = client["temps"]
	query = Query(my_database,selector= {'_id': {'$gt': 0}, 'l':location, 'd':dt.datetime.now().strftime("%m-%d-%Y")}, fields=['temp','l','d'],sort=[{'temp': 'desc'}])
	temp_dict={}

	###### for debugging uncomment following two lines
	# for doc in query(limit=30, skip=5)['docs']:
	#      print (doc)

	temp_dict=query(limit=1000, skip=5)['docs']

	value_list=[]

	for row in temp_dict:
		#print ("value number:", row, "is", row['temp'])
		value_list.append(row['temp'])


	if len(value_list)==0:
		msg="insuficient data to produce response"

	else:
		msg="The highest temp in the " + location + " was: "+str(max(value_list)) + " lowest "+str(min(value_list))

	return msg

def read_high_low_night_temp(location):

	#########################################
	###### DATA for MORNING update email ####
	#########################################
	user_data=get_user_data()
	try:
		client = Cloudant(user_data['cloud_acct_username'], user_data['cloud_acct_pword'], url = user_data['cloud_act_url'] )
		client.connect()

	except:
		print ('error connecting to cloudant')
		msg=' read_high_low_day_temp '
		return msg

	# location='Backyard'
	cur_date=dt.datetime.now()
	print ('the current date is', cur_date)
	newdate=cur_date-timedelta (days=1)
	target_date=newdate.strftime("%m-%d-%Y")
	print ("current date minus one day is", newdate.strftime("%m-%d-%Y"))
	my_database = client["temps"]
	query = Query(my_database,selector= {'_id': {'$gt': 0}, 'l':location, "$or":[{'d':dt.datetime.now().strftime("%m-%d-%Y")},{'d':newdate.strftime("%m-%d-%Y")}]}, fields=['temp','t','l','d'],sort=[{'temp': 'desc'}])
	temp_dict={}

	###### for debugging uncomment following two lines
	# for doc in query(limit=30, skip=5)['docs']:
	#      print (doc)

	temp_dict=query(limit=1000, skip=5)['docs']

	value_list=[]

	print ('filtering out last nights measurements, there are', len(temp_dict), 'readings')
	print ('currently there are', len(value_list), 'temps stored\n')


	for row in temp_dict:
		db_date=dt.datetime.strptime(row['d'],"%m-%d-%Y")
		db_time=dt.datetime.strptime(row['t'],"%H:%M:%S")
		
		db_date=db_date.strftime("%m-%d-%Y")
		db_time=db_time.strftime("%H:%M:%S")
		
		
		target_time=dt.datetime.strptime("20:00:00", "%H:%M:%S")
		target_time=target_time.strftime("%H:%M:%S")
		

		if db_date==target_date and db_time>target_time:		
			value_list.append(row['temp'])

		new_target_time=dt.datetime.strptime("6:00:00", "%H:%M:%S")
		new_target_time=new_target_time.strftime("%H:%M:%S")

		new_target_date=dt.datetime.now().strftime("%m-%d-%Y")

		if db_date==new_target_date and db_time==new_target_time:
			value_list.append(row['temp'])	


		if len(value_list)==0:
			message="Insuficient data to produce response"

		else:

			message = "so far there were "+str(len(value_list))+ " "+location+" readings, the high was "+ str(max(value_list)) + " and the lowest was " + str(min(value_list))

	
	return message


def read_status_from_cloudant(device_id,field):

	user_data=get_user_data()
	client = Cloudant(user_data['cloud_acct_username'],user_data['cloud_acct_pword'], url = user_data['cloud_act_url'] )
	client.connect()
	my_database = client["system_status"]
	my_document = my_database[device_id]
	value=my_document[field]


	return current_temp,current_time
def backyard_read_temp_from_cloudant(device_id):
	user_data=get_user_data()
	client = Cloudant(user_data['cloud_acct_username'],user_data['cloud_acct_pword'], url = user_data['cloud_act_url'] )
	client.connect()
	my_database = client["system_status"]
	my_document = my_database[device_id]
	current_temp=my_document['v']
	current_time=dt.datetime.strptime(my_document['t'],"%H:%M:%S")
	current_time=current_time.strftime("%I:%M %p")

	return current_temp,current_time

def build_status_dict():
	user_data=get_user_data()
	client = Cloudant(user_data['cloud_acct_username'],user_data['cloud_acct_pword'], url = user_data['cloud_act_url'] )
	client.connect()
	my_database = client["system_status"]
	local_status_dict=[]
	for doc in my_database:
		local_status_dict.append(doc)

	return local_status_dict

def evening_report(errors, reads):
	eol="\r\r\n"
	temp_base_dir = '/sys/bus/w1/devices/'
	os.chdir(temp_base_dir)
	message=""
	message="general error count = " + str(errors) + "\rread cycles = " + str(reads)+ "\r"
	message=message+"The number of online sensors = "+str(len(glob.glob("28*")))+ "\r"
	message=message+"ds18b20 errors = " + str(ds18b20_error_count)+"\r"

	user_data=get_user_data()


	status_dict=build_status_dict() 
	for row in status_dict:
		if row['l']=='Garage overhead':
			message=message+"Garage overhead door is: "+row['v']+eol

		if row['l']=='North fence gate':
			message=message+"The north fence gate is: "+row['v']+eol

		if row['type']=="temp":
			message=message+"The "+row['l']+" temperature is"+ str(row['v'])+eol



	print(message)
	send_html_email('evening report', message, gmail_user,gmail_password)


	