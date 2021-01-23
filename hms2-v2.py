#!/usr/bin/python
# -*- coding:UTF-8 -*-


import os, shutil, glob, time, subprocess, re, sys, sqlite3, logging, smtplib
import RPi.GPIO as GPIO
from datetime import timedelta
from datetime import datetime
import datetime as dt
import wiotp.sdk.application
import cloudant
from cloudant.client import Cloudant
from cloudant.query import Query
from cloudant.result import QueryResult
from cloudant.error import ResultException


####################################
######## FUNCTIONS #################
####################################

def send_html_email(subject,body):
	gmail_user = "smart.lehotsky.house@gmail.com"
	gmail_password = "27Kovelov"

	sent_from = gmail_user
	to = ["tim.lehotsky@wsp.com"]
	#subject = "3 Whoa Update from your SMART house"
	#body = "Hey, whats up?\n\n- You"

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
	    write_to_log('email sent with subject')
	    write_to_log(body)
	except:
	    print ("Something went wrong")
	    write_to_Error_log("error sending email, what follows is the message body")
	    write_to_Error_log(body)
	    time.sleep(10)

def send_email(subject,body):
	gmail_user = "smart.lehotsky.house@gmail.com"
	gmail_password = "27Kovelov"

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
	    write_to_log('email sent with subject')
	    write_to_log(body)
	except:
	    print ("Something went wrong")
	    write_to_Error_log("error sending email, what follows is the message body")
	    write_to_Error_log(body)
	    time.sleep(10)

def write_door_position_to_cloudant(door_name, door_position):
	ACCOUNT_NAME="f7thsh"
	USERNAME = "8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix"
	PASSWORD = "006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf"
	URL="https://8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix:006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf@8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix.cloudantnosqldb.appdomain.cloud"
	API_KEY="ZQPyqA9l8NAthQQ55_G5gneILma__jiP4JUOBdh8nQog"
	DATABASE_NAME="door_position"
	#print ("sub to write data to cloudant - SENSOR ID = ", sensor_id, "LOCATION = ", local, "TEMP = ", temp)

	client = Cloudant(USERNAME,PASSWORD, url = "https://8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix:006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf@8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix.cloudantnosqldb.appdomain.cloud" )
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
	ACCOUNT_NAME="f7thsh"
	USERNAME = "8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix"
	PASSWORD = "006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf"
	URL="https://8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix:006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf@8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix.cloudantnosqldb.appdomain.cloud"
	API_KEY="ZQPyqA9l8NAthQQ55_G5gneILma__jiP4JUOBdh8nQog"
	DATABASE_NAME="temps"
	print ("sub to write data to cloudant - SENSOR ID = ", sensor_id, "LOCATION = ", local, "TEMP = ", temp)

	client = Cloudant(USERNAME,PASSWORD, url = "https://8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix:006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf@8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix.cloudantnosqldb.appdomain.cloud" )
	
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

def edit_cloudant_system_status_doc(s,v):
	USERNAME = "8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix"
	PASSWORD = "006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf"

	client = Cloudant(USERNAME,PASSWORD, url = "https://8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix:006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf@8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix.cloudantnosqldb.appdomain.cloud" )
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
	print ('\n\n************** system table updated************ read cycle:',read_cycles,'\n\n')

