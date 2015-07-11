from device485 import Device
from comm485 import Conn485
import time, configparser

# # количество попыток чтения или записи в устройство, задержка между попытками
# ATTEMPTS = 5
# ATTEMPT_DELAY = 0.1

# конфигурационный файл устройтв
CONFIG_FILE = "cfg\\devices.cfg"

# типы управляющих устройства
CONTROL_TYPES = ["encoder", "switch", "virtual", "timer"]

# типы исполнительных устройств
EXEC_TYPES = ["pwm", "relay"]

# типы "железных" устройств
HARDWARE_TYPES = ["encoder", "switch", "pwm", "relay"]

# список управляющих устройств 
controllers = []

# список исполнительных устройств
executors = []

# создание подключения
conn = Conn485()

# создание объектов устройств по конфигурационному файлу
config = configparser.RawConfigParser()
config.read(CONFIG_FILE)
for section in config.sections():
	
	# выбор общих параметров
	name = config.get(section, 'name')
	dev_type = config.get(section, 'type')

	# создание устройства
	device = Device(name, dev_type)

	# определение устройства в управляющие или исполнительные
	if dev_type in CONTROL_TYPES:
		controls = config.get(section, 'controls')
		priority = config.getint(section, 'priority')
		device.init_as_controller(controls, priority)
		controllers.append(device)

	elif dev_type in EXEC_TYPES:
		executors.append(device)
	
	else:
		print ('Error creating "%s": incorrect device type "%s"' % (name, dev_type))

	# инициализация железного устройства
	if dev_type in HARDWARE_TYPES:
		
		address = config.getint(section, 'address')
		init_regs = [config.getint(section, 'reg1'), config.getint(section, 'reg2')]
		
		if device.init_as_hardware(address, init_regs, conn):
			print("{} addr {:d} ok".format(name, address))
		else:
			print("ERROR writing initial regs to {} with addr {:d}".format(name, address))

	# инициализация таймера
	if dev_type == "timer":
		regs_on = [config.getint(section, 'reg1on'), config.getint(section, 'reg2on')]
		regs_off = [config.getint(section, 'reg1off'), config.getint(section, 'reg2off')]
		time_on = config.get(section, 'time_on')
		time_off = config.get(section, 'time_off')		
		device.init_as_timer(regs_on, regs_off, time_on, time_off)

# формирование словаря вида "имя исполнителя : код в списке executors"
executors_id_by_name = { executor.get_name() : executors.index(executor) for executor in executors}

# инициализация словаря "код исполнителя: []" для дальнейшего заполнения управляющими
# сюда не попадают исполнители, управляемые по таймеру!
executors_controlled_by = {executors.index(executor): [] for executor in executors}

# заполнение словаря "код исполнителя: [список кодов управляющих]"
for controller in controllers:
	executor_id = executors_id_by_name[controller.controls()]
	executors_controlled_by[executor_id].append(controllers.index(controller))

#dummy = input(">>>")
# print (executors_controlled_by)

try:

	while True:

		for executor_id in range(0,len(executors)):

			if len(executors_controlled_by[executor_id]) == 1:
				# простой случай, один управляющий

				curr_controller = controllers[executors_controlled_by[executor_id][0]]

				# чтение регистров управляющего
				if curr_controller.read_registers(conn):
					regs_to_executor = curr_controller.get_registers()
					print("o")

					# time.sleep(0.1)
					# при удачном чтении - запись регистров исполнителя
					if executors[executor_id].write_registers(regs_to_executor,conn):
						print("x")
						pass
					else:
						print("ERROR writing {} addr {:d}".format(executors[executor_id].get_name(), executors[executor_id].get_address()))
				else:
					print("ERROR reading {} addr {:d}".format(curr_controller.get_name(), curr_controller.get_address()))

		time.sleep(1)		

finally:
	if "conn" in locals(): # проверка существования conn в локальной области видимости
		print("Closing COM port")
		del conn
	print("----Execution aborted----")

