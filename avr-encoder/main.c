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

#define MIN_LEVEL 20 // минимальный уровень яркости

// глобальная переменная пакета данных
unsigned char packet[5];

// регистры данных
// для энкодера с кнопкой первый (старший) байт хранит 0-255 значение,
// второй 0 или 255 соотв. выкл-вкл.
unsigned char data[2] = {0, 0};

// адрес этого устройства
// алярма: 255 не используем, он пишется в пакет при таймауте
unsigned char address = 50;

// флаг таймаута приема
unsigned char timeout = 0;

// флаг разрешения проверки энкодера
unsigned char encoder_enabled = 1;

// текущее состояние энкодера и кнопки
unsigned char encoder_state = 0;
unsigned char button_state = 0;


// Инициализация
void setup(void){
	// режим портов
	DDRD = 0b00000100; // PD2 = 1 - запись MAX485
	DDRC = 0b00000000; // PC0 вход кнопки, PC1-2 - энкодера
	PORTC = 0b11111111; // подключение подтягивающих резисторов

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

	// разрешение прерывания по переполнению timer2
	TIMSK2 = (1<<TOIE2);

	// запуск timer2 с делителем 32, дает примерно 1 кГц частоту
	TCNT2 = 0;
	TCCR2B = (1<<CS21) | (1<<CS20);

	// глобальное разрешение прерываний
	sei();
}

// Разрешение опроса энкодера
void encoder_enable(unsigned char val){

	if (val == 0) {
		encoder_enabled = 0;
	}
	else {
		encoder_enabled = 1;
	}
}

// опрос энкодера
void encoder_scan(void){

	// текущее состояние - биты 1 и 2 порта C
	// оно может быть 0 (00), 1 (01), 2(10), 3 (11)
	unsigned char new_encoder_state = (PINC & 0b00000110) >> 1;

	// последовательность увеличения: 00-10-11-01-...
	// уменьшения 00-01-11-10-...

	switch (encoder_state){

		case 3:
		{
			// 11 -> 01 +
			if ((new_encoder_state == 1) && (data[0] != 255)) data[0]++;
			// 11 -> 10 -
			if ((new_encoder_state == 2) && (data[0] != MIN_LEVEL)) data[0]--;
			break;
		}

		case 2:
		{
			// 10 -> 11 +
			if ((new_encoder_state == 3) && (data[0] != 255)) data[0]++;
			// 10 -> 00 -
			if ((new_encoder_state == 0) & (data[0] != MIN_LEVEL)) data[0]--;
			break;
		}

		case 1:
		{
			// 01 -> 00 +
			if ((new_encoder_state == 0) && (data[0] != 255)) data[0]++;
			// 01 -> 11 -
			if ((new_encoder_state == 3) && (data[0] != MIN_LEVEL)) data[0]--;
			break;
		}

		case 0:
		{
			// 00 -> 10 +
			if ((new_encoder_state == 2) && (data[0] != 255)) data[0]++;
			// 00 -> 01 -
			if ((new_encoder_state == 1) && (data[0] != MIN_LEVEL)) data[0]--;
			break;
		}

	}

	// опрос кнопки, отрабатывается нажатие (1-0)
	unsigned char new_button_state = PINC & 0b00000001;
	if ((button_state == 1) && (new_button_state == 0)) data[1] = !data[1];

	encoder_state = new_encoder_state; //фиксация состояния энкодера
	button_state = new_button_state; // фиксация состояния кнопки
}

// прерывание по таймеру0 - установка флаг таймаута приема
ISR(TIMER0_OVF_vect){
	timeout = 1;
}

// прерывание по таймеру1 - опрос энкодера, если разрешено
ISR(TIMER2_OVF_vect){
	if (encoder_enabled) encoder_scan();
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
	// запретить опрос энкодера и запустить таймер

	encoder_enable(0);

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
				encoder_enable(1); //разрешение опроса энкодера
				for (unsigned char counter1=0; counter1<5; counter1++){ packet[counter1] = 0xFF; };
				return 0x00;
			}
		}

		// получение байта
		packet[counter] = UDR0;
	}

	TCCR0B = 0; // остановка таймера
	encoder_enable(1); // разрешение опроса энкодера
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

	// запрет опроса энкодера
	encoder_enable(0);

	for (unsigned char counter=0; counter<5; counter++)
	{
		// ожидание освобождения буфера
		while(!(UCSR0A & (1<<UDRE0)));

		// отправка байта
  		UDR0 = packet[counter];
 	}

	encoder_enable(1); // разрешение опроса энкодера
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
			if (data[0] < MIN_LEVEL) data[0] = MIN_LEVEL; // проверка на минимальный уровень
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
		}
		_delay_ms(1);
	}

	return 0;
}
