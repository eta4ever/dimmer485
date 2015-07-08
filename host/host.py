from device485 import Device
from comm485 import Conn485
import time, configparser

# конфигурационный файл устройтв
CONFIG_FILE = "cfg\\devices.cfg"

# список объектов устройств
devices = []

# загрузка конфигурации
config = configparser.RawConfigParser()
config.read(CONFIG_FILE)

# создание подключения
conn = Conn485()

# создание объектов устройств по конфигурационному файлу
for section in config.sections():
	
	time.sleep(0.1)

	# conn = Conn485()

	address = config.getint(section, 'address')
	name = config.get(section, 'name')
	dev_type = config.get(section, 'type')
	init_regs = [config.getint(section, 'reg1'), config.getint(section, 'reg2')]
	devices.append(Device(address, name, dev_type, init_regs, conn))
	print ('Created device "%s" type "%s" with address %i' % (name, dev_type, address))

	# del conn

dummy = input(">>>")

# тестирование устройств - считывание регистров
# for device in devices:
# 	if device.read_registers(conn):
# 		print ("'%s' device type '%s' read: %s" % (device.get_name(), device.get_type(), device.get_registers()))
# 	#time.sleep(0.01)

# dummy = input(">>>")

del conn
time.sleep(0.1)

while True:
	
	conn = Conn485()

	brightness = 0
	new_brightness = brightness

	while brightness < 256:

		if devices[0].write_registers([brightness,0], conn):
			print ("Set to encoder", brightness)

		if devices[0].read_registers(conn):
			new_brightness = devices[0].get_registers()[0]
			print ("Read from encoder", new_brightness)

		if devices[1].write_registers([new_brightness,0], conn):
			print ("Set to driver", new_brightness)

		print ("---")

		time.sleep(0.05)
		#dummy = input(">>>")

		brightness += 10

	del conn
	time.sleep(1)

del conn