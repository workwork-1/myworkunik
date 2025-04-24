# booking_system.py
from datetime import datetime, time, timedelta
import sqlite3
from typing import List, Dict, Optional, Tuple
import logging

class BookingSystem:
    def __init__(self, db_path: str = 'beauty_salon.db'):
        self.conn = sqlite3.connect(db_path)
        self._init_db()
        self._init_services_and_masters()
        logging.info("Booking system initialized")

    def _init_db(self) -> None:
        """Инициализация всех таблиц базы данных"""
        with self.conn:
            # Клиенты
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL UNIQUE,
                    telegram_id INTEGER UNIQUE
                )""")
            
            # Услуги
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    duration INTEGER NOT NULL,
                    price INTEGER NOT NULL
                )""")
            
            # Мастера
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS masters (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    specialization TEXT
                )""")
            
            # Расписание мастеров
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS schedule (
                    id INTEGER PRIMARY KEY,
                    master_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    FOREIGN KEY(master_id) REFERENCES masters(id)
                )""")
            
            # Записи
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS bookings (
                    id INTEGER PRIMARY KEY,
                    client_id INTEGER NOT NULL,
                    service_id INTEGER NOT NULL,
                    master_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    status TEXT DEFAULT 'confirmed',
                    FOREIGN KEY(client_id) REFERENCES clients(id),
                    FOREIGN KEY(service_id) REFERENCES services(id),
                    FOREIGN KEY(master_id) REFERENCES masters(id)
                )""")

    def _init_services_and_masters(self) -> None:
        """Наполнение базы тестовыми данными"""
        with self.conn:
            # Стандартные услуги
            services = [
                ("Женская стрижка", 60, 1500),
                ("Мужская стрижка", 30, 800),
                ("Окрашивание", 120, 3000),
                ("Маникюр", 90, 2000),
                ("Педикюр", 90, 2500)
            ]
            
            self.conn.executemany(
                "INSERT OR IGNORE INTO services (name, duration, price) VALUES (?, ?, ?)",
                services
            )
            
            # Мастера
            masters = [
                ("Анна", "Парикмахер"),
                ("Елена", "Колорист"),
                ("Мария", "Мастер маникюра"),
                ("Ирина", "Мастер педикюра")
            ]
            
            self.conn.executemany(
                "INSERT OR IGNORE INTO masters (name, specialization) VALUES (?, ?)",
                masters
            )
            
            # Стандартное расписание на 2 недели
            masters = self.get_all_masters()
            for master in masters:
                for day in range(14):
                    date = (datetime.now() + timedelta(days=day)).strftime("%Y-%m-%d")
                    if datetime.strptime(date, "%Y-%m-%d").weekday() < 5:  # Только будни
                        self.add_schedule_slot(
                            master_id=master['id'],
                            date=date,
                            start_time="10:00",
                            end_time="19:00"
                        )

    def add_client(self, name: str, phone: str, telegram_id: int = None) -> Optional[int]:
     """Добавление нового клиента с проверкой дублей"""
     try:
        # Приводим телефон к единому формату
        cleaned_phone = self._normalize_phone(phone)
        
        # Пытаемся добавить нового клиента
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO clients (name, phone, telegram_id) VALUES (?, ?, ?)",
         (name, cleaned_phone, telegram_id)
        )
        return cur.lastrowid
        
     except sqlite3.IntegrityError as e:
        logging.warning(f"Client exists (phone={phone} or telegram_id={telegram_id}): {e}")
        
        # Ищем клиента по telegram_id ИЛИ phone
        client_id = self.get_client_id(telegram_id=telegram_id)
        if client_id:
            logging.info(f"Found client by telegram_id: {client_id}")
            return client_id
            
        client_id = self.get_client_id(phone=cleaned_phone)
        if client_id:
            logging.info(f"Found client by phone: {client_id}")
            # Обновляем telegram_id для найденного клиента
            self._update_client_telegram_id(client_id, telegram_id)
            return client_id
            
        logging.error("Client exists but not found by phone or telegram_id!")
        return None

def _normalize_phone(self, phone: str) -> str:
    """Приводит телефон к формату +7XXX..."""
    cleaned = ''.join(c for c in phone if c.isdigit())
    if cleaned.startswith('8') and len(cleaned) == 11:
        return '+7' + cleaned[1:]
    elif cleaned.startswith('7') and len(cleaned) == 11:
        return '+7' + cleaned[1:]
    return '+' + cleaned if not cleaned.startswith('+') else cleaned

def _update_client_telegram_id(self, client_id: int, telegram_id: int) -> bool:
    """Обновляет telegram_id для существующего клиента"""
    try:
        with self.conn:
            self.conn.execute(
                "UPDATE clients SET telegram_id = ? WHERE id = ?",
                (telegram_id, client_id)
            )
        return True
    except sqlite3.Error as e:
        logging.error(f"Error updating telegram_id: {e}")
        return False

    def get_client_id(self, phone: str = None, telegram_id: int = None) -> Optional[int]:
     """Поиск клиента с нормализацией телефона"""
     cur = self.conn.cursor()
     if telegram_id:
        cur.execute("SELECT id FROM clients WHERE telegram_id = ?", (telegram_id,))
        result = cur.fetchone()
        if result:
           return result[0]
    
     if phone:
        normalized_phone = self._normalize_phone(phone)
        cur.execute("SELECT id FROM clients WHERE phone = ?", (normalized_phone,))
        result = cur.fetchone()
        if result:
             return result[0]
    
     return None

    def get_all_services(self) -> List[Dict]:
        """Получение списка всех услуг"""
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, duration, price FROM services")
        return [dict(zip(['id', 'name', 'duration', 'price'], row)) for row in cur.fetchall()]

    def get_service_by_id(self, service_id: int) -> Optional[Dict]:
        """Получение услуги по ID"""
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, duration, price FROM services WHERE id = ?", (service_id,))
        result = cur.fetchone()
        return dict(zip(['id', 'name', 'duration', 'price'], result)) if result else None

    def get_all_masters(self) -> List[Dict]:
        """Получение списка всех мастеров"""
        cur = self.conn.cursor()
        cur.execute("SELECT id, name, specialization FROM masters")
        return [dict(zip(['id', 'name', 'specialization'], row)) for row in cur.fetchall()]

    def get_masters_for_service(self, service_id: int) -> List[Dict]:
        """Получение мастеров, выполняющих конкретную услугу"""
        # В реальной системе здесь должна быть связь многие-ко-многим
        # Для упрощения возвращаем всех мастеров
        return self.get_all_masters()

    def add_schedule_slot(self, master_id: int, date: str, start_time: str, end_time: str) -> bool:
        """Добавление слота в расписание мастера"""
        try:
            self.conn.execute(
                "INSERT INTO schedule (master_id, date, start_time, end_time) VALUES (?, ?, ?, ?)",
                (master_id, date, start_time, end_time)
            )
            return True
        except sqlite3.Error as e:
            logging.error(f"Error adding schedule slot: {e}")
            return False

    def get_available_slots(self, master_id: int, date: str, service_duration: int) -> List[Dict]:
        """Получение доступных временных слотов для записи"""
        # 1. Получаем рабочее время мастера на указанную дату
        cur = self.conn.cursor()
        cur.execute(
            "SELECT start_time, end_time FROM schedule WHERE master_id = ? AND date = ?",
            (master_id, date)
        )
        schedule = cur.fetchone()
        
        if not schedule:
            return []
        
        work_start, work_end = schedule
        work_start = datetime.strptime(work_start, "%H:%M").time()
        work_end = datetime.strptime(work_end, "%H:%M").time()
        
        # 2. Получаем уже занятые слоты
        cur.execute(
            """SELECT start_time, end_time FROM bookings 
               WHERE master_id = ? AND date = ? AND status = 'confirmed'""",
            (master_id, date)
        )
        booked_slots = cur.fetchall()
        
        # 3. Генерируем доступные слоты
        available_slots = []
        current_time = work_start
        
        while True:
            end_time = (datetime.combine(datetime.today(), current_time) + 
                        timedelta(minutes=service_duration)).time()
            
            if end_time > work_end:
                break
            
            # Проверяем, не пересекается ли слот с существующими записями
            slot_available = True
            for booked_start, booked_end in booked_slots:
                booked_start = datetime.strptime(booked_start, "%H:%M").time()
                booked_end = datetime.strptime(booked_end, "%H:%M").time()
                
                if not (end_time <= booked_start or current_time >= booked_end):
                    slot_available = False
                    break
            
            if slot_available:
                available_slots.append({
                    'start_time': current_time.strftime("%H:%M"),
                    'end_time': end_time.strftime("%H:%M")
                })
            
            # Переходим к следующему слоту с шагом 15 минут
            current_time = (datetime.combine(datetime.today(), current_time) + 
                           timedelta(minutes=15)).time()
        
        return available_slots

    def create_booking(self, client_id: int, service_id: int, master_id: int, 
                      date: str, start_time: str) -> bool:
        """Создание новой записи"""
        try:
            # Проверяем валидность client_id
            if not isinstance(client_id, int) or client_id <= 0:
             logging.error(f"Invalid client_id: {client_id}")
             return False
         
        # Проверяем существование клиента
            cur = self.conn.cursor()
            cur.execute("SELECT id FROM clients WHERE id = ?", (client_id,))
            if not cur.fetchone():
             logging.error(f"Client with id {client_id} not found")
            return False
        # Проверяем service_id и получаем продолжительность услуги
            if not isinstance(service_id, int) or service_id <= 0:
             logging.error(f"Invalid service_id: {service_id}")
             return False
            
            service = self.get_service_by_id(service_id)
            if not service:
             return False
         
         # Проверяем master_id
            if not isinstance(master_id, int) or master_id <= 0:
             logging.error(f"Invalid master_id: {master_id}")
             return False

            end_time = (datetime.strptime(start_time, "%H:%M") + 
                       timedelta(minutes=service['duration'])).strftime("%H:%M")
            
            # Логируем данные перед вставкой
            logging.info(f"Inserting booking: client_id={client_id}, service_id={service_id}, master_id={master_id}, date={date}, start_time={start_time}, end_time={end_time}")
            
            with self.conn:
                self.conn.execute(
                    """INSERT INTO bookings 
                       (client_id, service_id, master_id, date, start_time, end_time)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (client_id, service_id, master_id, date, start_time, end_time)
                )
            
            return True
        except sqlite3.Error as e:
            logging.error(f"Error creating booking: {e}")
            return False

    def get_client_bookings(self, client_id: int) -> List[Dict]:
        """Получение всех записей клиента"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT b.id, s.name as service, m.name as master, b.date, b.start_time, b.end_time
            FROM bookings b
            JOIN services s ON b.service_id = s.id
            JOIN masters m ON b.master_id = m.id
            WHERE b.client_id = ? AND b.status = 'confirmed'
            ORDER BY b.date, b.start_time
        """, (client_id,))
        
        columns = ['id', 'service', 'master', 'date', 'start_time', 'end_time']
        return [dict(zip(columns, row)) for row in cur.fetchall()]

    def cancel_booking(self, booking_id: int) -> bool:
        """Отмена записи"""
        try:
            with self.conn:
                self.conn.execute(
                    "UPDATE bookings SET status = 'cancelled' WHERE id = ?",
                    (booking_id,)
                )
            return True
        except sqlite3.Error as e:
            logging.error(f"Error cancelling booking: {e}")
            return False