def pickaccount():


	print("*************************************************************************")
	print("****       1.   tlehotsky@gmail.com                                   ***")
	print("****                                                                  ***")
	print("****       2.   smart.lehotsky.house@gmail.com                        ***")
	print("*************************************************************************")
	print("\n")


	#acct=input("enter 1 or 2: ")
	acct=1

	if acct==1:
		account_name="tlehotsky@gmail.com"
	else:
		account_name="smart.lehotsky.house@gmail.com"



	if account_name=="tlehotsky@gmail.com":
		orgId="rdj4wy"
		ds18b20_sensor_dict=    {'serial':'28-000005c6894a','location':'Basement RPi cabinet', 'token':'9CvY*mQZwV0Kf7792c','id':'ff02dab2420c92e6a664e0cb2252da16'},\
								{'serial':'28-000005c77fc7','location':'Driveway','token':'YEZPv9m0x1FY6L6byX','id':'4b72bb5e1b0d3c9981a8a92b9f7022c1'},\
								{'serial':'28-000005c685ba','location':'Kitchen','token':'3kQaAEj0!u*SIGyP(1','id':'d0adb1c0be3c69f3c9135fb1441886fb'},\
								{'serial':'28-000005c7ed65','location':'Basement outside RPi cabinet','token':'zr@+Kp2@pRLS1+h?sf','id':'0a7e3e128eaad5f9ab828b8c16bfaa09'},\
								{'serial':'28-000005c6ba08','location':'Garage', 'token':'Ljq*jt?EeCRfxbRare','id':'ccad5a0c4449b0e57dd0bd889ef6207c'},\
								{'serial':'28-000005c7ce08','location':'Familyroom','token':'Tdez_RuWsF(sbOX3tB','id':'4b72bb5e1b0d3c9981a8a92b9f6f6608'},\
								{'serial':'28-000005c6e555','location':'Water Heater','token':'2+5Oxwa4ms5@d+Vu(A','id':'9e3be499b46023556279c3d5714251af'},\
								{'serial':'28-000005c80eb9','location':'Backyard','token':'LJOXm62F8)OXRBMkkB','id':'df3026af6d7d123f5df440b365dfc888'} 

	if account_name=="smart.lehotsky.house@gmail.com":
		orgId="j5h59u"
		ds18b20_sensor_dict=    {'serial':'28-000005c6894a','location':'Basement RPi cabinet', 'token':'Ay(*g3zibFHGFSk8M('},\
								{'serial':'28-000005c77fc7','location':'Driveway','token':'srjfF&RXvDU7+qoYly'},\
								{'serial':'28-000005c685ba','location':'Kitchen','token':'9S8Y9rOA(bZnEMAB)9'},\
								{'serial':'28-000005c7ed65','location':'Basement outside RPi cabinet','token':'6lw!UIjk&DAi27CaA&'},\
								{'serial':'28-000005c6ba08','location':'Garage', 'token':'Y)SZpqT@HxKkvwWMZ8'},\
								{'serial':'28-000005c7ce08','location':'Familyroom','token':'yTS0f(Fi3)(ewKhJzG'},\
								{'serial':'28-000005c6e555','location':'Water Heater','token':'@x0CWfiM*-EH-mSIr@'},\
								{'serial':'28-000005c80eb9','location':'Backyard','token':'+D-)E4qlVNvwtxiJx&'} 

	return account_name, orgId, ds18b20_sensor_dict

def eventPublishCallback():
	print("\nCLOUDANT PUBLISHED\n")
	#

def write_to_iot_platform(OrgId, sensor_id, token, temp):
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

def defcon_five(msg,msg_code,tic):
	#def con five
	print ("going to DefCon five")
	defcon_num=5
	return defcon_num

def defcon_four(msg,msg_code,tic):
	#def con four
	print ("going to DefCon four")
	defcon_num=5
	return defcon_num

def defcon_three(msg,msg_code,tic):
	#def con three
	print ("going to DefCon three")
	defcon_num=5
	return defcon_num

def defcon_two(msg,msg_code,tic):
	#def con two
	print ("going to DefCon two")
	defcon_num=5
	return defcon_num

def defcon_one(msg,msg_code,tic):
	#def con one
	print ("going to DefCon one")
	defcon_num=5
	return defcon_num

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

