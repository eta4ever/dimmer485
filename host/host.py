from device485 import Device, Timer
from comm485 import Conn485
import time, configparser

# конфигурационный файл устройтв
CONFIG_FILE = "cfg\\devices.cfg"

# конфигурационный файл таймеров
TIMERS_CONFIG_FILE = "cfg\\timers.cfg"

# типы управляющих устройства
CONTROL_TYPES = ["encoder", "switch", "virtual"]

# список управляющих устройств 
controllers = []

# типы исполнительных устройств
EXEC_TYPES = ["pwm", "relay"]

# список исполнительных устройств
executors = []

# список таймеров
timers = []

# создание подключения
conn = Conn485()

# создание объектов устройств по конфигурационному файлу
config = configparser.RawConfigParser()
config.read(CONFIG_FILE)
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
	
# создание объектов таймеров по конфигурационному фвйлу
config = configparser.RawConfigParser()
config.read(TIMERS_CONFIG_FILE)
for section in config.sections():
	
	name = config.get(section, 'name')
	controls = config.get(section, 'controls')
	regs_on = [config.getint(section, 'reg1on'), config.getint(section, 'reg2on')]
	regs_off = [config.getint(section, 'reg1off'), config.getint(section, 'reg2off')]
	time_on = config.get(section, 'time_on')
	time_off = config.get(section, 'time_off')
	priority = config.getint(section, 'priority')

	timers.append(Timer(name, controls, priority, regs_on, regs_off, time_on, time_off))
	print ('Created timer "%s" controls "%s" priority %i %s - %s' % (name, controls, priority, time_on, time_off))

# формирование словаря вида "имя исполнителя : код в списке executors"
executors_id_by_name = { executor.get_name() : executors.index(executor) for executor in executors}

controllers[0].write_registers([100,1], conn)
controllers[1].write_registers([100,0], conn)

dummy = input(">>>")

try:

	while True:
		
		# for controller in controllers:

		# 	# если не читаются регистры управляющего устройства, дергать соединение
		# 	while not (controller.read_registers(conn)):
		# 		del conn
		# 		time.sleep(0.1)
		# 		conn = Conn485()
		# 		time.sleep(0.1)

		# 	print ("Read from %s: %i, %i" %(controller.get_name(), controller.get_registers()[0],
		# 		controller.get_registers()[1]))

		# 	# если не записываются регистры исполнительного устройства, дергать соединение
		# 	while not(executors[executors_id_by_name[controller.controls()]].write_registers(
		# 		controller.get_registers(), conn)):
		# 		del conn
		# 		conn = Conn485()
		# 		time.sleep(0.1)

		# 	print ("Wrote %i, %i" %(controller.get_registers()[0], controller.get_registers()[1]))

		# 	time.sleep(1)

		if timers[0].check():
			
			curr_regs = timers[0].get_regs_on()

		else:

			curr_regs = timers[0].get_regs_off()

		curr_executor = executors[executors_id_by_name[timers[0].controls()]]

		while not (curr_executor.read_registers(conn)):
			del conn
			time.sleep(0.1)
			conn = Conn485()
			time.sleep(0.1)
			
		if curr_executor.get_registers() != curr_regs:
			curr_executor.write_registers(curr_regs, conn)

		time.sleep(1)

finally:
	if "conn" in locals(): # проверка существования conn в локальной области видимости
		print("Closing COM port")
		del conn
	print("----Execution aborted----")

