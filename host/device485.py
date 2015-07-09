# Класс устройства с методами работы с железом
import time

# адрес мастера
MASTER = 1

# команды
READ_REG = 10
WRITE_REG = 20
CHANGE_ADDR = 30

class Device:

	def __init__(self, address, name, devtype, controls, priority, initial_regs, connection):
		""" конструктор"""

		self.address = address # адрес устройства
		self.name = name # имя устройства
		self.type = devtype # тип устройства
		self.what_controls = controls # имя устройства, управляемого этим
		self.control_priority = priority # приоритет управляющего устройства
		self.registers = [0,0] # создание полей регистров
		
		# для реального устройства - записать значения регистров в устройство и поля,
		# для виртуального - только в поля
		if self.type != "virtual":
			self.write_registers(initial_regs, connection) 
		else:
			self.registers = initial_regs

	def write_registers(self, registers, connection):
		""" запись регистров устройства, возвращает FF при успехе
		и 00 при неправильном подтверждении или его отсутствии
		записывает в поля только при успехе"""

		# для виртуального устройства - только в поля
		if self.type == "virtual":
			self.registers = registers
			return 0xFF

		# в устройство
		connection.send([self.address, WRITE_REG, registers[0], registers[1]])
		time.sleep(0.01)

		# подтверждение и его проверка
		ack_packet = connection.receive()
		
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

	def read_registers(self, connection):
		""" чтение регистров из устройства,
		записывает в поля и возвращает FF при успехе,
		иначе возвращает 0"""

		# для виртуального устройства - просто возврат FF,
		# так как поля всегда актуальны
		if self.type == "virtual":
			return 0xFF

		# запрос
		connection.send([self.address, READ_REG,0,0])
		time.sleep(0.01)

		# получение ответа
		ack_packet = connection.receive()

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

		# для виртуального - просто запись поля
		if self.type == "virtual":
			self.address = address
			return 0xFF

		# в устройство
		connection.send([self.address, CHANGE_ADDR, address, 0])
		time.sleep(0.01)

		# подтверждение и его проверка
		ack_packet = self.connection.receive()

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

	def controls(self):
		"""получение имени управлямого устройства"""

		return self.what_controls


	def priority(self):
		""" получение приоритета управляющего устройства"""

		return self.control_priority

class Timer:

	def __init__(self, name, controls, priority, regs_on, regs_off, time_on, time_off):
		"""конструктор"""

		self.name = name
		self.what_controls = controls
		self.priority = priority
		self.regs_on = regs_on
		self.regs_off = regs_off

		self.time_on = time.strptime(time_on, "%H:%M") # конвертация строки в struct_time по формату
		self.time_off = time.strptime(time_off, "%H:%M") 

	def check(self):
		""" проверка времени. Если исполнитель в это время должен быть выключен,
		возвращает 0, если включен - FF """

		current = time.localtime()

		current_on = list(current) # чтобы можно было изменить
		current_on[3] = self.time_on.tm_hour
		current_on[4] = self.time_on.tm_min
		current_on[5] = 0 # секунды
		current_on = time.struct_time(tuple(current_on)) # обратно в struct
		current_on = time.mktime(current_on) # и в секунды-с-начала-эпохи

		current_off = list(current) # чтобы можно было изменить
		current_off[3] = self.time_off.tm_hour
		current_off[4] = self.time_off.tm_min
		current_off[5] = 0 # секунды
		current_off = time.struct_time(tuple(current_off)) # обратно в struct
		current_off = time.mktime(current_off) # и в секунды-с-начала-эпохи

		# если время включения больше времени включения, значит, попадание
		# на переход через сутки
		if current_on > current_off:
			current_off += 86400

		current = time.mktime(current)

		print(current_on, current, current_off)

		if current in range(int(current_on), int(current_off)+1):
			return 0xFF
		else:
			return 0x00


	def get_regs_on(self):
		return self.regs_on

	def get_regs_off(self):
		return self.regs_off

	def controls(self):
		return self.what_controls