def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp():
	global ds18b20_error_count
	temp_total=0
	temp_read_cycles=0
	for x in range(9):
		try:

		    lines = read_temp_raw()
		    while lines[0].strip()[-3:] != 'YES':
		        time.sleep(0.5)
		        lines = read_temp_raw()
		    equals_pos = lines[1].find('t=')
		    if equals_pos != -1:
		        temp_string = lines[1][equals_pos+2:]
		        temp_c = float(temp_string) / 1000.0
		        temp_f = round(temp_c * 9.0 / 5.0 + 32.0,1)

		        #return temp_f
		        temp_total = temp_total + temp_f
		        temp_read_cycles= temp_read_cycles + 1
		        #print ("temp read", temp_read_cycles, "times")

		except:
			print ("Error reading ds18b20 sensor,sleeping for 10 seconds")
			time.sleep(10)
			ds18b20_error_count=ds18b20_error_count+1
			write_to_Error_log("ERROR reading DS18B20 sensor")
			
	#print ("final temp is", temp_total/temp_read_cycles)
	return round((temp_total/temp_read_cycles),1)


def write_to_log(text):
	msg=" STATUS Date:"+ str(RecDate()) + " AT TIME: "+ str(RecTime())+": "+ str(text)+str('\n')
	print ("Writting to LOG file:", msg)
	# os.chdir("")
	log_txt_file="/home/pi/hms/" + str(RecDate())+"-HMS-log.txt"
	f=open(log_txt_file, 'a')
	f.write(msg)
	f.close()

def write_to_Error_log(text):
	msg="ERROR - Date:"+ str(RecDate()) + " AT TIME: "+ str(RecTime())+": "+ str(text)+str('\n')
	print ("Writting to ERROR LOG file:", msg)
	# os.chdir("")
	log_txt_file="/home/pi/hms/" + str(RecDate())+"-HMS-log.txt"
	f=open(log_txt_file, 'a')
	f.write(msg)
	f.close()


def temp_analytics(sensor_id, local, temp, beginning_of_day):
	new_temp=temp

	#check if temps sensor has been read before

	if sensor_id not in current_sensor_data_dict.keys():
		#sensor being read for first time
		print("Sensor =", sensor_id, "that is located: ",local,"is not in the data dictionary, adding now")
		#logging.info("Sensor =%s that is located: %s is not in the data dictionary, adding now", sensor_id, local)
		current_sensor_data_dict[sensor_id] = temp
	else:
		print ("Sensor =", sensor_id,"in",local,"updating dictionary, WAS:", current_sensor_data_dict[sensor_id], "NOW:", temp)
		#logging.info("Sensor = %s in %s updating dictionary, WAS: %s NOW: %s", sensor_id, local, current_sensor_data_dict[sensor_id], temp)
		old_temp=current_sensor_data_dict[sensor_id]
		current_sensor_data_dict[sensor_id] = temp

	if beginning_of_day:
		#these are the first readings of the day
		print ("Sensor =", sensor_id,"first readings of day, will not perform analytics")
		# logging.info("Sensor = %s first readings of day, will not perform analytics", sensor_id)
		return

	else:
		#sensor is in the dictionary and its NOT the first reading
		print ("Sensor =", sensor_id,"**** starting analytics ****")
		for row in ds18b20_sensor_dict:
			if row['serial']== sensor_id:
				sensor_ext_int = row['location']
		
		print ("Sensor =", sensor_id,"is an", sensor_ext_int, "type")
		print ("Sensor =", sensor_id,"comparing indoor to outdoor temps" )

		if sensor_ext_int=="interior":

			global high_indoor_temp
			global high_indoor_temp_local
			global high_indoor_temp_time

			global low_indoor_temp
			global low_indoor_temp_local
			global low_indoor_temp_time


			#check for new high interior temp of day
			if temp>high_indoor_temp:
				high_indoor_temp=temp
				high_indoor_temp_local=local
				high_indoor_temp_time=RecTime()

				print ("!!!! New high interior temperature of", high_indoor_temp, "in", high_indoor_temp_local, "at", high_indoor_temp_time)

			#check for new low interior temp of day
			if temp<low_indoor_temp:
				low_indoor_temp=temp
				low_indoor_temp_local=local
				low_indoor_temp_time=RecTime()
				print ("!!!! New Low interior temperature of", high_indoor_temp, "in", high_indoor_temp_local, "at", high_indoor_temp_time)

		if sensor_ext_int=="exterior":

			global high_outdoor_temp
			global high_outdoor_temp_local
			global high_outdoor_temp_time

			global low_outdoor_temp
			global low_outdoor_temp_local
			global low_outdoor_temp_time

			if temp>high_outdoor_temp:
				high_outdoor_temp=temp
				high_outdoor_temp_local=local
				high_outdoor_temp_time=RecTime()
				print ("!!!! New High Outdoor Temp of", high_outdoor_temp, "at", high_outdoor_temp_time)

			if temp<low_outdoor_temp:
				low_outdoor_temp=temp
				low_outdoor_temp_local=local
				low_outdoor_temp_time=RecTime()
				print ("!!!! New Low Outdoor Temp of", low_outdoor_temp, "at", low_outdoor_temp_time)







		if sensor_ext_int=="interior":
			if cur_season =="summer":
				print ("checking if colder outside than inside")
				#print ("outside temp is....")
				#### get outdoor temp
				print ("outdoor temp =", current_sensor_data_dict['28-000005c80eb9'], "DIFFERENCE IS", "{:.2f}".format(float(current_sensor_data_dict['28-000005c80eb9'])-temp))
				#print ("start error expression, printing answer",current_sensor_data_dict['28-000005c80eb9']-temp)
				# formatted_str="{:.2f}".format(float(current_sensor_data_dict['28-000005c80eb9'])-temp)
				# x=float(formatted_str)
				# print("fixed number is", x)
				# print("here we go")

				if float(current_sensor_data_dict['28-000005c80eb9'])-temp<0:
					defcon_one(msg, 'oitemp',tic())

				#print ("past error message")

		if sensor_ext_int=="exterior":
			print ("current temp sensor is exterior, won't compare to interior")

		if sensor_ext_int=="utility":
			print ("current temp sensor is a utility sensor, won't compare to interior")




		print ("")

