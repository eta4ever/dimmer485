import serial, time

# параметры COM порта
comPort = "COM3"
baudRate = 38400

# 10 миллисекунд - приемный таймаут
serialConn = serial.Serial(comPort, baudRate, timeout = 1)

time.sleep(0.01)	
serialConn.setDTR(False)
time.sleep(0.01)	
serialConn.write([1,2,3,4,5,6,7,8,9,0])
time.sleep(0.01)	
serialConn.setDTR(True)
time.sleep(0.01)
print(list(serialConn.read(10)))

# закрыть порт
serialConn.close()