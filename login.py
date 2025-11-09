import bcrypt
import os
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from db import creer_gestionnaire_db


class ModernCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setObjectName("modernCard")
        # subtle shadow for a modern look
        effect = QGraphicsDropShadowEffect(self)
        effect.setBlurRadius(18)
        effect.setOffset(0, 6)
        effect.setColor(QColor(0, 0, 0, 30))
        self.setGraphicsEffect(effect)
        self.setStyleSheet("""
            QFrame#modernCard {
                background-color: #ffffff;
                border-radius: 12px;
                padding: 18px;
            }
        """)


class ModernButton(QPushButton):
    def __init__(self, text, primary=False, parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        base = """
            QPushButton {
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 13px;
                min-height: 34px;
            }
        """
        if primary:
            self.setStyleSheet(base + """
                QPushButton {
                    background-color: #2563EB;
                    color: white;
                    font-weight: 600;
                }
                QPushButton:hover { background-color: #1E40AF; }
                QPushButton:pressed { background-color: #1E3A8A; }
            """)
        else:
            self.setStyleSheet(base + """
                QPushButton {
                    background-color: transparent;
                    color: #2563EB;
                    border: 1px solid rgba(37,99,235,0.16);
                }
                QPushButton:hover { background-color: rgba(37,99,235,0.06); }
            """)


class ModernLineEdit(QLineEdit):
    def __init__(self, placeholder="", parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setStyleSheet("""
            QLineEdit {
                padding: 8px 10px;
                border: 1px solid #E6E9EE;
                border-radius: 8px;
                font-size: 13px;
                background-color: #FBFDFF;
                min-height: 32px;
            }
            QLineEdit:focus {
                border: 1px solid #2563EB;
                background-color: #FFFFFF;
            }
        """)


def hash_password(password: str) -> bytes:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())


def check_password(password: str, hashed: bytes) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed)
    except Exception:
        return False


# Codes d'invitation valides
VALID_INVITATION_CODES = [
    "PerspectiveD!vine",  # Code principal
    "admin2024",
    "perspectivo-beta",
]


