from device485 import Device
from comm485 import Conn485
import time, configparser

# количество попыток чтения или записи в устройство, задержка между попытками
ATTEMPTS = 100
ATTEMPT_DELAY = 0.1

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

# создание объектов устройств по конфигурационному файлу
config = configparser.RawConfigParser()
config.read(CONFIG_FILE)
for section in config.sections():
	
	time.sleep(0.1)

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
		
		# создание подключения
		conn = Conn485()

		address = config.getint(section, 'address')
		init_regs = [config.getint(section, 'reg1'), config.getint(section, 'reg2')]
		
		for attempt in range(0, ATTEMPTS):
			if device.init_as_hardware(address, init_regs, conn):
				print("{} addr {:d} ok".format(name, address))
				break
			else:
				print(".", end='')
				del conn
				conn = Conn485()
				time.sleep(ATTEMPT_DELAY)
		else:
			print("ERROR writing initial regs to {} with addr {:d}".format(name, address))

		del conn

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

		conn = Conn485()

		for executor_id in range(0,len(executors)):

			if len(executors_controlled_by[executor_id]) == 1:
				# простой случай, один управляющий

				curr_controller = controllers[executors_controlled_by[executor_id][0]]

				# чтение регистров управляющего
				for attempt_r in range(0,ATTEMPTS):
					if curr_controller.read_registers(conn):
						regs_to_executor = curr_controller.get_registers()

						print("+", end="")

						# при удачном чтении - запись регистров исполнителя
						time.sleep(0.1)
						for attempt_w in range(0, ATTEMPTS):
							if executors[executor_id].write_registers(regs_to_executor,conn):

								print("!")

								break
							else:
								del conn
								conn = Conn485()
								time.sleep(ATTEMPT_DELAY)
						else:
							print("ERROR writing {} addr {:d}".format(executors[executor_id].get_name(), executors[executor_id].get_address()))

						break
					
					else:
						del conn
						conn = Conn485()
						time.sleep(ATTEMPT_DELAY)
				else:
					print("ERROR reading {} addr {:d}".format(curr_controller.get_name(), curr_controller.get_address()))


			time.sleep(1)
			del conn


	# while True:
		
		# for executors in 




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

		



	# 	if timers[0].check():
			
	# 		curr_regs = timers[0].get_regs_on()

	# 	else:

	# 		curr_regs = timers[0].get_regs_off()

	# 	curr_executor = executors[executors_id_by_name[timers[0].controls()]]

	# 	while not (curr_executor.read_registers(conn)):
	# 		del conn
	# 		time.sleep(0.1)
	# 		conn = Conn485()
	# 		time.sleep(0.1)
			
	# 	if curr_executor.get_registers() != curr_regs:
	# 		curr_executor.write_registers(curr_regs, conn)

	# 	time.sleep(1)
	# pass

finally:
	if "conn" in locals(): # проверка существования conn в локальной области видимости
		print("Closing COM port")
		del conn
	print("----Execution aborted----")

