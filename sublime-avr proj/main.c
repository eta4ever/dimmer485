#define F_CPU 8000000UL // 8 МГц от встроенного генератора
#include <avr/io.h> // ввод-вывод
#include <util/delay.h> // задержки
#include <avr/interrupt.h> // прерывания

// тип пакета данных
typedef struct {
	unsigned char addr,
	unsigned char comm,
	unsigned char data1,
	unsigned char data2
	unsigned char checksum
} data_packet;

// Инициализация
void setup(void)
{
	// режим портов
	// DDRB = 0b11111111;
	// DDRC = 0b00111111;

	
	// настройка последовательного интерфейса

	// устанавливаем стандартный режим 8N1
	UCSRC=(1<<URSEL)|(3<<UCSZ0);

	// устанавливаем скорость 19200.
	// тут курим AVR Baudrate Calculator, почему
	// не все скорости одинаково полезны
	UBRRL=25;
	UBRRH=0;

	// разрешить прием и передачу по USART
	// RXENable, TXENable в регистре UCSRB
	UCSRB=(1<<RXEN)|(1<<TXEN);

}

// вычислить контрольную сумму пакета
unsigned char checksum(data_packet packet){

	return (packet.addr + packet.comm + packet.data1 + packet.data2) % 256;
}

// принять 5 байт по UART
data_packet receive_packet(void)
{
	// включить max485 на прием
	// предусмотреть прекращение приема по таймауту

	unsigned char buffer[5]; // буфер принятых данных

	for (bytesReceived=0; bytesReceived<5; bytesReceived++)
	{
		// ждем приемник
		while(!(UCSRA & (1<<RXC))) {}

		// забираем байт
		buffer[bytesReceived] = UDR;
	}

	data_packet result;
	result.addr = buffer[0];
	result.comm = buffer[1];
	result.data1 = buffer[2];
	result.data2 = buffer[3];
	result.checksum = buffer[4];

	return result;
}
