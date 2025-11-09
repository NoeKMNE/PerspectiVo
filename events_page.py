from PySide6.QtWidgets import *
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter
from datetime import datetime, date


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
                    padding: 10px 16px;
                    font-weight: bold;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #4338CA; }
                QPushButton:pressed { background-color: #3730A3; }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #F3F4F6;
                    color: #374151;
                    border: 1px solid #D1D5DB;
                    border-radius: 8px;
                    padding: 10px 16px;
                    font-size: 12px;
                }
                QPushButton:hover { background-color: #E5E7EB; }
            """)


class ModernCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 8px;
                padding: 12px;
                margin: 2px;
            }
            QFrame:hover {
                border: 1px solid #4F46E5;
                box-shadow: 0 4px 6px rgba(79, 70, 229, 0.1);
            }
        """)


class EventEditorDialog(QDialog):
    """Dialog pour créer/modifier un événement"""
    
    def __init__(self, evenements_mgr, groupes_mgr, event_id=None, parent=None):
        super().__init__(parent)
        self.evenements_mgr = evenements_mgr
        self.groupes_mgr = groupes_mgr
        self.event_id = event_id
        
        self.setWindowTitle("Nouvel événement" if event_id is None else "Modifier l'événement")
        self.setFixedSize(550, 480)
        self.setModal(True)
        self.init_ui()
        
        if event_id:
            self.load_event_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # Titre
        title = QLabel("Nouvel événement" if self.event_id is None else "Modifier l'événement")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F2937;")
        layout.addWidget(title)
        
        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        scroll_widget = QWidget()
        form_layout = QGridLayout(scroll_widget)
        form_layout.setSpacing(12)
        
        # Nom
        form_layout.addWidget(QLabel("Nom de l'événement *"), 0, 0)
        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Ex: Réunion hebdomadaire")
        self.nom_input.setFixedHeight(40)
        self.style_input(self.nom_input)
        form_layout.addWidget(self.nom_input, 0, 1)
        
        # Date
        form_layout.addWidget(QLabel("Date *"), 1, 0)
        self.date_input = QDateEdit()
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setFixedHeight(40)
        self.date_input.setCalendarPopup(True)
        self.style_input(self.date_input)
        form_layout.addWidget(self.date_input, 1, 1)
        
        # Heure
        form_layout.addWidget(QLabel("Heure"), 2, 0)
        self.time_input = QTimeEdit()
        self.time_input.setFixedHeight(40)
        self.style_input(self.time_input)
        form_layout.addWidget(self.time_input, 2, 1)
        
        # Lieu
        form_layout.addWidget(QLabel("Lieu"), 3, 0)
        self.lieu_input = QLineEdit()
        self.lieu_input.setPlaceholderText("Salle, adresse...")
        self.lieu_input.setFixedHeight(40)
        self.style_input(self.lieu_input)
        form_layout.addWidget(self.lieu_input, 3, 1)
        
        # Groupe associé
        form_layout.addWidget(QLabel("Groupe associé"), 4, 0)
        self.groupe_combo = QComboBox()
        self.groupe_combo.setFixedHeight(40)
        self.groupe_combo.addItem("Aucun groupe", None)
        groupes = self.groupes_mgr.obtenir_tous_groupes()
        for g in groupes:
            self.groupe_combo.addItem(g['nom'], g['id'])
        self.style_input(self.groupe_combo)
        form_layout.addWidget(self.groupe_combo, 4, 1)
        
        # Description
        form_layout.addWidget(QLabel("Description"), 5, 0, Qt.AlignTop)
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Détails de l'événement...")
        self.description_input.setMaximumHeight(100)
        self.style_textedit(self.description_input)
        form_layout.addWidget(self.description_input, 5, 1)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Note
        note = QLabel("* Champs obligatoires")
        note.setStyleSheet("color: #DC2626; font-size: 11px; font-style: italic;")
        layout.addWidget(note)
        
        # Boutons
        buttons_layout = QHBoxLayout()
        cancel_btn = ModernButton("Annuler")
        cancel_btn.clicked.connect(self.reject)
        
        save_text = "Créer l'événement" if self.event_id is None else "Enregistrer"
        save_btn = ModernButton(save_text, primary=True)
        save_btn.clicked.connect(self.validate_and_save)
        
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)
        layout.addLayout(buttons_layout)
    
    def style_input(self, widget):
        widget.setStyleSheet("""
            QLineEdit, QDateEdit, QTimeEdit, QComboBox {
                padding: 10px 12px;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                font-size: 12px;
                background-color: white;
            }
            QLineEdit:focus, QDateEdit:focus, QTimeEdit:focus, QComboBox:focus {
                border: 2px solid #4F46E5;
                outline: none;
            }
        """)
    
    def style_textedit(self, widget):
        widget.setStyleSheet("""
            QTextEdit {
                padding: 10px 12px;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                font-size: 12px;
                background-color: white;
            }
            QTextEdit:focus {
                border: 2px solid #4F46E5;
                outline: none;
            }
        """)
    
    def load_event_data(self):
        """Charge les données de l'événement"""
        event = self.evenements_mgr.obtenir_evenement(self.event_id)
        if event:
            self.nom_input.setText(event.get('nom', ''))
            
            date_str = event.get('date', '')
            if date_str:
                self.date_input.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
            
            heure_str = event.get('heure', '')
            if heure_str:
                self.time_input.setTime(self.time_input.time())
            
            self.lieu_input.setText(event.get('lieu', ''))
            self.description_input.setPlainText(event.get('description', ''))
            
            groupe_id = event.get('groupe_id')
            if groupe_id:
                index = self.groupe_combo.findData(groupe_id)
                if index >= 0:
                    self.groupe_combo.setCurrentIndex(index)
    
    def validate_and_save(self):
        """Valide et sauvegarde l'événement"""
        nom = self.nom_input.text().strip()
        
        if not nom:
            QMessageBox.warning(self, "Erreur", "Le nom est obligatoire.")
            self.nom_input.setFocus()
            return
        
        date_str = self.date_input.date().toString("yyyy-MM-dd")
        heure_str = self.time_input.time().toString("HH:mm")
        
        try:
            if self.event_id is None:
                self.evenements_mgr.ajouter_evenement(
                    nom=nom,
                    date_str=date_str,
                    heure=heure_str,
                    lieu=self.lieu_input.text().strip(),
                    description=self.description_input.toPlainText().strip(),
                    groupe_id=self.groupe_combo.currentData()
                )
                QMessageBox.information(self, "Succès", f"Événement '{nom}' créé!")
            else:
                cur = self.evenements_mgr.db.cursor()
                cur.execute("""
                    UPDATE events SET nom=?, date=?, heure=?, lieu=?, description=?, groupe_id=?
                    WHERE id=?
                """, (nom, date_str, heure_str, self.lieu_input.text().strip(),
                      self.description_input.toPlainText().strip(),
                      self.groupe_combo.currentData(), self.event_id))
                self.evenements_mgr.db.commit()
                QMessageBox.information(self, "Succès", "Événement modifié!")
            
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Erreur", str(e))


