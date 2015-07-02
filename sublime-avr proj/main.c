#define F_CPU 8000000UL // 8 МГц от встроенного генератора
#include <avr/io.h> // ввод-вывод
#include <util/delay.h> // задержки
#include <avr/interrupt.h> // прерывания

// тип пакета данных
typedef struct {
	unsigned char bytes[5];
} data_packet;

// адрес мастера сети
#define MASTER 1

// команды
#define READ_REG 10
#define WRITE_REG 20
#define CHANGE_ADDR 30

#define REGS_TO_MASTER 50 // код команды при отправке регистров мастеру
#define ACK_TO_MASTER 60 // код команды при отправке подтвердения мастеру

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
	DDRC = 0b00000000; // PC0-2 - вход энкодера

	// настройка последовательного интерфейса

	// установка стандартного режима 8N1
	UCSR0C=(1<<USBS0)|(3<<UCSZ00);

	// установка скорости 19200.
	// тут курим AVR Baudrate Calculator, почему
	// не все скорости одинаково полезны
	UBRR0L=25;
	UBRR0H=0;

	// разрешение приема и передачи по UART
	// RXENable, TXENable в регистре UCSRB
	UCSR0B=(1<<RXEN0)|(1<<TXEN0);

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

	// текущее состояние - биты 0 и 1 порта C
	// оно может быть 0 (00), 1 (01), 2(10), 3 (11)
	unsigned char new_encoder_state = PINC & 0b00000011; 

	// последовательность увеличения: 00-10-11-01-...
	// уменьшения 00-01-11-10-...

	switch (encoder_state){

		case 3:
		{
			// 11 -> 01 +
			if ((new_encoder_state == 1) && (data[0] != 255)) data[0]++;
			// 11 -> 10 -
			if ((new_encoder_state == 2) && (data[0] != 0)) data[0]--;
			break;
		}

		case 2:
		{
			// 10 -> 11 +
			if ((new_encoder_state == 3) && (data[0] != 255)) data[0]++;
			// 10 -> 00 -
			if ((new_encoder_state == 0) & (data[0] != 0)) data[0]--;
			break;
		}

		case 1:
		{
			// 01 -> 00 +
			if ((new_encoder_state == 0) && (data[0] != 255)) data[0]++;
			// 01 -> 11 -
			if ((new_encoder_state == 3) && (data[0] != 0)) data[0]--;
			break;
		}

		case 0:
		{
			// 00 -> 10 +
			if ((new_encoder_state == 2) && (data[0] != 255)) data[0]++;
			// 00 -> 01 -
			if ((new_encoder_state == 1) && (data[0] != 0)) data[0]--;
			break;
		}

	}
	
	// опрос кнопки, отрабатывается отпускание (1-0)
	unsigned char new_button_state = PINC & 0b00000100;
	if ((button_state == 1) && (new_button_state == 0)) data[1] = !data[1];

	encoder_state = new_encoder_state; //фиксация состояния энкодера
	button_state = new_button_state; // фиксация состояния кнопки
}

// вычисление контрольной суммы пакета
unsigned char checksum(data_packet packet){

	unsigned int sum = 0;
	for (unsigned char counter = 0; counter < 4; counter++){
		sum += packet.bytes[counter];
	}

	return sum % 256;
}

// прерывание по таймеру0 - установка флаг таймаута приема
ISR(TIMER0_OVF_vect){
	timeout = 1;
}

// прерывание по таймеру1 - опрос энкодера, если разрешено
ISR(TIMER2_OVF_vect){
	if (encoder_enabled) encoder_scan();
}

// прием 5 байт по UART
data_packet receive_packet(void)
{
	// включение max485 на прием
	PORTD &= 0b11111011;

	data_packet packet;

	// получение первого байта пакета
	while(!(UCSR0A & (1<<RXC0)));
	packet.bytes[0] = UDR0;

	// как только первый байт получен, 
	// запретить опрос энкодера и запустить таймер

	encoder_enable(0);

	// запуск timer0
	timeout = 0; // сброс флага переполнения таймера
	TCNT0 = 0; // обнуление счетчика таймера
	TCCR0B = (1<<CS02) | (1<<CS00); // запуск с делителем 1024

	// получение еще четырех байт пакета
	for (unsigned char bytesReceived=1; bytesReceived<5; bytesReceived++)
	{
		// ожидание приемника, если таймаут - 
		// запись FF во все поля пакета и выдача его
		while(!(UCSR0A & (1<<RXC0))) {

			if (timeout == 1){
				for (unsigned char counter = 0; counter<5; counter++){
					packet.bytes[counter] = 255;
				}
			return packet;
			}
		}

		// получение байта
		packet.bytes[bytesReceived] = UDR0;
	}

	TCCR0B = 0; // остановка таймера
	encoder_enable(1); // разрешение опроса энкодера
	return packet;
}

// отправка данных
void send_data(data_packet packet){

	// включение max485 на передачу
	PORTD |= 0b00000100;

	// запрет опроса энкодера
	encoder_enable(0);

	for (unsigned char counter=0; counter<5; counter++)
	{
		// ожидание освобождения буфера
		while(!(UCSR0A & (1<<UDRE0)));

		// отправка байта
  		UDR0 = packet.bytes[counter];
	}

	// разрешение опроса энкодера
	encoder_enable(1);
}

// отправка регистров данных мастеру сети
void data_for_master(void){

	data_packet packet;
	packet.bytes[0] = MASTER;
	packet.bytes[1] = REGS_TO_MASTER;
	packet.bytes[2] = data[0];
	packet.bytes[3] = data[1];
	packet.bytes[4] = checksum(packet);

	send_data(packet);
}

// отправка подтверждения мастеру
// data[0] - адрес устройства
void ack_for_master(void){

	data_packet packet;
	packet.bytes[0] = MASTER;
	packet.bytes[1] = ACK_TO_MASTER;
	packet.bytes[2] = address;
	packet.bytes[3] = 0;
	packet.bytes[4] = checksum(packet);

	send_data(packet);
}


// прием и обработка пакета
void process_packet(void)
{
	// получение пакета
	data_packet packet = receive_packet();

	// вычисление контрольной суммы пакета
	unsigned char current_checksum = checksum(packet);

	// если совпадают контрольная сумма и адрес устройства, 
	// обработка данных пакета
	if ((current_checksum == packet.bytes[4]) && (packet.bytes[0] == address)){

		// проверка команды
		switch (packet.bytes[1]){

			case READ_REG: { // отправка мастеру регистров
				_delay_ms(1); // задержка, чтобы мастер точно был на приеме
				data_for_master(); // отправка
			}
			case WRITE_REG: { // запись в регистры устройства
				data[0] = packet.bytes[2];
				data[1] = packet.bytes[3];

				// отправка подтверждения
				_delay_ms(1);
				ack_for_master();
			}

			case CHANGE_ADDR: {
				address = packet.bytes[2]; // смена адреса

				// отправка подтверждения
				_delay_ms(1);
				ack_for_master();
			}
		}
	}
}

int main (void){

	setup(); // инициализация всего
	
	while(1){

		process_packet(); // ожидание и обработка пакета
	}

	return 0;
}