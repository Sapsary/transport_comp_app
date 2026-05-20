import streamlit as st
import hashlib
from db_manager import db

def hash_password(password):
    """Хеширование пароля"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_session_state():
    """Инициализация session state"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'role' not in st.session_state:
        st.session_state.role = None
    if 'client_id' not in st.session_state:
        st.session_state.client_id = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None

def login(username, password):
    """Аутентификация пользователя"""
    user = db.get_system_user(username)
    if user and user[2] == hash_password(password):  # password_hash на позиции 2
        st.session_state.logged_in = True
        st.session_state.username = username
        st.session_state.role = user[3]  # role на позиции 3
        st.session_state.user_id = user[0]  # user_id на позиции 0
        st.session_state.client_id = user[4]  # client_id на позиции 4
        return True
    return False

def register(username, password, last_name, first_name, middle_name, passport, phone):
    """Регистрация нового пользователя"""
    # Проверяем, существует ли пользователь
    existing = db.get_system_user(username)
    if existing:
        return False, "Пользователь с таким именем уже существует"
    
    # Создаем клиента
    client_id = db.add_client(last_name, first_name, middle_name, passport, phone)
    
    # Создаем пользователя системы
    db.add_system_user(username, hash_password(password), 'user', client_id)
    
    return True, "Регистрация успешна"

def logout():
    """Выход из системы"""
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.client_id = None
    st.session_state.user_id = None

def is_admin():
    """Проверка, является ли пользователь админом"""
    return st.session_state.get('logged_in') and st.session_state.get('role') == 'admin'

def login_form():
    """Форма входа"""
    with st.form("login_form"):
        st.subheader("Вход в систему")
        username = st.text_input("Имя пользователя")
        password = st.text_input("Пароль", type="password")
        submitted = st.form_submit_button("Войти")
        
        if submitted:
            if login(username, password):
                st.success("Успешный вход!")
                st.rerun()
            else:
                st.error("Неверное имя пользователя или пароль")

def register_form():
    """Форма регистрации"""
    with st.form("register_form"):
        st.subheader("Регистрация")
        
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Имя пользователя (логин)")
            password = st.text_input("Пароль", type="password")
            last_name = st.text_input("Фамилия")
            first_name = st.text_input("Имя")
        with col2:
            confirm_password = st.text_input("Подтвердите пароль", type="password")
            middle_name = st.text_input("Отчество")
            passport = st.text_input("Паспорт")
            phone = st.text_input("Телефон")
        
        submitted = st.form_submit_button("Зарегистрироваться")
        
        if submitted:
            if not username or not password:
                st.error("Заполните обязательные поля")
            elif password != confirm_password:
                st.error("Пароли не совпадают")
            else:
                success, message = register(username, password, last_name, first_name, 
                                            middle_name, passport, phone)
                if success:
                    st.success(message)
                    st.info("Теперь вы можете войти в систему")
                else:
                    st.error(message)