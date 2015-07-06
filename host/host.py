from device485 import Device
import time, configparser

# конфигурационный файл устройтв
CONFIG_FILE = "cfg\\devices.cfg"

# список объектов устройств
devices = []

# загрузка конфигурации
config = configparser.RawConfigParser()
config.read(CONFIG_FILE)

# создание объектов устройств по конфигурационному файлу
for section in config.sections():
	
	address = config.getint(section, 'address')
	name = config.get(section, 'name')
	dev_type = config.get(section, 'type')
	init_regs = [config.getint(section, 'reg1'), config.getint(section, 'reg2')]
	devices.append(Device(address, name, dev_type, init_regs))
	print ('Created device "%s" type "%s" with address %i' % (name, dev_type, address))

if devices[2].read_registers():
	print ("Successfully read: %s" % devices[2].get_registers())


while True:
	brightness = 0
	while brightness < 256:

		if devices[2].write_registers([brightness,0]):
			print ("Successfully set", brightness)
		time.sleep(0.1)

		brightness += 10	