def read_high_low_day_temp(location):

	#########################################
	###### DATA for EVENING update email ####
	#########################################

	USERNAME = "8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix"
	PASSWORD = "006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf"

	client = Cloudant(USERNAME,PASSWORD, url = "https://8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix:006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf@8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix.cloudantnosqldb.appdomain.cloud" )
	client.connect()
	# location='Backyard'

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


	#print (value_list)

	#print("the highest temp in the",location, "is:", max(value_list), "lowest", min(value_list),)
	
	if len(value_list)==0:
		msg="insuficient data to produce response"

	else:
		msg="The highest temp in the " + location + " was: "+str(max(value_list)) + " lowest "+str(min(value_list))

	return msg

def read_high_low_night_temp(location):

	#########################################
	###### DATA for MORNING update email ####
	#########################################

	USERNAME = "8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix"
	PASSWORD = "006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf"

	client = Cloudant(USERNAME,PASSWORD, url = "https://8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix:006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf@8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix.cloudantnosqldb.appdomain.cloud" )
	client.connect()
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

	#filter out last nights temps
	print ('filtering out last nights measurements, there are', len(temp_dict), 'readings')
	print ('currently there are', len(value_list), 'temps stored\n')

	#Filter results that are night before and after 10
	for row in temp_dict:
		db_date=dt.datetime.strptime(row['d'],"%m-%d-%Y")
		db_time=dt.datetime.strptime(row['t'],"%H:%M:%S")
		
		db_date=db_date.strftime("%m-%d-%Y")
		db_time=db_time.strftime("%H:%M:%S")
		
		# print ('the database date is', db_date)
		# print ('the day before date is', target_date)
		# print ('the database time is', db_time, '\n')
		
		target_time=dt.datetime.strptime("20:00:00", "%H:%M:%S")
		target_time=target_time.strftime("%H:%M:%S")
		
		# print ('The target time is',target_time)
		# print ("the first date is", db_date, "and the temperature is", row['temp'],'\n')
		
		# print ('going to check if the database date', db_date, "matches the target date:",target_date)
		# print ('and if database time', db_time, 'is after (greater than) the target time', target_time) 
		#
		
		# name = input("press enter to continue ")
		if db_date==target_date and db_time>target_time:		
			# print ('The database time and date meet the requirements, adding to tuple')
			value_list.append(row['temp'])
		# else:
			# print ("doesn't meet first set of requirements")

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

