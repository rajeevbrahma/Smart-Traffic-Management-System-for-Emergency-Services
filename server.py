'''*****************************************************************************************
			Smart Traffic Management System for Emergency Services
*****************************************************************************************'''
#!usr/bin/python

# importing the required modules
import os
import sys
from pubnub import Pubnub
from traffic_calc.distance_calculation	import dis_calc
from traffic_calc.bearing import bearng
import time
import datetime 
import pytz      
from termcolor import colored 

# publish and subscribe keys
pub_key="pub-c-1394c3d6-4b89-443e-946a-f1ca36bedcae"       
sub_key="sub-c-7c47827c-159b-11e5-90f9-02ee2ddab7fe"

'''
	Names of the variables in the 'dic_ID[L_ID]' list
	dic_ID[L_ID][0] = L_ID --> client's unique identification number
	dic_ID[L_ID][1] = (NAS)Next approaching signal's number
	dic_ID[L_ID][2] = (PASA)Present approaching signal's angle
	dic_ID[L_ID][3] = command flag 

'''
# Dictionary to store each clients necessary data for calculation
dic_ID = {} 
# List to store the timestamp value of each client
dic_tme = []
# List to store the unique identification number of the client
g_process_list = []
# bff29478-089c-4dff-8895-883580885661

'''****************************************************************************************
Function Name 	:	error
Description		:	If error in the channel, prints the error
Parameters 		:	message - error message
****************************************************************************************'''
def error(message):
    print("ERROR : " + str(message))
'''****************************************************************************************
Function Name 	:	connect
Description		:	Responds if server connects with pubnub
Parameters 		:	message - connect message
****************************************************************************************'''	
def connect(message):
	print("CONNECTED")
'''****************************************************************************************
Function Name 	:	reconnect
Description		:	Responds if server reconnects with pubnub
Parameters 		:	message - reconnect message
****************************************************************************************'''	
def reconnect(message):
    print("RECONNECTED")
'''****************************************************************************************
Function Name 	:	disconnect
Description		:	Responds if server disconnects from pubnub
Parameters 		:	message - disconnect message
****************************************************************************************'''
def disconnect(message):
    print("DISCONNECTED")

'''***************************************************************************
Function Name 	:	calculation_function
Description		:	Initalize the pubnub keys and Starts Subscribing 
Parameters 		:	L_ID(uuid of the client),lat,lng(lattitude and longitude of the client)
***************************************************************************'''
def calculation_function(L_ID,lat,lng):
  	# List of the lattitude and longitude values of the signals
  	L_list1 = ["37.786188 -122.440033","37.787237 -122.431801",
				"37.785359 -122.424704","37.778739 -122.423349",
				"37.776381 -122.419514","37.772811 -122.412835",
		   		"37.765782 -122.407557"]

	L_ID =  str(L_ID)
	try:
		if (dic_ID != 0):
			if (dic_ID[L_ID][1]<=7):
				parameter_lat1 = float(lat)
				parameter_lng1 = float(lng)
				
				#selecting the signal from the list based on the NAS value
				L_spltvariable =  L_list1[dic_ID[L_ID][1]-1]
				L_spltvariable = L_spltvariable.split(' ')
				L_lat2 = L_spltvariable[0]
				L_lng2 = L_spltvariable[1]
				
				# calculating the distancse between the vehicle and the approaching signal
				L_distance = dis_calc(parameter_lat1,parameter_lng1,L_lat2,L_lng2) 
						
				# calculating the angle between the vehicle and the approaching signal						
				L_bearing  = bearng(parameter_lat1,parameter_lng1,L_lat2,L_lng2)   
						
				#print L_distance		
				# Quadrant change
				
				print "beforequdrantchange",L_bearing
				if (L_bearing >180 and L_bearing <= 360):                  
					L_bearing = str(180-L_bearing)
				L_brng2 = str (L_bearing)
				print "after Quadrant change",L_brng2
				
				L_temp1 = dic_ID[L_ID][2]
				L_temp1 = str(L_temp1)
				L_temp2  = L_brng2
				L_temp2 = str(L_temp2)
				
				# checking for the signal crossover  
				if(L_temp1[0] != (L_temp2[0])):	                              
					if (dic_ID[L_ID][3] == False):	
						# sending vehicle crossed message to the respective client
						pubnub.publish(channel = dic_ID[L_ID][0] ,message = {"signal_type":"withdraw","sig_num":dic_ID[L_ID][1]-1},error=error)
						
						print colored("server sent clearance message to %s for the signal %d " %(L_ID,dic_ID[L_ID][1]),'white','on_magenta',attrs=['bold'])
						dic_ID[L_ID][1] = dic_ID[L_ID][1]+1	
						dic_ID[L_ID][3] = True			
				
				# checking for the vehicle approaching near the signal				
				if (L_distance <=200 and L_distance >=100):	 
					if (dic_ID[L_ID][3] == True):
						# sending vehicle approaching message to the respective client
						pubnub.publish(channel=dic_ID[L_ID][0] ,message = {"signal_type":"green","sig_num":dic_ID[L_ID][1]-1},error=error)
						
						print colored("server sent green signal message to %s for the signal %d " %(L_ID,dic_ID[L_ID][1]),'white','on_magenta',attrs=['bold'])
						
						# updating the PASA	
						dic_ID[L_ID][2]= L_brng2
						# setting the flag 	
						dic_ID[L_ID][3] = False
			else:
				pass	
		else:
			pass	
	except Exception as calcException:
		print colored("the calcException is %s, %s"%(calcException,type(calcException)),'red','on_white',attrs=['bold'])

