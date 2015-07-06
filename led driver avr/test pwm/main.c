#define F_CPU 8000000UL // 8 МГц от встроенного генератора
#include <avr/io.h> // ввод-вывод
#include <util/delay.h> // задержки
#include <avr/interrupt.h> // прерывания

// Инициализация
void setup(void){

	// Порт B как выход, используется PB3 (OC2A) для ШИМ
	DDRB = 0b11111111;

	// биты 7-6 COM2A1 COM2A0 10 - Clear OC2A on Compare match (non-inverting mode)
	// биты 5-4 COM2B1 COM2B0 00 - не подключать OC2B
	// биты 3-2 не используются
	// биты 1-0 WGM21 WGM20 11 режим Fast PWM
	TCCR2A = 0b10000011;

	// биты 7-6 актуальны не при PWM, 5-4 не используются, 3 - WGM22, 
	// биты 2-0 001 задают тактирование без делителя
	TCCR2B = 0b00000001;

	// на выходе 0
	OCR2A = 0; 
}


int main(void){
	
	while(1){
		for (unsigned char counter = 0; counter<255; counter++){
			OCR2A = counter;
			_delay_ms(10);
		}
	}

	return 1;
}