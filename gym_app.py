import sys
import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                           QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, 
                           QMessageBox, QTabWidget, QComboBox, QFormLayout, QFrame, QHeaderView,
                           QListWidget, QListWidgetItem, QStackedWidget, QSizePolicy, QCheckBox,
                           QDialog, QDateEdit, QRadioButton, QGroupBox, QButtonGroup, QGridLayout,
                           QFileDialog, QTextEdit)
from PyQt6.QtCore import Qt, QDate, QSize, QDateTime
from PyQt6.QtGui import QIcon, QPixmap, QFont, QColor

# Constantes
DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123"  # Este será hasheado


def hash_password(password):
    """Crea un hash seguro de la contraseña con salt."""
    # En un sistema real, generaríamos un salt aleatorio para cada usuario
    salt = "fitapp2025"  # Este salt debería ser único por usuario en un sistema real
    salted = password + salt
    return hashlib.sha256(salted.encode()).hexdigest()


def verify_password(input_password, stored_password):
    """Verifica si la contraseña ingresada coincide con la almacenada."""
    salt = "fitapp2025"  # Debe ser el mismo salt usado para crear el hash
    input_hash = hashlib.sha256((input_password + salt).encode()).hexdigest()
    return input_hash == stored_password


class LoginWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FIT APP - Iniciar Sesión")
        self.setFixedSize(400, 400)
        self.setStyleSheet("""
            QWidget {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #221e5c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3b347e;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3d3d3d;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        
        self.setup_ui()
        self.init_database()
        
    def init_database(self):
        """Inicializa la base de datos y crea el usuario admin si no existe."""
        conn = sqlite3.connect('fitapp.db')
        cursor = conn.cursor()
        
        # Crear tabla de usuarios (dueños de gimnasios que compran el software)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                email TEXT UNIQUE,
                tipo TEXT NOT NULL,
                nombre_gimnasio TEXT,
                fecha_registro TEXT NOT NULL,
                ultimo_acceso TEXT,
                activo INTEGER DEFAULT 1
            )
        ''')
        
        # Crear tabla de licencias para los usuarios (gimnasios)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS licencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                tipo TEXT NOT NULL,
                fecha_inicio TEXT NOT NULL,
                fecha_vencimiento TEXT NOT NULL,
                precio REAL NOT NULL,
                activa INTEGER DEFAULT 1,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Verificar si existe el usuario admin
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE username = ?", (DEFAULT_ADMIN_USERNAME,))
        if cursor.fetchone()[0] == 0:
            # Crear usuario admin predeterminado
            hashed_password = hash_password(DEFAULT_ADMIN_PASSWORD)
            fecha_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO usuarios (username, password, email, tipo, nombre_gimnasio, fecha_registro, activo) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (DEFAULT_ADMIN_USERNAME, hashed_password, "admin@fitapp.com", "admin", "Administración FitApp", fecha_registro, 1)
            )
        
        conn.commit()
        conn.close()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Logo
        logo_label = QLabel("FIT APP")
        logo_label.setStyleSheet("color: #221e5c; font-size: 28px; font-weight: bold;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)
        
        # Formulario
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Nombre de usuario")
        form_layout.addRow("Usuario:", self.username_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Contraseña")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        form_layout.addRow("Contraseña:", self.password_input)
        
        # Remember me
        self.remember_checkbox = QCheckBox("Recordar usuario")
        self.remember_checkbox.setStyleSheet("color: #cccccc;")
        
        layout.addLayout(form_layout)
        layout.addWidget(self.remember_checkbox)
        
        # Login button
        login_button = QPushButton("Iniciar Sesión")
        login_button.clicked.connect(self.authenticate)
        layout.addWidget(login_button)
        
        # Info about default admin account
        info_label = QLabel("Admin por defecto: usuario=admin, contraseña=admin123")
        info_label.setStyleSheet("color: #7f8c8d; font-size: 10px;")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(info_label)
        
        # Error message
        self.error_label = QLabel("")
        self.error_label.setStyleSheet("color: #e74c3c;")
        self.error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.error_label)
        
        layout.addStretch()
        
    def authenticate(self):
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            self.error_label.setText("Ingrese usuario y contraseña")
            return
        
        # Verificar credenciales
        if self.check_credentials(username, password):
            self.accept()
        else:
            self.error_label.setText("Usuario o contraseña incorrectos")
            
    def check_credentials(self, username, password):
        # Conectar a la base de datos
        conn = sqlite3.connect('fitapp.db')
        cursor = conn.cursor()
        
        # Verificar hash de contraseña
        cursor.execute("SELECT id, password, tipo, nombre_gimnasio FROM usuarios WHERE username = ? AND activo = 1", (username,))
        user = cursor.fetchone()
        
        if user and verify_password(password, user[1]):
            # Guardar ID, tipo de usuario y nombre del gimnasio para la sesión
            self.user_id = user[0]
            self.user_type = user[2]
            self.gym_name = user[3]
            
            # Actualizar último acceso
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("UPDATE usuarios SET ultimo_acceso = ? WHERE id = ?", (current_time, user[0]))
            conn.commit()
            
            # Verificar licencia para gimnasios
            if self.user_type == "gimnasio":
                cursor.execute("""
                    SELECT fecha_vencimiento, activa
                    FROM licencias
                    WHERE usuario_id = ? AND activa = 1
                    ORDER BY fecha_vencimiento DESC
                    LIMIT 1
                """, (self.user_id,))
                
                license_info = cursor.fetchone()
                if not license_info:
                    self.error_label.setText("Su gimnasio no tiene una licencia activa. Contacte al administrador.")
                    conn.close()
                    return False
                
                fecha_venc = datetime.strptime(license_info[0], "%Y-%m-%d")
                if fecha_venc < datetime.now():
                    self.error_label.setText("Su licencia ha vencido. Contacte al administrador para renovarla.")
                    conn.close()
                    return False
                
                # Licencia activa y no vencida
                self.license_expiry = license_info[0]
            
            conn.close()
            return True
        
        conn.close()
        return False
        
    def accept(self):
        self.accepted = True
        self.close()


class AdminDashboard(QMainWindow):
    """Panel de administración para el dueño de la aplicación"""
    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.setWindowTitle("FIT APP - Panel de Administración")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QPushButton {
                background-color: #221e5c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3b347e;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
            QLineEdit, QComboBox, QDateEdit {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3d3d3d;
                padding: 5px;
                border-radius: 4px;
            }
            QTableWidget {
                background-color: #2d2d2d;
                alternate-background-color: #3d3d3d;
                color: white;
                gridline-color: #3d3d3d;
                border: none;
            }
            QHeaderView::section {
                background-color: #221e5c;
                color: white;
                padding: 5px;
                border: none;
            }
            QFrame {
                background-color: #2d2d2d;
                border-radius: 4px;
                padding: 10px;
            }
            QListWidget {
                background-color: #1e1e1e;
                color: white;
                border: none;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 0px;
            }
            QListWidget::item:selected {
                background-color: #221e5c;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
        """)
        
        self.init_database()
        self.setup_ui()
        
    def init_database(self):
        """Inicializa la conexión a la base de datos"""
        self.conn = sqlite3.connect('fitapp.db')
        self.cur = self.conn.cursor()
    
    def setup_ui(self):
        """Configura la interfaz de usuario principal"""
        # Widget central y layout principal
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Panel izquierdo (menú lateral)
        left_panel = QWidget()
        left_panel.setFixedWidth(250)
        left_panel.setStyleSheet("background-color: #1e1e1e;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        # Logo en la parte superior del panel izquierdo
        logo_container = QWidget()
        logo_container.setFixedHeight(100)
        logo_container.setStyleSheet("background-color: #1a1a1a; border-bottom: 1px solid #3d3d3d;")
        logo_layout = QHBoxLayout(logo_container)
        
        # Crear un QLabel para el logo
        logo_label = QLabel()
        logo_label.setText("FIT APP")
        logo_label.setStyleSheet("color: #FFF; font-size: 22px; font-weight: bold;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)
        
        left_layout.addWidget(logo_container)
        
        # Menú de navegación
        self.menu_list = QListWidget()
        self.menu_list.setIconSize(QSize(24, 24))
        self.menu_list.setSpacing(5)
        
        # Opciones de menú para admin
        menu_items = [
            ("Gestionar Gimnasios", "gyms_page"),
            ("Gestionar Licencias", "licenses_page"),
            ("Estadísticas", "stats_page"),
            ("Configuración", "settings_page")
        ]
        
        for text, page_name in menu_items:
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, page_name)
            self.menu_list.addItem(item)
        
        left_layout.addWidget(self.menu_list)
        
        # Widget para mostrar información en la parte inferior del menú
        info_widget = QWidget()
        info_widget.setFixedHeight(100)
        info_widget.setStyleSheet("background-color: #1a1a1a; border-top: 1px solid #3d3d3d;")
        info_layout = QVBoxLayout(info_widget)
        
        # Obtener el nombre de usuario
        self.cur.execute("SELECT username FROM usuarios WHERE id = ?", (self.user_id,))
        username = self.cur.fetchone()[0]
        
        user_label = QLabel(f"Usuario: {username}")
        user_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_label.setStyleSheet("color: #ffffff;")
        info_layout.addWidget(user_label)
        
        role_label = QLabel("Rol: Administrador")
        role_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        role_label.setStyleSheet("color: #7f8c8d;")
        info_layout.addWidget(role_label)
        
        version_label = QLabel("FIT APP v1.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #7f8c8d;")
        info_layout.addWidget(version_label)
        
        left_layout.addWidget(info_widget)
        
        # Panel derecho (contenido)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra superior
        top_bar = QWidget()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #3d3d3d;")
        top_bar_layout = QHBoxLayout(top_bar)
        
        self.page_title = QLabel("Gestionar Gimnasios")
        self.page_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        top_bar_layout.addWidget(self.page_title)
        
        top_bar_layout.addStretch()
        
        # Botón de cerrar sesión
        logout_button = QPushButton("Cerrar Sesión")
        logout_button.setFixedWidth(120)
        logout_button.clicked.connect(self.logout)
        top_bar_layout.addWidget(logout_button)
        
        right_layout.addWidget(top_bar)
        
        # Contenido principal (páginas apiladas)
        self.content_stack = QStackedWidget()
        
        # Configurar páginas
        self.gyms_page = QWidget()
        self.setup_gyms_page(self.gyms_page)
        self.content_stack.addWidget(self.gyms_page)
        
        self.licenses_page = QWidget()
        self.setup_licenses_page(self.licenses_page)
        self.content_stack.addWidget(self.licenses_page)
        
        self.stats_page = QWidget()
        self.setup_stats_page(self.stats_page)
        self.content_stack.addWidget(self.stats_page)
        
        self.settings_page = QWidget()
        self.setup_settings_page(self.settings_page)
        self.content_stack.addWidget(self.settings_page)
        
        right_layout.addWidget(self.content_stack)
        
        # Agregar paneles al layout principal
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # Conectar eventos
        self.menu_list.currentRowChanged.connect(self.change_page)
        self.menu_list.setCurrentRow(0)  # Seleccionar la primera opción por defecto
    
    def logout(self):
        """Cierra la sesión actual y regresa a la pantalla de login."""
        reply = QMessageBox.question(self, "Cerrar Sesión", 
                                    "¿Está seguro que desea cerrar la sesión?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.close()
            # El flujo regresará al main() que mostrará nuevamente la ventana de login
    
    def change_page(self, index):
        """Cambia la página mostrada en el contenido principal"""
        # Cambiar el título de la página
        self.page_title.setText(self.menu_list.item(index).text())
        # Cambiar la página mostrada
        self.content_stack.setCurrentIndex(index)
    
    def setup_gyms_page(self, page):
        """Configura la página de gestión de gimnasios"""
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título de la sección
        title_label = QLabel("Gestión de Clientes Gimnasios")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Formulario para añadir/editar gimnasios
        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QFormLayout(form_frame)
        
        self.gym_name_input = QLineEdit()
        self.gym_username_input = QLineEdit()
        self.gym_email_input = QLineEdit()
        self.gym_password_input = QLineEdit()
        self.gym_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        form_layout.addRow("Nombre del Gimnasio:", self.gym_name_input)
        form_layout.addRow("Nombre de Usuario:", self.gym_username_input)
        form_layout.addRow("Email:", self.gym_email_input)
        form_layout.addRow("Contraseña:", self.gym_password_input)
        
        layout.addWidget(form_frame)
        
        # Botones para gestionar gimnasios
        button_layout = QHBoxLayout()
        
        self.add_gym_button = QPushButton("Registrar Gimnasio")
        self.add_gym_button.clicked.connect(self.add_gym)
        
        self.update_gym_button = QPushButton("Actualizar Gimnasio")
        self.update_gym_button.clicked.connect(self.update_gym)
        self.update_gym_button.setEnabled(False)
        
        self.toggle_gym_button = QPushButton("Activar/Desactivar")
        self.toggle_gym_button.clicked.connect(self.toggle_gym_active)
        self.toggle_gym_button.setEnabled(False)
        
        self.clear_gym_button = QPushButton("Limpiar")
        self.clear_gym_button.clicked.connect(self.clear_gym_form)
        
        button_layout.addWidget(self.add_gym_button)
        button_layout.addWidget(self.update_gym_button)
        button_layout.addWidget(self.toggle_gym_button)
        button_layout.addWidget(self.clear_gym_button)
        
        layout.addLayout(button_layout)
        
        # Tabla de gimnasios
        self.gyms_table = QTableWidget()
        self.gyms_table.setColumnCount(6)
        self.gyms_table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Usuario", "Email", "Fecha Registro", "Estado"
        ])
        self.gyms_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.gyms_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.gyms_table.cellClicked.connect(self.select_gym)
        self.gyms_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.gyms_table)
        
        # Cargar datos en la tabla
        self.load_gyms()
    
    def load_gyms(self):
        """Carga la lista de gimnasios en la tabla"""
        self.cur.execute("""
            SELECT id, nombre_gimnasio, username, email, fecha_registro, activo
            FROM usuarios
            WHERE tipo = 'gimnasio'
            ORDER BY nombre_gimnasio
        """)
        gyms = self.cur.fetchall()
        
        self.gyms_table.setRowCount(0)  # Limpiar tabla
        
        for row_idx, gym in enumerate(gyms):
            self.gyms_table.insertRow(row_idx)
            
            for col_idx, value in enumerate(gym):
                # Formatear el valor de activo
                if col_idx == 5:  # Columna de estado (activo/inactivo)
                    value = "Activo" if value == 1 else "Inactivo"
                
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                # Colorear según el estado
                if col_idx == 5:
                    if value == "Activo":
                        item.setForeground(QColor("#2ecc71"))
                    else:
                        item.setForeground(QColor("#e74c3c"))
                
                self.gyms_table.setItem(row_idx, col_idx, item)
    
    def clear_gym_form(self):
        """Limpia el formulario de gimnasios"""
        self.gym_name_input.clear()
        self.gym_username_input.clear()
        self.gym_email_input.clear()
        self.gym_password_input.clear()
        
        self.add_gym_button.setEnabled(True)
        self.update_gym_button.setEnabled(False)
        self.toggle_gym_button.setEnabled(False)
        
        # Limpiar selección de la tabla
        self.gyms_table.clearSelection()
        if hasattr(self, 'selected_gym_id'):
            del self.selected_gym_id
    
    def select_gym(self, row, column):
        """Selecciona un gimnasio de la tabla para editar"""
        self.selected_gym_id = int(self.gyms_table.item(row, 0).text())
        
        # Cargar datos en el formulario
        self.gym_name_input.setText(self.gyms_table.item(row, 1).text())
        self.gym_username_input.setText(self.gyms_table.item(row, 2).text())
        self.gym_email_input.setText(self.gyms_table.item(row, 3).text())
        
        # No cargar la contraseña por seguridad
        self.gym_password_input.clear()
        
        # Activar botones
        self.add_gym_button.setEnabled(False)
        self.update_gym_button.setEnabled(True)
        self.toggle_gym_button.setEnabled(True)
    
    def add_gym(self):
        """Agrega un nuevo gimnasio a la base de datos"""
        nombre = self.gym_name_input.text().strip()
        username = self.gym_username_input.text().strip()
        email = self.gym_email_input.text().strip()
        password = self.gym_password_input.text()
        
        # Validación básica
        if not nombre or not username or not email or not password:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios.")
            return
        
        try:
            # Verificar si el usuario o email ya existe
            self.cur.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
            if self.cur.fetchone():
                QMessageBox.warning(self, "Error", f"Ya existe un usuario con el nombre '{username}'.")
                return
            
            self.cur.execute("SELECT id FROM usuarios WHERE email = ?", (email,))
            if self.cur.fetchone():
                QMessageBox.warning(self, "Error", f"Ya existe un usuario con el email '{email}'.")
                return
            
            # Crear hash de la contraseña
            hashed_password = hash_password(password)
            
            # Fecha de registro
            fecha_registro = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Insertar nuevo gimnasio
            self.cur.execute('''
                INSERT INTO usuarios (username, password, email, tipo, nombre_gimnasio, fecha_registro, activo)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, hashed_password, email, "gimnasio", nombre, fecha_registro, 1))
            
            self.conn.commit()
            
            QMessageBox.information(self, "Éxito", f"Gimnasio '{nombre}' registrado correctamente.")
            self.clear_gym_form()
            self.load_gyms()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al registrar gimnasio: {str(e)}")
    
    def update_gym(self):
        """Actualiza los datos de un gimnasio existente"""
        if not hasattr(self, 'selected_gym_id'):
            return
        
        nombre = self.gym_name_input.text().strip()
        username = self.gym_username_input.text().strip()
        email = self.gym_email_input.text().strip()
        password = self.gym_password_input.text()
        
        # Validación básica
        if not nombre or not username or not email:
            QMessageBox.warning(self, "Error", "Los campos Nombre, Usuario y Email son obligatorios.")
            return
        
        try:
            # Verificar si el usuario o email pertenece a otro usuario
            self.cur.execute("SELECT id FROM usuarios WHERE username = ? AND id != ?", (username, self.selected_gym_id))
            if self.cur.fetchone():
                QMessageBox.warning(self, "Error", f"Ya existe otro usuario con el nombre '{username}'.")
                return
            
            self.cur.execute("SELECT id FROM usuarios WHERE email = ? AND id != ?", (email, self.selected_gym_id))
            if self.cur.fetchone():
                QMessageBox.warning(self, "Error", f"Ya existe otro usuario con el email '{email}'.")
                return
            
            # Actualizar datos
            if password:  # Si se proporciona nueva contraseña
                hashed_password = hash_password(password)
                self.cur.execute('''
                    UPDATE usuarios
                    SET nombre_gimnasio = ?, username = ?, email = ?, password = ?
                    WHERE id = ?
                ''', (nombre, username, email, hashed_password, self.selected_gym_id))
            else:  # Mantener la misma contraseña
                self.cur.execute('''
                    UPDATE usuarios
                    SET nombre_gimnasio = ?, username = ?, email = ?
                    WHERE id = ?
                ''', (nombre, username, email, self.selected_gym_id))
            
            self.conn.commit()
            
            QMessageBox.information(self, "Éxito", f"Gimnasio '{nombre}' actualizado correctamente.")
            self.clear_gym_form()
            self.load_gyms()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar gimnasio: {str(e)}")
    
    def toggle_gym_active(self):
        """Activa o desactiva un gimnasio"""
        if not hasattr(self, 'selected_gym_id'):
            return
        
        # Obtener estado actual
        row = None
        for r in range(self.gyms_table.rowCount()):
            if int(self.gyms_table.item(r, 0).text()) == self.selected_gym_id:
                row = r
                break
        
        if row is None:
            return
        current_state = self.gyms_table.item(row, 5).text()
        new_state = 0 if current_state == "Activo" else 1
        
        nombre_gimnasio = self.gyms_table.item(row, 1).text()
        action = "desactivar" if current_state == "Activo" else "activar"
        
        reply = QMessageBox.question(self, "Confirmar", 
                                    f"¿Está seguro que desea {action} el gimnasio '{nombre_gimnasio}'?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.cur.execute("UPDATE usuarios SET activo = ? WHERE id = ?", (new_state, self.selected_gym_id))
                self.conn.commit()
                
                QMessageBox.information(self, "Éxito", f"Gimnasio '{nombre_gimnasio}' {action}do correctamente.")
                self.clear_gym_form()
                self.load_gyms()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al {action} gimnasio: {str(e)}")
    
    def setup_licenses_page(self, page):
        """Configura la página de gestión de licencias"""
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título de la sección
        title_label = QLabel("Gestión de Licencias")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Formulario para añadir/editar licencias
        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QFormLayout(form_frame)
        
        # Selector de gimnasio
        self.license_gym_combo = QComboBox()
        self.update_gym_combo()
        
        # Tipo de licencia
        self.license_type_combo = QComboBox()
        self.license_type_combo.addItems(["Mensual", "Trimestral", "Semestral", "Anual"])
        
        # Fecha de inicio
        self.license_start_date = QDateEdit()
        self.license_start_date.setCalendarPopup(True)
        self.license_start_date.setDate(QDate.currentDate())
        
        # Precio
        self.license_price_input = QLineEdit()
        
        form_layout.addRow("Gimnasio:", self.license_gym_combo)
        form_layout.addRow("Tipo de Licencia:", self.license_type_combo)
        form_layout.addRow("Fecha de Inicio:", self.license_start_date)
        form_layout.addRow("Precio:", self.license_price_input)
        
        layout.addWidget(form_frame)
        
        # Botones para gestionar licencias
        button_layout = QHBoxLayout()
        
        self.add_license_button = QPushButton("Añadir Licencia")
        self.add_license_button.clicked.connect(self.add_license)
        
        self.revoke_license_button = QPushButton("Revocar Licencia")
        self.revoke_license_button.clicked.connect(self.revoke_license)
        self.revoke_license_button.setEnabled(False)
        
        self.clear_license_button = QPushButton("Limpiar")
        self.clear_license_button.clicked.connect(self.clear_license_form)
        
        button_layout.addWidget(self.add_license_button)
        button_layout.addWidget(self.revoke_license_button)
        button_layout.addWidget(self.clear_license_button)
        
        layout.addLayout(button_layout)
        
        # Tabla de licencias
        self.licenses_table = QTableWidget()
        self.licenses_table.setColumnCount(7)
        self.licenses_table.setHorizontalHeaderLabels([
            "ID", "Gimnasio", "Tipo", "Fecha Inicio", "Fecha Vencimiento", "Precio", "Estado"
        ])
        self.licenses_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.licenses_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.licenses_table.cellClicked.connect(self.select_license)
        self.licenses_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.licenses_table)
        
        # Cargar datos en la tabla
        self.load_licenses()
    
    def update_gym_combo(self):
        """Actualiza el combo box de gimnasios"""
        self.license_gym_combo.clear()
        
        self.cur.execute("""
            SELECT id, nombre_gimnasio
            FROM usuarios
            WHERE tipo = 'gimnasio' AND activo = 1
            ORDER BY nombre_gimnasio
        """)
        
        gyms = self.cur.fetchall()
        
        for gym_id, gym_name in gyms:
            self.license_gym_combo.addItem(gym_name, gym_id)
    
    def load_licenses(self):
        """Carga la lista de licencias en la tabla"""
        self.cur.execute("""
            SELECT l.id, u.nombre_gimnasio, l.tipo, l.fecha_inicio, l.fecha_vencimiento, l.precio, l.activa
            FROM licencias l
            JOIN usuarios u ON l.usuario_id = u.id
            ORDER BY l.fecha_vencimiento DESC
        """)
        
        licenses = self.cur.fetchall()
        
        self.licenses_table.setRowCount(0)  # Limpiar tabla
        
        for row_idx, license in enumerate(licenses):
            self.licenses_table.insertRow(row_idx)
            
            for col_idx, value in enumerate(license):
                # Formatear precio
                if col_idx == 5:
                    value = f"${value:.2f}"
                
                # Formatear estado
                if col_idx == 6:
                    value = "Activa" if value == 1 else "Revocada"
                
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                
                # Colorear según el estado
                if col_idx == 6:
                    if value == "Activa":
                        item.setForeground(QColor("#2ecc71"))
                    else:
                        item.setForeground(QColor("#e74c3c"))
                
                self.licenses_table.setItem(row_idx, col_idx, item)
    
    def clear_license_form(self):
        """Limpia el formulario de licencias"""
        if self.license_gym_combo.count() > 0:
            self.license_gym_combo.setCurrentIndex(0)
        
        self.license_type_combo.setCurrentIndex(0)
        self.license_start_date.setDate(QDate.currentDate())
        self.license_price_input.clear()
        
        self.add_license_button.setEnabled(True)
        self.revoke_license_button.setEnabled(False)
        
        # Limpiar selección de la tabla
        self.licenses_table.clearSelection()
        if hasattr(self, 'selected_license_id'):
            del self.selected_license_id
    
    def select_license(self, row, column):
        """Selecciona una licencia de la tabla"""
        self.selected_license_id = int(self.licenses_table.item(row, 0).text())
        self.selected_license_state = self.licenses_table.item(row, 6).text()
        
        # Activar botones según estado
        self.add_license_button.setEnabled(True)
        self.revoke_license_button.setEnabled(self.selected_license_state == "Activa")
    
    def add_license(self):
        """Añade una nueva licencia a un gimnasio"""
        # Obtener datos del formulario
        if self.license_gym_combo.count() == 0:
            QMessageBox.warning(self, "Error", "No hay gimnasios activos disponibles.")
            return
        
        gym_id = self.license_gym_combo.currentData()
        license_type = self.license_type_combo.currentText()
        start_date = self.license_start_date.date().toString("yyyy-MM-dd")
        
        # Calcular fecha de vencimiento según tipo
        days_mapping = {
            "Mensual": 30,
            "Trimestral": 90,
            "Semestral": 180,
            "Anual": 365
        }
        
        days = days_mapping.get(license_type, 30)
        end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=days)).strftime("%Y-%m-%d")
        
        # Verificar precio
        price_text = self.license_price_input.text().strip()
        if not price_text:
            QMessageBox.warning(self, "Error", "Debe ingresar un precio.")
            return
        
        try:
            price = float(price_text)
            if price <= 0:
                QMessageBox.warning(self, "Error", "El precio debe ser mayor que cero.")
                return
        except ValueError:
            QMessageBox.warning(self, "Error", "El precio debe ser un número válido.")
            return
        
        try:
            # Verificar si ya existe una licencia activa
            self.cur.execute("""
                SELECT id FROM licencias
                WHERE usuario_id = ? AND activa = 1
            """, (gym_id,))
            
            existing_license = self.cur.fetchone()
            
            if existing_license:
                reply = QMessageBox.question(self, "Confirmar", 
                                           "Este gimnasio ya tiene una licencia activa. ¿Desea revocar la anterior y crear una nueva?",
                                           QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Revocar licencia anterior
                    self.cur.execute("""
                        UPDATE licencias
                        SET activa = 0
                        WHERE usuario_id = ? AND activa = 1
                    """, (gym_id,))
                else:
                    return
            
            # Insertar nueva licencia
            self.cur.execute("""
                INSERT INTO licencias (usuario_id, tipo, fecha_inicio, fecha_vencimiento, precio, activa)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (gym_id, license_type, start_date, end_date, price))
            
            self.conn.commit()
            
            gym_name = self.license_gym_combo.currentText()
            QMessageBox.information(self, "Éxito", f"Licencia {license_type} añadida al gimnasio '{gym_name}' correctamente.")
            
            self.clear_license_form()
            self.load_licenses()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al añadir licencia: {str(e)}")
    
    def revoke_license(self):
        """Revoca una licencia activa"""
        if not hasattr(self, 'selected_license_id') or self.selected_license_state != "Activa":
            return
        
        row = None
        for r in range(self.licenses_table.rowCount()):
            if int(self.licenses_table.item(r, 0).text()) == self.selected_license_id:
                row = r
                break
        
        if row is None:
            return
        
        gym_name = self.licenses_table.item(row, 1).text()
        license_type = self.licenses_table.item(row, 2).text()
        
        reply = QMessageBox.question(self, "Confirmar", 
                                   f"¿Está seguro que desea revocar la licencia {license_type} del gimnasio '{gym_name}'?",
                                   QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.cur.execute("UPDATE licencias SET activa = 0 WHERE id = ?", (self.selected_license_id,))
                self.conn.commit()
                
                QMessageBox.information(self, "Éxito", f"Licencia revocada correctamente.")
                self.clear_license_form()
                self.load_licenses()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al revocar licencia: {str(e)}")
    
    def setup_stats_page(self, page):
        """Configura la página de estadísticas"""
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título de la sección
        title_label = QLabel("Estadísticas del Sistema")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Panel de estadísticas generales
        stats_frame = QFrame()
        stats_frame.setFrameShape(QFrame.Shape.StyledPanel)
        stats_layout = QGridLayout(stats_frame)
        
        # Obtener estadísticas
        self.cur.execute("SELECT COUNT(*) FROM usuarios WHERE tipo = 'gimnasio'")
        total_gyms = self.cur.fetchone()[0]
        
        self.cur.execute("SELECT COUNT(*) FROM usuarios WHERE tipo = 'gimnasio' AND activo = 1")
        active_gyms = self.cur.fetchone()[0]
        
        self.cur.execute("SELECT COUNT(*) FROM licencias WHERE activa = 1")
        active_licenses = self.cur.fetchone()[0]
        
        # Calcular ingresos totales
        self.cur.execute("SELECT SUM(precio) FROM licencias")
        total_revenue = self.cur.fetchone()[0] or 0
        
        # Agregar datos al grid
        stats_layout.addWidget(QLabel("Total de Gimnasios:"), 0, 0)
        stats_layout.addWidget(QLabel(str(total_gyms)), 0, 1)
        
        stats_layout.addWidget(QLabel("Gimnasios Activos:"), 1, 0)
        stats_layout.addWidget(QLabel(f"{active_gyms} ({active_gyms/total_gyms*100:.1f}% del total)" if total_gyms > 0 else "0"), 1, 1)
        
        stats_layout.addWidget(QLabel("Licencias Activas:"), 2, 0)
        stats_layout.addWidget(QLabel(str(active_licenses)), 2, 1)
        
        stats_layout.addWidget(QLabel("Ingresos Totales:"), 3, 0)
        stats_layout.addWidget(QLabel(f"${total_revenue:.2f}"), 3, 1)
        
        layout.addWidget(stats_frame)
        
        # Botones para exportar informes
        reports_frame = QFrame()
        reports_frame.setFrameShape(QFrame.Shape.StyledPanel)
        reports_layout = QVBoxLayout(reports_frame)
        
        export_title = QLabel("Exportar Informes")
        export_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        reports_layout.addWidget(export_title)
        
        export_gyms_button = QPushButton("Exportar Lista de Gimnasios")
        export_gyms_button.clicked.connect(self.export_gyms_report)
        
        export_licenses_button = QPushButton("Exportar Informe de Licencias")
        export_licenses_button.clicked.connect(self.export_licenses_report)
        
        reports_layout.addWidget(export_gyms_button)
        reports_layout.addWidget(export_licenses_button)
        
        layout.addWidget(reports_frame)
        layout.addStretch()
    
    def export_gyms_report(self):
        """Exporta un informe de gimnasios a CSV"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Informe de Gimnasios", "", "CSV Files (*.csv)")
        
        if not file_path:
            return
        
        try:
            self.cur.execute("""
                SELECT id, nombre_gimnasio, username, email, fecha_registro, 
                       ultimo_acceso, activo
                FROM usuarios
                WHERE tipo = 'gimnasio'
                ORDER BY nombre_gimnasio
            """)
            
            gyms = self.cur.fetchall()
            
            with open(file_path, 'w', newline='') as file:
                import csv
                writer = csv.writer(file)
                # Escribir encabezados
                writer.writerow(["ID", "Nombre", "Usuario", "Email", "Fecha Registro", 
                               "Último Acceso", "Estado"])
                
                # Escribir datos
                for gym in gyms:
                    # Formatear estado
                    row = list(gym)
                    row[6] = "Activo" if row[6] == 1 else "Inactivo"
                    writer.writerow(row)
            
            QMessageBox.information(self, "Exportación Exitosa", f"Informe exportado a {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar informe: {str(e)}")
    
    def export_licenses_report(self):
        """Exporta un informe de licencias a CSV"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Informe de Licencias", "", "CSV Files (*.csv)")
        
        if not file_path:
            return
        
        try:
            self.cur.execute("""
                SELECT l.id, u.nombre_gimnasio, l.tipo, l.fecha_inicio, 
                       l.fecha_vencimiento, l.precio, l.activa
                FROM licencias l
                JOIN usuarios u ON l.usuario_id = u.id
                ORDER BY l.fecha_vencimiento DESC
            """)
            
            licenses = self.cur.fetchall()
            
            with open(file_path, 'w', newline='') as file:
                import csv
                writer = csv.writer(file)
                # Escribir encabezados
                writer.writerow(["ID", "Gimnasio", "Tipo", "Fecha Inicio", 
                               "Fecha Vencimiento", "Precio", "Estado"])
                
                # Escribir datos
                for license in licenses:
                    # Formatear estado
                    row = list(license)
                    row[6] = "Activa" if row[6] == 1 else "Revocada"
                    writer.writerow(row)
            
            QMessageBox.information(self, "Exportación Exitosa", f"Informe exportado a {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar informe: {str(e)}")
    
    def setup_settings_page(self, page):
        """Configura la página de configuración"""
        layout = QVBoxLayout(page)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título de la sección
        title_label = QLabel("Configuración de la Cuenta")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Panel de cambio de contraseña
        password_frame = QFrame()
        password_frame.setFrameShape(QFrame.Shape.StyledPanel)
        password_layout = QVBoxLayout(password_frame)
        
        password_title = QLabel("Cambiar Contraseña")
        password_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        password_layout.addWidget(password_title)
        
        form_layout = QFormLayout()
        
        self.current_password_input = QLineEdit()
        self.current_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        form_layout.addRow("Contraseña Actual:", self.current_password_input)
        form_layout.addRow("Nueva Contraseña:", self.new_password_input)
        form_layout.addRow("Confirmar Contraseña:", self.confirm_password_input)
        
        password_layout.addLayout(form_layout)
        
        change_password_button = QPushButton("Cambiar Contraseña")
        change_password_button.clicked.connect(self.change_password)
        password_layout.addWidget(change_password_button)
        
        layout.addWidget(password_frame)
        
        # Información del sistema
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_layout = QVBoxLayout(info_frame)
        
        info_title = QLabel("Información del Sistema")
        info_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        info_layout.addWidget(info_title)
        
        version_label = QLabel("Versión: FIT APP 1.0")
        build_label = QLabel("Build: 2025.03.01")
        license_label = QLabel("Licencia: Comercial")
        
        info_layout.addWidget(version_label)
        info_layout.addWidget(build_label)
        info_layout.addWidget(license_label)
        
        layout.addWidget(info_frame)
        layout.addStretch()
    
    def change_password(self):
        """Cambia la contraseña del administrador"""
        current_password = self.current_password_input.text()
        new_password = self.new_password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        if not current_password or not new_password or not confirm_password:
            QMessageBox.warning(self, "Error", "Todos los campos son obligatorios.")
            return
        
        if new_password != confirm_password:
            QMessageBox.warning(self, "Error", "Las nuevas contraseñas no coinciden.")
            return
        
        if len(new_password) < 6:
            QMessageBox.warning(self, "Error", "La nueva contraseña debe tener al menos 6 caracteres.")
            return
        
        try:
            # Verificar contraseña actual
            self.cur.execute("SELECT password FROM usuarios WHERE id = ?", (self.user_id,))
            stored_password = self.cur.fetchone()[0]
            
            if not verify_password(current_password, stored_password):
                QMessageBox.warning(self, "Error", "La contraseña actual es incorrecta.")
                return
            
            # Actualizar contraseña
            hashed_new_password = hash_password(new_password)
            self.cur.execute("UPDATE usuarios SET password = ? WHERE id = ?", (hashed_new_password, self.user_id))
            self.conn.commit()
            
            QMessageBox.information(self, "Éxito", "Contraseña actualizada correctamente.")
            
            # Limpiar campos
            self.current_password_input.clear()
            self.new_password_input.clear()
            self.confirm_password_input.clear()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al cambiar contraseña: {str(e)}")
    
    def closeEvent(self, event):
        """Maneja el cierre de la ventana"""
        # Cerrar conexión a la base de datos
        if hasattr(self, 'conn'):
            self.conn.close()
        
        event.accept()


class GymApp(QMainWindow):
    """Aplicación principal para los gimnasios"""
    def __init__(self, user_id, user_type, gym_name):
        super().__init__()
        
        # Almacenar información del usuario
        self.user_id = user_id
        self.user_type = user_type
        self.gym_name = gym_name
        
        # Configurar la ventana principal
        self.setWindowTitle(f"FIT APP - {gym_name}")
        self.setGeometry(100, 100, 1200, 700)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
            }
            QTabWidget {
                background-color: #2d2d2d;
            }
            QTabBar::tab {
                background-color: #1e1e1e;
                color: #ffffff;
                padding: 8px 16px;
                border: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #3d3d3d;
            }
            QPushButton {
                background-color: #221e5c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3b347e;
            }
            QPushButton:disabled {
                background-color: #7f8c8d;
            }
            QLineEdit, QComboBox {
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3d3d3d;
                padding: 5px;
                border-radius: 4px;
            }
            QTableWidget {
                background-color: #2d2d2d;
                alternate-background-color: #3d3d3d;
                color: white;
                gridline-color: #3d3d3d;
                border: none;
            }
            QHeaderView::section {
                background-color: #221e5c;
                color: white;
                padding: 5px;
                border: none;
            }
            QFrame {
                background-color: #2d2d2d;
                border-radius: 4px;
                padding: 10px;
            }
            QListWidget {
                background-color: #1e1e1e;
                color: white;
                border: none;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 10px;
                border-radius: 0px;
            }
            QListWidget::item:selected {
                background-color: #221e5c;
            }
            QListWidget::item:hover {
                background-color: #3d3d3d;
            }
        """)
        
        # Inicializar la base de datos
        self.init_database()
        
        # Configurar la interfaz
        self.setup_ui()
        
    def init_database(self):
        """Inicializa la conexión a la base de datos y crea las tablas si no existen"""
        self.conn = sqlite3.connect('gym.db')
        self.cur = self.conn.cursor()
        
        # Crear tabla de planes
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS planes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                descripcion TEXT,
                precio REAL NOT NULL
            )
        ''')
        
        # Crear tabla de socios
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS socios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL,
                apellido TEXT NOT NULL,
                dni TEXT UNIQUE NOT NULL,
                telefono TEXT,
                plan_id INTEGER,
                fecha_registro TEXT NOT NULL,
                fecha_vencimiento TEXT NOT NULL,
                estado_cuota TEXT NOT NULL,
                gimnasio_id INTEGER,
                FOREIGN KEY (plan_id) REFERENCES planes (id),
                FOREIGN KEY (gimnasio_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Crear tabla de asistencias
        self.cur.execute('''
            CREATE TABLE IF NOT EXISTS asistencias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                socio_id INTEGER,
                fecha TEXT NOT NULL,
                FOREIGN KEY (socio_id) REFERENCES socios (id)
            )
        ''')   
        
        # Verificar si la columna plan_id existe en la tabla socios, y si no, añadirla
        try:
            self.cur.execute("SELECT plan_id FROM socios LIMIT 1")
        except sqlite3.OperationalError:
            # Si ocurre un error, significa que la columna no existe
            self.cur.execute("ALTER TABLE socios ADD COLUMN plan_id INTEGER")
            self.conn.commit()
            print("Columna plan_id añadida a la tabla socios")
        
        # Verificar si la columna gimnasio_id existe en la tabla socios, y si no, añadirla
        try:
            self.cur.execute("SELECT gimnasio_id FROM socios LIMIT 1")
        except sqlite3.OperationalError:
            # Si ocurre un error, significa que la columna no existe
            self.cur.execute("ALTER TABLE socios ADD COLUMN gimnasio_id INTEGER")
            self.conn.commit()
            print("Columna gimnasio_id añadida a la tabla socios")
        
        # Insertar plan básico si no existe ninguno
        self.cur.execute("SELECT COUNT(*) FROM planes")
        if self.cur.fetchone()[0] == 0:
            self.cur.execute('''
                INSERT INTO planes (nombre, descripcion, precio)
                VALUES (?, ?, ?)
            ''', ("Plan Básico", "Acceso a todas las instalaciones", 5000.0))
        
        self.conn.commit()
        
    def setup_ui(self):
        """Configura la interfaz de usuario principal"""
        # Widget central y layout principal
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Panel izquierdo (menú lateral)
        left_panel = QWidget()
        left_panel.setFixedWidth(250)
        left_panel.setStyleSheet("background-color: #1e1e1e;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        # Logo en la parte superior del panel izquierdo
        logo_container = QWidget()
        logo_container.setFixedHeight(100)
        logo_container.setStyleSheet("background-color: #1a1a1a; border-bottom: 1px solid #3d3d3d;")
        logo_layout = QHBoxLayout(logo_container)
        
        # Crear un QLabel para el logo
        logo_label = QLabel()
        logo_label.setText("FIT APP")
        logo_label.setStyleSheet("color: #FFF; font-size: 22px; font-weight: bold;")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_layout.addWidget(logo_label)
        
        left_layout.addWidget(logo_container)
        
        # Menú de navegación
        self.menu_list = QListWidget()
        self.menu_list.setIconSize(QSize(24, 24))
        self.menu_list.setSpacing(5)
        
        # Agregar opciones de menú para gimnasios
        menu_items = [
            ("Control de Acceso", "access_tab"),
            ("Gestión de Socios", "members_tab"),
            ("Gestión de Planes", "plans_tab"),
            ("Informes", "reports_tab")
        ]
        
        for text, page_name in menu_items:
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, page_name)
            self.menu_list.addItem(item)
        
        left_layout.addWidget(self.menu_list)
        
        # Widget para mostrar información en la parte inferior del menú
        info_widget = QWidget()
        info_widget.setFixedHeight(100)
        info_widget.setStyleSheet("background-color: #1a1a1a; border-top: 1px solid #3d3d3d;")
        info_layout = QVBoxLayout(info_widget)
        
        # Obtener información de licencia
        conn = sqlite3.connect('fitapp.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT fecha_vencimiento FROM licencias
            WHERE usuario_id = ? AND activa = 1
            ORDER BY fecha_vencimiento DESC
            LIMIT 1
        """, (self.user_id,))
        
        license_info = cursor.fetchone()
        conn.close()
        
        gym_label = QLabel(f"Gimnasio: {self.gym_name}")
        gym_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        gym_label.setStyleSheet("color: #ffffff;")
        info_layout.addWidget(gym_label)
        
        if license_info:
            fecha_venc = license_info[0]
            days_left = (datetime.strptime(fecha_venc, "%Y-%m-%d") - datetime.now()).days
            license_label = QLabel(f"Licencia: {days_left} días restantes")
            license_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            license_label.setStyleSheet(f"color: {'#2ecc71' if days_left > 30 else '#f39c12'};")
            info_layout.addWidget(license_label)
        
        version_label = QLabel("FIT APP v1.0")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #7f8c8d;")
        info_layout.addWidget(version_label)
        
        left_layout.addWidget(info_widget)
        
        # Panel derecho (contenido)
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra superior
        top_bar = QWidget()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet("background-color: #2d2d2d; border-bottom: 1px solid #3d3d3d;")
        top_bar_layout = QHBoxLayout(top_bar)
        
        self.page_title = QLabel("Control de Acceso")
        self.page_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        top_bar_layout.addWidget(self.page_title)
        
        top_bar_layout.addStretch()
        
        # Botón de cerrar sesión
        logout_button = QPushButton("Cerrar Sesión")
        logout_button.setFixedWidth(120)
        logout_button.clicked.connect(self.logout)
        top_bar_layout.addWidget(logout_button)
        
        right_layout.addWidget(top_bar)
        
        # Contenido principal (páginas apiladas)
        self.content_stack = QStackedWidget()
        
        # Configurar páginas para gimnasios
        self.access_tab = QWidget()
        self.setup_access_tab(self.access_tab)
        self.content_stack.addWidget(self.access_tab)
        
        self.members_tab = QWidget()
        self.setup_members_tab(self.members_tab)
        self.content_stack.addWidget(self.members_tab)
        
        self.plans_tab = QWidget()
        self.setup_plans_tab(self.plans_tab)
        self.content_stack.addWidget(self.plans_tab)
        
        self.reports_tab = QWidget()
        self.setup_reports_tab(self.reports_tab)
        self.content_stack.addWidget(self.reports_tab)
        
        right_layout.addWidget(self.content_stack)
        
        # Agregar paneles al layout principal
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)
        
        # Conectar eventos
        self.menu_list.currentRowChanged.connect(self.change_page)
        self.menu_list.setCurrentRow(0)  # Seleccionar la primera opción por defecto
    
    def logout(self):
        """Cierra la sesión actual y regresa a la pantalla de login."""
        reply = QMessageBox.question(self, "Cerrar Sesión", 
                                    "¿Está seguro que desea cerrar la sesión?",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            self.close()
            # El flujo regresará al main() que mostrará nuevamente la ventana de login
    
    def change_page(self, index):
        """Cambia la página mostrada en el contenido principal"""
        # Cambiar el título de la página
        self.page_title.setText(self.menu_list.item(index).text())
        # Cambiar la página mostrada
        self.content_stack.setCurrentIndex(index)
        
    def setup_access_tab(self, tab):
        """Configura la pestaña de control de acceso"""
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title_label = QLabel("CONTROL DE ACCESO")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 20px;")
        layout.addWidget(title_label)
        
        # Entrada de DNI
        form_layout = QFormLayout()
        self.dni_input = QLineEdit()
        self.dni_input.setPlaceholderText("Ingrese DNI...")
        self.dni_input.setMaximumWidth(300)
        self.dni_input.returnPressed.connect(self.verify_member)
        
        self.plan_desc_label = QLabel("")
        self.plan_desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plan_desc_label.setStyleSheet("font-size: 14px; font-style: italic;")
        form_layout.addRow("DNI:", self.dni_input)
        
        form_container = QWidget()
        form_container.setLayout(form_layout)
        form_container.setMaximumWidth(500)
        
        form_hlayout = QHBoxLayout()
        form_hlayout.addWidget(form_container)
        form_hlayout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(form_hlayout)
        
        # Botón de verificar
        verify_button = QPushButton("Verificar")
        verify_button.clicked.connect(self.verify_member)
        verify_button.setMaximumWidth(500)
        
        button_layout = QHBoxLayout()
        button_layout.addWidget(verify_button)
        button_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(button_layout)
        
        # Resultado
        result_frame = QFrame()
        result_frame.setFrameShape(QFrame.Shape.StyledPanel)
        result_frame.setFixedSize(400, 300)  # Establece el tamaño exacto (ancho x alto)
        result_layout = QVBoxLayout(result_frame)
        
        self.member_name_label = QLabel("")
        self.member_name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.member_name_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        self.quota_status_label = QLabel("")
        self.quota_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quota_status_label.setStyleSheet("font-size: 16px;")
        
        self.plan_desc_label = QLabel("")
        self.plan_desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.plan_desc_label.setStyleSheet("font-size: 14px; font-style: italic;")
        
        result_layout.addWidget(self.member_name_label)
        result_layout.addWidget(self.quota_status_label)
        result_layout.addWidget(self.plan_desc_label)
        
        result_container = QHBoxLayout()
        result_container.addWidget(result_frame)
        result_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(result_container)
        layout.addStretch()
        
    def verify_member(self):
        """Verifica el estado de un socio por su DNI"""
        dni = self.dni_input.text().strip()
        
        if not dni:
            QMessageBox.warning(self, "Error", "Debe ingresar un DNI.")
            return
        
        try:
            self.cur.execute('''
                SELECT s.id, s.nombre, s.apellido, s.fecha_vencimiento, s.estado_cuota, 
                    p.nombre as plan_nombre, p.descripcion as plan_descripcion
                FROM socios s
                LEFT JOIN planes p ON s.plan_id = p.id
                WHERE s.dni = ? AND s.gimnasio_id = ?
            ''', (dni, self.user_id))
            
            member = self.cur.fetchone()
            
            if not member:
                self.member_name_label.setText("Socio no encontrado")
                self.quota_status_label.setText("")
                self.plan_desc_label.setText("")
                return
            
            member_id, nombre, apellido, fecha_vencimiento, estado_cuota, plan_nombre, plan_descripcion = member
            
            # Registrar asistencia
            fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cur.execute("INSERT INTO asistencias (socio_id, fecha) VALUES (?, ?)", 
                           (member_id, fecha_actual))
            self.conn.commit()
            
            # Mostrar nombre del socio y plan
            self.member_name_label.setText(f"{nombre} {apellido}")
            if plan_nombre:
                self.member_name_label.setText(f"{nombre} {apellido} - {plan_nombre}")
            
            if plan_descripcion:
                self.plan_desc_label.setText(f"{plan_descripcion}")
            else:
                self.plan_desc_label.setText("")
            
            # Verificar estado de cuota
            if estado_cuota == "No Pagada":
                self.quota_status_label.setText("Cuota no pagada")
                self.quota_status_label.setStyleSheet("font-size: 16px; color: #e74c3c; font-weight: bold;")
            else:
                # Calcular días restantes
                fecha_venc = datetime.strptime(fecha_vencimiento, "%Y-%m-%d")
                fecha_actual = datetime.now()
                dias_restantes = (fecha_venc - fecha_actual).days
                
                if dias_restantes <= 0:
                    # Actualizar estado a no pagada si venció
                    self.cur.execute('''
                        UPDATE socios
                        SET estado_cuota = 'No Pagada'
                        WHERE id = ?
                    ''', (member_id,))
                    self.conn.commit()
                    
                    self.quota_status_label.setText("Cuota vencida")
                    self.quota_status_label.setStyleSheet("font-size: 16px; color: #e74c3c; font-weight: bold;")
                elif dias_restantes <= 10:
                    self.quota_status_label.setText(f"Vence en {dias_restantes} días")
                    self.quota_status_label.setStyleSheet("font-size: 16px; color: #f39c12; font-weight: bold;")
                else:
                    self.quota_status_label.setText("Cuota al día")
                    self.quota_status_label.setStyleSheet("font-size: 16px; color: #2ecc71; font-weight: bold;")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al verificar socio: {str(e)}")
    
    def update_plan_combo(self):
        """Actualiza el combo box de planes"""
        self.plan_combo.clear()
        
        self.cur.execute("SELECT nombre FROM planes ORDER BY nombre")
        planes = self.cur.fetchall()
        
        for plan in planes:
            self.plan_combo.addItem(plan[0])
    
    def setup_members_tab(self, tab):
        """Configura la pestaña de gestión de socios"""
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 40, 20, 40)
        
        # Formulario de registro/edición
        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QFormLayout(form_frame)
        
        self.nombre_input = QLineEdit()
        self.apellido_input = QLineEdit()
        self.member_dni_input = QLineEdit()
        self.telefono_input = QLineEdit()
        
        # Aquí creamos el combo de planes UNA SOLA VEZ
        self.plan_combo = QComboBox()
        # Aumentar el ancho mínimo del combo box
        self.plan_combo.setMinimumWidth(300)  # Aumentar el ancho
        # Aumentar la altura
        self.plan_combo.setMinimumHeight(30)
        # Aplicar el estilo para mejorar la legibilidad
        self.plan_combo.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                padding: 6px 8px;
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: white;
                selection-background-color: #221e5c;
                padding: 8px;
            }
        """)
        # Luego actualizamos su contenido
        self.update_plan_combo()
        
        # También podemos aplicar formato similar al selector de estado de cuota
        self.estado_cuota = QComboBox()
        self.estado_cuota.setMinimumWidth(300)
        self.estado_cuota.setMinimumHeight(30)
        self.estado_cuota.setStyleSheet("""
            QComboBox {
                font-size: 14px;
                padding: 6px 8px;
                background-color: #2d2d2d;
                color: white;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                color: white;
                selection-background-color: #221e5c;
                padding: 8px;
            }
        """)
        self.estado_cuota.addItems(["Pagada", "No Pagada"])
        
        form_layout.addRow("Nombre:", self.nombre_input)
        form_layout.addRow("Apellido:", self.apellido_input)
        form_layout.addRow("DNI:", self.member_dni_input)
        form_layout.addRow("Teléfono:", self.telefono_input)
        form_layout.addRow("Plan:", self.plan_combo)
        form_layout.addRow("Estado Cuota:", self.estado_cuota)
        
        button_layout = QHBoxLayout()
        
        self.add_button = QPushButton("Registrar Socio")
        self.add_button.clicked.connect(self.add_member)
        
        self.update_button = QPushButton("Actualizar Socio")
        self.update_button.clicked.connect(self.update_member)
        self.update_button.setEnabled(False)
        
        self.delete_button = QPushButton("Eliminar Socio")
        self.delete_button.clicked.connect(self.delete_member)
        self.delete_button.setEnabled(False)
        
        self.clear_button = QPushButton("Limpiar")
        self.clear_button.clicked.connect(self.clear_form)
        
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addWidget(self.clear_button)
        
        layout.addWidget(form_frame)
        layout.addLayout(button_layout)
        
        # Tabla de socios
        self.members_table = QTableWidget()
        self.members_table.setColumnCount(8)
        self.members_table.setHorizontalHeaderLabels([
            "ID", "Nombre", "Apellido", "DNI", "Teléfono", "Fecha Vencimiento", "Estado Cuota", "Plan"
        ])
        self.members_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.members_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.members_table.cellClicked.connect(self.select_member)
        self.members_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.members_table)
        
        # Cargar datos en la tabla
        self.load_members()
        
    def clear_form(self):
        """Limpia el formulario de socios"""
        self.nombre_input.clear()
        self.apellido_input.clear()
        self.member_dni_input.clear()
        self.telefono_input.clear()
        self.estado_cuota.setCurrentIndex(0)
        
        self.add_button.setEnabled(True)
        self.update_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        
        # Limpiar selección de la tabla
        self.members_table.clearSelection()
        self.selected_member_id = None
        
    def load_members(self):
        """Carga la lista de socios en la tabla"""
        self.cur.execute("""
            SELECT s.id, s.nombre, s.apellido, s.dni, s.telefono, s.fecha_vencimiento, s.estado_cuota, p.nombre 
            FROM socios s
            LEFT JOIN planes p ON s.plan_id = p.id
            WHERE s.gimnasio_id = ?
        """, (self.user_id,))
        members = self.cur.fetchall()
        
        self.members_table.setRowCount(0)  # Limpiar tabla
        
        for row_idx, member in enumerate(members):
            self.members_table.insertRow(row_idx)
            
            for col_idx, value in enumerate(member):
                item = QTableWidgetItem(str(value))
                # Aplicar color según el estado de la cuota
                if col_idx == 6:  # Columna de estado de cuota
                    if value == "Pagada":
                        item.setForeground(QColor("#2ecc71"))  # Verde para pagada
                    else:
                        item.setForeground(QColor("#e74c3c"))  # Rojo para no pagada
                
                # Hacer las celdas no editables
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.members_table.setItem(row_idx, col_idx, item)
    
    def select_member(self, row, column):
        """Selecciona un socio de la tabla para editar"""
        self.selected_member_id = int(self.members_table.item(row, 0).text())
        
        # Cargar datos en el formulario
        self.nombre_input.setText(self.members_table.item(row, 1).text())
        self.apellido_input.setText(self.members_table.item(row, 2).text())
        self.member_dni_input.setText(self.members_table.item(row, 3).text())
        self.telefono_input.setText(self.members_table.item(row, 4).text())
        
        # Seleccionar el plan
        plan_nombre = self.members_table.item(row, 7).text()
        for i in range(self.plan_combo.count()):
            if self.plan_combo.itemText(i) == plan_nombre:
                self.plan_combo.setCurrentIndex(i)
                break
        
        estado = self.members_table.item(row, 6).text()
        index = 0 if estado == "Pagada" else 1
        self.estado_cuota.setCurrentIndex(index)
        
        # Activar botones
        self.add_button.setEnabled(False)
        self.update_button.setEnabled(True)
        self.delete_button.setEnabled(True)
    
    def add_member(self):
        """Agrega un nuevo socio a la base de datos"""
        nombre = self.nombre_input.text().strip()
        apellido = self.apellido_input.text().strip()
        dni = self.member_dni_input.text().strip()
        telefono = self.telefono_input.text().strip()
        estado_cuota = self.estado_cuota.currentText()
        
        # Obtener el ID del plan seleccionado
        plan_nombre = self.plan_combo.currentText()
        self.cur.execute("SELECT id FROM planes WHERE nombre = ?", (plan_nombre,))
        plan_id = self.cur.fetchone()[0]
        
        # Validación básica
        if not nombre or not apellido or not dni:
            QMessageBox.warning(self, "Error", "Los campos Nombre, Apellido y DNI son obligatorios.")
            return
        
        try:
            # Verificar si el DNI ya existe
            self.cur.execute("SELECT id FROM socios WHERE dni = ?", (dni,))
            if self.cur.fetchone():
                QMessageBox.warning(self, "Error", f"Ya existe un socio con el DNI {dni}.")
                return
            
            # Fechas de registro y vencimiento
            fecha_registro = datetime.now().strftime("%Y-%m-%d")
            fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            
            # Insertar nuevo socio
            self.cur.execute('''
                INSERT INTO socios (nombre, apellido, dni, telefono, plan_id, fecha_registro, fecha_vencimiento, estado_cuota, gimnasio_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nombre, apellido, dni, telefono, plan_id, fecha_registro, fecha_vencimiento, estado_cuota, self.user_id))
            
            self.conn.commit()
            
            QMessageBox.information(self, "Éxito", "Socio registrado correctamente.")
            self.clear_form()
            self.load_members()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al registrar socio: {str(e)}")
    
    def update_member(self):
        """Actualiza los datos de un socio existente"""
        if not hasattr(self, 'selected_member_id') or not self.selected_member_id:
            return
        
        nombre = self.nombre_input.text().strip()
        apellido = self.apellido_input.text().strip()
        dni = self.member_dni_input.text().strip()
        telefono = self.telefono_input.text().strip()
        estado_cuota = self.estado_cuota.currentText()
        
        # Obtener el ID del plan seleccionado
        plan_nombre = self.plan_combo.currentText()
        self.cur.execute("SELECT id FROM planes WHERE nombre = ?", (plan_nombre,))
        plan_id = self.cur.fetchone()[0]
        
        # Validación básica
        if not nombre or not apellido or not dni:
            QMessageBox.warning(self, "Error", "Los campos Nombre, Apellido y DNI son obligatorios.")
            return
        
        try:
            # Verificar si el DNI pertenece a otro socio
            self.cur.execute("SELECT id FROM socios WHERE dni = ? AND id != ?", (dni, self.selected_member_id))
            if self.cur.fetchone():
                QMessageBox.warning(self, "Error", f"Ya existe otro socio con el DNI {dni}.")
                return
            
            # Si el estado cambia a "Pagada", actualizar la fecha de vencimiento
            if estado_cuota == "Pagada":
                # Obtener el estado actual
                self.cur.execute("SELECT estado_cuota FROM socios WHERE id = ?", (self.selected_member_id,))
                estado_actual = self.cur.fetchone()[0]
                
                if estado_actual == "No Pagada":
                    # Actualizar fecha de vencimiento
                    fecha_vencimiento = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
                    
                    self.cur.execute('''
                        UPDATE socios
                        SET nombre = ?, apellido = ?, dni = ?, telefono = ?, plan_id = ?,
                            fecha_vencimiento = ?, estado_cuota = ?
                        WHERE id = ?
                    ''', (nombre, apellido, dni, telefono, plan_id, fecha_vencimiento, estado_cuota, self.selected_member_id))
                else:
                    # Mantener la fecha de vencimiento actual
                    self.cur.execute('''
                        UPDATE socios
                        SET nombre = ?, apellido = ?, dni = ?, telefono = ?, plan_id = ?, estado_cuota = ?
                        WHERE id = ?
                    ''', (nombre, apellido, dni, telefono, plan_id, estado_cuota, self.selected_member_id))
            else:
                # Actualizar sin cambiar fecha de vencimiento
                self.cur.execute('''
                    UPDATE socios
                    SET nombre = ?, apellido = ?, dni = ?, telefono = ?, plan_id = ?, estado_cuota = ?
                    WHERE id = ?
                ''', (nombre, apellido, dni, telefono, plan_id, estado_cuota, self.selected_member_id))
            
            self.conn.commit()
            
            QMessageBox.information(self, "Éxito", "Socio actualizado correctamente.")
            self.clear_form()
            self.load_members()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar socio: {str(e)}")
    
    def delete_member(self):
        """Elimina un socio de la base de datos"""
        if not hasattr(self, 'selected_member_id') or not self.selected_member_id:
            return
        
        reply = QMessageBox.question(self, "Confirmar", 
                                    "¿Está seguro que desea eliminar este socio? Esta acción no se puede deshacer.",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Eliminar socio
                self.cur.execute("DELETE FROM socios WHERE id = ?", (self.selected_member_id,))
                # Eliminar asistencias asociadas
                self.cur.execute("DELETE FROM asistencias WHERE socio_id = ?", (self.selected_member_id,))
                
                self.conn.commit()
                
                QMessageBox.information(self, "Éxito", "Socio eliminado correctamente.")
                self.clear_form()
                self.load_members()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar socio: {str(e)}")
    
    def setup_plans_tab(self, tab):
        """Configura la pestaña de gestión de planes"""
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Formulario para crear/editar planes
        form_frame = QFrame()
        form_frame.setFrameShape(QFrame.Shape.StyledPanel)
        form_layout = QFormLayout(form_frame)
        
        self.plan_nombre_input = QLineEdit()
        self.plan_descripcion_input = QLineEdit()
        self.plan_precio_input = QLineEdit()
        self.plan_precio_input.setPlaceholderText("Ej: 5000.00")
        
        form_layout.addRow("Nombre:", self.plan_nombre_input)
        form_layout.addRow("Descripción:", self.plan_descripcion_input)
        form_layout.addRow("Precio:", self.plan_precio_input)
        
        button_layout = QHBoxLayout()
        
        self.add_plan_button = QPushButton("Agregar Plan")
        self.add_plan_button.clicked.connect(self.add_plan)
        
        self.update_plan_button = QPushButton("Actualizar Plan")
        self.update_plan_button.clicked.connect(self.update_plan)
        self.update_plan_button.setEnabled(False)
        
        self.delete_plan_button = QPushButton("Eliminar Plan")
        self.delete_plan_button.clicked.connect(self.delete_plan)
        self.delete_plan_button.setEnabled(False)
        
        self.clear_plan_button = QPushButton("Limpiar")
        self.clear_plan_button.clicked.connect(self.clear_plan_form)
        
        button_layout.addWidget(self.add_plan_button)
        button_layout.addWidget(self.update_plan_button)
        button_layout.addWidget(self.delete_plan_button)
        button_layout.addWidget(self.clear_plan_button)
        
        layout.addWidget(form_frame)
        layout.addLayout(button_layout)
        
        # Tabla de planes
        self.plans_table = QTableWidget()
        self.plans_table.setColumnCount(4)
        self.plans_table.setHorizontalHeaderLabels(["ID", "Nombre", "Descripción", "Precio"])
        self.plans_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.plans_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.plans_table.cellClicked.connect(self.select_plan)
        self.plans_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.plans_table)
        
        # Cargar datos en la tabla
        self.load_plans()
    
    def clear_plan_form(self):
        """Limpia el formulario de planes"""
        self.plan_nombre_input.clear()
        self.plan_descripcion_input.clear()
        self.plan_precio_input.clear()
        
        self.add_plan_button.setEnabled(True)
        self.update_plan_button.setEnabled(False)
        self.delete_plan_button.setEnabled(False)
        
        # Limpiar selección de la tabla
        self.plans_table.clearSelection()
        self.selected_plan_id = None
    
    def load_plans(self):
        """Carga la lista de planes en la tabla"""
        self.cur.execute("SELECT id, nombre, descripcion, precio FROM planes")
        planes = self.cur.fetchall()
        
        self.plans_table.setRowCount(0)  # Limpiar tabla
        
        for row_idx, plan in enumerate(planes):
            self.plans_table.insertRow(row_idx)
            
            for col_idx, value in enumerate(plan):
                if col_idx == 3:  # Formatear el precio
                    value = f"${value:.2f}"
                
                item = QTableWidgetItem(str(value))
                # Hacer las celdas no editables
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.plans_table.setItem(row_idx, col_idx, item)
    
    def select_plan(self, row, column):
        """Selecciona un plan de la tabla para editar"""
        self.selected_plan_id = int(self.plans_table.item(row, 0).text())
        
        # Cargar datos en el formulario
        self.plan_nombre_input.setText(self.plans_table.item(row, 1).text())
        self.plan_descripcion_input.setText(self.plans_table.item(row, 2).text())
        
        # Obtener precio sin el símbolo $
        precio_text = self.plans_table.item(row, 3).text().replace('$', '')
        self.plan_precio_input.setText(precio_text)
        
        # Activar botones
        self.add_plan_button.setEnabled(False)
        self.update_plan_button.setEnabled(True)
        self.delete_plan_button.setEnabled(True)
    
    def add_plan(self):
        """Agrega un nuevo plan a la base de datos"""
        nombre = self.plan_nombre_input.text().strip()
        descripcion = self.plan_descripcion_input.text().strip()
        precio_text = self.plan_precio_input.text().strip()
        
        # Validación básica
        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre del plan es obligatorio.")
            return
        
        try:
            precio = float(precio_text)
            if precio <= 0:
                QMessageBox.warning(self, "Error", "El precio debe ser mayor que cero.")
                return
        except ValueError:
            QMessageBox.warning(self, "Error", "El precio debe ser un número válido.")
            return
        
        try:
            # Verificar si el nombre ya existe
            self.cur.execute("SELECT id FROM planes WHERE nombre = ?", (nombre,))
            if self.cur.fetchone():
                QMessageBox.warning(self, "Error", f"Ya existe un plan con el nombre {nombre}.")
                return
            
            # Insertar nuevo plan
            self.cur.execute('''
                INSERT INTO planes (nombre, descripcion, precio)
                VALUES (?, ?, ?)
            ''', (nombre, descripcion, precio))
            
            self.conn.commit()
            
            QMessageBox.information(self, "Éxito", "Plan registrado correctamente.")
            self.clear_plan_form()
            self.load_plans()
            self.update_plan_combo()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al registrar plan: {str(e)}")
    
    def update_plan(self):
        """Actualiza los datos de un plan existente"""
        if not hasattr(self, 'selected_plan_id') or not self.selected_plan_id:
            return
        
        nombre = self.plan_nombre_input.text().strip()
        descripcion = self.plan_descripcion_input.text().strip()
        precio_text = self.plan_precio_input.text().strip()
        
        # Validación básica
        if not nombre:
            QMessageBox.warning(self, "Error", "El nombre del plan es obligatorio.")
            return
        
        try:
            precio = float(precio_text)
            if precio <= 0:
                QMessageBox.warning(self, "Error", "El precio debe ser mayor que cero.")
                return
        except ValueError:
            QMessageBox.warning(self, "Error", "El precio debe ser un número válido.")
            return
        
        try:
            # Verificar si el nombre pertenece a otro plan
            self.cur.execute("SELECT id FROM planes WHERE nombre = ? AND id != ?", (nombre, self.selected_plan_id))
            if self.cur.fetchone():
                QMessageBox.warning(self, "Error", f"Ya existe otro plan con el nombre {nombre}.")
                return
            
            # Actualizar plan
            self.cur.execute('''
                UPDATE planes
                SET nombre = ?, descripcion = ?, precio = ?
                WHERE id = ?
            ''', (nombre, descripcion, precio, self.selected_plan_id))
            
            self.conn.commit()
            
            QMessageBox.information(self, "Éxito", "Plan actualizado correctamente.")
            self.clear_plan_form()
            self.load_plans()
            self.update_plan_combo()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al actualizar plan: {str(e)}")

    def delete_plan(self):
        """Elimina un plan de la base de datos"""
        if not hasattr(self, 'selected_plan_id') or not self.selected_plan_id:
            return
        
        # Verificar si hay socios usando este plan
        self.cur.execute("SELECT COUNT(*) FROM socios WHERE plan_id = ? AND gimnasio_id = ?", 
                        (self.selected_plan_id, self.user_id))
        count = self.cur.fetchone()[0]
        
        if count > 0:
            QMessageBox.warning(self, "Error", 
                            f"No se puede eliminar este plan porque hay {count} socios que lo están usando.")
            return
        
        reply = QMessageBox.question(self, "Confirmar", 
                                    "¿Está seguro que desea eliminar este plan? Esta acción no se puede deshacer.",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Eliminar plan
                self.cur.execute("DELETE FROM planes WHERE id = ?", (self.selected_plan_id,))
                self.conn.commit()
                
                QMessageBox.information(self, "Éxito", "Plan eliminado correctamente.")
                self.clear_plan_form()
                self.load_plans()
                self.update_plan_combo()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Error al eliminar plan: {str(e)}")
    
    def setup_reports_tab(self, tab):
        """Configura la pestaña de informes"""
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Título
        title_label = QLabel("INFORMES Y ESTADÍSTICAS")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 20px; font-weight: bold; margin: 20px;")
        layout.addWidget(title_label)
        
        # Panel de estadísticas
        stats_frame = QFrame()
        stats_frame.setFrameShape(QFrame.Shape.StyledPanel)
        stats_layout = QVBoxLayout(stats_frame)
        
        stats_title = QLabel("Estadísticas del Gimnasio")
        stats_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        stats_layout.addWidget(stats_title)
        
        # Grid de estadísticas
        stats_grid = QGridLayout()
        
        # Obtener número de socios
        self.cur.execute("SELECT COUNT(*) FROM socios WHERE gimnasio_id = ?", (self.user_id,))
        total_members = self.cur.fetchone()[0]
        
        # Socios con cuota al día
        self.cur.execute("SELECT COUNT(*) FROM socios WHERE gimnasio_id = ? AND estado_cuota = 'Pagada'", (self.user_id,))
        active_members = self.cur.fetchone()[0]
        
        # Asistencias del mes
        first_day = datetime.now().replace(day=1).strftime("%Y-%m-%d")
        self.cur.execute("""
            SELECT COUNT(*) FROM asistencias a
            JOIN socios s ON a.socio_id = s.id
            WHERE s.gimnasio_id = ? AND a.fecha >= ?
        """, (self.user_id, first_day))
        month_attendance = self.cur.fetchone()[0]
        
        # Agregar al grid
        stats_grid.addWidget(QLabel("Total de Socios:"), 0, 0)
        stats_grid.addWidget(QLabel(str(total_members)), 0, 1)
        
        stats_grid.addWidget(QLabel("Socios con Cuota al Día:"), 1, 0)
        percent_active = (active_members / total_members * 100) if total_members > 0 else 0
        stats_grid.addWidget(QLabel(f"{active_members} ({percent_active:.1f}%)"), 1, 1)
        
        stats_grid.addWidget(QLabel("Asistencias este Mes:"), 2, 0)
        stats_grid.addWidget(QLabel(str(month_attendance)), 2, 1)
        
        stats_layout.addLayout(stats_grid)
        
        layout.addWidget(stats_frame)
        
        # Panel de exportación de informes
        export_frame = QFrame()
        export_frame.setFrameShape(QFrame.Shape.StyledPanel)
        export_layout = QVBoxLayout(export_frame)
        
        export_title = QLabel("Exportar Informes")
        export_title.setStyleSheet("font-size: 16px; font-weight: bold;")
        export_layout.addWidget(export_title)
        
        # Botones de exportación
        members_button = QPushButton("Exportar Lista de Socios")
        members_button.clicked.connect(self.export_members_report)
        
        attendance_button = QPushButton("Exportar Informe de Asistencias")
        attendance_button.clicked.connect(self.export_attendance_report)
        
        payments_button = QPushButton("Exportar Informe de Pagos")
        payments_button.clicked.connect(self.export_payments_report)
        
        export_layout.addWidget(members_button)
        export_layout.addWidget(attendance_button)
        export_layout.addWidget(payments_button)
        
        layout.addWidget(export_frame)
        
        layout.addStretch()
    
    def export_members_report(self):
        """Exporta un informe de socios a un archivo CSV"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Informe de Socios", "", "CSV Files (*.csv)")
        
        if not file_path:
            return
        
        try:
            self.cur.execute("""
                SELECT s.id, s.nombre, s.apellido, s.dni, s.telefono, s.fecha_registro, 
                       s.fecha_vencimiento, s.estado_cuota, p.nombre as plan 
                FROM socios s
                LEFT JOIN planes p ON s.plan_id = p.id
                WHERE s.gimnasio_id = ?
                ORDER BY s.apellido, s.nombre
            """, (self.user_id,))
            
            members = self.cur.fetchall()
            
            with open(file_path, 'w', newline='') as file:
                import csv
                writer = csv.writer(file)
                # Escribir encabezados
                writer.writerow(["ID", "Nombre", "Apellido", "DNI", "Teléfono", "Fecha Registro", 
                                "Fecha Vencimiento", "Estado Cuota", "Plan"])
                # Escribir datos
                for member in members:
                    writer.writerow(member)
            
            QMessageBox.information(self, "Exportación Exitosa", f"Informe de socios exportado a {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar informe: {str(e)}")
    
    def export_attendance_report(self):
        """Exporta un informe de asistencias a un archivo CSV"""
        file_path, _ = QFileDialog.getSaveFileName(self, "Guardar Informe de Asistencias", "", "CSV Files (*.csv)")
        
        if not file_path:
            return
        
        try:
            # Obtener rango de fechas
            start_date = datetime.now().replace(day=1).strftime("%Y-%m-%d")  # Primer día del mes
            end_date = datetime.now().strftime("%Y-%m-%d")  # Hoy
            
            self.cur.execute("""
                SELECT a.fecha, s.nombre, s.apellido, s.dni
                FROM asistencias a
                JOIN socios s ON a.socio_id = s.id
                WHERE s.gimnasio_id = ? AND a.fecha BETWEEN ? AND ?
                ORDER BY a.fecha DESC, s.apellido, s.nombre
            """, (self.user_id, start_date, end_date))
            
            attendances = self.cur.fetchall()
            
            with open(file_path, 'w', newline='') as file:
                import csv
                writer = csv.writer(file)
                # Escribir encabezados
                writer.writerow(["Fecha", "Nombre", "Apellido", "DNI"])
                # Escribir datos
                for attendance in attendances:
                    writer.writerow(attendance)
            
            QMessageBox.information(self, "Exportación Exitosa", f"Informe de asistencias exportado a {file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error al exportar informe: {str(e)}")
    
    def export_payments_report(self):
        """Exporta un informe de pagos a un archivo CSV (pendiente para implementación futura)"""
        QMessageBox.information(self, "Funcionalidad no implementada", 
                             "Esta funcionalidad se implementará en futuras versiones.")
    
    def closeEvent(self, event):
        """Maneja el cierre de la aplicación"""
        # Cerrar conexión a la base de datos
        if hasattr(self, 'conn'):
            self.conn.close()
        event.accept()


def main():
    app = QApplication(sys.argv)
    
    # Mostrar ventana de login
    login_window = LoginWindow()
    login_window.show()
    
    # Bucle principal para login
    app.exec()
    
    # Verificar si el login fue exitoso
    if hasattr(login_window, 'accepted') and login_window.accepted:
        # Iniciar la aplicación correspondiente según el tipo de usuario
        if login_window.user_type == "admin":
            window = AdminDashboard(login_window.user_id)
        else:  # gimnasio
            window = GymApp(login_window.user_id, login_window.user_type, login_window.gym_name)
        
        window.show()
        sys.exit(app.exec())
    
if __name__ == "__main__":
    main()