# def read_high_low_night_temp(location):
# 	USERNAME = "8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix"
# 	PASSWORD = "006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf"

# 	client = Cloudant(USERNAME,PASSWORD, url = "https://8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix:006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf@8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix.cloudantnosqldb.appdomain.cloud" )
# 	client.connect()
# 	# location='Backyard'

# 	my_database = client["temps"]
# 	query = Query(my_database,selector= {'_id': {'$gt': 0}, 'l':location, 'd':dt.datetime.now().strftime("%m-%d-%Y")}, fields=['temp','l','d'],sort=[{'temp': 'desc'}])
# 	temp_dict={}

# 	###### for debugging uncomment following two lines
# 	# for doc in query(limit=30, skip=5)['docs']:
# 	#      print (doc)

# 	temp_dict=query(limit=1000, skip=5)['docs']

# 	value_list=[]

# 	for row in temp_dict:
# 		#print ("value number:", row, "is", row['temp'])
# 		value_list.append(row['temp'])


# 	#print (value_list)

# 	#print("the highest temp in the",location, "is:", max(value_list), "lowest", min(value_list),)
# 	msg=" the highest temp in the " + location + " was: "+str(max(value_list)) + " lowest "+str(min(value_list))
# 	return msg
def read_status_from_cloudant(device_id,field):
	USERNAME = "8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix"
	PASSWORD = "006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf"

	client = Cloudant(USERNAME,PASSWORD, url = "https://8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix:006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf@8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix.cloudantnosqldb.appdomain.cloud" )
	client.connect()
	my_database = client["system_status"]
	my_document = my_database[device_id]
	value=my_document[field]


	return current_temp,current_time
def backyard_read_temp_from_cloudant(device_id):
	USERNAME = "8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix"
	PASSWORD = "006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf"

	client = Cloudant(USERNAME,PASSWORD, url = "https://8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix:006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf@8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix.cloudantnosqldb.appdomain.cloud" )
	client.connect()
	my_database = client["system_status"]
	my_document = my_database[device_id]
	current_temp=my_document['v']
	current_time=dt.datetime.strptime(my_document['t'],"%H:%M:%S")
	current_time=current_time.strftime("%I:%M %p")

	return current_temp,current_time

def evening_report(errors, reads):
	eol="\r\r\n"
	temp_base_dir = '/sys/bus/w1/devices/'
	os.chdir(temp_base_dir)
	message=""
	message="general error count = " + str(errors) + "\rread cycles = " + str(reads)+ "\r"
	message=message+"The number of online sensors = "+str(len(glob.glob("28*")))+ "\r"
	message=message+"ds18b20 errors = " + str(ds18b20_error_count)+"\r"
	# online_ds18b20_sensor_serial_list=[]
	# online_ds18b20_sensor_name_list=[]
	# # message_body=[]

	# # for row in ds18b20_sensor_dict:
	# # 	print (row['location'])

	# ## develop a list of online sensors
	# for sensor_file in glob.glob("28*"):
	# 	device_file = temp_base_dir + sensor_file + '/w1_slave'
	# 	online_ds18b20_sensor_serial_list.append(sensor_file)


	# ## get the names for all the online sensors
	# for serial in online_ds18b20_sensor_serial_list:
	# 	for row in ds18b20_sensor_dict:
	# 		if serial == row['serial']:
	# 			online_ds18b20_sensor_name_list.append(row['location'])
	# message=message+"\r\r\nTEMPERATURE READINGS \r\r\n"
	### build email message body for temperatures
	# for n in online_ds18b20_sensor_name_list:
	# 	# message_body.append(read_high_low_day_temp(n))
	# 	msg_iteration=read_high_low_day_temp(n)
	# 	message=message+str(msg_iteration)+"\r\n"

	status_dict=build_status_dict() 
	for row in status_dict:
		if row['l']=='Garage overhead':
			message=message+"Garage overhead door is: "+row['v']+eol

		if row['l']=='North fence gate':
			message=message+"The north fence gate is: "+row['v']+eol

		if row['type']=="temp":
			message=message+"The "+row['l']+" temperature is"+ str(row['v'])+eol




		# for i in row:
		# 	print ('key', i,'has value', row[i])

	# for line in message_body:
	# 	message=message+line

	print(message)
	send_html_email('evening report', message)

