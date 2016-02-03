#!/usr/bin/python3 
# -*- coding: utf-8 -*-

"""
Programmer: Dipto Pratyaksa for LinuxCircle.com
August 2015. Tech: Python 3, SMBUS, i2C, TEA5767 FM Radio, Raspberry Pi 2
Project:Raspberry Pi Voice command robot via FM transmitter and receiver 
Module: Tea 5767 Station Scanner
Future wish list:
- Save strong stations into text file list
Reference:
https://raw.githubusercontent.com/JTechEng/tea5767/
https://github.com/pcnate/fm-radio-python
http://www.astromik.org/raspi/38.htm
"""

import smbus as smbus 
import subprocess
import time
import sys

import quick2wire.i2c as i2clib
from quick2wire.i2c import I2CMaster, writing_bytes, reading

cof = 32768 #crystal constant


class tea5767:
 def __init__(self):
   self.i2c = smbus.SMBus(1)
   self.bus = i2clib.I2CMaster()
   self.add = 0x60 # I2C address circuit 

   print("FM Radio Module TEA5767")
   #initiation
   if(not self.getReady()):
     print("resetting to default")
     self.i2c.write_byte(self.add, 0x00)
     self.getReady()

   self.freq = self.calculateFrequency()                         
   if self.freq < 87.5 or self.freq > 107.9:
     self.freq = 101.9


   print("Last frequency = " , self.freq, "FM")
   self.writeFrequency(self.freq, 0, 0)


 def getFreq(self):
   frequency = 0.0
   results = self.bus.transaction(
     reading(self.add, 5)
   )

   frequency = ((results[0][0]&0x3F) << 8) + results[0][1];
   # Determine the current frequency using the same high side formula as above
   frequency = round(frequency * 32768 / 4 - 225000) / 1000000;
   return frequency


 def calculateFrequency(self):
   """calculate the station frequency based upon the upper and lower bits read from the device"""
   repeat = 0
   f =0.0
   with i2clib.I2CMaster() as b:
     results = b.transaction(
       reading(self.add, 5)
     )

   uF = results[0][0]&0x3F
   lF = results[0][1]

   #good formula
   current_freq = round((float(round(int(((int(uF)<<8)+int(lF))*cof/4-22500)/100000)/10)-.2)*10)/10
   return current_freq



#script to get ready
 def getReady(self):

   readyFlag = 0 
   i = False
   attempt = 0
   results=[]
   standbyFlag = 0
   sys.stdout.flush()
   time.sleep(0.1) 
   print("Getting ready ", end ="")
   while (i==False):
     results = self.bus.transaction(
       reading(self.add, 5)
     )

     readyFlag = 1 if (results[0][0]&0x80)==128 else 0
     standbyFlag = 1 if (results[0][3]+0x40)!=319 else 0
   
     sys.stdout.flush()
     time.sleep(0.1)
     print(".", end = "")
     i=standbyFlag*readyFlag
     #if(i==0):
     #  try:
     #   self.i2c.write_byte(self.add,0x00)
     #  except:
     #   i=i
     attempt+=1
     if(attempt>20):
       break
     time.sleep(0.2)
 
   if(i==True):
     print("Ready! (",attempt,")")
     return True
# print("Raw output ", results[0])
   else:
     self.i2c.read_byte(self.add)
     print("Not ready! (", attempt, ")")
     return False

 def writeFrequency(self,f, mute, direction):
   freq =  f # desired frequency in MHz (at 101.1 popular music station in Melbourne) 
   #cof = 32768
   i=False
   attempt = 0
   # Frequency distribution for two bytes (according to the data sheet) 
   freq14bit = int (4 * (freq * 1000000 + 225000) / cof)
   freqH = freq14bit >>8
   freqL = freq14bit & 0xFF

   data = [0 for i in range(4)]
   # Descriptions of individual bits in a byte - viz.  catalog sheets 
   if(mute==0): 
     init = freqH&0x3F# freqH # 1.byte (MUTE bit; Frequency H)  // MUTE is 0x80 disable mute and search mode & 0x3F
   else:
     init = freqH&0x7F
   data[0] = freqL # 2.byte (frequency L) 
   if(mute==0 and direction==1):
     data[1] = 0b10010000 # 3.byte (SUD; SSL1, SSL2; HLSI, MS, MR, ML; SWP1) 
   elif(mute==0 and direction==0):
     data[1] = 0b00010000
   else:
     data[1] = 0b00010110 #mute L & R during scanning
   data[2] =  0b00010010 # 4.byte (SWP2; STBY, BL; XTAL; smut; HCC, SNC, SI) 
   data[3] =  0b00000000 # 5.byte (PLREFF; DTC; 0; 0; 0; 0; 0; 0) 

