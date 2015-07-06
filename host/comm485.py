# реализация мини-протокола работы с устройствами по RS-485:
# пакет из 5 байт. Адрес, команда, данные, данные, контрольная сумма.
import serial, time, configparser

CONFIG_FILE = "cfg\\connection.cfg"

class Conn485:

	def __init__(self):
		""" конструктор """
		
		# чтение настроек из конфигурационного файла
		config = configparser.RawConfigParser()
		config.read(CONFIG_FILE)

		port = config.get("MAIN", "port")
		baudrate = config.getint("MAIN", "baudrate")
		rx_timeout = config.getfloat("MAIN", "timeout")

		# открытие соединения UART

		self.conn = serial.Serial(port, baudrate, timeout = rx_timeout)
		time.sleep(0.01)

	def __del__(self):
		""" деструктор """

		# закрытие соединения UART
		self.conn.close()

	def checksum(self, packet):
		""" подсчет контрольной суммы пакета """

		return sum(packet[0:4]) % 256

	def send(self, packet):
		""" отправка пакета, на входе 4 байта """

		# формирование пакета
		packet_to_send = list(packet)
		packet_checksum = self.checksum(packet)
		packet_to_send.append(packet_checksum)

		# режим передачи
		self.conn.setDTR(False)
		time.sleep(0.01)

		# передача
		self.conn.write(packet_to_send)

	def receive(self):
		""" прием и проверка пакета. Возвращает [0], при несовпадении
		контрольной суммы или недостаточной длине пакета """

		# режим приема
		self.conn.setDTR(True)
		time.sleep(0.01)
		
		# прием
		received_packet = list(self.conn.read(5))

		#DEBUG
		#print (received_packet)

		# проверка длины пакета
		if len(received_packet) != 5:
			return [0]

		# проверка контрольной суммы	
		if received_packet[4] != self.checksum(received_packet[0:4]):
			return [0]

		return received_packet




