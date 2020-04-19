import logging
import re
import serial
import time
from datetime import datetime

#################################
#settings
#################################
comm_port = 'COM35'
baudrate = 115200
sleep_period = 20
ctrl_z = b"\x1a"
reset_modem_flag = False
#################################



#################################
#helper function for sending the commands
#       it will send the 'command' argument to the 'serial'
#       and look for 'expected_response' back, retrying 'retries' times before failling
#       the expected response is a regular expression
##################################
def sendATcommand( serial, command, expected_response, retries = 20):
    logging.debug("sending command   -- " + command)
    serial.write(command)
    serial.write("\r")     # write EOL

    while True:
        response = serial.readline()
        logging.debug("response received -- " + response.rstrip())
        				
        if re.match(expected_response, response):
            return 0
            break

        retries -= 1
        if retries == 0:
            return 1

        

ser = serial.Serial(comm_port, baudrate, timeout=2)  # open serial port
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

#########################
# Init command list
#
#  it must be a list with entries in the format [ command, response ], where
#  - both command and response are text strings
#  - command will be sent to the serial port
#  - response is a regular expression, that will be used to parse the returned data of the port
##########################
init_command_list = [
    ["AT", "OK"],
    ["ATI", "OK"],
    ["ATE1", "OK"],
    ["AT+COPS?", "OK"],
    ["AT+CPIN?", "OK"],
    ["AT+QICSGP=1,1,\"everywhere\"", "OK"],
    ["AT+CEREG=1", "OK"],
    ["AT+CFUN?", "OK"],
    ["AT+CFUN=1", "OK"],
    ["AT+COPS?",  "OK"],
    ["AT+QIACT=1", "OK"],
    ["AT+QIACT?", "OK"],
    ["AT+QMTCFG=\"will\",0", "OK"],
    ["AT+QMTCFG=\"timeout\",0,60,3,0", "OK"],
    ["AT+QMTCFG=\"keepalive\",0,60",  "OK"],
    ["AT+QMTOPEN=1,\"www.testmyquectel.net\",1883", "^\+QMTOPEN: 1,0"],
    ["AT+QMTCONN=1,\"mqtt_bg96\",\"quectel\",\"testmqtt\"", "^\+QMTCONN: 1,0,0"]
]

##########################
#reset the modem
#  this only works with UART connection!
##########################
if reset_modem_flag:
    if sendATcommand(ser, "AT+CFUN=1,1", "APP RDY", 30) == 1:
        logging.fatal("COMMAND[AT+CFUN=1,1] FAILED, ABORTING***********")
        exit(1)

##########################
#send the initial command list
##########################
for cmd, resp_pattern in init_command_list:
    if sendATcommand(ser, cmd, resp_pattern, 10) == 1:
        logging.fatal("COMMAND[" + cmd + "] FAILED, ABORTING***********")
        exit(1)
    #time.sleep(1)
##########################
#periodic loop, will be executed every sleep_period
##########################
ser.timeout = 1
counter=0
try:
    while True:

        payload = "P-" + str(counter).zfill(4) + chr(26)

        #############
        #periodic command list
        #   it's done here so variables can be send (useful for payloads)
        #   It follows the same rules as the inital command list
        #############
        periodic_command_list = [
            [ 	"AT+QMTPUB=1,1,1,0,\"example/label1\"",  "^>" ],
            [ payload, "^\+QMTPUB: 1,1,0" ],
        ]


        for cmd, resp_pattern in periodic_command_list:
                if sendATcommand(ser, cmd, resp_pattern, 30) == 1:
                        logging.fatal("COMMAND[" + cmd + "] RETURNED UNEXPECTED VALUE")
                        break

        time.sleep(sleep_period)
        counter += 1

except KeyboardInterrupt:
    # quit
    ser.close()         


