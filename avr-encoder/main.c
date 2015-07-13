#define F_CPU 8000000UL // 8 ��� �� ����������� ����������
#include <avr/io.h> // ����-�����
#include <util/delay.h> // ��������
#include <avr/interrupt.h> // ����������

// ����� ������� ����
#define MASTER 1

// �������
#define READ_REG 10
#define WRITE_REG 20
#define CHANGE_ADDR 30

#define REGS_TO_MASTER 50 // ��� ������� ��� �������� ��������� �������

#define MIN_LEVEL 20 // ����������� ������� �������

// ���������� ���������� ������ ������
unsigned char packet[5];

// �������� ������
// ��� �������� � ������� ������ (�������) ���� ������ 0-255 ��������,
// ������ 0 ��� 255 �����. ����-���.
unsigned char data[2] = {0, 0};

// ����� ����� ����������
// ������: 255 �� ����������, �� ������� � ����� ��� ��������
unsigned char address = 50;

// ���� �������� ������
unsigned char timeout = 0;

// ���� ���������� �������� ��������
unsigned char encoder_enabled = 1;

// ������� ��������� �������� � ������
unsigned char encoder_state = 0;
unsigned char button_state = 0;


// �������������
void setup(void){
	// ����� ������
	DDRD = 0b00000100; // PD2 = 1 - ������ MAX485
	DDRC = 0b00000000; // PC0 ���� ������, PC1-2 - ��������
	PORTC = 0b11111111; // ����������� ������������� ����������

	// ��������� ����������������� ����������

	// ��������� ������������ ������ 8N1
	UCSR0C=(1<<USBS0)|(1<<UCSZ01)|(1<<UCSZ00);

	// ��������� ��������.
	// ��� ����� AVR Baudrate Calculator, ������
	// �� ��� �������� ��������� �������
	// UBRR0L=25; // 19200
	UBRR0L=12; // 38400
	UBRR0H=0;

	// ���������� ������ � �������� �� UART
	// RXENable, TXENable � �������� UCSRB
	//UCSR0B=(1<<RXEN0)|(1<<TXEN0);

	// ���������� ���������� �� ������������ timer0
	TIMSK0 = (1<<TOIE0);

	// ���������� ���������� �� ������������ timer2
	TIMSK2 = (1<<TOIE2);

	// ������ timer2 � ��������� 32, ���� �������� 1 ��� �������
	TCNT2 = 0;
	TCCR2B = (1<<CS21) | (1<<CS20);

	// ���������� ���������� ����������
	sei();
}

// ���������� ������ ��������
void encoder_enable(unsigned char val){

	if (val == 0) {
		encoder_enabled = 0;
	}
	else {
		encoder_enabled = 1;
	}
}

// ����� ��������
void encoder_scan(void){

	// ������� ��������� - ���� 1 � 2 ����� C
	// ��� ����� ���� 0 (00), 1 (01), 2(10), 3 (11)
	unsigned char new_encoder_state = (PINC & 0b00000110) >> 1;

	// ������������������ ����������: 00-10-11-01-...
	// ���������� 00-01-11-10-...

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

	// ����� ������, �������������� ������� (1-0)
	unsigned char new_button_state = PINC & 0b00000001;
	if ((button_state == 1) && (new_button_state == 0)) data[1] = !data[1];

	encoder_state = new_encoder_state; //�������� ��������� ��������
	button_state = new_button_state; // �������� ��������� ������
}

// ���������� �� �������0 - ��������� ���� �������� ������
ISR(TIMER0_OVF_vect){
	timeout = 1;
}

// ���������� �� �������1 - ����� ��������, ���� ���������
ISR(TIMER2_OVF_vect){
	if (encoder_enabled) encoder_scan();
}

// ���������� ����������� ����� ������
unsigned char checksum(){

	unsigned int sum = 0;
	for (unsigned char counter = 0; counter < 4; counter++){
		sum += packet[counter];
	}

	return sum % 256;
}

// ����� 5 ���� �� UART
// ���������� 0xFF ��� �������� ������
// 0x00 ��� �������� ������, ������������ ����������� �����
// ��� �������������� ������
unsigned char receive_packet(void){

	PORTD &= 0b11111011; // ��������� max485 �� �����
	_delay_us(1); // �������� �� ������������ ������
	UCSR0B=(1<<RXEN0); // ���������� ������ �� UART

	// ��������� ������� ����� ������
	while(!(UCSR0A & (1<<RXC0)));
	packet[0] = UDR0;

	// ��� ������ ������ ���� �������,
	// ��������� ����� �������� � ��������� ������

	encoder_enable(0);

	// ������ timer0
	timeout = 0; // ����� ����� ������������ �������
	TCNT0 = 0; // ��������� �������� �������
	TCCR0B = (1<<CS02) | (1<<CS00); // ������ � ��������� 1024

	// ��������� ��� ������� ���� ������
	for (unsigned char counter=1; counter<5; counter++)
	{
		// �������� ���������, ���� ������� -
		// ������ FF �� ��� ���� ������ � ������ ���������� 0x00
		while(!(UCSR0A & (1<<RXC0))) {

			if (timeout == 1){
				TCCR0B = 0; // ��������� �������
				encoder_enable(1); //���������� ������ ��������
				for (unsigned char counter1=0; counter1<5; counter1++){ packet[counter1] = 0xFF; };
				return 0x00;
			}
		}

		// ��������� �����
		packet[counter] = UDR0;
	}

	TCCR0B = 0; // ��������� �������
	encoder_enable(1); // ���������� ������ ��������
	UCSR0B=0; // ������ UART

	// �������� ����������� �����. �� ��������� - ������� 0x00
	unsigned char packet_checksum = checksum();
	if (packet[4] != packet_checksum) {return 0x00;};

	// �������� ������ ���������. �� ��������� - ������� 0x00
	if (packet[0] != address) {return 0x00;};

	return 0xFF; // ������� ����������
}

// �������� ������
void send_packet(void){

	unsigned char packet_checksum = checksum(); // ���������� ����������� ����� ������
	packet[4] = packet_checksum;

	PORTD |= 0b00000100; // ��������� max485 �� ��������
	_delay_ms(1); // �������� �� ������������ ������
	UCSR0B=(1<<TXEN0); // ���������� ��������

	// ������ ������ ��������
	encoder_enable(0);

	for (unsigned char counter=0; counter<5; counter++)
	{
		// �������� ������������ ������
		while(!(UCSR0A & (1<<UDRE0)));

		// �������� �����
  		UDR0 = packet[counter];
 	}

	encoder_enable(1); // ���������� ������ ��������
	UCSR0B = 0; // ������ UART
}

// �������� ��������� �������
// ������������ � ��� ������������� ������ �������
void send_registers(void){
	packet[0] = MASTER;
	packet[1] = REGS_TO_MASTER;
	packet[2] = data[0];
	packet[3] = data[1];

	send_packet();
}

// ��������� ������, ��������� �������� ������
void process_packet(void){

	switch (packet[1]){

		case READ_REG: {
			send_registers(); // �������� ���������
			break;
		}

		case WRITE_REG:{	// ������ ���������
			data[0] = packet[2];
			data[1] = packet[3];
			if (data[0] < MIN_LEVEL) data[0] = MIN_LEVEL; // �������� �� ����������� �������
			send_registers();
			break;
		}

		case CHANGE_ADDR:{ // ����� ������
			address = packet[2];
			send_registers();
			break;
		}
	}
}

// ����� ������, ���� ����� ���������� - ���������� ���
int main (void){

	setup(); // ������������� �����
	unsigned char rx_result; // ��������� ������ ������

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
