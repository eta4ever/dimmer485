# Класс устройства с методами работы с железом
import time

# адрес мастера
MASTER = 1

# команды
READ_REG = 10
WRITE_REG = 20
CHANGE_ADDR = 30

class Device:

	def __init__(self, name, devtype):
		""" конструктор основного объекта"""

		self.name = name # имя устройства
		self.type = devtype # тип устройства

	def init_as_hardware(self, address, init_regs, connection):
		""" инициализация "железного" или виртуального устройства"""
		self.address = address
		self.registers = [0,0]

		if self.write_registers(init_regs, connection):
			return 0xFF
		else: 
			return 0
	
	def init_as_controller(self, controls, priority):
		""" инициализация как управляющего """
		self.what_controls = controls
		self.priority = priority

	def init_as_timer(self, regs_on, regs_off, time_on, time_off):
		""" инициализация таймера """

		self.regs_on = regs_on
		self.regs_off = regs_off

		self.time_on = time.strptime(time_on, "%H:%M") # конвертация строки в struct_time по формату
		self.time_off = time.strptime(time_off, "%H:%M") 

		# преобразование в минуты для простого сравнения
		# так работать в итоге проще, чем преобразовывать туда-сюда форматы времени и 
		# учитывать дату
		self.time_on = self.time_on.tm_hour * 60 + self.time_on.tm_min
		self.time_off = self.time_off.tm_hour * 60 + self.time_off.tm_min

	def write_registers(self, registers, connection):
		""" запись регистров устройства, возвращает FF при успехе
		и 00 при неправильном подтверждении или его отсутствии
		записывает в поля только при успехе"""

		# не работает для таймера
		if self.type == "timer":
			return 0

		# для виртуального устройства - только в поля
		if self.type == "virtual":
			self.registers = registers
			return 0xFF

		# в устройство
		connection.send([self.address, WRITE_REG, registers[0], registers[1]])
		# time.sleep(0.01)

		# подтверждение и его проверка
		ack_packet = connection.receive()

		# print(ack_packet)

		# неполный прием или неверная контрольная сумма
		if ack_packet == [0]: 
			# print(1)
			return 0
		
		# несовпадение адреса мастера или несовпадение регистров с переданными
		elif (ack_packet[0] != MASTER) or (ack_packet[2] != registers[0]) or (ack_packet[3] != registers[1]):
			# print(ack_packet[0], MASTER, ack_packet[2], registers[0], ack_packet[3], registers[1])
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

		# не работает для таймера
		if self.type == "timer":
			return 0

		# для виртуального устройства - просто возврат FF,
		# так как поля всегда актуальны
		if self.type == "virtual":
			return 0xFF

		# запрос
		connection.send([self.address, READ_REG,0,0])
		# time.sleep(0.01)

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

		# не работает для таймера и виртуального устройства
		if self.type in ["virtual","timer"]:
			return 0

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

	def get_address(self):
		""" получение адреса """

		# не работает для таймера и виртуального устройства
		if self.type in ["timer", "virtual"]:
			return 0
		else:
			return self.address

	def get_type(self):
		""" получение типа устройства"""

		return self.type

	def controls(self):
		"""получение имени управлямого устройства"""

		return self.what_controls

	def get_priority(self):
		""" получение приоритета управляющего устройства"""

		return self.priority

	def check_time(self):
		""" проверка времени. Если исполнитель в это время должен быть выключен,
		возвращает 0, если включен - FF """

		# работает только для таймера
		if self.type != "timer":
			return 0

		current = time.localtime() # получение struct текущего времени
		current = current.tm_hour * 60 + current.tm_min # преобразование в минуты для простого сравнения

		if self.time_off >= self.time_on:
			# если время выключения больше времени включения - все просто,
			# перехода на следующие сутки нет
			
			if current in range(self.time_on, self.time_off):
				return 0xFF
			else:
				return 0

		else:
			# обработка перехода на следующие сутки
			if current <= 1439: # если текущее время в промежутке до 23:59 включительно
				if current in range(self.time_on, 1440): # проверить левый интервал
					return 0xFF
				else:
					return 0
			else: 
				if current in range(0, self.time_off): # проверить правый интервал
					return 0xFF
				else:
					return 0

	def get_regs_on(self):
		""" возвращает значения регистров для состояния ВКЛ """

		# работает только для таймера
		if self.type != "timer":
			return [0,0]
		return self.regs_on

	def get_regs_off(self):
		""" возвращает значения регистров для состояния ВЫКЛ """

		# работает только для таймера
		if self.type != "timer":
			return [0,0]
		return self.regs_off

	def controls(self):
		""" возвращает имя управляемого устройства"""

		# не работает для исполнительных устройств
		if self.type in ["pwm", "relay"]:
			return ""
		return self.what_controls


