#define F_CPU 8000000UL // 8 МГц от встроенного генератора
#include <avr/io.h> // ввод-вывод
#include <util/delay.h> // задержки
#include <avr/interrupt.h> // прерывания

// тип пакета данных
typedef struct {
	unsigned char bytes[5];
} data_packet;

// адрес мастера сети
#define MASTER 1;

// регистры данных
unsigned char data[2] = {52, 50};


// Инициализация
void setup(void)
{
	// режим портов
	DDRD = 0b00000100; // PD2 = 1 - запись MAX485
	//DDRC = 0b00000000; // PC0-2 - вход энкодера

	
	// настройка последовательного интерфейса

	// устанавливаем стандартный режим 8N1
	UCSR0C=(1<<USBS0)|(3<<UCSZ00);

	// устанавливаем скорость 19200.
	// тут курим AVR Baudrate Calculator, почему
	// не все скорости одинаково полезны
	UBRR0L=25;
	UBRR0H=0;

	// разрешить прием и передачу по USART
	// RXENable, TXENable в регистре UCSRB
	UCSR0B=(1<<RXEN0)|(1<<TXEN0);

}

// вычислить контрольную сумму пакета
unsigned char checksum(data_packet packet){

	unsigned int sum = 0;
	for (unsigned char counter = 0; counter < 4; counter++){
		sum += packet.bytes[counter];
	}

	return sum % 256;
}

// принять 5 байт по UART
data_packet receive_packet(void)
{
	// включить max485 на прием
	PORTD &= 0b11111011;

	// предусмотреть прекращение приема по таймауту
	// TODO

	data_packet packet;

	for (unsigned char bytesReceived=0; bytesReceived<5; bytesReceived++)
	{
		// ждем приемник
		while(!(UCSR0A & (1<<RXC0))) {}

		// забираем байт
		packet.bytes[bytesReceived] = UDR0;
	}

	return packet;
}

// отправка данных
void send_data(data_packet packet){

	// включить max485 на передачу
	PORTD |= 0b00000100;

	for (unsigned char counter=0; counter<5; counter++)
	{
		// ждать освобождения буфера
		while(!(UCSR0A & (1<<UDRE0)));

		// отправить байт
  		UDR0 = packet.bytes[counter];
	}
}

// отправка регистров данных мастеру сети
void data_for_master(void){

	data_packet packet;
	packet.bytes[0] = MASTER;
	packet.bytes[1] = 0;
	packet.bytes[2] = data[0];
	packet.bytes[3] = data[1];
	packet.bytes[4] = checksum(packet);

	send_data(packet);
}



int main (void){

	setup();
	
	while(1){

		// data_packet packet = receive_packet();

		// data[0] = packet.bytes[2];
		// data[1] = packet.bytes[3];

		// _delay_ms(500);

		// data_packet test_packet;
		// test_packet.bytes[0] = 49;
		// test_packet.bytes[1] = 50;
		// test_packet.bytes[2] = 51;
		// test_packet.bytes[3] = 52;
		// test_packet.bytes[4] = 53;

		// send_data(test_packet);

		// PORTD |= 0b00000100;
		// PORTD &= 0b11111011;
		// while(!(UCSR0A & (1<<UDRE0)));
  		// UDR0 = 49;

  		data_for_master();

		_delay_ms(500);
	}




	return 0;
}