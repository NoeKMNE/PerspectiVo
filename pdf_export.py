"""
Module d'export PDF pour les statistiques
"""

from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import tempfile
import os


class PDFExporter:
    """Génère des rapports PDF avec les statistiques et graphiques"""
    
    def __init__(self, titre_rapport="Rapport Statistiques"):
        self.titre_rapport = titre_rapport
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Configure les styles personnalisés"""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor("#4F46E5"),
            spaceAfter=30,
            alignment=1  # Center
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionTitle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor("#1F2937"),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        self.styles.add(ParagraphStyle(
            name='TableHeader',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.white,
            backColor=colors.HexColor("#4F46E5"),
            alignment=1,
            fontName='Helvetica-Bold'
        ))
    
    def export_stats_report(self, filepath, stats_data, canvases_dict):
        """
        Exporte un rapport PDF complet avec statistiques et graphiques
        
        Args:
            filepath: Chemin du fichier PDF
            stats_data: Dict contenant les données statistiques
            canvases_dict: Dict des canvas matplotlib avec clés comme 'ecoles', 'filieres', etc.
        """
        doc = SimpleDocTemplate(
            filepath,
            pagesize=landscape(A4),
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )
        
        story = []
        
        # En-tête
        story.append(Paragraph(self.titre_rapport, self.styles['CustomTitle']))
        story.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}",
            self.styles['Normal']
        ))
        story.append(Spacer(1, 0.3 * inch))
        
        # Section Résumé
        story.append(Paragraph("Résumé Général", self.styles['SectionTitle']))
        
        # Tableau de résumé
        summary_data = [
            ["Métrique", "Valeur"],
            ["Nombre de membres", str(stats_data.get('total_membres', 0))],
            ["Nombre de groupes", str(stats_data.get('total_groupes', 0))],
            ["Nombre d'événements", str(stats_data.get('total_evenements', 0))],
            ["Événements à venir", str(stats_data.get('evenements_futurs', 0))],
            ["Assiduité moyenne", f"{stats_data.get('presence_moyenne', 0):.1f}%"],
        ]
        
        summary_table = Table(summary_data, colWidths=[3.5 * inch, 2 * inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4F46E5")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F9FAFB")),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#E5E7EB")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.4 * inch))
        
        # Graphiques
        story.append(Paragraph("Analyses Détaillées", self.styles['SectionTitle']))
        
        # Ajouter les graphiques
        canvas_configs = [
            ('ecoles_canvas', 'Répartition par École', 4.5 * inch, 3 * inch),
            ('filieres_canvas', 'Répartition par Filière', 4.5 * inch, 3 * inch),
            ('residence_canvas', 'Répartition par Résidence', 4.5 * inch, 3 * inch),
        ]
        
        for canvas_key, title, width, height in canvas_configs:
            if canvas_key in canvases_dict:
                story.append(Paragraph(title, self.styles['SectionTitle']))
                
                # Sauvegarder le canvas en image temporaire
                img_path = self._save_canvas_image(canvases_dict[canvas_key])
                if img_path:
                    story.append(Image(img_path, width=width, height=height))
                    story.append(Spacer(1, 0.3 * inch))
        
        story.append(PageBreak())
        
        # Graphiques de tendance
        story.append(Paragraph("Évolution et Tendances", self.styles['SectionTitle']))
        story.append(Spacer(1, 0.2 * inch))
        
        if 'evolution_canvas' in canvases_dict:
            story.append(Paragraph("Évolution des Inscriptions", self.styles['SectionTitle']))
            img_path = self._save_canvas_image(canvases_dict['evolution_canvas'])
            if img_path:
                story.append(Image(img_path, width=8 * inch, height=3 * inch))
                story.append(Spacer(1, 0.3 * inch))
        
        if 'tendance_canvas' in canvases_dict:
            story.append(Paragraph("Tendance des Présences", self.styles['SectionTitle']))
            img_path = self._save_canvas_image(canvases_dict['tendance_canvas'])
            if img_path:
                story.append(Image(img_path, width=8 * inch, height=3 * inch))
                story.append(Spacer(1, 0.3 * inch))
        
        story.append(PageBreak())
        
        # Analyse des membres
        story.append(Paragraph("Analyse des Membres", self.styles['SectionTitle']))
        story.append(Spacer(1, 0.2 * inch))
        
        if 'top_membres_canvas' in canvases_dict:
            story.append(Paragraph("Top 10 Membres les Plus Actifs", self.styles['SectionTitle']))
            img_path = self._save_canvas_image(canvases_dict['top_membres_canvas'])
            if img_path:
                story.append(Image(img_path, width=8 * inch, height=3.5 * inch))
                story.append(Spacer(1, 0.3 * inch))
        
        if 'ecole_stats_canvas' in canvases_dict:
            story.append(Paragraph("Assiduité par École", self.styles['SectionTitle']))
            img_path = self._save_canvas_image(canvases_dict['ecole_stats_canvas'])
            if img_path:
                story.append(Image(img_path, width=8 * inch, height=3.5 * inch))
                story.append(Spacer(1, 0.3 * inch))
        
        story.append(PageBreak())
        
        # Analyse des présences
        story.append(Paragraph("Analyse des Présences", self.styles['SectionTitle']))
        story.append(Spacer(1, 0.2 * inch))
        
        if 'presence_canvas' in canvases_dict:
            story.append(Paragraph("Distribution des Taux de Présence", self.styles['SectionTitle']))
            img_path = self._save_canvas_image(canvases_dict['presence_canvas'])
            if img_path:
                story.append(Image(img_path, width=5 * inch, height=3 * inch))
                story.append(Spacer(1, 0.3 * inch))
        
        if 'risque_canvas' in canvases_dict:
            story.append(Paragraph("Membres avec Faible Assiduité (<70%)", self.styles['SectionTitle']))
            img_path = self._save_canvas_image(canvases_dict['risque_canvas'])
            if img_path:
                story.append(Image(img_path, width=8 * inch, height=3.5 * inch))
                story.append(Spacer(1, 0.3 * inch))
        
        story.append(PageBreak())
        
        # Analyse des groupes
        story.append(Paragraph("Analyse des Groupes", self.styles['SectionTitle']))
        story.append(Spacer(1, 0.2 * inch))
        
        if 'groupes_size_canvas' in canvases_dict:
            story.append(Paragraph("Taille des Groupes", self.styles['SectionTitle']))
            img_path = self._save_canvas_image(canvases_dict['groupes_size_canvas'])
            if img_path:
                story.append(Image(img_path, width=5 * inch, height=3 * inch))
                story.append(Spacer(1, 0.3 * inch))
        
        if 'groupe_assiduite_canvas' in canvases_dict:
            story.append(Paragraph("Assiduité par Groupe", self.styles['SectionTitle']))
            img_path = self._save_canvas_image(canvases_dict['groupe_assiduite_canvas'])
            if img_path:
                story.append(Image(img_path, width=5 * inch, height=3 * inch))
                story.append(Spacer(1, 0.3 * inch))
        
        if 'groupe_compare_canvas' in canvases_dict:
            story.append(Paragraph("Comparaison Détaillée des Groupes", self.styles['SectionTitle']))
            img_path = self._save_canvas_image(canvases_dict['groupe_compare_canvas'])
            if img_path:
                story.append(Image(img_path, width=8 * inch, height=3.5 * inch))
                story.append(Spacer(1, 0.3 * inch))
        
        # Pied de page
        story.append(Spacer(1, 0.5 * inch))
        story.append(Paragraph(
            f"Rapport généré automatiquement par PerspectiVo le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}",
            self.styles['Normal']
        ))
        
        # Construire le PDF
        doc.build(story)
    
    def _save_canvas_image(self, canvas, dpi=150):
        """
        Sauvegarde un canvas matplotlib en image PNG
        
        Args:
            canvas: Le FigureCanvas matplotlib
            dpi: Qualité de l'image
        
        Returns:
            Chemin du fichier image temporaire ou None
        """
        try:
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmpfile:
                canvas.figure.savefig(tmpfile.name, format='png', dpi=dpi, bbox_inches='tight')
                return tmpfile.name
        except Exception as e:
            print(f"Erreur sauvegarde image: {e}")
            return None
    
    @staticmethod
    def cleanup_temp_files(image_paths):
        """Nettoie les fichiers temporaires"""
        for path in image_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                print(f"Erreur suppression {path}: {e}")