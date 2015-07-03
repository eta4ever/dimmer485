from device485 import Device

test_device = Device(51, "test encoder", "encoder")

for counter in range(0,10):
	
	if test_device.read_registers():
		print ("Successfully read: %s" % test_device.get_registers())
	if test_device.write_registers([counter,counter+1]):
		print ("Successfully set: %s" % test_device.get_registers())
	print("---")

if test_device.set_address(51):
	print ("Successfully changed address")

	if test_device.read_registers():
		print ("Successfully read: %s" % test_device.get_registers())

