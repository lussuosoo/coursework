import os # основные операции над файлами моей ОС
import tkinter as tk # для создания графического интерфейса (окна и элементы GUI)
from tkinter import ttk, messagebox
from datetime import datetime # для работы с датами (отображение даты изменения, запись времени, изменение времени)
import platform # определение операционной системы (Windows)
import subprocess # запуск внешних программ для открытия файлов
import webbrowser


class AdvancedFileManager:
    def __init__(self, root):
        # инициализация главного окна
        self.root = root # сохраняю ссылку на главное окно Tkinter
        self.root.title("Advanced File Manager") # заголовок окна
        self.root.geometry("1200x800") # ширина и высота окна начальная

        # Система навигации
        self.nav_history = []  # создаем список для хранения истории посещенных папок, паттерн снимок
        self.history_index = -1 # индекс текущей позиции в истории - начальное значение, паттерн снимок

        # визуал и стиль приложения
        self.setup_styles() # метод для настройки внешнего вида виджетов

        # Создание интерфейса пользовательского
        self.create_ui() # создание всех элементов интерфейса

        # загрузка данных файловой системы о дисках ОС
        self.load_real_drives() # загрузка информации о файлах

        # отображение данных первое
        self.update_display() # Обновление интерфейса с загруженными данными

    def setup_styles(self):
        """Настраивает стили для виджетов"""
        # объект для работы со стилями
        style = ttk.Style() # создаем объект для управления стилями виджетов

        # схема того, как будет оформления
        style.theme_use('clam') # кастомизация clam

        # дерево файлов
        style.configure("Treeview",
                        background="#808080", #фон
                        foreground="#F8F8FF", #текст
                        rowheight=30,
                        fieldbackground="#F8F8FF", # данные
                        bordercolor="#cccccc",
                        borderwidth=1)

        # настройка дерева
        style.map('Treeview',
                  background=[('selected', '#F8F8FF')],
                  foreground=[('selected', 'white')])


        # Кнопки
        style.configure("TButton",
                        padding=8,
                        relief="flat",
                        background="#333333",
                        foreground="white",
                        font=('Segoe UI', 9))


        style.map("TButton",
                  background=[('active', '#808080')])

        # Статус бар
        style.configure("Status.TLabel",
                        background="#e0e0e0",
                        foreground="#333333",
                        padding=6,
                        font=('Segoe UI', 9))

    def create_ui(self):
        """Создает пользовательский интерфейс"""
        # Основной контейнер - рамка для всего содержимого
        main_frame = ttk.Frame(self.root)
        # fill=tk.BOTH - заполняет все доступное пространство, expand=True - расширяется при увеличении окна, padx/pady=10 - отступы по краям 10 пикселей
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Панель инструментов, то есть верхняя панель
        toolbar = ttk.Frame(main_frame)
        # Заполняет по ширине, отступ снизу 10px
        toolbar.pack(fill=tk.X, pady=(0, 10))

        # Кнопки навигации
        nav_frame = ttk.Frame(toolbar) # контейнер для кнопок навигации
        nav_frame.pack(side=tk.LEFT) # прижимает к левому краю

        self.back_btn = ttk.Button(nav_frame, text="Назад",
                                   command=self.navigate_back, width=10)
        self.back_btn.pack(side=tk.LEFT, padx=2)

        self.forward_btn = ttk.Button(nav_frame, text="Вперед",
                                      command=self.navigate_forward, width=10)
        self.forward_btn.pack(side=tk.LEFT, padx=2)

        self.up_btn = ttk.Button(nav_frame, text="Вверх",
                                 command=self.navigate_up, width=10)
        self.up_btn.pack(side=tk.LEFT, padx=2)

        # Кнопки действий
        action_frame = ttk.Frame(toolbar) # кнопки действия контейнер
        action_frame.pack(side=tk.RIGHT) # прижимает к правому краю

        ttk.Button(action_frame, text="Открыть", command=self.open_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Новая папка", command=self.create_folder).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Удалить", command=self.delete_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Переименовать", command=self.rename_item).pack(side=tk.LEFT, padx=2)
        ttk.Button(action_frame, text="Обновить", command=self.refresh).pack(side=tk.LEFT, padx=2)

        # Поле пути
        self.path_var = tk.StringVar() # текущий путь
        path_frame = ttk.Frame(main_frame) # контейнер поля пути
        path_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(path_frame, text="Путь:").pack(side=tk.LEFT)
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var) # поля ввода
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5) # растягивает на всю ширину поле

        # Дерево файлов
        self.tree = ttk.Treeview(main_frame, columns=("type", "size", "modified"), selectmode="browse")

        # Настройка колонок
        self.tree.heading("#0", text="Имя", anchor=tk.W)
        self.tree.heading("type", text="Тип", anchor=tk.W)
        self.tree.heading("size", text="Размер", anchor=tk.W)
        self.tree.heading("modified", text="Изменен", anchor=tk.W)

        self.tree.column("#0", width=400)
        self.tree.column("type", width=150)
        self.tree.column("size", width=100)
        self.tree.column("modified", width=150)

        # Полосы прокрутки
        vsb = ttk.Scrollbar(main_frame, orient="vertical", command=self.tree.yview) # вертикальная
        hsb = ttk.Scrollbar(main_frame, orient="horizontal", command=self.tree.xview) # горизонтальная
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set) # привязывание скроллов к дереву

        # Размещение элементов
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True) # дерево слева, расстягивается
        vsb.pack(side=tk.RIGHT, fill=tk.Y) # справа скролл вертикаль
        hsb.pack(side=tk.BOTTOM, fill=tk.X) # снизу скролл горизонт

        # Привязка событий
        self.tree.bind("<Double-1>", self.on_double_click) # двойной клик
        self.tree.bind("<Return>", self.on_double_click) # ENTER

        # Контекстное меню
        self.setup_context_menu()

        # Статус бар
        self.status_var = tk.StringVar()
        status_bar = ttk.Label(self.root, textvariable=self.status_var, style="Status.TLabel")
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    def setup_context_menu(self):
        """Создает контекстное меню"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Открыть", command=self.open_item)
        self.context_menu.add_command(label="Открыть с помощью...", command=self.open_with)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Копировать путь", command=self.copy_path)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Удалить", command=self.delete_item)
        self.context_menu.add_command(label="Переименовать", command=self.rename_item)

        self.tree.bind("<Button-3>", self.show_context_menu)

    def show_context_menu(self, event):
        """Показывает контекстное меню"""
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    def load_real_drives(self):
        """Загружает реальные диски компьютера"""
        self.root_node = {
            "path": "Этот компьютер",
            "name": "Этот компьютер",
            "type": "computer",
            "parent": None
        }

        # Получаем список дисков
        if os.name == 'nt':  # Windows
            import string
            drives = [f"{d}:\\" for d in string.ascii_uppercase if os.path.exists(f"{d}:\\")]
        else:  # Linux/Mac
            drives = ["/"]

        self.root_node["children"] = []

        for drive in drives:
            drive_name = drive
            if os.name == 'nt':
                try:
                    import win32api
                    label = win32api.GetVolumeInformation(drive)[0]
                    if label:
                        drive_name = f"{drive} ({label})"
                except:
                    pass

            self.root_node["children"].append({
                "path": drive,
                "name": drive_name,
                "type": "drive",
                "parent": self.root_node
            })

        self.current_node = self.root_node

    def get_node_children(self, node):
        """Возвращает дочерние элементы для узла"""
        if "children" in node:
            return node["children"]

        children = []
        path = node["path"]

        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    try:
                        if entry.is_dir():
                            children.append({
                                "path": entry.path,
                                "name": entry.name,
                                "type": "folder",
                                "parent": node,
                                "modified": datetime.fromtimestamp(entry.stat().st_mtime)
                            })
                        else:
                            size = entry.stat().st_size
                            children.append({
                                "path": entry.path,
                                "name": entry.name,
                                "type": "file",
                                "size": self.format_size(size),
                                "parent": node,
                                "modified": datetime.fromtimestamp(entry.stat().st_mtime)
                            })
                    except:
                        continue
        except:
            messagebox.showerror("Ошибка", f"Нет доступа к {path}")
            return None

        node["children"] = children
        return children

    def format_size(self, size):
        """Форматирует размер файла"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def update_display(self):
        """Обновляет отображение файловой системы"""
        self.tree.delete(*self.tree.get_children())
        self.path_var.set(self.get_current_path())

        # Обновляем состояние кнопок навигации
        self.back_btn.state(['!disabled' if self.history_index > 0 else 'disabled'])
        self.forward_btn.state(['!disabled' if self.history_index < len(self.nav_history) - 1 else 'disabled'])
        self.up_btn.state(['!disabled' if self.current_node != self.root_node else 'disabled'])

        # Получаем дочерние элементы
        children = self.get_node_children(self.current_node)
        if children is None:
            return

        # Добавляем элементы в дерево
        if self.current_node["type"] == "computer":
            # Показываем диски
            for child in sorted(children, key=lambda x: x["name"]):
                self.add_tree_item("", child)
        else:
            # Добавляем родительскую ссылку (кроме корня)
            if self.current_node != self.root_node:
                self.tree.insert("", "end", text="..", values=("Папка", "", ""))

            # Сортируем: сначала папки, потом файлы
            folders = [c for c in children if c["type"] == "folder"]
            files = [c for c in children if c["type"] == "file"]

            # Добавляем папки
            for child in sorted(folders, key=lambda x: x["name"]):
                self.add_tree_item("", child)

            # Добавляем файлы
            for child in sorted(files, key=lambda x: x["name"]):
                self.add_tree_item("", child)

        # Обновляем статус бар
        count = len(children)
        if self.current_node != self.root_node and ".." in [self.tree.item(i, "text") for i in
                                                            self.tree.get_children()]:
            count -= 1
        self.status_var.set(f"Элементов: {count} | {self.get_current_path()}")

    def add_tree_item(self, parent, node):
        """Добавляет узел в дерево"""
        if node["type"] == "folder":
            icon = "📁"
            item_type = "Папка"
            size = ""
        elif node["type"] == "drive":
            icon = "💽"
            item_type = "Диск"
            size = ""
        elif node["type"] == "computer":
            icon = "🖥️"
            item_type = "Компьютер"
            size = ""
        else:
            icon = self.get_file_icon(node["name"])
            ext = os.path.splitext(node["name"])[1][1:].upper()
            item_type = f"{ext} файл" if ext else "Файл"
            size = node.get("size", "")

        modified = node.get("modified", datetime.now()).strftime("%Y-%m-%d %H:%M")
        self.tree.insert(parent, "end", text=f"{icon} {node['name']}",
                         values=(item_type, size, modified))


    def get_current_path(self):
        """Возвращает текущий путь"""
        return self.current_node["path"]

    def on_double_click(self, event):
        """Обработка двойного щелчка"""
        item = self.tree.focus()
        if not item:
            return

        name = self.tree.item(item, "text")

        if name == "..":
            self.navigate_up()
            return

        # Убираем иконку из имени
        if " " in name:
            name = name.split(" ", 1)[1]

        # Ищем выбранный узел
        selected_node = None
        for child in self.get_node_children(self.current_node) or []:
            if child["name"] == name:
                selected_node = child
                break

        if selected_node:
            if selected_node["type"] in ("folder", "drive"):
                self.navigate_to(selected_node)
            else:
                self.open_file(selected_node["path"])

    def navigate_to(self, node):
        """Переходит к указанному узлу"""
        # Сохраняем текущий узел в истории
        if self.history_index < len(self.nav_history) - 1:
            self.nav_history = self.nav_history[:self.history_index + 1]

        self.nav_history.append(self.current_node)
        self.history_index = len(self.nav_history) - 1

        self.current_node = node
        self.update_display()

    def navigate_back(self):
        """Переход назад по истории"""
        if self.history_index > 0:
            self.history_index -= 1
            self.current_node = self.nav_history[self.history_index]
            self.update_display()

    def navigate_forward(self):
        """Переход вперед по истории"""
        if self.history_index < len(self.nav_history) - 1:
            self.history_index += 1
            self.current_node = self.nav_history[self.history_index]
            self.update_display()

    def navigate_up(self):
        """Переход в родительскую папку"""
        if self.current_node["parent"]:
            self.navigate_to(self.current_node["parent"])

    def refresh(self):
        """Обновляет текущую директорию"""
        if "children" in self.current_node:
            del self.current_node["children"]
        self.update_display()

    def open_item(self):
        """Открывает выбранный элемент"""
        item = self.tree.focus()
        if not item:
            return

        name = self.tree.item(item, "text")

        if name == "..":
            self.navigate_up()
            return

        # Убираем иконку из имени
        if " " in name:
            name = name.split(" ", 1)[1]

        # Ищем выбранный узел
        selected_node = None
        for child in self.get_node_children(self.current_node) or []:
            if child["name"] == name:
                selected_node = child
                break

        if selected_node:
            if selected_node["type"] in ("folder", "drive"):
                self.navigate_to(selected_node)
            else:
                self.open_file(selected_node["path"])

    def open_file(self, filepath):
        """Открывает файл с помощью системного приложения"""
        try:
            if platform.system() == 'Windows':
                os.startfile(filepath)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.run(['open', filepath])
            else:  # Linux
                subprocess.run(['xdg-open', filepath])
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл: {e}")

    def open_with(self):
        """Открывает диалог выбора программы для открытия файла"""
        item = self.tree.focus()
        if not item:
            return

        name = self.tree.item(item, "text")
        if " " in name:
            name = name.split(" ", 1)[1]

        # Ищем выбранный файл
        selected_node = None
        for child in self.get_node_children(self.current_node) or []:
            if child["name"] == name and child["type"] == "file":
                selected_node = child
                break

        if selected_node:
            if platform.system() == 'Windows':
                try:
                    import win32gui
                    import win32con

                    # Открываем стандартный диалог "Открыть с помощью"
                    win32gui.ShellExecute(
                        0,
                        "openas",
                        selected_node["path"],
                        None,
                        None,
                        win32con.SW_SHOW)
                except:
                    self.open_file(selected_node["path"])
            else:
                # Для других ОС просто открываем файл
                self.open_file(selected_node["path"])

    def copy_path(self):
        """Копирует путь к файлу в буфер обмена"""
        item = self.tree.focus()
        if not item:
            return

        name = self.tree.item(item, "text")
        if " " in name:
            name = name.split(" ", 1)[1]

        # Ищем выбранный узел
        selected_node = None
        for child in self.get_node_children(self.current_node) or []:
            if child["name"] == name:
                selected_node = child
                break

        if selected_node:
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_node["path"])
            messagebox.showinfo("Скопировано", f"Путь скопирован в буфер обмена:\n{selected_node['path']}")

    def create_folder(self):
        """Создает новую папку"""
        if self.current_node["type"] not in ("drive", "folder"):
            messagebox.showerror("Ошибка", "Нельзя создать папку в этом месте")
            return

        name = self.get_input("Новая папка", "Введите имя папки:")
        if not name:
            return

        new_path = os.path.join(self.current_node["path"], name)

        try:
            os.mkdir(new_path)

            # Добавляем новую папку в текущий узел
            new_folder = {
                "path": new_path,
                "name": name,
                "type": "folder",
                "parent": self.current_node,
                "modified": datetime.now()
            }

            if "children" not in self.current_node:
                self.current_node["children"] = []

            self.current_node["children"].append(new_folder)
            self.update_display()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать папку: {e}")

    def delete_item(self):
        """Удаляет выбранный элемент"""
        item = self.tree.focus()
        if not item:
            return

        name = self.tree.item(item, "text")
        if name == "..":
            return

        # Убираем иконку из имени
        if " " in name:
            name = name.split(" ", 1)[1]

        if not messagebox.askyesno("Подтверждение", f"Удалить '{name}'?"):
            return

        # Ищем выбранный узел
        selected_node = None
        for child in self.get_node_children(self.current_node) or []:
            if child["name"] == name:
                selected_node = child
                break

        if selected_node:
            try:
                if selected_node["type"] == "folder":
                    os.rmdir(selected_node["path"])
                else:
                    os.remove(selected_node["path"])

                # Удаляем из списка детей
                self.current_node["children"] = [c for c in self.current_node["children"] if c["name"] != name]
                self.update_display()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")

    def rename_item(self):
        """Переименовывает выбранный элемент"""
        item = self.tree.focus()
        if not item:
            return

        old_name = self.tree.item(item, "text")
        if old_name == "..":
            return

        # Убираем иконку из имени
        if " " in old_name:
            old_name = old_name.split(" ", 1)[1]

        new_name = self.get_input("Переименование", "Введите новое имя:", old_name)
        if not new_name or new_name == old_name:
            return

        # Проверяем уникальность имени
        if any(child["name"] == new_name for child in self.get_node_children(self.current_node) or []):
            messagebox.showerror("Ошибка", "Элемент с таким именем уже существует")
            return

        # Ищем выбранный узел
        selected_node = None
        for child in self.get_node_children(self.current_node) or []:
            if child["name"] == old_name:
                selected_node = child
                break

        if selected_node:
            old_path = selected_node["path"]
            new_path = os.path.join(os.path.dirname(old_path), new_name)

            try:
                os.rename(old_path, new_path)

                # Обновляем данные узла
                selected_node["name"] = new_name
                selected_node["path"] = new_path
                selected_node["modified"] = datetime.now()

                self.update_display()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось переименовать: {e}")

    def get_input(self, title, prompt, default=""):
        """Отображает диалог ввода"""
        dialog = tk.Toplevel(self.root)
        dialog.title(title)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=prompt).pack(padx=10, pady=5)

        entry_var = tk.StringVar(value=default)
        entry = ttk.Entry(dialog, textvariable=entry_var)
        entry.pack(padx=10, pady=5)
        entry.select_range(0, tk.END)
        entry.focus_set()

        result = None

        def on_ok():
            nonlocal result
            result = entry_var.get()
            dialog.destroy()

        def on_cancel():
            nonlocal result
            result = None
            dialog.destroy()

        ttk.Button(dialog, text="OK", command=on_ok).pack(side=tk.RIGHT, padx=5, pady=5)
        ttk.Button(dialog, text="Отмена", command=on_cancel).pack(side=tk.RIGHT, padx=5, pady=5)

        dialog.wait_window()
        return result


if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedFileManager(root)
    root.mainloop()