'''***************************************************************************
Function Name 	:	clearing_function
Description		:	Function to clear the all stored values in the dictionary once it is discarded in the middle 
Parameters 		:	None
***************************************************************************'''
def clearing_function():
	try:
		for i in range (0,len(dic_tme)):
			if (len(dic_tme) >=1):
				client = dic_tme[i]
				client_hour = int(client.strftime("%H"))	
				client_min = int(client.strftime("%M"))
				client_sec = int(client.strftime("%S"))
				
				client_day = int(client.strftime("%d")) # testing for day client removal
				
				
				present_time = datetime.datetime.now(pytz.timezone('UTC'))
				present_hour = int(present_time.strftime("%H"))
				present_min = int(present_time.strftime("%M"))
				present_sec = int(present_time.strftime("%S"))
				
				present_day = int(present_time.strftime("%d")) # testing for day client removal
				
				presenttime = (present_hour *60*60) + (present_min*60) + (present_sec)
				clienttime = (client_hour *60*60) + (client_min*60) + (client_sec)
				# Time difference between present Time and the client's starting time 
				time_difference =  (presenttime-clienttime)
				time_difference = time_difference/60
				try:
					if (time_difference >= 2 or (client_day != present_day)):
						L_ID = g_process_list[i+1]
						print colored("The Expired client id is %s"%(L_ID),'red','on_white',attrs=['bold'])
						del dic_ID[L_ID]
						del dic_tme[i]
						del g_process_list[i+1]
						print colored("At the time of new client entry stats ---> \n\nDictionary of each clients necessary data for calculation: %s \n\nTimestamp value list of each client : %s \n\nUUID number of the client: %s \n\nLength of Timestamp list: %s "%(dic_ID,dic_tme,g_process_list,len(dic_tme)),'yellow','on_blue',attrs=['bold'])
						break
				except Exception as clearinException:
					print colored("the clearinException is %s %s "%(clearinException,type(clearinException)),'red','on_white',attrs=['bold'])
	except Exception as clearException:
		print colored("the clearException is %s %s "%(clearException,type(clearException)),'red','on_white',attrs=['bold'])

'''***************************************************************************
Function Name 	:	callback
Description		:	 
Parameters 		:	message - status,lattitude,longitude from client,channel-channel name
***************************************************************************'''
def callback(message,channel):
	# print message
	UUID = message['ID']
	L_count = 0

	try:
		if (message['status'] == "start"):  
			L_ID = UUID
			clearing_function()
			client_time = datetime.datetime.now(pytz.timezone('UTC'))
			dic_tme.append(client_time)
			print dic_tme
			if UUID in g_process_list:
				pass
			else:
				g_process_list.append(UUID)
				dic_ID[L_ID] = [L_ID,1,'167',True]
	except Exception as startexception:
		print colored("The startException is %s %s "%(startException,type(startException)),'red','on_white',attrs=['bold'])				
	
	try:		
		if(message['status'] == "stop"):
			S_ID = str(message['ID'])
			del dic_ID[S_ID]
			for i in range (0,len(g_process_list)):
				if (S_ID == g_process_list[i]):
					del g_process_list[i]
					del dic_tme[i-1]
					break
	except Exception as stopException:
		print colored("The stopexception is %s %s "%(stopException,type(stopException)),'red','on_white',attrs=['bold'])
	
	try:
		if(message['status'] == "run"):
			client_id = message['ID']
			if client_id in g_process_list:
				L_ID = message['ID']
				lat = message['lat']	
				lng = message['lon']
				calculation_function(L_ID,lat,lng)
			else:
				print colored("The %s id client is expired "%(message['ID']),'red','on_white',attrs=['bold']) 
				try:
					pubnub.publish(channel= client_id ,message = {"signal_type":"timeout"},error = error)	
				except Exception as pubxpireExcption:
					print colored("The pubxpireExcption is %s %s "%(pubxpireExcption,type(pubxpireExcption)),'red','on_white',attrs=['bold'])
	except Exception as runException:
		print colored("The runException is %s %s"%(runException,type(runException)),'red','on_white',attrs=['bold'])

	return True

'''***************************************************************************
Function Name 	:	pub_Init
Description		:	Initalizing the pubnub keys and Starts Subscribing 
Parameters 		:	None
***************************************************************************'''
def pub_Init():
	global pubnub
	try:
		pubnub = Pubnub(publish_key=pub_key,subscribe_key=sub_key) 
		pubnub.subscribe(channels='trail2pub_channel', callback=callback,error=error,
    	connect=connect, reconnect=reconnect, disconnect=disconnect)
	except Exception as pubException:
		print colored("The pubException is %s %s"%(pubException,type(pubException)),'red','on_white',attrs=['bold'])

'''****************************************************************************************
Function Name 	:	__main__
Description		:	Conditional Stanza where the Script starts to run
Parameters 		:	None
****************************************************************************************'''
if __name__ == "__main__":
	pub_Init()
	
#End of the Script 
##*****************************************************************************************************##




    
