from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                               QFrame, QComboBox, QScrollArea, QTabWidget, QFileDialog, QMessageBox, QProgressBar)
from PySide6.QtCore import Qt, QThread, Signal
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from collections import Counter
from datetime import datetime, timedelta
import json
import tempfile
from pdf_export import PDFExporter


class MplCanvas(FigureCanvas):
    """Canvas pour matplotlib"""
    def __init__(self, parent=None, width=3, height=2, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi, facecolor='white')
        self.axes = fig.add_subplot(111)
        self.axes.spines['top'].set_visible(False)
        self.axes.spines['right'].set_visible(False)
        self.axes.spines['left'].set_color('#E5E7EB')
        self.axes.spines['left'].set_linewidth(0.8)
        self.axes.spines['bottom'].set_color('#E5E7EB')
        self.axes.spines['bottom'].set_linewidth(0.8)
        super().__init__(fig)
        self.setParent(parent)


class StatisticsWorker(QThread):
    """Worker pour calculer les stats sans bloquer l'UI"""
    progress = Signal(str)
    finished = Signal(dict)
    
    def __init__(self, membres_mgr, evenements_mgr, groupes_mgr, presences_mgr, 
                 filtre_periode, filtre_groupe):
        super().__init__()
        self.membres_mgr = membres_mgr
        self.evenements_mgr = evenements_mgr
        self.groupes_mgr = groupes_mgr
        self.presences_mgr = presences_mgr
        self.filtre_periode = filtre_periode
        self.filtre_groupe = filtre_groupe
    
    def run(self):
        try:
            self.progress.emit("Chargement des données...")
            results = {}
            
            # 1. Membres filtrés
            membres = self._get_filtered_membres()
            results['membres'] = membres
            
            # 2. Stats de base
            self.progress.emit("Calcul des statistiques...")
            results['total_membres'] = len(membres)
            results['total_groupes'] = len(self.groupes_mgr.obtenir_tous_groupes())
            results['total_evenements'] = len(self.evenements_mgr.obtenir_tous_evenements())
            results['evenements_futurs'] = len(self.evenements_mgr.obtenir_tous_evenements(futurs_seulement=True))
            
            # 3. Taux de présence
            self.progress.emit("Calcul des taux de présence...")
            taux_moyens = []
            taux_dict = {}
            for m in membres:
                taux = self.membres_mgr.calculer_taux_presence(m['id'])
                taux_moyens.append(taux)
                taux_dict[m['id']] = taux
            
            results['presence_moyenne'] = sum(taux_moyens) / len(taux_moyens) if taux_moyens else 0
            results['taux_par_membre'] = taux_dict
            
            # 4. Données pour graphiques
            self.progress.emit("Préparation des graphiques...")
            results['ecoles_data'] = self._prepare_ecoles_data(membres)
            results['filieres_data'] = self._prepare_filieres_data(membres)
            results['residences_data'] = self._prepare_residences_data(membres)
            results['evolution_data'] = self._prepare_evolution_data()
            results['top_membres_data'] = self._prepare_top_membres(membres, taux_dict)
            results['ecole_stats_data'] = self._prepare_ecole_stats(membres, taux_dict)
            results['presence_distribution'] = taux_moyens
            results['tendance_data'] = self._prepare_tendance_data()
            results['risque_data'] = self._prepare_risque_data(membres, taux_dict)
            results['groupes_data'] = self._prepare_groupes_data(taux_dict)
            
            self.progress.emit("Terminé!")
            self.finished.emit(results)
        
        except Exception as e:
            print(f"Erreur: {e}")
            import traceback
            traceback.print_exc()
    
    def _get_filtered_membres(self):
        membres = self.membres_mgr.obtenir_tous_membres()
        
        if self.filtre_groupe:
            membres_groupe = self.groupes_mgr.obtenir_membres_du_groupe(self.filtre_groupe)
            membres_ids = [m['id'] for m in membres_groupe]
            membres = [m for m in membres if m['id'] in membres_ids]
        
        if self.filtre_periode != "all":
            now = datetime.now()
            if self.filtre_periode == "month":
                date_limite = now - timedelta(days=30)
            elif self.filtre_periode == "quarter":
                date_limite = now - timedelta(days=90)
            elif self.filtre_periode == "year":
                date_limite = now - timedelta(days=365)
            else:
                return membres
            
            membres_filtres = []
            for m in membres:
                date_str = m.get('date_inscription', '')
                if date_str:
                    try:
                        date = datetime.fromisoformat(date_str.split()[0])
                        if date >= date_limite:
                            membres_filtres.append(m)
                    except:
                        pass
            membres = membres_filtres
        
        return membres
    
    def _prepare_ecoles_data(self, membres):
        ecoles = [m['ecole'] for m in membres if m['ecole']]
        return dict(Counter(ecoles))
    
    def _prepare_filieres_data(self, membres):
        filieres = [m['filiere'] for m in membres if m['filiere']]
        return dict(Counter(filieres))
    
    def _prepare_residences_data(self, membres):
        residences = [m['residence'] for m in membres if m['residence']]
        return dict(Counter(residences))
    
    def _prepare_evolution_data(self):
        membres = self.membres_mgr.obtenir_tous_membres()
        dates_inscription = []
        for m in membres:
            date_str = m.get('date_inscription', '')
            if date_str:
                try:
                    date = datetime.fromisoformat(date_str.split()[0])
                    dates_inscription.append(date)
                except:
                    pass
        
        if not dates_inscription:
            return {'labels': [], 'values': []}
        
        dates_inscription.sort()
        date_min = dates_inscription[0]
        date_max = datetime.now()
        
        mois_labels = []
        counts = []
        current_date = date_min.replace(day=1)
        
        while current_date <= date_max:
            count_month = sum(1 for d in dates_inscription if d <= current_date)
            mois_labels.append(current_date.strftime('%b %y'))
            counts.append(count_month)
            
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return {'labels': mois_labels, 'values': counts}
    
    def _prepare_top_membres(self, membres, taux_dict):
        membres_avec_taux = []
        for m in membres:
            taux = taux_dict.get(m['id'], 0)
            if taux > 0:
                membres_avec_taux.append({
                    'nom': f"{m['nom']} {m['prenoms']}"[:25],
                    'taux': taux
                })
        
        membres_avec_taux.sort(key=lambda x: x['taux'], reverse=True)
        return membres_avec_taux[:10]
    
    def _prepare_ecole_stats(self, membres, taux_dict):
        ecoles = [m['ecole'] for m in membres if m['ecole']]
        ecole_counts = Counter(ecoles)
        
        ecole_assiduite = {}
        for ecole in ecole_counts.keys():
            membres_ecole = [m for m in membres if m['ecole'] == ecole]
            taux = [taux_dict.get(m['id'], 0) for m in membres_ecole]
            ecole_assiduite[ecole] = sum(taux) / len(taux) if taux else 0
        
        return sorted(ecole_assiduite.items(), key=lambda x: x[1], reverse=True)
    
    def _prepare_tendance_data(self):
        evenements = self.evenements_mgr.obtenir_tous_evenements()
        if not evenements:
            return {'labels': [], 'values': []}
        
        evenements_sorted = sorted(evenements, key=lambda e: e['date'])
        recent_events = evenements_sorted[-10:]
        
        labels = []
        taux_presence = []
        
        for event in recent_events:
            presences = self.presences_mgr.obtenir_presences_evenement(event['id'])
            if presences:
                presents = sum(1 for p in presences if p.get('present') == 1)
                total = len(presences)
                taux = (presents / total * 100) if total > 0 else 0
                taux_presence.append(taux)
                labels.append(event['nom'][:15])
        
        return {'labels': labels, 'values': taux_presence}
    
    def _prepare_risque_data(self, membres, taux_dict):
        membres_risque = []
        for m in membres:
            taux = taux_dict.get(m['id'], 0)
            if 0 < taux < 70:
                membres_risque.append({
                    'nom': f"{m['nom']} {m['prenoms']}"[:25],
                    'taux': taux
                })
        
        membres_risque.sort(key=lambda x: x['taux'])
        return membres_risque[:15]
    
    def _prepare_groupes_data(self, taux_dict):
        groupes = self.groupes_mgr.obtenir_tous_groupes()
        groupe_data = []
        
        for g in groupes:
            membres = self.groupes_mgr.obtenir_membres_du_groupe(g['id'])
            if membres:
                taux = [taux_dict.get(m['id'], 0) for m in membres]
                moyenne = sum(taux) / len(taux) if taux else 0
                groupe_data.append({
                    'nom': g['nom'][:20],
                    'assiduite': moyenne,
                    'couleur': g['couleur'],
                    'taille': len(membres)
                })
        
        return groupe_data


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
                    padding: 10px 20px;
                    font-size: 14px;
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
                border-radius: 12px;
                padding: 1px;
            }
        """)


class StatisticsPage(QWidget):
    def __init__(self, membres_mgr, evenements_mgr, groupes_mgr, presences_mgr):
        super().__init__()
        self.membres_mgr = membres_mgr
        self.evenements_mgr = evenements_mgr
        self.groupes_mgr = groupes_mgr
        self.presences_mgr = presences_mgr
        
        self.filtre_periode = "all"
        self.filtre_groupe = None
        self.worker = None
        self.stats_data = {}
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # En-tête
        header_layout = QHBoxLayout()
        title = QLabel("📊 Tableau de bord")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1F2937;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        export_btn = ModernButton("📥 Exporter en JSON")
        export_btn.clicked.connect(self.export_stats)
        header_layout.addWidget(export_btn)
        
        export_pdf_btn = ModernButton("📄 Exporter en PDF", primary=True)
        export_pdf_btn.clicked.connect(self.export_to_pdf)
        header_layout.addWidget(export_pdf_btn)
        
        refresh_btn = ModernButton("🔄 Actualiser", primary=True)
        refresh_btn.clicked.connect(self.refresh_stats)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximum(0)  # Indéterminé
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Filtres
        filters_layout = QHBoxLayout()
        
        periode_label = QLabel("Période:")
        self.periode_combo = QComboBox()
        self.periode_combo.addItems(["Toutes périodes", "30 derniers jours", "3 derniers mois", "Cette année"])
        self.periode_combo.currentIndexChanged.connect(self.on_filtre_changed)
        filters_layout.addWidget(periode_label)
        filters_layout.addWidget(self.periode_combo)
        
        groupe_label = QLabel("Groupe:")
        self.groupe_combo = QComboBox()
        self.load_groupes_filter()
        self.groupe_combo.currentIndexChanged.connect(self.on_filtre_changed)
        filters_layout.addWidget(groupe_label)
        filters_layout.addWidget(self.groupe_combo)
        
        filters_layout.addStretch()
        
        self.update_label = QLabel("")
        self.update_label.setStyleSheet("color: #9CA3AF; font-size: 11px;")
        filters_layout.addWidget(self.update_label)
        
        layout.addLayout(filters_layout)
        
        # Cartes de stats (placeholder)
        self.cards_layout = QHBoxLayout()
        self.stat_cards = []
        layout.addLayout(self.cards_layout)
        
        # Onglets
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #E5E7EB; border-radius: 8px; }
            QTabBar::tab {
                background-color: #F3F4F6; color: #6B7280; padding: 8px 16px;
                border-top-left-radius: 6px; border-top-right-radius: 6px;
            }
            QTabBar::tab:selected { background-color: white; color: #4F46E5; font-weight: bold; }
        """)
        
        self.overview_tab = QWidget()
        self.tabs.addTab(self.overview_tab, "Vue d'ensemble")
        
        layout.addWidget(self.tabs)
        
        # Lancer le chargement initial
        self.refresh_stats()
    
    def load_groupes_filter(self):
        self.groupe_combo.clear()
        self.groupe_combo.addItem("Tous les groupes", None)
        groupes = self.groupes_mgr.obtenir_tous_groupes()
        for g in groupes:
            self.groupe_combo.addItem(g['nom'], g['id'])
    
    def on_filtre_changed(self):
        periode_index = self.periode_combo.currentIndex()
        self.filtre_periode = ["all", "month", "quarter", "year"][periode_index]
        self.filtre_groupe = self.groupe_combo.currentData()
        self.refresh_stats()
    
    def refresh_stats(self):
        # Arrêter le worker précédent
        if self.worker and self.worker.isRunning():
            self.worker.wait()
        
        # Lancer le worker
        self.progress_bar.setVisible(True)
        self.worker = StatisticsWorker(
            self.membres_mgr, self.evenements_mgr, 
            self.groupes_mgr, self.presences_mgr,
            self.filtre_periode, self.filtre_groupe
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_stats_ready)
        self.worker.start()
    
    def on_progress(self, message):
        self.update_label.setText(message)
    
    def on_stats_ready(self, results):
        self.stats_data = results
        self.progress_bar.setVisible(False)
        self.update_label.setText(f"Mise à jour: {datetime.now().strftime('%H:%M:%S')}")
        self.update_stat_cards()
    
    def update_stat_cards(self):
        for card in self.stat_cards:
            card.setParent(None)
        self.stat_cards.clear()
        
        data = self.stats_data
        stats = [
            ("Membres", str(data.get('total_membres', 0)), "#4F46E5", "👥"),
            ("Groupes", str(data.get('total_groupes', 0)), "#059669", "👨‍👩‍👧‍👦"),
            ("Événements", str(data.get('total_evenements', 0)), "#DC2626", "📅"),
            ("À venir", str(data.get('evenements_futurs', 0)), "#EA580C", "🔜"),
            ("Assiduité moy.", f"{data.get('presence_moyenne', 0):.1f}%", "#9333EA", "📈"),
        ]
        
        for title, value, color, icon in stats:
            card = ModernCard()
            card.setMinimumHeight(85)
            card.setMinimumWidth(160)
            layout = QVBoxLayout(card)
            layout.setContentsMargins(12, 10, 12, 10)
            
            icon_label = QLabel(icon)
            icon_label.setStyleSheet(f"font-size: 20px; color: {color};")
            value_label = QLabel(value)
            value_label.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {color};")
            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 11px; color: #6B7280;")
            
            layout.addWidget(icon_label)
            layout.addWidget(value_label)
            layout.addWidget(title_label)
            layout.addStretch()
            
            self.stat_cards.append(card)
            self.cards_layout.addWidget(card)
        
        self.cards_layout.addStretch()
    
    def export_stats(self):
        """Exporte les stats en JSON"""
        export_data = {
            'date_export': datetime.now().isoformat(),
            'totaux': {
                'membres': self.stats_data.get('total_membres', 0),
                'groupes': self.stats_data.get('total_groupes', 0),
                'evenements': self.stats_data.get('total_evenements', 0),
            },
            'presence_moyenne': self.stats_data.get('presence_moyenne', 0),
        }
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exporter en JSON", 
            f"stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON Files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "Succès", f"Exporté vers:\n{filename}")
            except Exception as e:
                QMessageBox.warning(self, "Erreur", str(e))
    
    def export_to_pdf(self):
        """Exporte un rapport PDF complet avec graphiques"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Exporter en PDF",
            f"rapport_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
            "PDF Files (*.pdf)"
        )
        
        if not filename:
            return
        
        try:
            # Montrer un message de progression
            progress_msg = QMessageBox(self)
            progress_msg.setWindowTitle("Export PDF")
            progress_msg.setText("Génération du rapport PDF en cours...\nCela peut prendre quelques secondes.")
            progress_msg.setIcon(QMessageBox.Information)
            progress_msg.setStandardButtons(QMessageBox.NoButton)
            progress_msg.show()
            
            # Préparer les canvas
            canvases = {
                'ecoles_canvas': self.ecoles_canvas,
                'filieres_canvas': self.filieres_canvas,
                'residence_canvas': self.residence_canvas,
                'evolution_canvas': self.evolution_canvas,
                'top_membres_canvas': self.top_membres_canvas,
                'ecole_stats_canvas': self.ecole_stats_canvas,
                'presence_canvas': self.presence_canvas,
                'tendance_canvas': self.tendance_canvas,
                'risque_canvas': self.risque_canvas,
                'groupes_size_canvas': self.groupes_size_canvas,
                'groupe_assiduite_canvas': self.groupe_assiduite_canvas,
                'groupe_compare_canvas': self.groupe_compare_canvas,
            }
            
            # Créer l'exporteur et générer le PDF
            exporter = PDFExporter(titre_rapport="PerspectiVo - Rapport Statistiques")
            exporter.export_stats_report(filename, self.stats_data, canvases)
            
            progress_msg.close()
            
            QMessageBox.information(
                self,
                "Succès",
                f"Rapport PDF généré avec succès!\n\nEmplacement:\n{filename}"
            )
        
        except Exception as e:
            QMessageBox.warning(self, "Erreur lors de l'export PDF", str(e))
            print(f"Erreur export PDF: {e}")
            import traceback
            traceback.print_exc()