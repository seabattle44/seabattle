import random
import os
from enum import Enum


class GameMode(Enum):
    # режим сложности
    EASY = 1  # видны все детали - где расположены корабли противника, куда стрелял, что подбил
    NORMAL = 2  # видны частичные детали - куда стрелял, что подбил


class ContentType(Enum):
    # содержимое ячеек карты
    BLANK = 1  # пустота, водная гладь
    CRATER = 2  # сюда был выстрел, появился кратер
    SHIP = 3  # корабль
    SKIP = 4  # сюда нет смысла стрелять, ячейка рядом с подбитым кораблём


class Cell:
    # ячейка карты
    def __init__(self, y: int, x: int, content: ContentType = ContentType.BLANK):
        # координаты на карте
        self.y = y
        self.x = x
        self.content = content

    def __repr__(self):
        return f'Cell(y={self.y} x={self.x} ={self.content})'


class UnitStatus(Enum):
    # статус юнита/палубы корабля
    SUCCESSFUL = 1
    BROKEN = 2  # подбит, но не уничтожен


class ShipUnit:
    def __init__(self, y: int, x: int):
        # координаты части корабля
        self.y = y
        self.x = x
        self.status = UnitStatus.SUCCESSFUL

    def is_broken(self):
        return self.status == UnitStatus.BROKEN

    def __repr__(self):
        return f'ShipUnit(y={self.y} x={self.x} ={self.status})'


class Orientation(Enum):
    # ориентация корабля на игровом поле
    HORIZONTAL = 1
    VERTICAL = 2


class Ship(Cell):
    def __init__(self, y: int, x: int, size: int, orientation: Orientation = Orientation.HORIZONTAL):
        Cell.__init__(self, y, x, ContentType.SHIP)
        self.size = size  # размер корабля
        self.orientation = orientation  # ориентация корабля на карте (горизонтальная, вертикальная)
        self.unit = []  # части корабля

    def width(self):
        # ширина корабля на игровом поле
        if self.orientation == Orientation.HORIZONTAL:
            width = self.size
        else:
            width = 1
        return width

    def height(self):
        # высота корабля на игровом поле
        if self.orientation == Orientation.HORIZONTAL:
            height = 1
        else:
            height = self.size
        return height

    def add_unit(self, y, x):
        # добавление палуб кораблю
        unit = ShipUnit(y, x)
        self.unit.append(unit)
        return unit

    def get_unit(self, y, x):
        # возвращает палубу корабля по координатам
        result = None
        for u in self.unit:
            if u.y == y and u.x == x:
                result = u
                break
        return result

    def break_unit(self, y, x):
        # уничтожаем палубу корабля по координатам
        u = self.get_unit(y, x)
        result = u.status == UnitStatus.SUCCESSFUL
        if result:
            u.status = UnitStatus.BROKEN
        return result

    def is_destroyed(self):
        # корабль уничтожен, если все палубы сломаны
        for u in self.unit:
            if u.status == UnitStatus.SUCCESSFUL:
                return False
        return True

    # для отладки
    def __repr__(self):
        return (f'Ship(y={self.y} x={self.x} ={self.content} size={self.size} ={self.orientation}'
                f' unit={self.unit})')


class Player:
    def __init__(self, name, bot):
        self.name = name
        self.bot = bot
        self.map = None
        self.ship = []
        self.score = 0

    def inc_score(self):
        self.score += 1

    def set_map(self, map):
        self.map = map

    def add_ship(self, ship):
        self.ship.append(ship)

    def remove_ship(self, ship):
        self.ship.remove(ship)

    def is_ship_empty(self):
        return len(self.ship) == 0


class Man(Player):
    # играет за людей
    def __init__(self, name):
        Player.__init__(self, name, False)
        self._reader = CellReader()

    def get_coordinate(self):
        return self._reader.input(self.name)


class Bot(Player):
    def __init__(self, name):
        Player.__init__(self, name, True)

    def get_coordinate(self):
        # бот
        col = list(CellReader.COL_NAMES.keys())[random.randrange(10)]
        row = random.randint(1, 10)
        return CellReader.convert(col + str(row))


