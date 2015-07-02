#define F_CPU 8000000UL // 8 МГц от встроенного генератора
#include <avr/io.h> // ввод-вывод
#include <util/delay.h> // задержки
#include <avr/interrupt.h> // прерывания

// Инициализация
void setup(void){
	// режим портов
	DDRD = 0b00000100; // PD2 = 1 - запись MAX485

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
}

int main (void){

	setup(); // инициализация всего
	
	unsigned char packet[10];

	while(1){
		
		UCSR0B = 0;
		PORTD &= 0b11111011;
		_delay_ms(5);
		UCSR0B=(1<<RXEN0);
		for (unsigned char counter=0; counter<10; counter++){
			while(!(UCSR0A & (1<<RXC0)));
			packet[counter] = UDR0;
		}
		
		_delay_ms(5);
		UCSR0B = 0;
		PORTD |= 0b00000100;
		_delay_ms(5);
		UCSR0B=(1<<TXEN0);
		for (unsigned char counter=0; counter<10; counter++)
		{
			while(!(UCSR0A & (1<<UDRE0)));
  			UDR0 = packet[counter];
		}
		_delay_ms(5);
	}

	return 0;
}