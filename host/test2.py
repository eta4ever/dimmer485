from comm485 import Conn485
from device485 import Device
import time

conn = Conn485()
time.sleep(0.1)

led1 = Device("led1","pwm")

led1.address = 60
led1.registers = [0,0]

led1.read_registers(conn)

led1.write_registers([1,1],conn)

led1.write_registers([255,1],conn)

del conn


# dummy = input(">")

# try:
# 	while True:

# 		# dummy = input(">")
# 		# conn = Conn485()
# 		time.sleep(0.1)
# 		print(led1.write_registers([100,1],conn))
# 		# del conn
# 			# print("o")
# 		# print (conn.receive())
# 		# time.sleep(0.01)
# 		# dummy = input(">")
# 		# conn = Conn485()
# 		time.sleep(0.1)
# 		print(led1.write_registers([200,0],conn))
# 		# del conn
# 			# print ("x")
# 		# time.sleep(0.01)

# finally:
# 	del conn