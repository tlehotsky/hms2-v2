#!/usr/bin/python
# -*- coding:UTF-8 -*-

#git update 1/23/2021

from tims_modules import *



def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_temp(ds18b20_error_count):
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
	if temp_read_cycles>1:
		return round((temp_total/temp_read_cycles),1), ds18b20_error_count

	else:
		return_temp=0
		return return_temp, ds18b20_error_count


####################################
######## constants #################
####################################


user_data=get_user_data()
cloud_acct_org_name =user_data['cloud_acct_org_name']
cloud_acct_pword=user_data['cloud_acct_pword']
cloud_act_url= user_data['cloud_act_url']
cloud_acct_API_key= user_data['cloud_acct_API_key']
gmail_user= user_data['gmail_user']
gmail_password= user_data['gmail_password']
cloudant_username=user_data['cloud_acct_username']
orgId=user_data['cloud_org_ID']
account_name=user_data['cloud_top_level_account_username']

ds18b20_sensor_dict=    {'serial':'28-000005c6894a','location':'Basement RPi cabinet', 'token':'9CvY*mQZwV0Kf7792c','id':'ff02dab2420c92e6a664e0cb2252da16'},\
						{'serial':'28-000005c77fc7','location':'Driveway','token':'YEZPv9m0x1FY6L6byX','id':'4b72bb5e1b0d3c9981a8a92b9f7022c1'},\
						{'serial':'28-000005c685ba','location':'Kitchen','token':'3kQaAEj0!u*SIGyP(1','id':'d0adb1c0be3c69f3c9135fb1441886fb'},\
						{'serial':'28-000005c7ed65','location':'Basement outside RPi cabinet','token':'zr@+Kp2@pRLS1+h?sf','id':'0a7e3e128eaad5f9ab828b8c16bfaa09'},\
						{'serial':'28-000005c6ba08','location':'Garage', 'token':'Ljq*jt?EeCRfxbRare','id':'ccad5a0c4449b0e57dd0bd889ef6207c'},\
						{'serial':'28-000005c7ce08','location':'Familyroom','token':'Tdez_RuWsF(sbOX3tB','id':'4b72bb5e1b0d3c9981a8a92b9f6f6608'},\
						{'serial':'28-000005c6e555','location':'Water Heater','token':'2+5Oxwa4ms5@d+Vu(A','id':'9e3be499b46023556279c3d5714251af'},\
						{'serial':'28-000005c80eb9','location':'Backyard','token':'LJOXm62F8)OXRBMkkB','id':'df3026af6d7d123f5df440b365dfc888'} 


base_dir = '/sys/bus/w1/devices/'
online_sensor_list=[]
cur_sensor=""
cur_temp=0
cur_local=""
read_cycles=0
error_count=0
ds18b20_error_count=0
skip_IoT=True

sleep_between_sensor_reads=9
sleep_end_of_loop=60

base_dir = '/sys/bus/w1/devices/'
online_sensor_list=[]
testserial="28-000005c6ba08"

########################################################
######## Analytics onstants ############################
########################################################


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

log_msg="Program started at" + str(RecTime())+" on " + str(RecDate())
write_to_log(log_msg)
# logging.info('\n')
print ("The number of online sensors is: ", len(glob.glob("28*")))
write_to_log("The number of online sensors is: " + str(len(glob.glob("28*"))))



# account_name, orgId, ds18b20_sensor_dict=pickaccount()

print ("\n")
print ("Your account name is:", account_name)
write_to_log("Your account name is: "+ account_name)


print ("Your Organization Id is:", orgId, "\n")
write_to_log("Your Organization Id is: " + orgId)

# print ("ds18b20 Sensor Dictionary =",ds18b20_sensor_dict)
# time.sleep(5)


while day_of_year == dt.datetime.now().timetuple().tm_yday:

	if dt.datetime.now().hour>7 and morning_report_sent == False and read_cycles>0:

		try:
			msg1= read_high_low_night_temp("Backyard", cloudant_username, cloud_acct_pword, cloud_act_url)
			morning_report_sent=True
		except:
			print ("error reading high/low temps, sleeping 30 seconds to let error flush")
			time.sleep(30)
			error_count+=1
		
		msg2=read_high_low_night_temp("Driveway")
		morning_report_sent=True




		# try:

		# except:
		# 	print ("error reading high/low temps, sleeping 30 seconds to let error flush")
		# 	time.sleep(30)
		# 	error_count+=1
		# 	morning_report_sent=True


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

			send_email(subject, message, gmail_user, gmail_password)

		except:
			print ("error sending email")
			error_count+=1
		
		# if dt.datetime.now().hour>21 and morning_report_sent == True and evening_report_sent ==False and read_cycles>2:

	if dt.datetime.now().hour>20 and  morning_report_sent == True and evening_report_sent ==False and read_cycles>1:
		evening_report(error_count,read_cycles)



	read_cycles=read_cycles+1
	print ("\n\nStarting read cycle number",read_cycles, "\n\n")
	os.chdir(base_dir)
	for sensor_file in glob.glob("28*"):
		device_file = base_dir + sensor_file + '/w1_slave'
		for row in ds18b20_sensor_dict:
			print (" looking for sensor: ", sensor_file, " The current row in dictionary is for sensors", row['serial'])
			if row['serial']==sensor_file:
				print ("found correct row in dict, exiting loop")
				# print ""
				break
			# else:
			# 	print "trying next row"
		cur_sensor=sensor_file
		cur_temp, ds18b20_error_count=read_temp(ds18b20_error_count)
		cur_local=row['location']
		token=row['token']
		cur_id=row['id']
		print ("Sensor =",cur_sensor, "temp is:", cur_temp,"sensor location is:", cur_local)
		print ("the cloundat id for this is:",cur_id)
		evening_report_sent=True

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
		print ('********************************************************* read cycles =', read_cycles)


		if skip_IoT==False:
			print ('your orgID is',orgId, 'sensor is:', cur_sensor, 'token is', token, 'temp is', cur_temp)
			write_to_iot_platform(orgId, cur_sensor, token, cur_temp)
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



