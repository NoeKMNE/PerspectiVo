from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import QComboBox, QMessageBox


class ModernCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 6px;
                margin: 2px;
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
                    border-radius: 5px;
                    padding: 4px 8px;
                    font-weight: bold;
                    font-size: 11px;
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
                    border-radius: 5px;
                    padding: 4px 8px;
                    font-size: 11px;
                }
                QPushButton:hover {
                    background-color: #E5E7EB;
                }
            """)

class SidebarButton(QPushButton):
    def __init__(self, text, icon, parent=None):
        super().__init__(parent)
        self.setText(f"{text}")
        self.setIcon(icon)
        self.setCheckable(True)
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 6px 8px;
                margin: 1px 0;
                border: none;
                border-radius: 5px;
                font-size: 11px;
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



class MessagesPage(QWidget):
    def __init__(self, groupes_mgr, membres_mgr):
        super().__init__()
        self.groupes_mgr = groupes_mgr
        self.membres_mgr = membres_mgr
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(24, 24, 24, 24)

        # En-tête
        header_layout = QHBoxLayout()

        title = QLabel("Messages")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #1F2937;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        new_message_btn = ModernButton("+ Nouveau message", primary=True)
        header_layout.addWidget(new_message_btn)

        layout.addLayout(header_layout)

        # Interface de messagerie
        content_layout = QHBoxLayout()

        # Liste des groupes
        recipients_card = ModernCard()
        recipients_layout = QVBoxLayout(recipients_card)
        recipients_title = QLabel("Groupe destinataire")
        recipients_title.setStyleSheet("font-size: 13px; font-weight: bold; margin-bottom: 8px;")
        recipients_layout.addWidget(recipients_title)

        self.group_combo = QComboBox()
        self.group_combo.setFixedHeight(28)
        self.group_combo.setStyleSheet("""
            QComboBox {
                padding: 6px;
                border: 1px solid #D1D5DB;
                border-radius: 5px;
                font-size: 11px;
                background-color: white;
            }
        """)
        # Remplir la liste des groupes depuis la base
        groupes = self.groupes_mgr.obtenir_tous_groupes()
        for groupe in groupes:
            self.group_combo.addItem(groupe['nom'], groupe['id'])
        recipients_layout.addWidget(self.group_combo)
        content_layout.addWidget(recipients_card)

        # Zone de composition
        compose_card = ModernCard()
        compose_layout = QVBoxLayout(compose_card)
        compose_title = QLabel("Composer un message WhatsApp")
        compose_title.setStyleSheet("font-size: 13px; font-weight: bold; margin-bottom: 8px; color: #1F2937;")
        compose_layout.addWidget(compose_title)

        subject_input = QLineEdit()
        subject_input.setPlaceholderText("Objet du message (optionnel)...")
        subject_input.setFixedHeight(28)
        subject_input.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                border: 1px solid #D1D5DB;
                border-radius: 5px;
                font-size: 11px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4F46E5;
                outline: none;
            }
        """)
        compose_layout.addWidget(subject_input)
        message_text = QTextEdit()
        message_text.setPlaceholderText("Tapez votre message ici...")
        message_text.setMinimumHeight(100)
        message_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #D1D5DB;
                border-radius: 5px;
                padding: 6px;
                font-size: 11px;
                background-color: white;
            }
            QTextEdit:focus {
                border-color: #4F46E5;
                outline: none;
            }
        """)
        compose_layout.addWidget(message_text)

        send_btn = ModernButton("Envoyer au groupe sur WhatsApp", primary=True)
        send_btn.clicked.connect(lambda: self.send_whatsapp_group_message(
            subject_input.text(), message_text.toPlainText()))
        compose_layout.addWidget(send_btn)

        content_layout.addWidget(compose_card)
        layout.addLayout(content_layout)

    def send_whatsapp_group_message(self, subject, message):
        group_id = self.group_combo.currentData()
        if not group_id or not message.strip():
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un groupe et saisir le message.")
            return

        membres = self.membres_mgr.obtenir_membres_du_groupe(group_id)
        if not membres:
            QMessageBox.warning(self, "Erreur", "Aucun membre dans ce groupe.")
            return

        full_message = f"{subject}\n{message}" if subject.strip() else message
        errors = []
        try:
            import pywhatkit
            for membre in membres:
                phone = membre.get('contact', '').strip()
                if phone:
                    try:
                        pywhatkit.sendwhatmsg_instantly(phone, full_message)
                    except Exception as e:
                        errors.append(f"{membre['nom']} : {e}")
        except Exception:
            QMessageBox.warning(self, "Connexion Internet requise",
                                "Impossible d'envoyer les messages WhatsApp sans connexion Internet.\n"
                                "Les autres fonctionnalités de l'application restent disponibles.")
            return

        if errors:
            QMessageBox.warning(self, "Envoi partiel", "Certains messages n'ont pas pu être envoyés:\n" + "\n".join(errors))
        else:
            QMessageBox.information(self, "Succès", "Message envoyé à tous les membres du groupe via WhatsApp.")