def build_status_dict():
	USERNAME = "8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix"
	PASSWORD = "006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf"

	client = Cloudant(USERNAME,PASSWORD, url = "https://8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix:006d4df070101f4d115325956e7f9133a26697c0ab2765c6ed5709f6b26cddbf@8c1205d4-f169-4cb0-a62e-73d6dba754fb-bluemix.cloudantnosqldb.appdomain.cloud" )
	client.connect()
	my_database = client["system_status"]
	local_status_dict=[]
	for doc in my_database:
		local_status_dict.append(doc)

	return local_status_dict
	

####################################
######## constants #################
####################################

base_dir = '/sys/bus/w1/devices/'
online_sensor_list=[]
cur_sensor=""
cur_temp=0
cur_local=""
read_cycles=0
error_count=0
ds18b20_error_count=0
skip_IoT=False

sleep_between_sensor_reads=9
sleep_end_of_loop=60

base_dir = '/sys/bus/w1/devices/'
online_sensor_list=[]
testserial="28-000005c6ba08"

high_outdoor_temp=0
high_outdoor_temp_local=""
high_outdoor_temp_time=""

low_outdoor_temp=100
low_outdoor_temp_local=""
low_outdoor_temp_time=""

high_indoor_temp=0
high_indoor_temp_local=""
high_indoor_temp_time=""

low_indoor_temp=80
low_indoor_temp_local=""
low_indoor_temp_time=""

cur_month=int(datetime.now().strftime('%m'))	
if cur_month >11 or cur_month<3: cur_season="winter" # months 12, 1, 2
if cur_month>5 and cur_month<9: cur_season="summer" # months 6, 7, 8
if cur_month>2 and cur_month<6: cur_season="spring" # months 3, 4, 5
if cur_month>8 and cur_month<12: cur_season="fall" # months 9. 10, 11

current_sensor_data_dict={}
day_of_year = dt.datetime.now().timetuple().tm_yday
beginning_of_day=True
morning_report_sent=False
evening_report_sent=False

####################################
######## GPIO ######################
####################################

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False) # Ignore warning for now
GPIO.setmode(GPIO.BCM)
####################################
######## program code ##############
####################################
door_dict={'door_name':'Basement', 'pin':'22', '_id':'0a7e3e128eaad5f9ab828b8c16b6d389'},\
          {'door_name':'Garage overhead', 'pin':'23', '_id':'9e3be499b46023556279c3d571451c55'},\
          {'door_name':'North fence gate', 'pin':'24', '_id':'d0adb1c0be3c69f3c9135fb1441b862a'}

for row in door_dict:
	GPIO.setup(int(row['pin']), GPIO.IN, pull_up_down=GPIO.PUD_UP) 

# print ("day of year is",day_of_year)

os.system('clear')
os.chdir(base_dir)
# initialize_logger('/home/pi/hms') #start logger

print ("Core test 5")
print ("day of year is",day_of_year)

# time.sleep(5)

write_to_log("Program started at" + str(RecTime())+" on " + str(RecDate()))
# logging.info('\n')
print ("The number of online sensors is: ", len(glob.glob("28*")),)
write_to_log("The number of online sensors is: " + str(len(glob.glob("28*"))))
account_name, orgId, ds18b20_sensor_dict=pickaccount()
print ("\n")
print ("Your account name is:", account_name)
write_to_log("Your account name is: "+ account_name)


print ("Your Organization Id is:", orgId, "\n")
write_to_log("Your Organization Id is: " + orgId)

# print ("ds18b20 Sensor Dictionary =",ds18b20_sensor_dict)
# time.sleep(5)


