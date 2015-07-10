from comm485 import Conn485
import time

conn = Conn485()

time.sleep(0.1)

conn.send([50,10,0,0])

time.sleep(0.02)

print (conn.receive())