from comm485 import Conn485
from device485 import Device
import time

conn = Conn485()
time.sleep(0.1)

# led1 = Device("led1","pwm")
# led1.init_as_hardware(60, [0,0], conn)

enc1 = Device("enc1", "encoder", 1)
enc1.init_as_hardware(50, [0,0], conn)

# dummy = input(">")

try:
	while True:

		# time.sleep(0.1)
		# print(led1.write_registers([100,1],conn))

		# time.sleep(0.1)
		# print(led1.write_registers([200,0],conn))

		time.sleep(0.1)
		enc1.read_registers(conn)
		print (enc1.get_registers())

finally:
	del conn