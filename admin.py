# admin.py
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from booking_system import BookingSystem

class AdminPanel:
    def __init__(self):
        try:
            self.booking = BookingSystem()
            self.window = tk.Tk()
            self.window.title("Beauty Salon Admin Panel")
            self.window.geometry("1000x600")
            self._setup_ui()
            self._load_data()
        except Exception as e:
            messagebox.showerror("Ошибка инициализации", f"Не удалось запустить приложение: {str(e)}")
            self.window.destroy()
            raise

    def _setup_ui(self):
        """Настройка интерфейса администратора"""
        # Основные фреймы
        control_frame = ttk.Frame(self.window, padding="10")
        control_frame.pack(fill=tk.X)

        display_frame = ttk.Frame(self.window)
        display_frame.pack(fill=tk.BOTH, expand=True)

        # Элементы управления
        ttk.Button(control_frame, text="Обновить", command=self._load_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Добавить запись", command=self._add_booking_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Отменить запись", command=self._cancel_booking).pack(side=tk.LEFT, padx=5)
        
        # Период отображения
        self.period_var = tk.StringVar(value="today")
        ttk.Radiobutton(control_frame, text="Сегодня", variable=self.period_var, 
                       value="today", command=self._load_data).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(control_frame, text="Завтра", variable=self.period_var, 
                       value="tomorrow", command=self._load_data).pack(side=tk.LEFT, padx=5)
        ttk.Radiobutton(control_frame, text="Неделя", variable=self.period_var, 
                       value="week", command=self._load_data).pack(side=tk.LEFT, padx=5)

        # Таблица записей
        columns = ("id", "client", "phone", "service", "master", "date", "time", "duration")
        self.bookings_tree = ttk.Treeview(
            display_frame, columns=columns, show="headings", selectmode="browse"
        )
        
        # Настройка колонок
        for col in columns:
            self.bookings_tree.heading(col, text=col.capitalize())
        
        self.bookings_tree.column("id", width=50, anchor=tk.CENTER)
        self.bookings_tree.column("client", width=150)
        self.bookings_tree.column("phone", width=120)
        self.bookings_tree.column("service", width=150)
        self.bookings_tree.column("master", width=150)
        self.bookings_tree.column("date", width=100)
        self.bookings_tree.column("time", width=80)
        self.bookings_tree.column("duration", width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, command=self.bookings_tree.yview)
        self.bookings_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.bookings_tree.pack(fill=tk.BOTH, expand=True)

    def _load_data(self):
        """Загрузка данных в таблицу"""
        period = self.period_var.get()
        today = datetime.now().date()
        
        if period == "today":
            date_from = today
            date_to = today
        elif period == "tomorrow":
            date_from = today + timedelta(days=1)
            date_to = date_from
        else:  # week
            date_from = today
            date_to = today + timedelta(days=7)
        
        # Очищаем таблицу
        for item in self.bookings_tree.get_children():
            self.bookings_tree.delete(item)
        
        # Получаем записи из БД
        bookings = self._get_bookings_for_period(date_from, date_to)
        
        # Заполняем таблицу
        for booking in bookings:
            self.bookings_tree.insert("", tk.END, values=(
                booking['id'],
                booking['client_name'],
                booking['client_phone'],
                booking['service_name'],
                booking['master_name'],
                booking['date'],
                booking['start_time'],
                booking['duration']
            ))

    def _get_bookings_for_period(self, date_from, date_to):
        """Получение записей за период (вспомогательный метод)"""
        # В реальной системе нужно добавить соответствующий метод в BookingSystem
        # Здесь упрощенная версия для демонстрации
        all_bookings = []
        current_date = date_from
        
        while current_date <= date_to:
            date_str = current_date.strftime("%Y-%m-%d")
            bookings = self.booking.conn.execute(
                """SELECT b.id, c.name as client_name, c.phone as client_phone,
                          s.name as service_name, m.name as master_name,
                          b.date, b.start_time, s.duration
                   FROM bookings b
                   JOIN clients c ON b.client_id = c.id
                   JOIN services s ON b.service_id = s.id
                   JOIN masters m ON b.master_id = m.id
                   WHERE b.date = ? AND b.status = 'confirmed'
                   ORDER BY b.start_time""",
                (date_str,)
            ).fetchall()
            
            all_bookings.extend([dict(zip(
                ['id', 'client_name', 'client_phone', 'service_name', 
                 'master_name', 'date', 'start_time', 'duration'], row)) 
                for row in bookings])
            
            current_date += timedelta(days=1)
        
        return all_bookings

    def _add_booking_dialog(self):
        """Диалог добавления новой записи"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Добавить запись")
        dialog.geometry("400x400")
        
        # Переменные для формы
        client_name = tk.StringVar()
        client_phone = tk.StringVar()
        service_var = tk.StringVar()
        master_var = tk.StringVar()
        date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        time_var = tk.StringVar()
        
        # Заполняем списки услуг и мастеров
        services = [s['name'] for s in self.booking.get_all_services()]
        masters = [m['name'] for m in self.booking.get_all_masters()]
        
        # Элементы формы
        ttk.Label(dialog, text="Клиент:").pack(pady=(10, 0))
        ttk.Entry(dialog, textvariable=client_name).pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(dialog, text="Телефон:").pack()
        ttk.Entry(dialog, textvariable=client_phone).pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(dialog, text="Услуга:").pack()
        service_cb = ttk.Combobox(dialog, textvariable=service_var, values=services)
        service_cb.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(dialog, text="Мастер:").pack()
        master_cb = ttk.Combobox(dialog, textvariable=master_var, values=masters)
        master_cb.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(dialog, text="Дата (ГГГГ-ММ-ДД):").pack()
        ttk.Entry(dialog, textvariable=date_var).pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(dialog, text="Время (ЧЧ:ММ):").pack()
        ttk.Entry(dialog, textvariable=time_var).pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(dialog, text="Сохранить", 
                  command=lambda: self._save_booking(
                      client_name.get(),
                      client_phone.get(),
                      service_var.get(),
                      master_var.get(),
                      date_var.get(),
                      time_var.get(),
                      dialog
                  )).pack(pady=10)

    def _save_booking(self, client_name, client_phone, service_name, 
                     master_name, date_str, time_str, dialog):
        """Сохранение новой записи"""
        try:
            # Проверка данных
            if not all([client_name, client_phone, service_name, master_name, date_str, time_str]):
                messagebox.showerror("Ошибка", "Все поля обязательны для заполнения")
                return
            
            # Получаем ID сервиса и мастера
            service_id = next((s['id'] for s in self.booking.get_all_services() 
                             if s['name'] == service_name), None)
            master_id = next((m['id'] for m in self.booking.get_all_masters() 
                            if m['name'] == master_name), None)
            
            if not service_id or not master_id:
                messagebox.showerror("Ошибка", "Услуга или мастер не найдены")
                return
            
            # Добавляем клиента или получаем существующего
            client_id = self.booking.add_client(client_name, client_phone)
            
            # Создаем запись
            success = self.booking.create_booking(
                client_id=client_id,
                service_id=service_id,
                master_id=master_id,
                date=date_str,
                start_time=time_str
            )
            
            if success:
                messagebox.showinfo("Успех", "Запись успешно добавлена")
                dialog.destroy()
                self._load_data()
            else:
                messagebox.showerror("Ошибка", "Не удалось создать запись")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")

    def _cancel_booking(self):
        """Отмена выбранной записи"""
        selected_item = self.bookings_tree.selection()
        if not selected_item:
            messagebox.showwarning("Предупреждение", "Выберите запись для отмены")
            return
        
        booking_id = self.bookings_tree.item(selected_item)['values'][0]
        
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите отменить эту запись?"):
            success = self.booking.cancel_booking(booking_id)
            if success:
                messagebox.showinfo("Успех", "Запись отменена")
                self._load_data()
            else:
                messagebox.showerror("Ошибка", "Не удалось отменить запись")


if __name__ == "__main__":
    try:
        app = AdminPanel()
        app.window.mainloop()
    except Exception as e:
        print(f"Произошла ошибка: {e}")