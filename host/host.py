from device485 import Device
from comm485 import Conn485
import time, configparser

# конфигурационный файл устройтв
CONFIG_FILE = "cfg\\devices.cfg"

# типы управляющих устройства
CONTROL_TYPES = ["encoder", "switch", "virtual"]

# список управляющих устройств 
controllers = []

# типы исполнительных устройств
EXEC_TYPES = ["pwm", "relay"]

# список исполнительных устройств
executors = []

# загрузка конфигурации
config = configparser.RawConfigParser()
config.read(CONFIG_FILE)

# создание подключения
conn = Conn485()

# создание объектов устройств по конфигурационному файлу
for section in config.sections():
	
	time.sleep(0.1)

	# парсинг секции конфигурационного файла 
	address = config.getint(section, 'address')
	name = config.get(section, 'name')
	dev_type = config.get(section, 'type')
	init_regs = [config.getint(section, 'reg1'), config.getint(section, 'reg2')]
	controls = config.get(section, 'controls')
	priority = config.getint(section, 'priority')

	# определение устройства в управляющие или исполнительные
	if dev_type in CONTROL_TYPES:
		controllers.append(Device(address, name, dev_type, controls, priority, init_regs, conn))
		print ('Created controller "%s" type "%s" with address %i (controls %s priority %i)' % (name, dev_type, address, controls, priority))

	elif dev_type in EXEC_TYPES:
		executors.append(Device(address, name, dev_type, controls, priority, init_regs, conn))
		print ('Created executor "%s" type "%s" with address %i' % (name, dev_type, address))

	else:
		print ('Error creating "%s": incorrect device type "%s"' % (name, dev_type))	
	


try:

	while True:
		if executors[0].read_registers(conn):
			# print (executors[0].get_registers())
			pass
		else:
			del conn
			time.sleep(0.1)
			conn = Conn485()

		time.sleep(0.1)

		if executors[0].write_registers([50,1],conn):
			print("on")

		time.sleep(1)

		if executors[0].write_registers([50,0],conn):
			print("off")
		time.sleep(1)
	

finally:
	if "conn" in locals(): # проверка существования conn в локальной области видимости
		print("Closing COM port")
		del conn
	print("----Execution aborted----")

