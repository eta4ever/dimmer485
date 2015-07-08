# Класс устройства с методами работы с железом
import time

# адрес мастера
MASTER = 1

# команды
READ_REG = 10
WRITE_REG = 20
CHANGE_ADDR = 30

class Device:

	def __init__(self, address, name, devtype, initial_regs, connection):
		""" конструктор"""

		self.address = address
		self.name = name
		self.type = devtype
		self.registers = [0,0]
		
		self.write_registers(initial_regs, connection)

	# def connect(self):
	# 	""" подключение к устройству """
	# 	self.connection = Conn485()

	# def disconnect(self):
	# 	""" отключение от устройства """
	# 	del self.connection

	def write_registers(self, registers, connection):
		""" запись регистров устройства, возвращает FF при успехе
		и 00 при неправильном подтверждении или его отсутствии
		записывает в поля только при успехе"""

		# в устройство
		# self.connect()
		connection.send([self.address, WRITE_REG, registers[0], registers[1]])
		time.sleep(0.01)

		# подтверждение и его проверка
		ack_packet = connection.receive()

		# отключение от устройства
		# self.disconnect()
		
		# неполный прием или неверная контрольная сумма
		if ack_packet == [0]: 
			return 0
		
		# несовпадение адреса мастера или несовпадение регистров с переданными
		elif (ack_packet[0] != MASTER) or (ack_packet[2] != registers[0]) or (ack_packet[3] != registers[1]):
			return 0

		# успешно
		else:
			# в поля объекта
			self.registers[0] = registers[0]
			self.registers[1] = registers[1]	

			return 0xFF	
		# return 0xFF

	def read_registers(self, connection):
		""" чтение регистров из устройства,
		записывает в поля и возвращает FF при успехе,
		иначе возвращает 0"""

		# подключение
		# self.connect()

		# запрос
		connection.send([self.address, READ_REG,0,0])
		time.sleep(0.01)

		# получение ответа
		ack_packet = connection.receive()

		# отключение от устройства
		# self.disconnect()

		# неполный прием или неверная контрольная сумма
		if ack_packet == 0: 
			return 0

		# несовпадение адреса мастера
		if ack_packet[0] != MASTER:
			return 0

		# запись регистров в поля
		self.registers[0] = ack_packet[2]
		self.registers[1] = ack_packet[3]

		return 0xFF

	def set_address(self, address, connection):
		""" изменение адреса устройства
		возвращает 0 при неудаче, при успехе записывает в поле
		и возращает FF"""

		# в устройство
		# self.connect()
		connection.send([self.address, CHANGE_ADDR, address, 0])
		time.sleep(0.01)

		# подтверждение и его проверка
		ack_packet = self.connection.receive()

		# отключение от устройства
		# self.disconnect()
		
		# неполный прием или неверная контрольная сумма
		if ack_packet == [0]: 
			return 0
		
		# несовпадение адреса мастера
		if ack_packet[0] != MASTER:
			return 0

		# запись нового адреса в поле
		self.address = address

		return 0xFF

	def get_registers(self):
		""" получение регистров устройства"""

		return self.registers

	def get_name(self):
		""" чтение имени устройства"""

		return self.name

	def get_type(self):
		""" получение типа устройства"""

		return self.type

