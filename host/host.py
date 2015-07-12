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
        enabled = config.getint(section, 'enabled')

        # создание устройства
        device = Device(name, dev_type, enabled)

        # определение устройства в управляющие или исполнительные
        if dev_type in CONTROL_TYPES:
            controls = config.get(section, 'controls')
            priority = config.getint(section, 'priority')
            init_regs = [
                config.getint(section, 'reg1'), config.getint(section, 'reg2')]
            device.init_as_controller(controls, priority, init_regs)
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

create_devices()

# формирование словаря вида "имя исполнителя : код в списке executors"
executors_id_by_name = {
    executor.get_name(): executors.index(executor) for executor in executors}

# инициализация словаря "код исполнителя: []" для дальнейшего заполнения
# управляющими
executors_controlled_by = {
    executors.index(executor): [] for executor in executors}

# заполнение словаря "код исполнителя: [список кодов управляющих]"
for controller in controllers:
    executor_id = executors_id_by_name[controller.controls()]
    executors_controlled_by[executor_id].append(controllers.index(controller))

# DEBUG
# if controllers[0].write_registers([100, 1], conn):
#     print("set")

try:

    while True:

        for executor_id in range(0, len(executors)):

            # если исполнитель не задействован, пропустить его
            if not(executors[executor_id].enabled()):
                continue

            # обработка устройств, управляющих этим исполнителем
            # с учетом статуса задействованности и приоритета

            # список пар (приоритет, id управляющего)
            controllers_by_priority = []

            # наполнение этого списка
            for controller_id in executors_controlled_by[executor_id]:

                # если управляющий задействован, добавить его
                # приоритет и индекс в список
                if controllers[controller_id].enabled():
                    controllers_by_priority.append(
                        (controllers[controller_id].get_priority(),
                         controller_id))

            # сортировка по приоритету
            controllers_by_priority.sort()

            # если список не пустой
            if len(controllers_by_priority) > 0:

                # выбор id приоритетного контроллера
                top_controller_id = controllers_by_priority[0][1]

                # и удаление его пары из списка
                del controllers_by_priority[0]

                # получение регистров приоритетного контроллера
                actual_registers = [0, 0]
                if controllers[top_controller_id].read_registers(conn):
                    actual_registers = controllers[
                        top_controller_id].get_registers()
                else:
                    print("ERROR reading {} addr {:d}".format(
                        controllers[top_controller_id].get_name(), controllers[top_controller_id].get_address()))

                # если в списке есть другие управляющие,
                # синхронизировать их регистры с приоритетным
                for priority_controller_pair in controllers_by_priority:
                    controller_id = priority_controller_pair[1]
                    if controllers[controller_id].write_registers(actual_registers, conn):
                        print(
                            "Sync to {}".format(controllers[controller_id].get_name()))
                    else:
                        print("ERROR writing {} addr {:d}".format(
                            controllers[controller_id].get_name(), controllers[controller_id].get_address()))

                # передача регистров исполнителю
                if executors[executor_id].write_registers(actual_registers, conn):
                    print("Exec {}".format(executors[executor_id].get_name()))
                else:
                    print("ERROR writing {} addr {:d}".format(
                        executors[executor_id].get_name(), executors[executor_id].get_address()))

        time.sleep(1)

finally:
    # проверка существования conn в локальной области видимости
    if "conn" in locals():
        print("Closing COM port")
        del conn
    print("----Execution aborted----")
