from device485 import Device
import configparser

# конфигурационный файл устройтв
CONFIG_FILE = "devices.cfg"

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
	print ('Created device %s type %s with address %i' % (name, dev_type, address))

if devices[0].read_registers():
	print ("Successfully read: %s" % devices[0].get_registers())

# for counter in range(0,3):
	
# 	if devices[0].read_registers():
# 		print ("Successfully read: %s" % devices[0].get_registers())
# 	if devices[0].write_registers([counter,counter+1]):
# 		print ("Successfully set: %s" % devices[0].get_registers())
# 	print("---")

# if test_device.set_address(51):
# 	print ("Successfully changed address")

# 	if test_device.read_registers():
# 		print ("Successfully read: %s" % test_device.get_registers())