class EventsPage(QWidget):
    events_changed = Signal()
    
    def __init__(self, evenements_mgr, groupes_mgr, presences_mgr):
        super().__init__()
        self.evenements_mgr = evenements_mgr
        self.groupes_mgr = groupes_mgr
        self.presences_mgr = presences_mgr
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # En-tête
        header_layout = QHBoxLayout()
        title = QLabel("📅 Événements")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1F2937;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        add_btn = ModernButton("➕ Créer un événement", primary=True)
        add_btn.clicked.connect(self.add_event)
        header_layout.addWidget(add_btn)
        
        layout.addLayout(header_layout)
        
        # Filtre
        filter_layout = QHBoxLayout()
        filter_label = QLabel("Afficher:")
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Tous les événements", "Événements à venir", "Événements passés"])
        self.filter_combo.currentIndexChanged.connect(self.refresh_events)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        # Scroll area pour les cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.scroll_widget = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(16)
        
        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)
        
        self.refresh_events()
    
    def refresh_events(self):
        """Recharge la liste des événements"""
        # Vider le layout
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        filter_index = self.filter_combo.currentIndex()
        if filter_index == 1:
            evenements = self.evenements_mgr.obtenir_tous_evenements(futurs_seulement=True)
        elif filter_index == 2:
            all_events = self.evenements_mgr.obtenir_tous_evenements()
            today = date.today().isoformat()
            evenements = [e for e in all_events if e['date'] < today]
        else:
            evenements = self.evenements_mgr.obtenir_tous_evenements()
        
        if not evenements:
            empty_label = QLabel("Aucun événement. Cliquez sur '➕ Créer un événement' pour commencer.")
            empty_label.setStyleSheet("color: #9CA3AF; font-size: 13px; padding: 20px;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.scroll_layout.addWidget(empty_label, 0, 0)
            return
        
        for i, event in enumerate(evenements):
            event_card = self.create_event_card(event)
            self.scroll_layout.addWidget(event_card, i // 3, i % 3)
        
        self.scroll_layout.setRowStretch(self.scroll_layout.rowCount(), 1)
        self.scroll_layout.setColumnStretch(3, 1)
    
    def create_event_card(self, event):
        """Crée une carte pour un événement"""
        card = ModernCard()
        card.setMinimumHeight(180)
        card.setMaximumWidth(320)
        card_layout = QVBoxLayout(card)
        card_layout.setSpacing(8)
        
        # Indicateur de statut (passé/à venir)
        today = date.today()
        try:
            event_date = datetime.strptime(event['date'], '%Y-%m-%d').date()
            if event_date < today:
                status_indicator = QFrame()
                status_indicator.setFixedHeight(3)
                status_indicator.setStyleSheet("background-color: #059669; border-radius: 1.5px; border: none;")
                status_label = QLabel("✓ Passé")
                status_label.setStyleSheet("color: #059669; font-size: 11px; font-weight: bold;")
                card_layout.addWidget(status_indicator)
                card_layout.addWidget(status_label)
            else:
                status_indicator = QFrame()
                status_indicator.setFixedHeight(3)
                status_indicator.setStyleSheet("background-color: #4F46E5; border-radius: 1.5px; border: none;")
                status_label = QLabel("📍 À venir")
                status_label.setStyleSheet("color: #4F46E5; font-size: 11px; font-weight: bold;")
                card_layout.addWidget(status_indicator)
                card_layout.addWidget(status_label)
        except:
            pass
        
        # Nom
        nom_label = QLabel(event['nom'])
        nom_label.setStyleSheet("font-size: 15px; font-weight: bold; color: #1F2937;")
        nom_label.setWordWrap(True)
        card_layout.addWidget(nom_label)
        
        # Date et heure
        date_str = event.get('date', '')
        heure_str = event.get('heure', '')
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
            date_formatted = date_obj.strftime('%d/%m/%Y')
        except:
            date_formatted = date_str
        
        datetime_label = QLabel(f"📅 {date_formatted} à {heure_str}")
        datetime_label.setStyleSheet("color: #6B7280; font-size: 12px;")
        card_layout.addWidget(datetime_label)
        
        # Lieu
        lieu = event.get('lieu', '')
        if lieu:
            lieu_label = QLabel(f"📍 {lieu}")
            lieu_label.setStyleSheet("color: #6B7280; font-size: 12px;")
            card_layout.addWidget(lieu_label)
        
        # Groupe
        groupe_id = event.get('groupe_id')
        if groupe_id:
            groupe = self.groupes_mgr.obtenir_groupe(groupe_id)
            if groupe:
                groupe_label = QLabel(f"👥 {groupe['nom']}")
                groupe_label.setStyleSheet(f"color: {groupe['couleur']}; font-size: 11px; font-weight: bold;")
                card_layout.addWidget(groupe_label)
        
        card_layout.addStretch()
        
        # Boutons d'action
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(6)
        
        view_btn = QPushButton("👁️")
        view_btn.setFixedSize(36, 36)
        view_btn.setStyleSheet("""
            QPushButton {
                background-color: #DBEAFE;
                border: 1px solid #93C5FD;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #BFDBFE; }
        """)
        view_btn.clicked.connect(lambda: self.view_event(event['id']))
        
        edit_btn = QPushButton("✏️")
        edit_btn.setFixedSize(36, 36)
        edit_btn.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #E5E7EB; }
        """)
        edit_btn.clicked.connect(lambda: self.edit_event(event['id']))
        
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(36, 36)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #FEE2E2;
                border: 1px solid #FECACA;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #FCA5A5; }
        """)
        delete_btn.clicked.connect(lambda: self.delete_event(event['id'], event['nom']))
        
        actions_layout.addWidget(view_btn)
        actions_layout.addWidget(edit_btn)
        actions_layout.addWidget(delete_btn)
        card_layout.addLayout(actions_layout)
        
        return card
    
    def add_event(self):
        """Crée un nouvel événement"""
        dialog = EventEditorDialog(self.evenements_mgr, self.groupes_mgr, parent=self)
        if dialog.exec():
            self.refresh_events()
            self.events_changed.emit()
    
    def edit_event(self, event_id):
        """Modifie un événement"""
        dialog = EventEditorDialog(self.evenements_mgr, self.groupes_mgr, event_id=event_id, parent=self)
        if dialog.exec():
            self.refresh_events()
            self.events_changed.emit()
    
    def view_event(self, event_id):
        """Affiche les détails d'un événement"""
        event = self.evenements_mgr.obtenir_evenement(event_id)
        if not event:
            QMessageBox.warning(self, "Erreur", "Événement non trouvé.")
            return
        
        presences = self.presences_mgr.obtenir_presences_evenement(event_id)
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Détails: {event['nom']}")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(450)
        layout = QVBoxLayout(dialog)
        
        # Titre
        title = QLabel(event['nom'])
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F2937;")
        layout.addWidget(title)
        
        # Infos
        info_layout = QGridLayout()
        info_layout.setSpacing(10)
        
        info_layout.addWidget(QLabel("Date:"), 0, 0)
        info_layout.addWidget(QLabel(event.get('date', '')), 0, 1)
        
        info_layout.addWidget(QLabel("Heure:"), 1, 0)
        info_layout.addWidget(QLabel(event.get('heure', '')), 1, 1)
        
        info_layout.addWidget(QLabel("Lieu:"), 2, 0)
        info_layout.addWidget(QLabel(event.get('lieu', 'N/A')), 2, 1)
        
        groupe_id = event.get('groupe_id')
        if groupe_id:
            groupe = self.groupes_mgr.obtenir_groupe(groupe_id)
            groupe_nom = groupe['nom'] if groupe else 'N/A'
        else:
            groupe_nom = 'Aucun'
        info_layout.addWidget(QLabel("Groupe:"), 3, 0)
        info_layout.addWidget(QLabel(groupe_nom), 3, 1)
        
        layout.addLayout(info_layout)
        
        # Description
        if event.get('description'):
            layout.addWidget(QLabel("Description:"))
            desc = QTextEdit()
            desc.setPlainText(event['description'])
            desc.setReadOnly(True)
            desc.setMaximumHeight(100)
            layout.addWidget(desc)
        
        # Présences
        layout.addWidget(QLabel(f"Présences ({len(presences)}):"))
        presences_list = QListWidget()
        presences_list.setMaximumHeight(150)
        
        if presences:
            for p in presences:
                status = "✓ Présent" if p.get('present') == 1 else "✗ Absent"
                presences_list.addItem(status)
        else:
            presences_list.addItem("Aucune présence enregistrée")
        
        layout.addWidget(presences_list)
        
        # Bouton fermer
        close_btn = ModernButton("Fermer")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec()
    
    def delete_event(self, event_id, nom):
        """Supprime un événement"""
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Supprimer '{nom}' ?\n\nCette action est irréversible.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.evenements_mgr.supprimer_evenement(event_id)
                QMessageBox.information(self, "Succès", f"'{nom}' a été supprimé.")
                self.refresh_events()
                self.events_changed.emit()
            except Exception as e:
                QMessageBox.warning(self, "Erreur", str(e))