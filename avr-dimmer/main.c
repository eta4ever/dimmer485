#define F_CPU 8000000UL // 8 МГц от встроенного генератора
#include <avr/io.h> // ввод-вывод
#include <util/delay.h> // задержки
#include <avr/interrupt.h> // прерывания

// адрес мастера сети
#define MASTER 1

// команды
#define READ_REG 10
#define WRITE_REG 20
#define CHANGE_ADDR 30

#define REGS_TO_MASTER 50 // код команды при отправке регистров мастеру

// глобальная переменная пакета данных
unsigned char packet[5];

// регистры данных
// первый [0] хранит яркость, второй выкл (0)/ вкл (не 0)
unsigned char data[2] = {0, 0};

// адрес этого устройства
// алярма: 255 не используем, он пишется в пакет при таймауте
unsigned char address = 60;

// флаг таймаута приема
unsigned char timeout = 0;

// Инициализация
void setup(void){
	// режим портов
	DDRD = 0b00000100; // PD2 = 1 - запись MAX485

	// Порт B как выход, используется PB3 (OC2A) для ШИМ
	DDRB = 0b11111111;

	// настройка последовательного интерфейса

	// установка стандартного режима 8N1
	UCSR0C=(1<<USBS0)|(1<<UCSZ01)|(1<<UCSZ00);

	// установка скорости.
	// тут курим AVR Baudrate Calculator, почему
	// не все скорости одинаково полезны
	// UBRR0L=25; // 19200
	UBRR0L=12; // 38400
	UBRR0H=0;

	// разрешение приема и передачи по UART
	// RXENable, TXENable в регистре UCSRB
	//UCSR0B=(1<<RXEN0)|(1<<TXEN0);

	// разрешение прерывания по переполнению timer0
	TIMSK0 = (1<<TOIE0);

	// глобальное разрешение прерываний
	sei();

	// настройка ШИМ

	// биты 7-6 COM2A1 COM2A0 10 - Clear OC2A on Compare match (non-inverting mode)
	// биты 5-4 COM2B1 COM2B0 00 - не подключать OC2B
	// биты 3-2 не используются
	// биты 1-0 WGM21 WGM20 11 режим Fast PWM
	//	TCCR2A = 0b10000011;

	// биты 7-6 актуальны не при PWM, 5-4 не используются, 3 - WGM22,
	// биты 2-0 001 задают тактирование без делителя
	TCCR2B = 0b00000001;

	// на выходе 0
	OCR2A = 0;
}

// прерывание по таймеру0 - установка флаг таймаута приема
ISR(TIMER0_OVF_vect){
	timeout = 1;
}

// вычисление контрольной суммы пакета
unsigned char checksum(){

	unsigned int sum = 0;
	for (unsigned char counter = 0; counter < 4; counter++){
		sum += packet[counter];
	}

	return sum % 256;
}

// прием 5 байт по UART
// возвращает 0xFF при успешном приеме
// 0x00 при таймауте приема, несовпадении контрольной суммы
// или несоответствии адреса
unsigned char receive_packet(void){

	PORTD &= 0b11111011; // включение max485 на прием
	_delay_us(1); // задержка на установление режима
	UCSR0B=(1<<RXEN0); // разрешение приема по UART

	// получение первого байта пакета
	while(!(UCSR0A & (1<<RXC0)));
	packet[0] = UDR0;

	// как только первый байт получен,
	// запустить таймер

	// запуск timer0
	timeout = 0; // сброс флага переполнения таймера
	TCNT0 = 0; // обнуление счетчика таймера
	TCCR0B = (1<<CS02) | (1<<CS00); // запуск с делителем 1024

	// получение еще четырех байт пакета
	for (unsigned char counter=1; counter<5; counter++)
	{
		// ожидание приемника, если таймаут -
		// запись FF во все поля пакета и выдача результата 0x00
		while(!(UCSR0A & (1<<RXC0))) {

			if (timeout == 1){
				TCCR0B = 0; // остановка таймера
				for (unsigned char counter1=0; counter1<5; counter1++){ packet[counter1] = 0xFF; };
				return 0x00;
			}
		}

		// получение байта
		packet[counter] = UDR0;
	}

	TCCR0B = 0; // остановка таймера
	UCSR0B=0; // запрет UART

	// проверка контрольной суммы. Не совпадает - вернуть 0x00
	unsigned char packet_checksum = checksum();
	if (packet[4] != packet_checksum) {return 0x00;};

	// проверка адреса приемника. Не совпадает - вернуть 0x00
	if (packet[0] != address) {return 0x00;};

	return 0xFF; // удачное завершение
}

// отправка пакета
void send_packet(void){

	unsigned char packet_checksum = checksum(); // вычисление контрольной суммы пакета
	packet[4] = packet_checksum;

	PORTD |= 0b00000100; // включение max485 на передачу
	_delay_ms(1); // задержка на установление режима
	UCSR0B=(1<<TXEN0); // разрешение передачи

	for (unsigned char counter=0; counter<5; counter++)
	{
		// ожидание освобождения буфера
		while(!(UCSR0A & (1<<UDRE0)));

		// отправка байта
  		UDR0 = packet[counter];
 	}
	UCSR0B = 0; // запрет UART
}

// отправка регистров мастеру
// используется и как подтверждение приема команды
void send_registers(void){
	packet[0] = MASTER;
	packet[1] = REGS_TO_MASTER;
	packet[2] = data[0];
	packet[3] = data[1];

	send_packet();
}

// обработка пакета, отработка принятых команд
void process_packet(void){

	switch (packet[1]){

		case READ_REG: {
			send_registers(); // отправка регистров
			break;
		}

		case WRITE_REG:{	// запись регистров
			data[0] = packet[2];
			data[1] = packet[3];
			send_registers();
			break;
		}

		case CHANGE_ADDR:{ // смена адреса
			address = packet[2];
			send_registers();
			break;
		}
	}
}

// прием пакета, если пакет понравился - обработать его
int main (void){

	setup(); // инициализация всего
	unsigned char rx_result; // результат приема пакета

	while(1){

		rx_result = receive_packet();
		_delay_us(1);

		if (rx_result) {
			process_packet();

			if (data[1]){
				TCCR2A = 0b10000011; // шим активна
				OCR2A = data[0]; // установка яркости
			}
			else {
				TCCR2A = 0b00000011; // если в data2 0, шим отключается
			}
		}
		_delay_ms(1);
	}

	return 0;
}
