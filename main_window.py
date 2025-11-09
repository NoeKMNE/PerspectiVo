import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame,
    QLabel, QPushButton, QButtonGroup, QStackedWidget)
from PySide6.QtGui import QIcon, QFont

from membres import MembersPage
from groupes_page import GroupsPage
from messages_page import MessagesPage
from events_page import EventsPage
from stats_page import StatisticsPage

from db import creer_gestionnaire_db
from login import AuthWindow


class ModernCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 12px;
                padding: 16px;
            }
        """)


class ModernButton(QPushButton):
    def __init__(self, text, primary=False, parent=None):
        super().__init__(text, parent)
        if primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #4F46E5;
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-weight: bold;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #4338CA;
                }
                QPushButton:pressed {
                    background-color: #3730A3;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #F3F4F6;
                    color: #374151;
                    border: 1px solid #D1D5DB;
                    border-radius: 8px;
                    padding: 10px 20px;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background-color: #E5E7EB;
                }
            """)


class SidebarButton(QPushButton):
    def __init__(self, text, icon, parent=None):
        super().__init__(parent)
        self.setText(f"{text}")
        self.setCheckable(True)
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 12px 16px;
                margin: 2px 0;
                border: none;
                border-radius: 8px;
                font-size: 14px;
                background-color: transparent;
                color: #6B7280;
            }
            QPushButton:checked {
                background-color: #EEF2FF;
                color: #4F46E5;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #F9FAFB;
            }
        """)


class MainWindow(QMainWindow):
    def __init__(self, username=""):
        super().__init__()
        self.current_user = username
        self.setWindowIcon(QIcon("app_icon.svg") if __import__('os').path.exists("app_icon.svg") else QIcon())
        self.setWindowTitle("A.C.E.E.P.C.I")
        self.setGeometry(100, 100, 800, 700)
        
        # Créer les managers DB
        self.db, self.membres_mgr, self.evenements_mgr, self.groupes_mgr, \
            self.presences_mgr, self.messages_mgr = creer_gestionnaire_db()
        
        self.init_ui()

    def init_ui(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #FAFAFA;
                border-right: 1px solid #E5E7EB;
            }
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 16, 12, 16)
        sidebar_layout.setSpacing(8)

        # Logo/Titre de l'app
        app_title = QLabel("A.C.E.E.P.C.I")
        app_title.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #1F2937;
            margin-bottom: 12px;
            padding: 8px;
        """)
        sidebar_layout.addWidget(app_title)

        # Boutons de navigation
        self.nav_buttons = []
        nav_items = [
            ("👤", "Membres"),
            ("📅", "Événements"),
            ("👥", "Groupes"),
            ("💬", "Messages"),
            ("📊", "Statistiques")
        ]

        self.button_group = QButtonGroup()
        for icon, text in nav_items:
            btn = SidebarButton(f"{icon} {text}", icon)
            self.nav_buttons.append(btn)
            self.button_group.addButton(btn)
            sidebar_layout.addWidget(btn)

        # Connecter les signaux
        self.nav_buttons[0].clicked.connect(lambda: self.show_page(0))
        self.nav_buttons[1].clicked.connect(lambda: self.show_page(1))
        self.nav_buttons[2].clicked.connect(lambda: self.show_page(2))
        self.nav_buttons[3].clicked.connect(lambda: self.show_page(3))
        self.nav_buttons[4].clicked.connect(lambda: self.show_page(4))

        sidebar_layout.addStretch()

        # Informations utilisateur
        user_info = QLabel(f"👤 {self.current_user}\n\nConnecté à l'app")
        user_info.setStyleSheet("""
            background-color: #EEF2FF;
            padding: 10px;
            border-radius: 8px;
            font-size: 11px;
            color: #4F46E5;
            font-weight: 600;
        """)
        sidebar_layout.addWidget(user_info)

        # Bouton déconnexion
        logout_btn = ModernButton("Déconnexion", primary=False)
        logout_btn.clicked.connect(self.logout)
        sidebar_layout.addWidget(logout_btn)

        main_layout.addWidget(sidebar)

        # Zone de contenu principal
        self.content_area = QStackedWidget()
        self.content_area.setStyleSheet("background-color: #F9FAFB;")

        # Créer les pages
        self.members_page = MembersPage(self.membres_mgr)
        self.events_page = EventsPage(self.evenements_mgr, self.groupes_mgr, self.membres_mgr)
        self.groups_page = GroupsPage(self.groupes_mgr, self.membres_mgr)
        self.messages_page = MessagesPage(self.groupes_mgr, self.membres_mgr)
        self.stat_page = StatisticsPage(self.membres_mgr, self.evenements_mgr, self.groupes_mgr, self.presences_mgr)

        # Connecter les signaux de synchronisation
        self.groups_page.groups_changed.connect(self.stat_page.refresh_stats)
        self.members_page.members_changed.connect(self.stat_page.refresh_stats)
        self.events_page.events_changed.connect(self.stat_page.refresh_stats)

        # Ajouter les pages au stack
        self.content_area.addWidget(self.members_page)
        self.content_area.addWidget(self.events_page)
        self.content_area.addWidget(self.groups_page)
        self.content_area.addWidget(self.messages_page)
        self.content_area.addWidget(self.stat_page)

        main_layout.addWidget(self.content_area)

        # Sélectionner la première page par défaut
        self.nav_buttons[0].setChecked(True)
        self.content_area.setCurrentIndex(0)

    def show_page(self, index):
        """Affiche la page à l'index spécifié"""
        self.content_area.setCurrentIndex(index)
        # Décocher tous les autres boutons
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)

    def logout(self):
        """Déconnecte l'utilisateur et retourne à la page de connexion"""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Déconnexion",
            "Êtes-vous sûr de vouloir vous déconnecter?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.close()
            # Afficher la fenêtre de login
            auth_window = AuthWindow()
            auth_window.show()


def main():
    """Point d'entrée principal de l'application"""
    app = QApplication(sys.argv)
    
    # Configuration de la police système
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Créer et afficher la fenêtre de login d'abord
    auth_window = AuthWindow()
    auth_window.show()
    
    # Variable pour stocker la fenêtre principale
    main_window = None
    
    def on_auth_completed(username):
        """Appelé quand l'authentification est réussie"""
        nonlocal main_window
        main_window = MainWindow(username=username)
        main_window.show()
    
    try:
        auth_window.authentication_completed.connect(on_auth_completed)
    except Exception as e:
        print(f"Erreur: {e}")
        sys.exit(1)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()