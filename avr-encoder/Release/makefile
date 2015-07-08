################################################################################
# Automatically-generated file. Do not edit!
################################################################################

-include ../makefile.init

RM := rm -rf

# All of the sources participating in the build are defined here
-include sources.mk
-include subdir.mk
-include objects.mk

ifneq ($(MAKECMDGOALS),clean)
ifneq ($(strip $(ASM_DEPS)),)
-include $(ASM_DEPS)
endif
ifneq ($(strip $(S_DEPS)),)
-include $(S_DEPS)
endif
ifneq ($(strip $(S_UPPER_DEPS)),)
-include $(S_UPPER_DEPS)
endif
ifneq ($(strip $(C_DEPS)),)
-include $(C_DEPS)
endif
endif

-include ../makefile.defs

# Add inputs and outputs from these tool invocations to the build variables 
LSS += \
avr-encoder.lss \

FLASH_IMAGE += \
avr-encoder.hex \

EEPROM_IMAGE += \
avr-encoder.eep \

SIZEDUMMY += \
sizedummy \


# All Target
all: avr-encoder.elf secondary-outputs

# Tool invocations
avr-encoder.elf: $(OBJS) $(USER_OBJS)
	@echo 'Building target: $@'
	@echo 'Invoking: AVR C Linker'
	avr-gcc -Wl,-Map,avr-encoder.map -mmcu=atmega328p -o "avr-encoder.elf" $(OBJS) $(USER_OBJS) $(LIBS)
	@echo 'Finished building target: $@'
	@echo ' '

avr-encoder.lss: avr-encoder.elf
	@echo 'Invoking: AVR Create Extended Listing'
	-avr-objdump -h -S avr-encoder.elf  >"avr-encoder.lss"
	@echo 'Finished building: $@'
	@echo ' '

avr-encoder.hex: avr-encoder.elf
	@echo 'Create Flash image (ihex format)'
	-avr-objcopy -R .eeprom -R .fuse -R .lock -R .signature -O ihex avr-encoder.elf  "avr-encoder.hex"
	@echo 'Finished building: $@'
	@echo ' '

avr-encoder.eep: avr-encoder.elf
	@echo 'Create eeprom image (ihex format)'
	-avr-objcopy -j .eeprom --no-change-warnings --change-section-lma .eeprom=0 -O ihex avr-encoder.elf  "avr-encoder.eep"
	@echo 'Finished building: $@'
	@echo ' '

sizedummy: avr-encoder.elf
	@echo 'Invoking: Print Size'
	-avr-size --format=avr --mcu=atmega328p avr-encoder.elf
	@echo 'Finished building: $@'
	@echo ' '

# Other Targets
clean:
	-$(RM) $(FLASH_IMAGE)$(ELFS)$(OBJS)$(ASM_DEPS)$(EEPROM_IMAGE)$(S_DEPS)$(SIZEDUMMY)$(S_UPPER_DEPS)$(LSS)$(C_DEPS) avr-encoder.elf
	-@echo ' '

secondary-outputs: $(LSS) $(FLASH_IMAGE) $(EEPROM_IMAGE) $(SIZEDUMMY)

.PHONY: all clean dependents
.SECONDARY:

-include ../makefile.targets
