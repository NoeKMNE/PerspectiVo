from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QTextEdit,QHBoxLayout, QComboBox, QListWidget, \
    QListWidgetItem, QMessageBox, QPushButton


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

class GroupEditorDialog(QDialog):
    """Dialog pour créer ou modifier un groupe"""

    def __init__(self, groupes_mgr, membres_mgr, groupe_id=None, parent=None):
        super().__init__(parent)
        self.groupes_mgr = groupes_mgr
        self.membres_mgr = membres_mgr
        self.groupe_id = groupe_id
        self.selected_members = []

        self.setWindowTitle("Nouveau groupe" if groupe_id is None else "Modifier le groupe")
        self.setFixedSize(600, 700)
        self.setModal(True)
        self.init_ui()

        # Si on modifie un groupe existant, charger ses données
        if self.groupe_id:
            self.load_groupe_data()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)

        # Titre
        title = QLabel("Nouveau groupe" if self.groupe_id is None else "Modifier le groupe")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F2937; margin-bottom: 16px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Nom du groupe
        nom_label = QLabel("Nom du groupe *")
        nom_label.setStyleSheet("font-weight: bold; color: #374151; margin-bottom: 4px;")
        layout.addWidget(nom_label)

        self.nom_input = QLineEdit()
        self.nom_input.setPlaceholderText("Ex: Jeunes Adultes")
        self.nom_input.setFixedHeight(40)
        self.nom_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #4F46E5;
                outline: none;
            }
        """)
        layout.addWidget(self.nom_input)

        # Description
        desc_label = QLabel("Description")
        desc_label.setStyleSheet("font-weight: bold; color: #374151; margin-bottom: 4px;")
        layout.addWidget(desc_label)

        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Description du groupe...")
        self.description_input.setMaximumHeight(80)
        self.description_input.setStyleSheet("""
            QTextEdit {
                padding: 10px 12px;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                font-size: 14px;
                background-color: white;
            }
            QTextEdit:focus {
                border-color: #4F46E5;
                outline: none;
            }
        """)
        layout.addWidget(self.description_input)

        # Couleur
        color_layout = QHBoxLayout()
        color_label = QLabel("Couleur du groupe")
        color_label.setStyleSheet("font-weight: bold; color: #374151;")
        color_layout.addWidget(color_label)

        self.color_combo = QComboBox()
        self.color_combo.setFixedHeight(40)
        self.colors = {
            "Indigo": "#4F46E5",
            "Vert": "#059669",
            "Rouge": "#DC2626",
            "Marron": "#7C2D12",
            "Violet": "#9333EA",
            "Orange": "#EA580C",
            "Bleu": "#2563EB",
            "Rose": "#DB2777"
        }
        for name, color in self.colors.items():
            self.color_combo.addItem(name, color)
        color_layout.addWidget(self.color_combo)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        # Section sélection des membres
        membres_section_label = QLabel("Sélectionner les membres")
        membres_section_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #1F2937; margin-top: 12px; margin-bottom: 8px;")
        layout.addWidget(membres_section_label)

        # Barre de recherche pour les membres
        search_layout = QHBoxLayout()
        self.search_membres_input = QLineEdit()
        self.search_membres_input.setPlaceholderText("Rechercher un membre...")
        self.search_membres_input.setFixedHeight(40)
        self.search_membres_input.setStyleSheet("""
            QLineEdit {
                padding: 10px 12px;
                border: 1px solid #D1D5DB;
                border-radius: 6px;
                font-size: 14px;
                background-color: white;
            }
        """)
        self.search_membres_input.textChanged.connect(self.filter_membres)
        search_layout.addWidget(self.search_membres_input)
        layout.addLayout(search_layout)

        # Liste des membres avec checkboxes
        self.membres_list = QListWidget()
        self.membres_list.setMaximumHeight(250)
        self.membres_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #D1D5DB;
                border-radius: 8px;
                background-color: white;
                padding: 4px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #F3F4F6;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:hover {
                background-color: #F9FAFB;
            }
            
        """)
        layout.addWidget(self.membres_list)

        # Charger tous les membres
        self.load_membres()

        # Compteur de membres sélectionnés
        self.count_label = QLabel("Membres sélectionnés : 0")
        self.count_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #4F46E5; margin-top: 8px;")
        layout.addWidget(self.count_label)

        layout.addStretch()

        # Note
        note = QLabel("* Champs obligatoires")
        note.setStyleSheet("color: #DC2626; font-size: 12px; font-style: italic;")
        layout.addWidget(note)

        # Boutons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)

        cancel_btn = ModernButton("Annuler")
        cancel_btn.clicked.connect(self.reject)

        save_text = "Créer le groupe" if self.groupe_id is None else "Enregistrer les modifications"
        save_btn = ModernButton(save_text, primary=True)
        save_btn.clicked.connect(self.validate_and_save)

        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)
        layout.addLayout(buttons_layout)

    def load_membres(self):
        """Charge tous les membres dans la liste avec des checkboxes"""
        self.membres_list.clear()
        tous_membres = self.membres_mgr.obtenir_tous_membres()

        for membre in tous_membres:
            item = QListWidgetItem(f"{membre['nom']} {membre['prenoms']}")
            item.setData(Qt.UserRole, membre['id'])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.membres_list.addItem(item)

        # Connecter le signal de changement
        self.membres_list.itemChanged.connect(self.update_count)

    def filter_membres(self):
        """Filtre la liste des membres selon la recherche"""
        search_text = self.search_membres_input.text().lower()

        for i in range(self.membres_list.count()):
            item = self.membres_list.item(i)
            item_text = item.text().lower()
            item.setHidden(search_text not in item_text)

    def update_count(self):
        """Met à jour le compteur de membres sélectionnés"""
        count = 0
        for i in range(self.membres_list.count()):
            item = self.membres_list.item(i)
            if item.checkState() == Qt.Checked:
                count += 1

        self.count_label.setText(f"Membres sélectionnés : {count}")

    def load_groupe_data(self):
        """Charge les données d'un groupe existant"""
        groupe = self.groupes_mgr.obtenir_groupe(self.groupe_id)
        if groupe:
            self.nom_input.setText(groupe['nom'])
            self.description_input.setPlainText(groupe.get('description', ''))

            # Sélectionner la couleur
            couleur = groupe.get('couleur', '#4F46E5')
            index = self.color_combo.findData(couleur)
            if index >= 0:
                self.color_combo.setCurrentIndex(index)

            # Cocher les membres du groupe
            membres_groupe = self.groupes_mgr.obtenir_membres_groupe(self.groupe_id)
            membres_ids = [m['id'] for m in membres_groupe]

            for i in range(self.membres_list.count()):
                item = self.membres_list.item(i)
                membre_id = item.data(Qt.UserRole)
                if membre_id in membres_ids:
                    item.setCheckState(Qt.Checked)

    def validate_and_save(self):
        """Valide et sauvegarde le groupe"""
        nom = self.nom_input.text().strip()

        if not nom:
            QMessageBox.warning(self, "Erreur", "Le nom du groupe est obligatoire.")
            self.nom_input.setFocus()
            return

        description = self.description_input.toPlainText().strip()
        couleur = self.color_combo.currentData()

        # Récupérer les membres sélectionnés
        selected_members = []
        for i in range(self.membres_list.count()):
            item = self.membres_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_members.append(item.data(Qt.UserRole))
        try:
            if self.groupe_id is None:
                # Créer un nouveau groupe
                groupe_id = self.groupes_mgr.ajouter_groupe(nom, description, couleur)
                # Ajouter les membres au groupe
                for membre_id in selected_members:
                    self.groupes_mgr.ajouter_membre_groupe(membre_id, groupe_id)

                QMessageBox.information(self, "Succès", f"Groupe '{nom}' créé avec {len(selected_members)} membre(s)!")
            else:
                # Modifier le groupe existant
                # Mettre à jour les informations du groupe
                self.groupes_mgr.modifier_groupe(
                    self.groupe_id,
                    nom=nom,
                    description=description,
                    couleur=couleur
                )

                # Récupérer les membres actuels
                membres_actuels = self.groupes_mgr.obtenir_membres_du_groupe(self.groupe_id)
                membres_actuels_ids = [m['id'] for m in membres_actuels]

                # Retirer les membres qui ne sont plus sélectionnés
                for membre_id in membres_actuels_ids:
                    if membre_id not in selected_members:
                        self.groupes_mgr.retirer_membre_du_groupe(membre_id, self.groupe_id)

                # Ajouter les nouveaux membres
                for membre_id in selected_members:
                    if membre_id not in membres_actuels_ids:
                        self.groupes_mgr.ajouter_membre_au_groupe(membre_id, self.groupe_id)

                QMessageBox.information(self, "Succès",
                                        f"Groupe '{nom}' modifié avec {len(selected_members)} membre(s)!")

            self.accept()

        except ValueError as e:
            QMessageBox.warning(self, "Erreur", str(e))
