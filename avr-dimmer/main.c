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

// ���������� ���������� ������ ������
unsigned char packet[5];

// �������� ������
// ������ [0] ������ �������, ������ ���� (0)/ ��� (�� 0)
unsigned char data[2] = {0, 0};

// ����� ����� ����������
// ������: 255 �� ����������, �� ������� � ����� ��� ��������
unsigned char address = 60;

// ���� �������� ������
unsigned char timeout = 0;

// �������������
void setup(void){
	// ����� ������
	DDRD = 0b00000100; // PD2 = 1 - ������ MAX485

	// ���� B ��� �����, ������������ PB3 (OC2A) ��� ���
	DDRB = 0b11111111;

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

	// ���������� ���������� ����������
	sei();

	// ��������� ���

	// ���� 7-6 COM2A1 COM2A0 10 - Clear OC2A on Compare match (non-inverting mode)
	// ���� 5-4 COM2B1 COM2B0 00 - �� ���������� OC2B
	// ���� 3-2 �� ������������
	// ���� 1-0 WGM21 WGM20 11 ����� Fast PWM
	//	TCCR2A = 0b10000011;

	// ���� 7-6 ��������� �� ��� PWM, 5-4 �� ������������, 3 - WGM22,
	// ���� 2-0 001 ������ ������������ ��� ��������
	TCCR2B = 0b00000001;

	// �� ������ 0
	OCR2A = 0;
}

// ���������� �� �������0 - ��������� ���� �������� ������
ISR(TIMER0_OVF_vect){
	timeout = 1;
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
	// ��������� ������

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
				for (unsigned char counter1=0; counter1<5; counter1++){ packet[counter1] = 0xFF; };
				return 0x00;
			}
		}

		// ��������� �����
		packet[counter] = UDR0;
	}

	TCCR0B = 0; // ��������� �������
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

	for (unsigned char counter=0; counter<5; counter++)
	{
		// �������� ������������ ������
		while(!(UCSR0A & (1<<UDRE0)));

		// �������� �����
  		UDR0 = packet[counter];
 	}
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

			if (data[1]){
				TCCR2A = 0b10000011; // ��� �������
				OCR2A = data[0]; // ��������� �������
			}
			else {
				TCCR2A = 0b00000011; // ���� � data2 0, ��� �����������
			}
		}
		_delay_ms(1);
	}

	return 0;
}
