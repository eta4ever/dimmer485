from device485 import Device
from comm485 import Conn485
import time
import configparser

CONFIG_FILE = "cfg\\devices.cfg"  # конфигурационный файл устройств
CONTROL_TYPES = ["encoder", "switch", "virtual", "timer"]  # управляющие
EXEC_TYPES = ["pwm", "relay"]  # исполнительные устройства
HARDWARE_TYPES = ["encoder", "switch", "pwm", "relay"]  # "железные" устройства

controllers = []  # список управляющих устройств
executors = []  # список исполнительных устройств

conn = Conn485()  # создание подключения


def create_devices():
    """ создание объектов устройств"""

    # создание объектов устройств по конфигурационному файлу
    config = configparser.RawConfigParser()
    config.read(CONFIG_FILE)
    for section in config.sections():

        # выбор общих параметров
        name = config.get(section, 'name')
        dev_type = config.get(section, 'type')

        # создание устройства
        device = Device(name, dev_type)

        # определение устройства в управляющие или исполнительные
        if dev_type in CONTROL_TYPES:
            controls = config.get(section, 'controls')
            priority = config.getint(section, 'priority')
            device.init_as_controller(controls, priority)
            controllers.append(device)

        elif dev_type in EXEC_TYPES:
            executors.append(device)

        else:
            print('Error creating "%s": incorrect device type "%s"' %
                  (name, dev_type))

        # инициализация железного устройства
        if dev_type in HARDWARE_TYPES:

            address = config.getint(section, 'address')
            init_regs = [
                config.getint(section, 'reg1'), config.getint(section, 'reg2')]

            if device.init_as_hardware(address, init_regs, conn):
                print("{} addr {:d} ok".format(name, address))
            else:
                print(
                    "ERROR writing initial regs to {} with addr {:d}".format(name, address))

        # инициализация таймера
        if dev_type == "timer":
            regs_on = [
                config.getint(section, 'reg1on'), config.getint(section, 'reg2on')]
            regs_off = [
                config.getint(section, 'reg1off'), config.getint(section, 'reg2off')]
            time_on = config.get(section, 'time_on')
            time_off = config.get(section, 'time_off')
            device.init_as_timer(regs_on, regs_off, time_on, time_off)


def controller_to_executor(controller, connection):
    """ чтение регистров управляющего, запись регистров
    соответствующего исполнителя"""

    # определение управляющего
    curr_executor_id = executors[executors_id_by_name[controller.controls()]]

    # чтение регистров управляющего
    if controller.read_registers(connection):
        regs_to_executor = curr_controller.get_registers()
        print("o")

        # запись регистров исполнителя
        if executors[executor_id].write_registers(regs_to_executor, connection):
            print("x")
            pass
        else:
            print("ERROR writing {} addr {:d}".format(executors[
                  curr_executor_id].get_name(), executors[curr_executor_id].get_address()))

    else:
        print("ERROR reading {} addr {:d}".format(
            controller.get_name(), controller.get_address()))

create_devices()

# формирование словаря вида "имя исполнителя : код в списке executors"
executors_id_by_name = {
    executor.get_name(): executors.index(executor) for executor in executors}

# инициализация словаря "код исполнителя: []" для дальнейшего заполнения управляющими
executors_controlled_by = {
    executors.index(executor): [] for executor in executors}

# заполнение словаря "код исполнителя: [список кодов управляющих]"
for controller in controllers:
    executor_id = executors_id_by_name[controller.controls()]
    executors_controlled_by[executor_id].append(controllers.index(controller))

# DEBUG
if controllers[0].write_registers([100, 1], conn):
    print("set")

try:

    while True:

        for executor_id in range(0, len(executors)):

            if len(executors_controlled_by[executor_id]) == 1:
                # простой случай, один управляющий

                # выбор первого (и единственного) управляющего для данного
                # исполнителя
                curr_controller = controllers[
                    executors_controlled_by[executor_id][0]]

                # чтение из управляющего, запись регистров исполнителя
                controller_to_executor(curr_controller, conn)

            else:
                # несколько управляющих на одного исполнителя, обработка
                # приоритетов
                pass

        time.sleep(1)

finally:
    # проверка существования conn в локальной области видимости
    if "conn" in locals():
        print("Closing COM port")
        del conn
    print("----Execution aborted----")