while day_of_year == dt.datetime.now().timetuple().tm_yday:
	# if beginning_of_day==False and read_cycles>2:
	# 	try:
	# 		print (read_high_low_day_temp("Backyard"))
	# 	except:
	# 		print ("error reading high/low temps, sleeping 30 seconds to let error flush")
	# 		time.sleep(30)
	# 		error_count+=1


	# 	try:
	# 		print (read_high_low_day_temp("Driveway"))
	# 	except:
	# 		print ("error reading high/low temps, sleeping 30 seconds to let error flush")
	# 		time.sleep(30)
	# 		error_count+=1

	if dt.datetime.now().hour>7 and morning_report_sent == False and read_cycles>1:

		try:
			msg1= read_high_low_night_temp("Backyard")
			morning_report_sent=True
		except:
			print ("error reading high/low temps, sleeping 30 seconds to let error flush")
			time.sleep(30)
			error_count+=1
		
		try:
			msg2=read_high_low_night_temp("Driveway")
			morning_report_sent=True
		except:
			print ("error reading high/low temps, sleeping 30 seconds to let error flush")
			time.sleep(30)
			error_count+=1
			morning_report_sent=True


		try:
			# send_email('morning update',msg1 + "\n" + msg2)
			# morning_report_sent=True
			print ("prepping morning message")
			msg1=read_high_low_night_temp("Backyard")
			msg2=read_high_low_night_temp("Driveway")
			message=msg1+"\r\r\n"+msg2
			# print (message)
			backyard_device_id="df3026af6d7d123f5df440b365dfc888"

			backyard_temp, backyard_temp_time=backyard_read_temp_from_cloudant(backyard_device_id)

			subject="at " +str(backyard_temp_time)+" the backyard temp was: "+str(backyard_temp)
			# print (subject)

			send_email(subject, message)

		except:
			print ("error sending email")
			error_count+=1
		
		# if dt.datetime.now().hour>21 and morning_report_sent == True and evening_report_sent ==False and read_cycles>2:

	if dt.datetime.now().hour>20 and  morning_report_sent == True and evening_report_sent ==False and read_cycles>1:
		evening_report(error_count,read_cycles)


		# msg1=read_high_low_day_temp("Backyard")
		# msg2=read_high_low_day_temp("Driveway")
		# msg3=""
		# ####  insert send evening report sub here

		# for row in door_dict:
		# 	print ("going to read" , row['door_name'], "door, on pin number", row['pin'],"\n")

		# 	curDoor_name=row['door_name']
		# 	curPin_number=int(row['pin'])
		# 	test_total=0

		# 	for x in range(9):
		# 		text_num=str(x)
		# 		#curReading=str(GPIO.input(curPin_number))

		# 		#print ("reading number",text_num, "is", GPIO.input(curPin_number))

		# 		if GPIO.input(curPin_number) == 1:
		# 			test_total=test_total+1


		# 	if test_total>8: 
		# 		msg3=msg3 + "\r\r\n" + curDoor_name + " door is open"
		# 		cur_door_status="open"
		# 	if test_total<2:
		# 		cur_door_status="closed"
		# 		msg3=msg3 + "\r\r\n" + curDoor_name+" door is closed"

		# send_email('evening update', msg1 + "\r\r\n" + msg2 + "\r\r\n" + msg3)
		# evening_report_sent=True


	read_cycles=read_cycles+1
	print ("\n\nStarting read cycle number",read_cycles, "\n\n")
	os.chdir(base_dir)
	for sensor_file in glob.glob("28*"):
		device_file = base_dir + sensor_file + '/w1_slave'
		for row in ds18b20_sensor_dict:
			#print " looking for sensor: ", sensor_file, " The current row in dictionary is for sensors", row['serial']
			#print " looking for sensor: ", sensor_file, " The current row in dictionary is for sensors", row['serial']
			if row['serial']==sensor_file:
				# print "found correct row in dict, exiting loop"
				# print ""
				break
			# else:
			# 	print "trying next row"
		cur_sensor=sensor_file
		cur_temp=read_temp()
		cur_local=row['location']
		token=row['token']
		cur_id=row['id']
		print ("Sensor =",cur_sensor, "temp is:", cur_temp,"sensor location is:", cur_local)
		print ("the cloundat id for this is:",cur_id)
		#logging.info("Sensor = %s temp is: %s sensor location is: %s",cur_sensor, cur_temp, cur_local)

		# print "sensor ID = ",sensor_file, "that has the temperature of:", read_temp(),\
		#  " this sensor is located at the: ", row['location']

		### send data to analytics sub routine:

		#temp_analytics(cur_sensor, cur_local, cur_temp, beginning_of_day)
		try:
			write_to_cloudant(cur_sensor, cur_local, cur_temp)
		except:
			write_to_Error_log("error writting temperature to cloudant, waiting 30 seconds then retrying")
			time.sleep(30)
			error_count+=1

			try:
				write_to_cloudant(cur_sensor, cur_local, cur_temp)
			except:
				write_to_Error_log("2nd error in a row writting to cloundant, sleeping 5 minuts then skipping")
				time.sleep(300)
				error_count+=1

		edit_cloudant_system_status_doc(row['id'] ,cur_temp)


		if skip_IoT==False:
			try: 
				write_to_iot_platform(orgId, cur_sensor, token, cur_temp)
			except:
				write_to_Error_log("error writting to IoT platform, waiting 30 seconds then retrying")
				time.sleep(30)

				try:
					write_to_iot_platform(orgId, cur_sensor, token, cur_temp)
					
				except:
					write_to_Error_log("2nd error in a row writting to IoT platform, sleeping 5 minutes then skipping")
					time.sleep(300)
					error_count+=1

		else:
			print ("********* IoT platform disabled **********")


		if sensor_file not in online_sensor_list:
			online_sensor_list.append(sensor_file)
			msg="NEW ONLINE SENSOR "+ sensor_file + " located at "+ row['location']
			# print msg
			write_to_log(msg)
		time.sleep(sleep_between_sensor_reads)

	cur_door_status=""

	for row in door_dict:
		print ("going to read" , row['door_name'], "door, on pin number", row['pin'],"\n")

		curDoor_name=row['door_name']
		curPin_number=int(row['pin'])
		test_total=0

		for x in range(9):
			text_num=str(x)
			#curReading=str(GPIO.input(curPin_number))

			#print ("reading number",text_num, "is", GPIO.input(curPin_number))

			if GPIO.input(curPin_number) == 1:
				test_total=test_total+1


		if test_total>8: 
			# print (curDoor_name, "door is open")
			cur_door_status="open"
		if test_total<2:
			cur_door_status="closed"
			# print (curDoor_name, "door is closed")

		# print ("writing to cloudant")
		try:
			write_door_position_to_cloudant(curDoor_name, cur_door_status)
		except:
			write_to_log("error writing door position to cloudant, sleeping for 30 seconds then re-trying")
			error_count+=1

			try:
				write_door_position_to_cloudant(curDoor_name, cur_door_status)

			except:
				write_to_log("2nd error in a row writing door position to cloudant, sleeping for 5 minutes then skipping")
				time.sleep(300)
				error_count+=1

		# print ("NEXT DOOR\n")
		time.sleep(sleep_between_sensor_reads)
		# read_cycles=read_cycles+1
	print ("\n\nSo far there's been", read_cycles, "read cycles\n\n")
	print ("\n")
	print ("*****************************************************************************************")
	print ("************************ ALL TEMP SENSORS READ, SLEEPING NOW, for ",sleep_end_of_loop,"seconds ***********")
	print ("************************ CHECKING DOOR POSITION STATUS **********************************")
	print ("*****************************************************************************************\n")



	time.sleep(sleep_end_of_loop)
	beginning_of_day=False
		# time.sleep(2)
	# msg= raw_input('going to next sensor...press enter to continue...')


print ("its  a new day !!!!")
write_to_log("the previous day is over, total number of reads for that day = " + str(read_cycles))
print ("going to sleep for 30 sconds then rebooting")
write_to_log ("going to sleep for 30 sconds then rebooting")
time.sleep(30)
os.system('sudo reboot')

#sys.exit()



