import streamlit as st
import pandas as pd
from datetime import datetime
from db_manager import db
from auth import init_session_state, login_form, register_form, logout, is_admin

# Настройка страницы
st.set_page_config(
    page_title="Транспортная компания",
    page_icon="🚌",
    layout="wide"
)

# ==================== CSS СТИЛИ (ИСПРАВЛЕННЫЕ) ====================
st.markdown("""
<style>
    /* Главный заголовок */
    .main-header {
        background: linear-gradient(135deg, #C71585  0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* Карточка билета */
    .ticket-card {
        background: white;
        border-left: 5px solid #2a5298;
        padding: 1.2rem;
        margin-bottom: 1rem;
        border-radius: 10px;
        transition: transform 0.2s;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        color: #333;
    }
    .ticket-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0,0,0,0.15);
    }
    
    /* Карточка статистики - темный фон, светлый текст */
    .stat-card {
        background: linear-gradient(135deg, #C71585 0%, #2a5298 100%);
        color: white !important;
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        transition: transform 0.2s;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .stat-card:hover {
        transform: translateY(-5px);
    }
    .stat-card h2 {
        font-size: 2.5rem;
        margin: 0;
        font-weight: bold;
        color: white !important;
    }
    .stat-card p {
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
        color: rgba(255,255,255,0.9) !important;
    }
    
    /* Кнопки */
    div.stButton > button {
        background: linear-gradient(135deg, #C71585 0%, #2a5298 100%);
        color: white;
        border: none;
        padding: 0.6rem 1.2rem;
        border-radius: 10px;
        font-weight: 500;
        transition: all 0.3s;
        width: 100%;
    }
    div.stButton > button:hover {
        opacity: 0.9;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(30, 60, 114, 0.4);
    }
    
    /* Карточка рейса */
    .trip-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        border: 1px solid #e0e0e0;
        transition: all 0.3s;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        color: #333;
    }
    .trip-card:hover {
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        border-color: #2a5298;
    }
    .trip-card h3 {
        color: #1e3c72;
        margin-bottom: 0.5rem;
    }
    
    /* Информационные сообщения */
    .info-box {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #333;
    }
    
    .success-box {
        background: #e8f5e9;
        border-left: 4px solid #4caf50;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #333;
    }
    
    .warning-box {
        background: #fff3e0;
        border-left: 4px solid #ff9800;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #333;
    }
    
    /* Метрики Streamlit - исправление цветов */
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }
    
    /* Текст в sidebar */
    .css-1d391kg, .css-1633tjr {
        color: #333;
    }
    
    /* Общий текст */
    .stMarkdown, .stText, .stWrite {
        color: #E0FFFF;
    }
    
    /* Заголовки */
    h1, h2, h3, h4 {
        color: #00CED1 !important;
    }
    
    /* Анимации */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-in;
    }
    
    /* Таблицы */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        color: #1e3c72 !important;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ==================== ЗАГОЛОВОК ====================
st.markdown("""
<div class="main-header fade-in">
    <h1 style="color: white; text-align: center; margin: 0;">🚌 Транспортная компания</h1>
    <p style="color: rgba(255,255,255,0.9); text-align: center; margin: 0.5rem 0 0 0;">
        Управление перевозками и продажа билетов
    </p>
</div>
""", unsafe_allow_html=True)

# Инициализация
db.init_tables()
init_session_state()

# Инициализация дополнительных переменных
if 'search_performed' not in st.session_state:
    st.session_state.search_performed = False
if 'filters' not in st.session_state:
    st.session_state.filters = {}
if 'show_buy_form' not in st.session_state:
    st.session_state.show_buy_form = False
if 'selected_trip' not in st.session_state:
    st.session_state.selected_trip = None

# Боковая панель
with st.sidebar:
    st.markdown("### 🎯 Меню")
    
    if not st.session_state.logged_in:
        menu = ["🔐 Вход", "📝 Регистрация"]
        choice = st.radio("Выберите действие", menu)
        
        if choice == "🔐 Вход":
            login_form()
        else:
            register_form()
    else:
        st.markdown(f"""
        <div class="info-box">
            👋 Здравствуйте, <b>{st.session_state.username}</b><br>
            🎭 Роль: <b>{'Администратор' if is_admin() else 'Пользователь'}</b>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Меню для авторизованных пользователей
        if is_admin():
            menu_items = [
                "🏠 Главная", 
                "🔍 Поиск и покупка", 
                "🎫 Мои билеты", 
                "👤 Профиль",
                "⚙️ Управление маршрутами", 
                "🚛 Управление ТС", 
                "👨‍✈️ Управление водителями",
                "🗺️ Управление рейсами", 
                "👥 Управление клиентами", 
                "📊 Статистика"
            ]
        else:
            menu_items = [
                "🏠 Главная", 
                "🔍 Поиск и покупка", 
                "🎫 Мои билеты", 
                "👤 Профиль"
            ]
        
        choice = st.radio("Навигация", menu_items)
        
        st.markdown("---")
        if st.button("🚪 Выход", use_container_width=True):
            logout()
            st.rerun()

# Основной контент
if not st.session_state.logged_in:
    st.info("👋 Добро пожаловать! Пожалуйста, войдите или зарегистрируйтесь.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <h2>{len(db.get_all_routes())}</h2>
            <p>🚌 Маршрутов</p>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="stat-card">
            <h2>{len(db.get_all_trips())}</h2>
            <p>🚛 Рейсов</p>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="stat-card">
            <h2>{len(db.get_all_clients())}</h2>
            <p>👥 Клиентов</p>
        </div>
        """, unsafe_allow_html=True)
else:
    # ==================== ГЛАВНАЯ СТРАНИЦА ====================
    if choice == "🏠 Главная":
        st.markdown("<h2>🏠 Добро пожаловать в систему!</h2>", unsafe_allow_html=True)
        
        col1, col2, col3, col4 = st.columns(4)
        
        routes = db.get_all_routes()
        trips = db.get_all_trips()
        vehicles = db.get_all_vehicles()
        clients = db.get_all_clients()
        
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <h2>{len(routes)}</h2>
                <p>📍 Маршрутов</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <h2>{len(trips)}</h2>
                <p>🚌 Рейсов</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <h2>{len(vehicles)}</h2>
                <p>🚛 Транспорта</p>
            </div>
            """, unsafe_allow_html=True)
        with col4:
            st.markdown(f"""
            <div class="stat-card">
                <h2>{len(clients)}</h2>
                <p>👥 Клиентов</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("<h3>📅 Ближайшие рейсы</h3>", unsafe_allow_html=True)
        
        if trips:
            for trip in trips[:5]:
                st.markdown(f"""
                <div class="trip-card">
                    <b>🚌 {trip[3]}</b><br>
                    📍 {trip[4]} → {trip[5]}<br>
                    📅 {trip[1].strftime('%d.%m.%Y %H:%M') if trip[1] else 'Не указано'}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Нет доступных рейсов")
    
    # ==================== ПОИСК И ПОКУПКА ====================
    elif choice == "🔍 Поиск и покупка":
        st.markdown("<h2>🔍 Поиск и покупка билетов</h2>", unsafe_allow_html=True)
        
        # Форма поиска
        with st.form("search_form"):
            col1, col2 = st.columns(2)
            with col1:
                start_point = st.text_input("📍 Откуда", placeholder="Например: Алматы")
            with col2:
                end_point = st.text_input("🎯 Куда", placeholder="Например: Астана")
            
            col3, col4 = st.columns(2)
            with col3:
                start_date = st.date_input("📅 Дата отправления от", value=None)
            with col4:
                end_date = st.date_input("📅 Дата отправления до", value=None)
            
            submitted = st.form_submit_button("🔍 Найти рейсы", use_container_width=True)
        
        if submitted:
            st.session_state.search_performed = True
            st.session_state.filters = {
                'start_point': start_point,
                'end_point': end_point,
                'start_date': start_date,
                'end_date': end_date
            }
        
        if st.session_state.search_performed:
            filters = {}
            if st.session_state.filters.get('start_point'):
                filters['start_point'] = st.session_state.filters['start_point']
            if st.session_state.filters.get('end_point'):
                filters['end_point'] = st.session_state.filters['end_point']
            if st.session_state.filters.get('start_date'):
                filters['start_date'] = datetime.combine(st.session_state.filters['start_date'], datetime.min.time())
            if st.session_state.filters.get('end_date'):
                filters['end_date'] = datetime.combine(st.session_state.filters['end_date'], datetime.max.time())
            
            trips = db.get_all_trips(filters)
            
            if trips:
                st.success(f"✅ Найдено {len(trips)} рейсов")
                
                for trip in trips:
                    with st.container():
                        capacity = trip[10] if len(trip) > 10 else 0
                        sold = trip[14] if len(trip) > 14 else 0
                        available = capacity - sold
                        distance = trip[6] if len(trip) > 6 else 500
                        price = int(10000 * (distance / 500))
                        
                        st.markdown(f"""
                        <div class="trip-card">
                            <h3>🚌 {trip[3]}</h3>
                            <table style="width: 100%;">
                                <tr>
                                    <td>📍 Маршрут:</td>
                                    <td><b>{trip[4]} → {trip[5]}</b></td>
                                    <td>📏 Расстояние:</td>
                                    <td><b>{distance} км</b></td>
                                </tr>
                                <tr>
                                    <td>📅 Отправление:</td>
                                    <td><b>{trip[1].strftime('%d.%m.%Y %H:%M')}</b></td>
                                    <td>📅 Прибытие:</td>
                                    <td><b>{trip[2].strftime('%d.%m.%Y %H:%M')}</b></td>
                                </tr>
                                <tr>
                                    <td>🚌 Транспорт:</td>
                                    <td><b>{trip[7]} {trip[8]}</b></td>
                                    <td>💺 Свободно мест:</td>
                                    <td><b style="color: #4caf50;">{available} из {capacity}</b></td>
                                </tr>
                                <tr>
                                    <td>💰 Цена билета:</td>
                                    <td colspan="3"><b style="color: #1e3c72; font-size: 1.2rem;">{price} ₸</b></td>
                                </tr>
                            </table>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        if st.button(f"🎫 Купить билет", key=f"buy_btn_{trip[0]}", use_container_width=True):
                            st.session_state.selected_trip = trip[0]
                            st.session_state.show_buy_form = True
                            st.rerun()
                        
                        if st.session_state.get('show_buy_form') and st.session_state.selected_trip == trip[0]:
                            st.markdown('<div class="info-box">✏️ <b>Оформление билета</b></div>', unsafe_allow_html=True)
                            available_seats = db.get_available_seats(trip[0])
                            
                            if available_seats:
                                col1, col2 = st.columns(2)
                                with col1:
                                    seat = st.selectbox("💺 Выберите место", available_seats, key=f"seat_select_{trip[0]}")
                                with col2:
                                    st.metric("💰 Цена билета", f"{price} ₸")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("✅ Подтвердить покупку", key=f"confirm_{trip[0]}", type="primary"):
                                        ticket_id = db.buy_ticket(trip[0], st.session_state.client_id, seat, price)
                                        if ticket_id:
                                            st.success(f"✅ Билет успешно приобретен! Место: {seat}")
                                            st.balloons()
                                            st.session_state.show_buy_form = False
                                            st.session_state.selected_trip = None
                                            st.rerun()
                                        else:
                                            st.error("Ошибка при покупке")
                                with col2:
                                    if st.button("❌ Отмена", key=f"cancel_{trip[0]}"):
                                        st.session_state.show_buy_form = False
                                        st.session_state.selected_trip = None
                                        st.rerun()
                            else:
                                st.warning("😞 Нет свободных мест на этот рейс")
            else:
                st.warning("😞 Рейсы не найдены. Попробуйте изменить параметры поиска.")
    
    # ==================== МОИ БИЛЕТЫ ====================
    elif choice == "🎫 Мои билеты":
        st.markdown("<h2>🎫 Мои билеты</h2>", unsafe_allow_html=True)
        
        tickets = db.get_user_tickets(st.session_state.client_id)
        
        if tickets:
            for ticket in tickets:
                st.markdown(f"""
                <div class="ticket-card">
                    <b>🎫 Билет #{ticket[0]}</b><br>
                    🚌 {ticket[7]} → {ticket[8]}<br>
                    💺 Место: <b>{ticket[1]}</b> | 💰 Цена: <b>{ticket[2]} ₸</b><br>
                    📅 Отправление: {ticket[4].strftime('%d.%m.%Y %H:%M')}<br>
                    📅 Прибытие: {ticket[5].strftime('%d.%m.%Y %H:%M')}
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("📭 У вас пока нет билетов. Перейдите в раздел 'Поиск и покупка' чтобы купить билет.")
    
    # ==================== ПРОФИЛЬ ====================
    elif choice == "👤 Профиль":
        st.markdown("<h2>👤 Мой профиль</h2>", unsafe_allow_html=True)
        
        client = db.get_client_by_id(st.session_state.client_id)
        
        if client:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="info-box">
                    <b>📝 Личная информация:</b><br>
                    Фамилия: {client[1]}<br>
                    Имя: {client[2]}<br>
                    Отчество: {client[3] or '-'}
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="info-box">
                    <b>📞 Контакты:</b><br>
                    Паспорт: {client[4]}<br>
                    Телефон: {client[5]}<br>
                    Логин: {st.session_state.username}
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("<h3>📊 Моя статистика</h3>", unsafe_allow_html=True)
            
            tickets = db.get_user_tickets(st.session_state.client_id)
            total_spent = sum(t[2] for t in tickets)
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="stat-card">
                    <h2>{len(tickets)}</h2>
                    <p>🎫 Куплено билетов</p>
                </div>
                """, unsafe_allow_html=True)
            with col2:
                st.markdown(f"""
                <div class="stat-card">
                    <h2>{total_spent} ₸</h2>
                    <p>💰 Потрачено всего</p>
                </div>
                """, unsafe_allow_html=True)
    
    # ==================== АДМИН ФУНКЦИИ ====================
        # ==================== УПРАВЛЕНИЕ МАРШРУТАМИ ====================
    elif is_admin() and choice == "⚙️ Управление маршрутами":
        st.markdown("<h2>⚙️ Управление маршрутами</h2>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["📋 Список маршрутов", "➕ Добавить маршрут"])
        
        with tab1:
            routes = db.get_all_routes()
            if routes:
                for route in routes:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{route[1]}** - {route[2]} → {route[3]} ({route[4]} км)")
                    with col2:
                        if st.button("✏️ Редактировать", key=f"edit_route_{route[0]}"):
                            st.session_state.edit_route = route
                    with col3:
                        if st.button("🗑️ Удалить", key=f"del_route_{route[0]}"):
                            db.delete_route(route[0])
                            st.success("Маршрут удален")
                            st.rerun()
                
                if 'edit_route' in st.session_state:
                    route = st.session_state.edit_route
                    st.markdown("---")
                    st.subheader("✏️ Редактирование маршрута")
                    with st.form("edit_route_form"):
                        name = st.text_input("Название", value=route[1])
                        start = st.text_input("Откуда", value=route[2])
                        end = st.text_input("Куда", value=route[3])
                        distance = st.number_input("Расстояние (км)", value=float(route[4]))
                        
                        if st.form_submit_button("💾 Сохранить"):
                            db.update_route(route[0], name, start, end, distance)
                            st.success("Маршрут обновлен")
                            del st.session_state.edit_route
                            st.rerun()
            else:
                st.info("Нет маршрутов")
        
        with tab2:
            with st.form("add_route_form"):
                name = st.text_input("Название маршрута")
                col1, col2 = st.columns(2)
                with col1:
                    start = st.text_input("Пункт отправления")
                with col2:
                    end = st.text_input("Пункт назначения")
                distance = st.number_input("Расстояние (км)", min_value=1.0)
                
                if st.form_submit_button("➕ Добавить маршрут"):
                    if name and start and end:
                        db.add_route(name, start, end, distance)
                        st.success("✅ Маршрут добавлен")
                        st.rerun()
                    else:
                        st.error("Заполните все поля")
    
    # ==================== УПРАВЛЕНИЕ ТС ====================
    elif is_admin() and choice == "🚛 Управление ТС":
        st.markdown("<h2>🚛 Управление транспортными средствами</h2>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["📋 Список ТС", "➕ Добавить ТС"])
        
        with tab1:
            vehicles = db.get_all_vehicles()
            if vehicles:
                for v in vehicles:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{v[2]} {v[3]}** - {v[1]}, {v[4]}, {v[5]} мест")
                    with col2:
                        if st.button("✏️ Ред", key=f"edit_veh_{v[0]}"):
                            st.session_state.edit_vehicle = v
                    with col3:
                        if st.button("🗑️ Удал", key=f"del_veh_{v[0]}"):
                            db.delete_vehicle(v[0])
                            st.success("ТС удалено")
                            st.rerun()
                
                if 'edit_vehicle' in st.session_state:
                    v = st.session_state.edit_vehicle
                    st.markdown("---")
                    st.subheader("✏️ Редактирование ТС")
                    with st.form("edit_vehicle_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            vehicle_type = st.selectbox("Тип ТС", ["Автобус", "Грузовик", "Микроавтобус"], index=["Автобус", "Грузовик", "Микроавтобус"].index(v[1]) if v[1] in ["Автобус", "Грузовик", "Микроавтобус"] else 0)
                            brand = st.text_input("Бренд", value=v[2])
                            model = st.text_input("Модель", value=v[3])
                        with col2:
                            license_plate = st.text_input("Гос. номер", value=v[4])
                            capacity = st.number_input("Вместимость", value=v[5], min_value=1)
                        
                        if st.form_submit_button("💾 Сохранить"):
                            db.update_vehicle(v[0], vehicle_type, brand, model, license_plate, capacity)
                            st.success("ТС обновлено")
                            del st.session_state.edit_vehicle
                            st.rerun()
            else:
                st.info("Нет транспортных средств")
        
        with tab2:
            with st.form("add_vehicle_form"):
                col1, col2 = st.columns(2)
                with col1:
                    vehicle_type = st.selectbox("Тип ТС", ["Автобус", "Грузовик", "Микроавтобус"])
                    brand = st.text_input("Бренд")
                    model = st.text_input("Модель")
                with col2:
                    license_plate = st.text_input("Гос. номер")
                    capacity = st.number_input("Вместимость", min_value=1, value=40)
                
                if st.form_submit_button("➕ Добавить ТС"):
                    if brand and model and license_plate:
                        db.add_vehicle(vehicle_type, brand, model, license_plate, capacity)
                        st.success("✅ ТС добавлено")
                        st.rerun()
                    else:
                        st.error("Заполните все поля")
    
    # ==================== УПРАВЛЕНИЕ ВОДИТЕЛЯМИ ====================
    elif is_admin() and choice == "👨‍✈️ Управление водителями":
        st.markdown("<h2>👨‍✈️ Управление водителями</h2>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["📋 Список водителей", "➕ Добавить водителя"])
        
        with tab1:
            drivers = db.get_all_drivers()
            if drivers:
                for d in drivers:
                    with st.expander(f"🚹 {d[1]} {d[2]} {d[3] or ''}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**Дата рождения:** {d[4]}")
                            st.write(f"**Паспорт:** {d[5]}")
                        with col2:
                            st.write(f"**Телефон:** {d[6]}")
                            st.write(f"**Категория:** {d[7]}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✏️ Редактировать", key=f"edit_driver_{d[0]}"):
                                st.session_state.edit_driver = d
                        with col2:
                            if st.button("🗑️ Удалить", key=f"del_driver_{d[0]}"):
                                db.delete_driver(d[0])
                                st.success("Водитель удален")
                                st.rerun()
                
                if 'edit_driver' in st.session_state:
                    d = st.session_state.edit_driver
                    st.markdown("---")
                    st.subheader("✏️ Редактирование водителя")
                    with st.form("edit_driver_form"):
                        col1, col2 = st.columns(2)
                        with col1:
                            last_name = st.text_input("Фамилия", value=d[1])
                            first_name = st.text_input("Имя", value=d[2])
                            middle_name = st.text_input("Отчество", value=d[3] or "")
                        with col2:
                            birth_date = st.date_input("Дата рождения", value=d[4] if d[4] else datetime.now().date())
                            passport = st.text_input("Паспорт", value=d[5] or "")
                            phone = st.text_input("Телефон", value=d[6] or "")
                        license_category = st.text_input("Категория прав", value=d[7] or "")
                        
                        if st.form_submit_button("💾 Сохранить"):
                            db.update_driver(d[0], last_name, first_name, middle_name, birth_date, passport, phone, license_category)
                            st.success("Водитель обновлен")
                            del st.session_state.edit_driver
                            st.rerun()
            else:
                st.info("Нет водителей")
        
        with tab2:
            with st.form("add_driver_form"):
                col1, col2 = st.columns(2)
                with col1:
                    last_name = st.text_input("Фамилия")
                    first_name = st.text_input("Имя")
                    middle_name = st.text_input("Отчество")
                with col2:
                    birth_date = st.date_input("Дата рождения")
                    passport = st.text_input("Паспорт")
                    phone = st.text_input("Телефон")
                license_category = st.text_input("Категория прав")
                
                if st.form_submit_button("➕ Добавить водителя"):
                    if last_name and first_name:
                        db.add_driver(last_name, first_name, middle_name, birth_date, passport, phone, license_category)
                        st.success("✅ Водитель добавлен")
                        st.rerun()
                    else:
                        st.error("Заполните фамилию и имя")
    
    # ==================== УПРАВЛЕНИЕ РЕЙСАМИ ====================
    elif is_admin() and choice == "🗺️ Управление рейсами":
        st.markdown("<h2>🗺️ Управление рейсами</h2>", unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["📋 Список рейсов", "➕ Добавить рейс"])
        
        with tab1:
            trips = db.get_all_trips()
            if trips:
                for t in trips:
                    with st.expander(f"🚌 Рейс #{t[0]} - {t[3]} ({t[1].strftime('%d.%m.%Y')})"):
                        st.write(f"**Маршрут:** {t[3]}")
                        st.write(f"**Откуда:** {t[4]}")
                        st.write(f"**Куда:** {t[5]}")
                        st.write(f"**Отправление:** {t[1]}")
                        st.write(f"**Прибытие:** {t[2]}")
                        st.write(f"**Транспорт:** {t[7]} {t[8]}")
                        st.write(f"**Водитель:** {t[11]} {t[12] if len(t) > 12 else ''}")
                        
                        if st.button("🗑️ Удалить рейс", key=f"del_trip_{t[0]}"):
                            db.delete_trip(t[0])
                            st.success("Рейс удален")
                            st.rerun()
            else:
                st.info("Нет рейсов")
        
        with tab2:
            with st.form("add_trip_form"):
                routes = db.get_all_routes()
                vehicles = db.get_all_vehicles()
                drivers = db.get_all_drivers()
                
                if not routes:
                    st.warning("Сначала добавьте маршруты")
                if not vehicles:
                    st.warning("Сначала добавьте транспорт")
                if not drivers:
                    st.warning("Сначала добавьте водителей")
                
                if routes and vehicles and drivers:
                    route_options = {r[1]: r[0] for r in routes}
                    vehicle_options = {f"{v[2]} {v[3]} ({v[4]})": v[0] for v in vehicles}
                    driver_options = {f"{d[1]} {d[2]}": d[0] for d in drivers}
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        route = st.selectbox("Маршрут", list(route_options.keys()))
                        dep_date = st.date_input("Дата отправления")
                        dep_time = st.time_input("Время отправления")
                    with col2:
                        vehicle = st.selectbox("Транспорт", list(vehicle_options.keys()))
                        arr_date = st.date_input("Дата прибытия")
                        arr_time = st.time_input("Время прибытия")
                    driver = st.selectbox("Водитель", list(driver_options.keys()))
                    
                    departure = datetime.combine(dep_date, dep_time)
                    arrival = datetime.combine(arr_date, arr_time)
                    
                    if st.form_submit_button("➕ Добавить рейс"):
                        if arrival > departure:
                            db.add_trip(route_options[route], vehicle_options[vehicle], 
                                       driver_options[driver], departure, arrival)
                            st.success("✅ Рейс добавлен")
                            st.rerun()
                        else:
                            st.error("Дата прибытия должна быть позже даты отправления")
    
    # ==================== УПРАВЛЕНИЕ КЛИЕНТАМИ ====================
    elif is_admin() and choice == "👥 Управление клиентами":
        st.markdown("<h2>👥 Управление клиентами</h2>", unsafe_allow_html=True)
        
        clients = db.get_all_clients()
        if clients:
            for c in clients:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"**{c[1]} {c[2]} {c[3] or ''}** - {c[5]}")
                with col2:
                    if st.button("✏️ Ред", key=f"edit_client_{c[0]}"):
                        st.session_state.edit_client = c
                with col3:
                    if st.button("🗑️ Удал", key=f"del_client_{c[0]}"):
                        db.delete_client(c[0])
                        st.success("Клиент удален")
                        st.rerun()
            
            if 'edit_client' in st.session_state:
                c = st.session_state.edit_client
                st.markdown("---")
                st.subheader("✏️ Редактирование клиента")
                with st.form("edit_client_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        last_name = st.text_input("Фамилия", value=c[1])
                        first_name = st.text_input("Имя", value=c[2])
                        middle_name = st.text_input("Отчество", value=c[3] or "")
                    with col2:
                        passport = st.text_input("Паспорт", value=c[4] or "")
                        phone = st.text_input("Телефон", value=c[5] or "")
                    
                    if st.form_submit_button("💾 Сохранить"):
                        db.update_client(c[0], last_name, first_name, middle_name, passport, phone)
                        st.success("Клиент обновлен")
                        del st.session_state.edit_client
                        st.rerun()
        else:
            st.info("Нет клиентов")
    
    # ==================== СТАТИСТИКА ====================
    elif is_admin() and choice == "📊 Статистика":
        st.markdown("<h2>📊 Статистика</h2>", unsafe_allow_html=True)
        
        trips = db.get_all_trips()
        tickets_count = 0
        total_revenue = 0
        for client in db.get_all_clients():
            tickets = db.get_user_tickets(client[0])
            tickets_count += len(tickets)
            total_revenue += sum(t[2] for t in tickets)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <h2>{len(trips)}</h2>
                <p>🚌 Всего рейсов</p>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <h2>{tickets_count}</h2>
                <p>🎫 Продано билетов</p>
            </div>
            """, unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="stat-card">
                <h2>{total_revenue} ₸</h2>
                <p>💰 Общий доход</p>
            </div>
            """, unsafe_allow_html=True)

# Запуск
if __name__ == "__main__":
    pass