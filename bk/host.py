import serial, time

# параметры COM порта
comPort = "COM3"
baudRate = 19200

MASTER = 1 # адрес этого хоста - мастера

# команды
READ_REG = 10
WRITE_REG = 20
CHANGE_ADDR = 30

REGS_TO_MASTER = 50 # код команды при отправке регистров мастеру
ACK_TO_MASTER = 60 # код команды при подтверждении мастеру

# 10 миллисекунд - приемный таймаут
serialConn = serial.Serial(comPort, baudRate, timeout = 1)

def checksum(packet):
	""" вычисление контрольной суммы пакета """

	return sum(packet[0:3]) % 256

def sendPacket(packet):
	""" отправка пакета, аргумент 4 байта """

	serialConn.setDTR(False) # высокий уровень, передача

	packetToSend = list(packet)
	packetToSend.append(checksum(packet))
	serialConn.write(packetToSend)

def receivePacket():
	""" прием пакета """

	serialConn.setDTR(True) # низкий уровень, прием

	#serialConn.flushInput() # очистка буфера

	# ожидание появления чего-то в буфере
	# while serialConn.inWaiting() == 0:
	# 	time.sleep(0.001)
	
	# чтение 5 байт
	packet = list(serialConn.read(5))

	print(packet)
	
	# если принято меньше 5 байт, вернуть 0x00
	if len(packet) < 5:
		return [0x00]

	# если контрольная сумма не совпадает, вернуть 0x00
	if packet[4] != checksum(packet):
		return [0x00]

	return packet

def readDevice(address):
	""" получение пакета с регистрами устройства """
	
	# запрос устройству
	sendPacket([address, READ_REG, 0, 0])

	# получение ответа
	packet = receivePacket()

	# если не получен нормальный ответ, вернуть 0x00
	if packet[0] == [0x00]:
		return [0x00]
	else:
		return packet

def writeDevice(address, registers):
	"""запись в регистры устройства"""

	# запрос устройству
	sendPacket([address, WRITE_REG, registers[0], registers[1]])
	
	# получение ответа
	packet = receivePacket()

	# если не получен нормальный ответ, вернуть 0x00
	if packet[0] == [0x00]:
		return [0x00]

	# если получено что-то, непохожее на подтверждение, вернуть 0x00
	elif (packet[0] != MASTER) or (packet[1] != ACK_TO_MASTER):
		return [0x00]

	else:
		return [0xFF]

#serialConn.flushInput()
time.sleep(0.01)	
serialConn.setDTR(False)
time.sleep(0.01)	
serialConn.write([1,2,3,4,5])
time.sleep(0.01)	
serialConn.setDTR(True)
time.sleep(0.01)
print(list(serialConn.read(5)))


# закрыть порт
serialConn.close()