class LoginPage(QWidget):
    login_successful = Signal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.db_manager, *_ = creer_gestionnaire_db()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        container = QWidget()
        container.setMaximumWidth(480)
        inner = QVBoxLayout(container)
        inner.setSpacing(18)

        # Header
        title = QLabel("PerspectiVo")
        title.setStyleSheet("font-size:22px; font-weight:700; color:#0f172a;")
        subtitle = QLabel("Gestion — Membres · Groupes · Évènements")
        subtitle.setStyleSheet("color:#6B7280; font-size:12px;")
        header = QVBoxLayout()
        header.addWidget(title)
        header.addWidget(subtitle)
        header.setSpacing(4)
        inner.addLayout(header)

        # Login card
        login_card = ModernCard()
        login_layout = QVBoxLayout(login_card)
        login_layout.setSpacing(12)

        login_title = QLabel("Connexion")
        login_title.setStyleSheet("font-size:15px; font-weight:600; color:#0f172a;")
        login_layout.addWidget(login_title)

        self.email_input = ModernLineEdit("Email ou nom d'utilisateur")
        login_layout.addWidget(self.email_input)

        self.password_input = ModernLineEdit("Mot de passe")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.login)
        login_layout.addWidget(self.password_input)

        # remember & forgot
        tools = QHBoxLayout()
        self.remember_checkbox = QCheckBox("Se souvenir de moi")
        self.remember_checkbox.setStyleSheet("color:#6B7280; font-size:12px;")
        tools.addWidget(self.remember_checkbox)
        tools.addStretch()
        forgot_btn = QPushButton("Mot de passe oublié ?")
        forgot_btn.setFlat(True)
        forgot_btn.setStyleSheet("color:#2563EB; font-size:12px;")
        forgot_btn.clicked.connect(self.forgot_password)
        tools.addWidget(forgot_btn)
        login_layout.addLayout(tools)

        # actions
        self.login_button = ModernButton("Se connecter", primary=True)
        self.login_button.clicked.connect(self.login)
        login_layout.addWidget(self.login_button)

        alt_btn = ModernButton("Créer un compte")
        alt_btn.clicked.connect(self.show_signup)
        login_layout.addWidget(alt_btn)

        inner.addWidget(login_card)
        main_layout.addStretch()
        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch()

    def login(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()

        if not email or not password:
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs.")
            return

        try:
            conn = self.db_manager
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ? OR nom = ?", (email, email))
            user = cursor.fetchone()
        except Exception as e:
            QMessageBox.critical(self, "Erreur BDD", "Impossible de contacter la base de données.")
            return

        if not user:
            QMessageBox.warning(self, "Erreur", "Utilisateur inconnu.")
            return

        stored = user['password_hash'] if 'password_hash' in user.keys() else user.get('password_hash', "")
        if isinstance(stored, str):
            stored_bytes = stored.encode()
        else:
            stored_bytes = stored

        if not check_password(password, stored_bytes):
            QMessageBox.warning(self, "Erreur", "Mot de passe incorrect.")
            return

        QMessageBox.information(self, "Succès", "Connexion réussie.")
        self.login_successful.emit(email)

    def forgot_password(self):
        QMessageBox.information(self, "Mot de passe oublié",
                                "Un email de récupération vous sera envoyé prochainement.\n\n"
                                "Pour le moment, utilisez: utilisateur 'admin' / mot de passe 'admin'")

    def show_signup(self):
        parent = self.parent()
        if isinstance(parent, QStackedWidget):
            parent.setCurrentIndex(1)


class SignupPage(QWidget):
    signup_successful = Signal(str)

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.db_manager, *_ = creer_gestionnaire_db()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        container = QWidget()
        container.setMaximumWidth(480)
        inner = QVBoxLayout(container)
        inner.setSpacing(14)

        # Back button
        back_layout = QHBoxLayout()
        back_btn = QPushButton("← Retour")
        back_btn.setFlat(True)
        back_btn.setStyleSheet("color:#2563EB; font-size:12px;")
        back_btn.clicked.connect(self.go_back)
        back_layout.addWidget(back_btn)
        back_layout.addStretch()
        inner.addLayout(back_layout)

        title = QLabel("Créer un compte")
        title.setStyleSheet("font-size:18px; font-weight:700; color:#0f172a;")
        inner.addWidget(title)

        signup_card = ModernCard()
        signup_layout = QVBoxLayout(signup_card)
        signup_layout.setSpacing(10)

        # Code d'invitation (NOUVEAU)
        invitation_label = QLabel("Code d'invitation *")
        invitation_label.setStyleSheet("font-size:12px; font-weight:600; color:#374151;")
        signup_layout.addWidget(invitation_label)
        
        self.invitation_code = ModernLineEdit("Entrez le code d'invitation")
        self.invitation_code.setEchoMode(QLineEdit.EchoMode.Password)
        signup_layout.addWidget(self.invitation_code)

        separator = QLabel("━" * 40)
        separator.setStyleSheet("color:#E6E9EE;")
        signup_layout.addWidget(separator)

        self.first_name = ModernLineEdit("Prénom")
        signup_layout.addWidget(self.first_name)
        
        self.last_name = ModernLineEdit("Nom de famille")
        signup_layout.addWidget(self.last_name)
        
        self.username = ModernLineEdit("Nom d'utilisateur / Email")
        signup_layout.addWidget(self.username)
        
        self.password = ModernLineEdit("Mot de passe")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        signup_layout.addWidget(self.password)
        
        self.confirm = ModernLineEdit("Confirmer le mot de passe")
        self.confirm.setEchoMode(QLineEdit.EchoMode.Password)
        signup_layout.addWidget(self.confirm)

        self.terms = QCheckBox("J'accepte les conditions d'utilisation")
        self.terms.setStyleSheet("color:#6B7280; font-size:12px;")
        signup_layout.addWidget(self.terms)

        self.signup_button = ModernButton("Créer mon compte", primary=True)
        self.signup_button.clicked.connect(self.signup)
        signup_layout.addWidget(self.signup_button)

        signup_layout.addStretch()
        inner.addWidget(signup_card)
        main_layout.addStretch()
        main_layout.addWidget(container, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addStretch()

    def signup(self):
        # Vérifier le code d'invitation EN PREMIER
        invitation_code = self.invitation_code.text().strip()
        
        if not invitation_code:
            QMessageBox.warning(self, "Erreur", "Le code d'invitation est obligatoire.")
            self.invitation_code.setFocus()
            return
        
        if invitation_code not in VALID_INVITATION_CODES:
            QMessageBox.warning(
                self,
                "Code invalide",
                "Le code d'invitation que vous avez entré est incorrect.\n\n"
                "Veuillez vérifier et réessayer."
            )
            self.invitation_code.clear()
            self.invitation_code.setFocus()
            return

        # Puis vérifier les autres champs
        if not all([self.first_name.text().strip(), self.last_name.text().strip(),
                    self.username.text().strip(), self.password.text()]):
            QMessageBox.warning(self, "Erreur", "Veuillez remplir tous les champs requis.")
            return

        if self.password.text() != self.confirm.text():
            QMessageBox.warning(self, "Erreur", "Les mots de passe ne correspondent pas.")
            return

        if len(self.password.text()) < 6:
            QMessageBox.warning(self, "Erreur", "Le mot de passe doit contenir au moins 6 caractères.")
            return

        if not self.terms.isChecked():
            QMessageBox.warning(self, "Erreur", "Vous devez accepter les conditions.")
            return

        hashed = hash_password(self.password.text())

        try:
            conn = self.db_manager
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (nom, prenoms, email, password_hash)
                VALUES (?, ?, ?, ?)
            """, (self.last_name.text().strip(), self.first_name.text().strip(),
                  self.username.text().strip(), hashed.decode()))
            conn.commit()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", f"Impossible de créer le compte: {e}")
            return

        QMessageBox.information(self, "Succès", "Compte créé avec succès. Vous pouvez vous connecter.")
        self.signup_successful.emit(self.username.text().strip())
        parent = self.parent()
        if isinstance(parent, QStackedWidget):
            parent.setCurrentIndex(0)

    def go_back(self):
        parent = self.parent()
        if isinstance(parent, QStackedWidget):
            parent.setCurrentIndex(0)


class AuthWindow(QMainWindow):
    authentication_completed = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("PerspectiVo — Connexion")
        self.setWindowIcon(QIcon("app_icon.svg") if os.path.exists("app_icon.svg") else QIcon())
        self.resize(680, 560)
        self.center_window()
        self.init_ui()
        self.apply_light_theme()

    def center_window(self):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )

    def init_ui(self):
        central_widget = QStackedWidget()

        self.login_page = LoginPage()
        self.signup_page = SignupPage()

        central_widget.addWidget(self.login_page)
        central_widget.addWidget(self.signup_page)

        self.login_page.login_successful.connect(self.on_authentication_success)
        self.signup_page.signup_successful.connect(self.on_authentication_success)

        # top bar with theme toggle
        top_bar = QWidget()
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(12, 8, 12, 8)
        top_layout.addStretch()

        self.theme_toggle = QToolButton()
        self.theme_toggle.setText("🌙")
        self.theme_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_toggle.setAutoRaise(True)
        self.theme_toggle.clicked.connect(self.toggle_theme)
        top_layout.addWidget(self.theme_toggle)

        top_bar.setLayout(top_layout)

        # main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(top_bar)
        main_layout.addWidget(central_widget)

        wrapper = QWidget()
        wrapper.setLayout(main_layout)

        self.setCentralWidget(wrapper)

    def apply_light_theme(self):
        self.setStyleSheet("""
            QMainWindow { background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #F8FAFC, stop:1 #EDF2F7); }
            QLabel { color: #0f172a; }
            QCheckBox, QPushButton, QLineEdit { font-family: "Segoe UI", Roboto, Arial; }
        """)
        self.theme_toggle.setText("🌙")
        self._dark = False

    def apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #0b1220; }
            QLabel { color: #E6EEF8; }
            QLineEdit { background-color: #071122; color: #E6EEF8; border: 1px solid #234; }
            QPushButton { color: #E6EEF8; }
        """)
        self.theme_toggle.setText("☀️")
        self._dark = True

    def toggle_theme(self):
        if getattr(self, "_dark", False):
            self.apply_light_theme()
        else:
            self.apply_dark_theme()

    def on_authentication_success(self, username):
        self.authentication_completed.emit(username)
        self.close()