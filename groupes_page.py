from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from group_editor import GroupEditorDialog


class ModernCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #E5E7EB;
                border-radius: 6px;
                padding: 6px;
                margin: 2px;
                transition: all 0.3s ease;
            }
            QFrame:hover {
                border: 1px solid #4F46E5;
                box-shadow: 0 4px 6px rgba(79, 70, 229, 0.1);
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


class GroupsPage(QWidget):
    # Signal pour notifier les autres pages d'un changement
    groups_changed = Signal()
    
    def __init__(self, groupes_mgr, membres_mgr):
        super().__init__()
        self.groupes_mgr = groupes_mgr
        self.membres_mgr = membres_mgr
        self.refresh_timer = QTimer()
        self.init_ui()
        self.setup_signals()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # En-tête
        header_layout = QHBoxLayout()
        title = QLabel("👥 Groupes")
        title.setStyleSheet("font-size: 13px; font-weight: bold; color: #1F2937;")
        header_layout.addWidget(title)
        header_layout.addStretch()

        new_group_btn = ModernButton("➕ Créer un groupe", primary=True)
        new_group_btn.clicked.connect(self.create_group)
        header_layout.addWidget(new_group_btn)
        layout.addLayout(header_layout)

        # Scroll area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self.scroll_widget = QWidget()
        self.scroll_layout = QGridLayout(self.scroll_widget)
        self.scroll_layout.setSpacing(16)

        self.scroll_area.setWidget(self.scroll_widget)
        layout.addWidget(self.scroll_area)

        # Charger les groupes
        self.refresh_groups()

    def setup_signals(self):
        """Configure les signaux et timers"""
        # Timer pour rafraîchir tous les 30 secondes (optionnel)
        self.refresh_timer.timeout.connect(self.refresh_groups)
        self.refresh_timer.start(30000)  # Décommenter si rafraîchissement auto souhaité

    def refresh_groups(self):
        """Recharge et affiche tous les groupes"""
        # Vider le layout
        for i in reversed(range(self.scroll_layout.count())):
            widget = self.scroll_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        # Charger les groupes
        groupes = self.groupes_mgr.obtenir_tous_groupes()

        if not groupes:
            empty_label = QLabel("Aucun groupe créé. Cliquez sur '➕ Créer un groupe' pour commencer.")
            empty_label.setStyleSheet("color: #9CA3AF; font-size: 13px; padding: 20px;")
            empty_label.setAlignment(Qt.AlignCenter)
            self.scroll_layout.addWidget(empty_label, 0, 0)
            return

        for i, groupe in enumerate(groupes):
            group_card = self.create_group_card(groupe)
            self.scroll_layout.addWidget(group_card, i // 3, i % 3)

        # Ajouter du stretch
        self.scroll_layout.setRowStretch(self.scroll_layout.rowCount(), 1)
        self.scroll_layout.setColumnStretch(3, 1)

    def create_group_card(self, groupe):
        """Crée une carte pour un groupe"""
        group_card = ModernCard()
        group_card.setMinimumHeight(160)
        group_card.setMaximumWidth(300)
        group_layout = QVBoxLayout(group_card)
        group_layout.setSpacing(8)

        # Indicateur de couleur
        color_indicator = QFrame()
        color_indicator.setFixedHeight(4)
        color_indicator.setStyleSheet(
            f"background-color: {groupe['couleur']}; border-radius: 2px; border: none;"
        )
        group_layout.addWidget(color_indicator)

        # Nom
        name_label = QLabel(groupe['nom'])
        name_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1F2937; margin: 8px 0;")
        name_label.setWordWrap(True)
        group_layout.addWidget(name_label)

        # Nombre de membres
        count_label = QLabel(f"👥 {groupe['nombre_membres']} membres")
        count_label.setStyleSheet("color: #6B7280; font-size: 14px; margin-bottom: 12px;")
        group_layout.addWidget(count_label)

        # Description (si présente)
        if groupe.get('description'):
            desc_label = QLabel(groupe['description'][:50] + "...")
            desc_label.setStyleSheet("color: #9CA3AF; font-size: 11px; font-style: italic;")
            desc_label.setWordWrap(True)
            group_layout.addWidget(desc_label)

        group_layout.addStretch()

        # Boutons d'action
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(8)

        view_btn = ModernButton("👁️ Voir")
        view_btn.setMaximumHeight(35)
        view_btn.clicked.connect(lambda: self.view_group(groupe['id']))

        edit_btn = ModernButton("✏️ Modifier")
        edit_btn.setMaximumHeight(35)
        edit_btn.clicked.connect(lambda: self.edit_group(groupe['id']))

        delete_btn = ModernButton("🗑️ Supprimer")
        delete_btn.setMaximumHeight(35)
        delete_btn.clicked.connect(lambda: self.delete_group(groupe['id'], groupe['nom']))

        actions_layout.addWidget(view_btn)
        actions_layout.addWidget(edit_btn)
        actions_layout.addWidget(delete_btn)
        group_layout.addLayout(actions_layout)

        return group_card

    def create_group(self):
        """Ouvre le dialog de création de groupe"""
        dialog = GroupEditorDialog(self.groupes_mgr, self.membres_mgr, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_groups()
            self.groups_changed.emit()  # Notifier les autres pages

    def edit_group(self, groupe_id):
        """Ouvre le dialog de modification de groupe"""
        dialog = GroupEditorDialog(self.groupes_mgr, self.membres_mgr, groupe_id=groupe_id, parent=self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_groups()
            self.groups_changed.emit()  # Notifier les autres pages

    def view_group(self, groupe_id):
        """Affiche les détails d'un groupe dans un dialog"""
        groupe = self.groupes_mgr.obtenir_groupe(groupe_id)
        if not groupe:
            QMessageBox.warning(self, "Erreur", "Groupe non trouvé.")
            return
        
        membres = self.membres_mgr.obtenir_membres_du_groupe(groupe_id)

        # Créer un dialog personnalisé
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Détails du groupe: {groupe['nom']}")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)
        layout = QVBoxLayout(dialog)

        # Titre
        title = QLabel(groupe['nom'])
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1F2937;")
        layout.addWidget(title)

        # Informations
        info_layout = QGridLayout()
        info_layout.setSpacing(10)

        # Couleur
        color_box = QFrame()
        color_box.setFixedHeight(30)
        color_box.setFixedWidth(100)
        color_box.setStyleSheet(f"background-color: {groupe['couleur']}; border-radius: 4px; border: 1px solid #E5E7EB;")
        info_layout.addWidget(QLabel("Couleur:"), 0, 0)
        info_layout.addWidget(color_box, 0, 1)

        # Description
        info_layout.addWidget(QLabel("Description:"), 1, 0, Qt.AlignTop)
        desc_text = QTextEdit()
        desc_text.setPlainText(groupe.get('description', 'Aucune description'))
        desc_text.setReadOnly(True)
        desc_text.setMaximumHeight(80)
        info_layout.addWidget(desc_text, 1, 1)

        # Nombre de membres
        info_layout.addWidget(QLabel("Nombre de membres:"), 2, 0)
        count_label = QLabel(str(len(membres)))
        count_label.setStyleSheet("font-weight: bold; color: #4F46E5;")
        info_layout.addWidget(count_label, 2, 1)

        layout.addLayout(info_layout)

        # Liste des membres
        layout.addWidget(QLabel("Membres:"))
        membres_list = QListWidget()
        membres_list.setMaximumHeight(200)
        
        if membres:
            for m in membres:
                item = QListWidgetItem(f"{m['nom']} {m['prenoms']}")
                item.setIcon(self.get_member_icon())
                membres_list.addItem(item)
        else:
            item = QListWidgetItem("Aucun membre dans ce groupe")
            item.setFlags(item.flags() & ~Qt.ItemIsSelectable)
            membres_list.addItem(item)

        layout.addWidget(membres_list)

        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()

        close_btn = QPushButton("Fermer")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #F3F4F6;
                color: #374151;
                border: 1px solid #D1D5DB;
                border-radius: 5px;
                padding: 6px 12px;
            }
            QPushButton:hover { background-color: #E5E7EB; }
        """)
        close_btn.clicked.connect(dialog.accept)
        buttons_layout.addWidget(close_btn)

        layout.addLayout(buttons_layout)
        layout.addStretch()

        dialog.exec()

    def get_member_icon(self):
        """Retourne une icône pour les membres"""
        pixmap = QPixmap(20, 20)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.drawEllipse(2, 2, 16, 16)
        painter.fillRect(2, 2, 16, 16, QColor("#4F46E5"))
        painter.end()
        return QIcon(pixmap)

    def delete_group(self, groupe_id, nom_groupe):
        """Supprime un groupe après confirmation"""
        reply = QMessageBox.question(
            self,
            "Confirmer la suppression",
            f"Êtes-vous sûr de vouloir supprimer le groupe '{nom_groupe}' ?\n\nCette action est irréversible.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self.groupes_mgr.supprimer_groupe(groupe_id):
                QMessageBox.information(self, "Succès", f"Le groupe '{nom_groupe}' a été supprimé.")
                self.refresh_groups()
                self.groups_changed.emit()  # Notifier les autres pages
            else:
                QMessageBox.warning(self, "Erreur", "Impossible de supprimer le groupe.")

    def closeEvent(self, event):
        """Nettoie les ressources avant fermeture"""
        self.refresh_timer.stop()
        super().closeEvent(event)