#data[1]=0xB0; #3 byte (0xB0): high side LO injection is on,.
#data[2]=0x10; #4 byte (0x10) : Xtal is 32.768 kHz
#data[3]=0x00; #5 byte0x00)

   while (i==False):
     try:
       self.i2c.write_i2c_block_data (self.add, init, data) # Setting a new frequency to the circuit 
     except IOError as e :
       i = False
       attempt +=1
       if attempt > 100000:
         break
     except Exception as e:
       print("I/O error: {0}".format(e))

     else:
       i = True


 def scan(self,direction):
   i=False
   fadd = 0
   while (i==False):
     if(direction==1):
       fadd=0.1
     else:
       fadd=-0.1
     #get current frequency, more accurately by averaging 2 method results
     self.freq = round((self.calculateFrequency()+self.getFreq())/2,2)
     if(self.freq<87.5):
       self.freq=108
     elif(self.freq>107.9):
       self.freq=87.5
     self.writeFrequency(self.freq+fadd,1,direction)

     #give time to finish writing, and then read status
     time.sleep(0.1)
     results = self.bus.transaction(
       reading(self.add, 5)
     )
     self.freq = round((self.calculateFrequency()+self.getFreq())/2,2) #read again

     readyFlag = 1 if (results[0][0]&0x80)==128 else 0
     level = results[0][3]>>4
     #print(results[0][0]&0x80 , " " , results[0][3]>>4)

     #tune into station that has strong signal only
     if(readyFlag and level>9):
       i=True
       print("Frequency tuned: ",self.freq , "FM (Strong Signal: ",level,")")
     else:
       i=False
       print("Station skipped: ",self.freq , "FM (Weak Signal: ",level,")")
     #time.sleep(0.1)
   self.writeFrequency(self.freq ,0,direction)




 def gapscan( self ):
   run=1
   self.freq = 87.4
   fadd = 0.1
   f = open("run_"+str(run),"w")
   while ( 1 ):
     if(self.freq < 87.4 ):
       self.freq=87.4
     if(self.freq > 107.9 ):
       self.freq=87.4
       run = run + 1
       f.close()
       f = open("run_"+str(run),"w")	 
     self.writeFrequency(self.freq+fadd,1,1)

     #give time to finish writing, and then read status
     time.sleep(0.1)
     results = self.bus.transaction(
       reading(self.add, 5)
     )
     self.freq = round((self.calculateFrequency()+self.getFreq())/2,2) #read again

     readyFlag = 1 if (results[0][0]&0x80)==128 else 0
     level = results[0][3]>>4
     #print(results[0][0]&0x80 , " " , results[0][3]>>4)

     if( readyFlag ):
       print(self.freq , "MHz, Level: ",level)
       f.write( str(self.freq) + " " + str(level) + "\n" )



 def off(self):
   print("Radio off: Goodbye now!")
   self.writeFrequency(self.calculateFrequency(), 1,0) 

 def test(self):
   print("Testing mode")
   print("Scanning up...")
   self.scan(1)
   print("Listening for 10 seconds")
   time.sleep(10)
   print("Scanning down...")
   self.scan(0)
   print("Listening for 10 seconds")
   time.sleep(10)
   print("done")
#sample usage below:
#radio = tea5767()
#radio.scan(1)
#time.sleep(15)
#radio.scan(1)
#time.sleep(15)
#radio.scan(0)
#time.sleep(15)
#radio.scan(0)
#time.sleep(15)
#radio.off()

