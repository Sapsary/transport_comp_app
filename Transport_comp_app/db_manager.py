import psycopg2
from psycopg2 import pool, sql
import os
from dotenv import load_dotenv
import pandas as pd
from contextlib import contextmanager
import streamlit as st
import hashlib

load_dotenv()

def hash_password(password):
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()


class DatabaseManager:
    def __init__(self):
        self.connection_pool = None
        self.init_pool()
    
    def init_pool(self):
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 20,
                host=os.getenv('DB_HOST', 'localhost'),
                database=os.getenv('DB_NAME', 'transport_company'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD', 'postgres'),
                port=os.getenv('DB_PORT', '5432')
            )
        except Exception as e:
            st.error(f"Ошибка подключения к БД: {e}")
    
    @contextmanager
    def get_connection(self):
        conn = self.connection_pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            self.connection_pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
            finally:
                cursor.close()
    
    def init_tables(self):
        """Инициализация таблиц БД"""
        with self.get_cursor() as cursor:
            # Таблица routes
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS routes (
                    route_id SERIAL PRIMARY KEY,
                    name VARCHAR(255),
                    start_point VARCHAR(100),
                    end_point VARCHAR(100),
                    distance NUMERIC(10,2)
                )
            """)
            
            # Таблица vehicles
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vehicles (
                    vehicle_id SERIAL PRIMARY KEY,
                    type VARCHAR(50) NOT NULL,
                    brand VARCHAR(100),
                    model VARCHAR(100),
                    license_plate VARCHAR(20) UNIQUE,
                    capacity INT CHECK (capacity >= 1)
                )
            """)
            
            # Таблица drivers
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drivers (
                    driver_id SERIAL PRIMARY KEY,
                    last_name VARCHAR(100) NOT NULL,
                    first_name VARCHAR(100) NOT NULL,
                    middle_name VARCHAR(100),
                    birth_date DATE,
                    passport VARCHAR(50),
                    phone VARCHAR(20),
                    license_category VARCHAR(10)
                )
            """)
            
            # Таблица trips
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS trips (
                    trip_id SERIAL PRIMARY KEY,
                    route_id INT REFERENCES routes(route_id) ON DELETE CASCADE,
                    vehicle_id INT REFERENCES vehicles(vehicle_id) ON DELETE SET NULL,
                    driver_id INT REFERENCES drivers(driver_id) ON DELETE SET NULL,
                    departure_date TIMESTAMP NOT NULL,
                    arrival_date TIMESTAMP NOT NULL,
                    CONSTRAINT chk_dates CHECK (arrival_date > departure_date)
                )
            """)
            
            # Таблица clients
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS clients (
                    client_id SERIAL PRIMARY KEY,
                    last_name VARCHAR(100) NOT NULL,
                    first_name VARCHAR(100) NOT NULL,
                    middle_name VARCHAR(100),
                    passport VARCHAR(50),
                    phone VARCHAR(20)
                )
            """)
            
            # Таблица tickets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tickets (
                    ticket_id SERIAL PRIMARY KEY,
                    trip_id INT REFERENCES trips(trip_id) ON DELETE CASCADE,
                    client_id INT REFERENCES clients(client_id) ON DELETE CASCADE,
                    seat VARCHAR(10),
                    price NUMERIC(10,2) CHECK (price > 0)
                )
            """)
            
            # Таблица cargo
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cargo (
                    cargo_id SERIAL PRIMARY KEY,
                    trip_id INT REFERENCES trips(trip_id) ON DELETE CASCADE,
                    description VARCHAR(255) NOT NULL,
                    weight NUMERIC(10,2) CHECK (weight > 0),
                    volume NUMERIC(10,2) CHECK (volume > 0),
                    sender VARCHAR(255) NOT NULL,
                    receiver VARCHAR(255) NOT NULL,
                    price NUMERIC(10,2) CHECK (price > 0)
                )
            """)
            
            # Таблица пользователей системы
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS system_users (
                    user_id SERIAL PRIMARY KEY,
                    username VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL,
                    role VARCHAR(20) DEFAULT 'user',
                    client_id INT REFERENCES clients(client_id) ON DELETE SET NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Добавление другого администратора
            cursor.execute("""
                INSERT INTO system_users (username, password, role)
                VALUES (%s, %s, %s)
                ON CONFLICT (username) DO NOTHING
            """, ('admin', hash_password('admin123'), 'admin'))

            # Проверяем и добавляем тестовые данные
            self.insert_test_data(cursor)
    
    def insert_test_data(self, cursor):
        """Вставка тестовых данных"""
        # Проверяем, есть ли уже данные в routes
        cursor.execute("SELECT COUNT(*) FROM routes")
        if cursor.fetchone()[0] == 0:
            # Маршруты
            routes_data = [
                ('Алматы -- Астана', 'Алматы', 'Астана', 1200),
                ('Алматы -- Шымкент', 'Алматы', 'Шымкент', 700),
                ('Астана -- Караганда', 'Астана', 'Караганда', 200),
                ('Алматы -- Бишкек', 'Алматы', 'Бишкек', 250),
            ]
            for route in routes_data:
                cursor.execute("""
                    INSERT INTO routes (name, start_point, end_point, distance)
                    VALUES (%s, %s, %s, %s)
                """, route)
            
            # Транспорт
            vehicles_data = [
                ('Автобус', 'Mercedes', 'Tourismo', 'KZ123ABC', 50),
                ('Автобус', 'MAN', "Lion's Coach", 'KZ456DEF', 55),
                ('Грузовик', 'Volvo', 'FH16', 'KZ789GHI', 20),
                ('Автобус', 'Hyundai', 'Universe', 'KZ321JKL', 45),
            ]
            for vehicle in vehicles_data:
                cursor.execute("""
                    INSERT INTO vehicles (type, brand, model, license_plate, capacity)
                    VALUES (%s, %s, %s, %s, %s)
                """, vehicle)
            
            # Водители
            drivers_data = [
                ('Иванов', 'Петр', 'Сергеевич', '1980-05-12', 'AB123456', '+77011234567', 'D'),
                ('Смирнов', 'Андрей', 'Иванович', '1975-03-20', 'CD654321', '+77019876543', 'D'),
                ('Ким', 'Алексей', 'Николаевич', '1988-07-15', 'EF987654', '+77015554433', 'C'),
                ('Ахметов', 'Данияр', 'Муратович', '1990-11-01', 'GH112233', '+77017778899', 'D'),
            ]
            for driver in drivers_data:
                cursor.execute("""
                    INSERT INTO drivers (last_name, first_name, middle_name, birth_date, passport, phone, license_category)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, driver)
            
            # Рейсы
            trips_data = [
                (1, 1, 1, '2026-02-10 08:00:00', '2026-02-11 08:00:00'),
                (2, 2, 2, '2026-02-12 09:00:00', '2026-02-12 18:00:00'),
                (3, 3, 3, '2026-02-13 07:00:00', '2026-02-13 12:00:00'),
                (4, 4, 4, '2026-02-14 06:00:00', '2026-02-14 11:00:00'),
            ]
            for trip in trips_data:
                cursor.execute("""
                    INSERT INTO trips (route_id, vehicle_id, driver_id, departure_date, arrival_date)
                    VALUES (%s, %s, %s, %s, %s)
                """, trip)
            
            # Клиенты
            clients_data = [
                ('Сидоров', 'Алексей', 'Иванович', 'CD654321', '+77019876543'),
                ('Петрова', 'Мария', 'Андреевна', 'JK223344', '+77012223344'),
                ('Жумагалиев', 'Ерлан', 'Кайратович', 'LM556677', '+77014445566'),
                ('Кузнецов', 'Олег', 'Владимирович', 'NP889900', '+77016667788'),
            ]
            for client in clients_data:
                cursor.execute("""
                    INSERT INTO clients (last_name, first_name, middle_name, passport, phone)
                    VALUES (%s, %s, %s, %s, %s)
                """, client)
            
            # Билеты
            tickets_data = [
                (1, 1, '12A', 15000),
                (1, 2, '12B', 15000),
                (2, 3, '5C', 10000),
                (3, 4, '7D', 8000),
                (4, 1, '1A', 12000),
            ]
            for ticket in tickets_data:
                cursor.execute("""
                    INSERT INTO tickets (trip_id, client_id, seat, price)
                    VALUES (%s, %s, %s, %s)
                """, ticket)
            
            # Грузы
            cargo_data = [
                (1, 'Электроника', 120.5, 2.3, 'Компания А', 'Компания Б', 50000),
                (2, 'Мебель', 300.0, 10.0, 'Магазин Интерьер', 'Склад Шымкент', 75000),
                (3, 'Продукты питания', 150.0, 5.0, 'Ферма Караганда', 'Супермаркет Астана', 40000),
                (4, 'Одежда', 200.0, 8.0, 'Фабрика Бишкек', 'Бутик Алматы', 60000),
            ]
            for cargo in cargo_data:
                cursor.execute("""
                    INSERT INTO cargo (trip_id, description, weight, volume, sender, receiver, price)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, cargo)
    
    # Методы для работы с данными
    def get_all_routes(self):
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM routes ORDER BY route_id")
            return cursor.fetchall()
    
    def get_route_by_id(self, route_id):
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM routes WHERE route_id = %s", (route_id,))
            return cursor.fetchone()
    
    def add_route(self, name, start_point, end_point, distance):
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO routes (name, start_point, end_point, distance)
                VALUES (%s, %s, %s, %s) RETURNING route_id
            """, (name, start_point, end_point, distance))
            return cursor.fetchone()[0]
    
    def update_route(self, route_id, name, start_point, end_point, distance):
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE routes SET name=%s, start_point=%s, end_point=%s, distance=%s
                WHERE route_id=%s
            """, (name, start_point, end_point, distance, route_id))
    
    def delete_route(self, route_id):
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM routes WHERE route_id=%s", (route_id,))
    
    def get_all_vehicles(self):
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM vehicles ORDER BY vehicle_id")
            return cursor.fetchall()
    
    def get_vehicle_by_id(self, vehicle_id):
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM vehicles WHERE vehicle_id = %s", (vehicle_id,))
            return cursor.fetchone()
    
    def add_vehicle(self, vehicle_type, brand, model, license_plate, capacity):
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO vehicles (type, brand, model, license_plate, capacity)
                VALUES (%s, %s, %s, %s, %s) RETURNING vehicle_id
            """, (vehicle_type, brand, model, license_plate, capacity))
            return cursor.fetchone()[0]
    
    def update_vehicle(self, vehicle_id, vehicle_type, brand, model, license_plate, capacity):
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE vehicles SET type=%s, brand=%s, model=%s, license_plate=%s, capacity=%s
                WHERE vehicle_id=%s
            """, (vehicle_type, brand, model, license_plate, capacity, vehicle_id))
    
    def delete_vehicle(self, vehicle_id):
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM vehicles WHERE vehicle_id=%s", (vehicle_id,))
    
    def get_all_drivers(self):
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM drivers ORDER BY driver_id")
            return cursor.fetchall()
    
    def get_driver_by_id(self, driver_id):
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM drivers WHERE driver_id = %s", (driver_id,))
            return cursor.fetchone()
    
    def add_driver(self, last_name, first_name, middle_name, birth_date, passport, phone, license_category):
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO drivers (last_name, first_name, middle_name, birth_date, passport, phone, license_category)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING driver_id
            """, (last_name, first_name, middle_name, birth_date, passport, phone, license_category))
            return cursor.fetchone()[0]
    
    def update_driver(self, driver_id, last_name, first_name, middle_name, birth_date, passport, phone, license_category):
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE drivers SET last_name=%s, first_name=%s, middle_name=%s, birth_date=%s, 
                passport=%s, phone=%s, license_category=%s WHERE driver_id=%s
            """, (last_name, first_name, middle_name, birth_date, passport, phone, license_category, driver_id))
    
    def delete_driver(self, driver_id):
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM drivers WHERE driver_id=%s", (driver_id,))
    
    def get_all_trips(self, filters=None):
        with self.get_cursor() as cursor:
            query = """
                SELECT t.trip_id, t.departure_date, t.arrival_date,
                       r.name as route_name, r.start_point, r.end_point, r.distance,
                       v.brand, v.model, v.license_plate, v.capacity,
                       d.last_name as driver_last_name, d.first_name as driver_first_name,
                       (SELECT COUNT(*) FROM tickets WHERE trip_id = t.trip_id) as tickets_sold
                FROM trips t
                JOIN routes r ON t.route_id = r.route_id
                LEFT JOIN vehicles v ON t.vehicle_id = v.vehicle_id
                LEFT JOIN drivers d ON t.driver_id = d.driver_id
                WHERE 1=1
            """
            params = []
            
            if filters:
                if filters.get('route_id'):
                    query += " AND t.route_id = %s"
                    params.append(filters['route_id'])
                if filters.get('start_date'):
                    query += " AND t.departure_date >= %s"
                    params.append(filters['start_date'])
                if filters.get('end_date'):
                    query += " AND t.departure_date <= %s"
                    params.append(filters['end_date'])
                if filters.get('start_point'):
                    query += " AND r.start_point ILIKE %s"
                    params.append(f'%{filters["start_point"]}%')
                if filters.get('end_point'):
                    query += " AND r.end_point ILIKE %s"
                    params.append(f'%{filters["end_point"]}%')
            
            query += " ORDER BY t.departure_date"
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_trip_by_id(self, trip_id):
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT t.*, r.name as route_name, r.start_point, r.end_point, r.distance,
                       v.brand, v.model, v.license_plate, v.capacity,
                       d.last_name as driver_last_name, d.first_name as driver_first_name
                FROM trips t
                JOIN routes r ON t.route_id = r.route_id
                LEFT JOIN vehicles v ON t.vehicle_id = v.vehicle_id
                LEFT JOIN drivers d ON t.driver_id = d.driver_id
                WHERE t.trip_id = %s
            """, (trip_id,))
            return cursor.fetchone()
    
    def add_trip(self, route_id, vehicle_id, driver_id, departure_date, arrival_date):
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO trips (route_id, vehicle_id, driver_id, departure_date, arrival_date)
                VALUES (%s, %s, %s, %s, %s) RETURNING trip_id
            """, (route_id, vehicle_id, driver_id, departure_date, arrival_date))
            return cursor.fetchone()[0]
    
    def update_trip(self, trip_id, route_id, vehicle_id, driver_id, departure_date, arrival_date):
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE trips SET route_id=%s, vehicle_id=%s, driver_id=%s, departure_date=%s, arrival_date=%s
                WHERE trip_id=%s
            """, (route_id, vehicle_id, driver_id, departure_date, arrival_date, trip_id))
    
    def delete_trip(self, trip_id):
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM trips WHERE trip_id=%s", (trip_id,))
    
    def get_available_seats(self, trip_id):
        """Получение доступных мест на рейс"""
        with self.get_cursor() as cursor:
            # Получаем вместимость транспорта
            cursor.execute("""
                SELECT v.capacity FROM trips t
                JOIN vehicles v ON t.vehicle_id = v.vehicle_id
                WHERE t.trip_id = %s
            """, (trip_id,))
            capacity = cursor.fetchone()
            if not capacity:
                return []
            
            # Получаем занятые места
            cursor.execute("SELECT seat FROM tickets WHERE trip_id = %s", (trip_id,))
            taken_seats = [row[0] for row in cursor.fetchall()]
            
            # Генерируем все возможные места
            all_seats = []
            for row in range(1, capacity[0] // 4 + 2):
                for col in ['A', 'B', 'C', 'D']:
                    seat = f"{row}{col}"
                    all_seats.append(seat)
            
            available = [seat for seat in all_seats if seat not in taken_seats]
            return available[:capacity[0]]
    
    def buy_ticket(self, trip_id, client_id, seat, price):
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO tickets (trip_id, client_id, seat, price)
                VALUES (%s, %s, %s, %s) RETURNING ticket_id
            """, (trip_id, client_id, seat, price))
            return cursor.fetchone()[0]
    
    def get_user_tickets(self, client_id):
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT t.ticket_id, t.seat, t.price, t.trip_id,
                       tr.departure_date, tr.arrival_date,
                       r.name as route_name, r.start_point, r.end_point
                FROM tickets t
                JOIN trips tr ON t.trip_id = tr.trip_id
                JOIN routes r ON tr.route_id = r.route_id
                WHERE t.client_id = %s
                ORDER BY tr.departure_date DESC
            """, (client_id,))
            return cursor.fetchall()
    
    def get_all_clients(self):
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM clients ORDER BY client_id")
            return cursor.fetchall()
    
    def get_client_by_id(self, client_id):
        with self.get_cursor() as cursor:
            cursor.execute("SELECT * FROM clients WHERE client_id = %s", (client_id,))
            return cursor.fetchone()
    
    def add_client(self, last_name, first_name, middle_name, passport, phone):
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO clients (last_name, first_name, middle_name, passport, phone)
                VALUES (%s, %s, %s, %s, %s) RETURNING client_id
            """, (last_name, first_name, middle_name, passport, phone))
            return cursor.fetchone()[0]
    
    def update_client(self, client_id, last_name, first_name, middle_name, passport, phone):
        with self.get_cursor() as cursor:
            cursor.execute("""
                UPDATE clients SET last_name=%s, first_name=%s, middle_name=%s, passport=%s, phone=%s
                WHERE client_id=%s
            """, (last_name, first_name, middle_name, passport, phone, client_id))
    
    def delete_client(self, client_id):
        with self.get_cursor() as cursor:
            cursor.execute("DELETE FROM clients WHERE client_id=%s", (client_id,))
    
    def get_system_user(self, username):
        with self.get_cursor() as cursor:
            cursor.execute("""
                SELECT u.*, c.client_id as cid, c.last_name, c.first_name 
                FROM system_users u
                LEFT JOIN clients c ON u.client_id = c.client_id
                WHERE u.username = %s
            """, (username,))
            return cursor.fetchone()
    
    def add_system_user(self, username, password, role='user', client_id=None):
        with self.get_cursor() as cursor:
            cursor.execute("""
                INSERT INTO system_users (username, password, role, client_id)
                VALUES (%s, %s, %s, %s) RETURNING user_id
            """, (username, password, role, client_id))
            return cursor.fetchone()[0]

# Глобальный экземпляр БД
db = DatabaseManager()