class SeaRender:
    # отрисовывает в консоли игровую карту

    _map_name = (
        "     Карта: %s                         Счёт       Карта: %s\n"
        "                                         %s:%s")
    _map_header = ("\033[32m"
                   "     А  Б  В  Г  Д  Е  Ж  З  И  К                   А  Б  В  Г  Д  Е  Ж  З  И  К  "
                   "\033[0m")
    _map_delimiter = ("\033[32m"
                      "   +——-——-——-——-——-——-——-——-——-——-+               +——-——-——-——-——-——-——-——-——-——-+"
                      "\033[0m")

    def __init__(self, mode):
        self._mode = mode

    def clear_terminal(self):
        # очищает содержимое консоли
        if os.name in ('nt', 'dos'):
            os.system("cls")
        elif os.name in ('linux', 'osx', 'posix'):
            os.system("clear")
        else:
            print("\n" * 120)
        print()

    def print_map_row(self, row, i, ship_visible=True):
        not_last_row = i + 1 < len(row)
        # номер строки на поле
        if not_last_row:
            print('\033[32m', i + 1, end=' |\033[0m')
        else:
            print('\033[32m', i + 1, end='|\033[0m')
        for j, elem in enumerate(row):
            if elem.content == ContentType.SHIP:
                unit = elem.get_unit(i, j)
                if unit.status == UnitStatus.SUCCESSFUL and ship_visible:
                    # живой корабль: ███
                    print('\u2588' * 3, end='')
                elif unit.status == UnitStatus.BROKEN:
                    # подбитый корабль: ░░░
                    print('\u2591' * 3, end='')
                else:
                    print(' ' * 3, end='')
            elif elem.content == ContentType.CRATER:
                # промах, мимо: ¤
                print(' ¤ ', end='')
            elif elem.content == ContentType.SKIP:
                # нет смысла стрелять: ·
                print(' \u00B7 ', end='')
            elif elem.content == ContentType.BLANK:
                # пустое поле
                print(' ' * 3, end='')
            else:
                # не понятно как сюда попали :)
                print('?' * 3, end='')
        # номер строки на поле
        if not_last_row:
            print('\033[32m|', i + 1, end='\033[0m          ')
        else:
            print('\033[32m|', i + 1, end='\033[0m         ')

    def print_map(self, men, bot, map_size):
        # выводит в консоль игровую карту
        self.clear_terminal()
        print(SeaRender._map_name % (men.name, bot.name, men.score, bot.score))
        print(SeaRender._map_header)
        print(SeaRender._map_delimiter)
        for i in range(map_size):
            self.print_map_row(men.map[i], i)
            self.print_map_row(bot.map[i], i, self._mode == GameMode.EASY)
            print()
        print(SeaRender._map_delimiter)
        print(SeaRender._map_header)
        print()


class CellReader:
    # преобразует пользовательский ввод в координаты матрицы игрового поля
    COL_NAMES = {'А': 0, 'Б': 1, 'В': 2, 'Г': 3, 'Д': 4, 'Е': 5, 'Ж': 6, 'З': 7, 'И': 8, 'К': 9}
    ROW_NAMES = {'1': 0, '2': 1, '3': 2, '4': 3, '5': 4, '6': 5, '7': 6, '8': 7, '9': 8, '10': 9}

    @staticmethod
    def convert(cell_name):
        # преобразует имя ячейки в координаты матрицы игрового поля
        cell_name = cell_name.strip().upper()
        cell_name_len = len(cell_name)

        if cell_name_len != 2 and cell_name_len != 3:
            raise ValueError("Неверный формат данных, попробуйте ещё. Пример: А2")

        # получаем номер столбца поля
        col_str = cell_name[0]
        col = CellReader.COL_NAMES.get(col_str)
        if col is None:
            raise ValueError("Неверное имя столбца: %s, попробуйте ещё. Пример: е2" % col_str)

        # получаем номер строки поля
        row_str = cell_name[1:]
        row = CellReader.ROW_NAMES.get(row_str)
        if row is None:
            raise ValueError("Неверный номер строки: %s, попробуйте ещё. Пример: к10" % row_str)
        return [row, col, cell_name]

    def input(self, player_name):
        while True:
            try:
                cell_name = input("%s, введите координаты: " % player_name).strip().upper()
                cell_name_len = len(cell_name)
                # выход из игры
                if cell_name_len == 1 and (cell_name == 'Q' or cell_name == 'В'):
                    print("Game Over")
                    exit()
                return CellReader.convert(cell_name)
            except ValueError as e:
                print(e.args[0])


