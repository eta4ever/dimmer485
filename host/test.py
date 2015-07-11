from comm485 import Conn485
import time

conn = Conn485()

time.sleep(0.1)

conn.send([60,20,127,0])

time.sleep(0.01)

print (conn.receive())

try:
	while True:

		conn.send([60,20,127,0])
		# time.sleep(0.01)
		print (conn.receive())
		time.sleep(0.01)
		conn.send([60,20,127,1])
		time.sleep(0.01)

finally:
	del conn