class GameStatus(Enum):
    # статусы игры
    NONE = 0
    INIT = 1
    IN_PROGRESS = 2
    GAME_OVER = 3


class ShotResult(Enum):
    # возможные результаты выстрела
    MISS = 1  # промахнулся
    RETRY = 2  # нужно повторить попытку
    BROKEN = 3  # корабль подбит, но не уничтожен
    DESTROYED = 4  # корабль уничтожен


class SeaBattle:
    # основной класс игры
    MAP_SIZE = 10  # размер игрового поля
    # возможные размеры и кол-во кораблей
    SHIP_CONFIG = (4, 3, 3, 2, 2, 2, 1, 1, 1, 1)

    def __init__(self, mode: GameMode = GameMode.NORMAL):
        self._mode = mode
        self.current_player = None
        self.next_player = None
        self.status = GameStatus.NONE
        self.message = []
        self._render = SeaRender(mode)

    def add_player(self, current_player, next_player):
        # добавление игроков
        self.current_player = current_player
        self.next_player = next_player

    def init(self):
        self.status = GameStatus.INIT
        self.generate_map(self.current_player, SeaBattle.MAP_SIZE)
        self.generate_map(self.next_player, SeaBattle.MAP_SIZE)

    def generate_available_cell(self, ship_size, orientation, map, map_size):
        # формирует список ячеек игрового поля, куда влезает корабль заданного размера
        result = []
        if orientation == Orientation.HORIZONTAL:
            for y in range(map_size):
                size = 0
                for x in range(map_size):
                    if map[y][x] == 0:
                        size += 1
                    else:
                        size = 0
                    if size == ship_size:
                        result.append((y, x - size + 1))
                        size -= 1
        elif orientation == Orientation.VERTICAL:
            for x in range(map_size):
                size = 0
                for y in range(map_size):
                    if map[y][x] == 0:
                        size += 1
                    else:
                        size = 0
                    if size == ship_size:
                        result.append((y - size + 1, x))
                        size -= 1
        else:
            raise ValueError("Неподдерживаемое значение enum %s" % orientation)
        if len(result) == 0:
            raise ValueError("Не найдены подходящие клетки для корабля, размер %s %s" % (ship_size, orientation))
        return result

    def generate_map(self, player, map_size):
        # формируем игровое поле, создаём и расставляем корабли каждого типа
        # шаблон карты
        map = [[0 for i in range(map_size)] for j in range(map_size)]
        # создаём и расставляем корабли каждого типа
        for ship_size in SeaBattle.SHIP_CONFIG:
            orientation = Orientation(random.randint(1, len(Orientation)))
            y, x = random.choice(self.generate_available_cell(ship_size, orientation, map, map_size))
            ship = Ship(y, x, ship_size, orientation)
            player.add_ship(ship)
            width = ship.width()
            height = ship.height()
            # размещаем корабль на игровом поле и заполняем ячейки вокруг корабля
            for i in range(y - 1, y + height + 1):
                for j in range(x - 1, x + width + 1):
                    # если координаты не выходят за рамки игрового поля
                    if i >= 0 and i < map_size and j >= 0 and j < map_size:
                        # если координаты не совпадают с координатами корабля
                        if i < y or i >= y + height or j < x or j >= x + width:
                            # формируем пустое поле
                            map[i][j] = Cell(i, j)
                        else:
                            # размещаем корабль
                            map[i][j] = ship
                            # добавляем палубу с соответствующими координатами
                            ship.add_unit(i, j)
        # заполняем не используемые ячейки
        for i in range(map_size):
            for j in range(map_size):
                if map[i][j] == 0:
                    map[i][j] = Cell(i, j)
        player.set_map(map)

    def update_skip_cell(self, y, x, map, map_size):
        # помечаем ячейки в которые нет смысла стрелять, расположены вокруг подбитого корабля
        ship = map[y][x]
        y = ship.y
        x = ship.x
        width = ship.width()
        height = ship.height()
        # помечаем ячейки вокруг корабля
        for i in range(y - 1, y + height + 1):
            for j in range(x - 1, x + width + 1):
                # если координаты не выходят за рамки игрового поля
                if i >= 0 and i < map_size and j >= 0 and j < map_size:
                    # если координаты не совпадают с координатами корабля
                    if i < y or i >= y + height or j < x or j >= x + width:
                        cell = map[i][j]
                        # помечаем, если в поле ничего нет
                        if cell.content == ContentType.BLANK:
                            cell.content = ContentType.SKIP

    def shoot(self, y, x, player):
        # выстрел по координатам
        result = ShotResult.RETRY
        cell = player.map[y][x]
        # обработка выстрела
        if cell.content == ContentType.SHIP:
            if cell.break_unit(y, x):
                # попал в живую палубу корабля
                if cell.is_destroyed():
                    player.remove_ship(cell)
                    result = ShotResult.DESTROYED
                else:
                    result = ShotResult.BROKEN
        elif cell.content == ContentType.BLANK:
            # промах, мимо
            cell.content = ContentType.CRATER
            result = ShotResult.MISS
        return result

    def print_map(self):
        # выводит карту в консоль, игрок - слева, бот - справа
        men = self.current_player
        bot = self.next_player
        if self.current_player.bot:
            men, bot = bot, men
        self._render.print_map(men, bot, SeaBattle.MAP_SIZE)

    def swap_players(self):
        # передаём ход другому игроку
        self.current_player, self.next_player = self.next_player, self.current_player

    def add_message(self, message):
        self.message.append(message)

    def clear_message(self):
        self.message.clear()

    def print_message(self):
        for line in self.message:
            print(line)

    def run(self):
        self.status = GameStatus.IN_PROGRESS

        while self.status == GameStatus.IN_PROGRESS:
            self.print_map()
            self.print_message()
            y, x, cell_name = self.current_player.get_coordinate()
            if not self.current_player.bot:
                # очищаем историю сообщений, если ходит человек
                self.clear_message()
            result = self.shoot(y, x, self.next_player)
            # обработка выстрела
            if result == ShotResult.BROKEN:
                self.add_message('%s - %s бьёт точно в цель, продолжайте!' % (cell_name, self.current_player.name))
                # увеличиваем счёт
                self.current_player.inc_score()
            elif result == ShotResult.DESTROYED:
                self.add_message('%s - %s уничтожил корабль!' % (cell_name, self.current_player.name))
                # увеличиваем счёт
                self.current_player.inc_score()
                # помечаем ячейки вокруг уничтоженного корабля
                self.update_skip_cell(y, x, self.next_player.map, SeaBattle.MAP_SIZE)
                # игра закончена, если кораблей не осталось
                if self.next_player.is_ship_empty():
                    self.status = GameStatus.GAME_OVER
            elif result == ShotResult.MISS:
                self.add_message('%s - %s промахнулся!' % (cell_name, self.current_player.name))
                # передаём ход другому игроку
                self.swap_players()
            elif result == ShotResult.RETRY:
                self.add_message('%s - %s, попробуйте еще раз!' % (cell_name, self.current_player.name))
        if self.status == GameStatus.GAME_OVER:
            self.add_message('%s, это был ваш последний корабль.' % self.next_player.name)
            self.add_message('%s выиграл матч со счётом %s:%s! Поздравляем!' % (self.current_player.name,
                                                                                self.current_player.score,
                                                                                self.next_player.score))
        self.print_map()
        self.print_message()


# запуск игры
if __name__ == '__main__':
    game = SeaBattle(GameMode.NORMAL)
    game.add_player(Man('Игрок'), Bot('Бот'))
    game.init()
    game.run()
