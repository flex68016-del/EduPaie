# =============================================================================
# receipt_preview_dialog.py - Dialogue d'aperçu des reçus
# =============================================================================
# Rôle : Affiche un aperçu du reçu PDF généré par receipt_service.
# =============================================================================
# Ce fichier utilise :
# - PySide6.QtWidgets pour le dialogue et les boutons
# - PySide6.QtPdfWidgets pour l'affichage du PDF (QPdfView, QPdfDocument)
# - PySide6.QtGui pour l'impression (QPrinter, QPainter)
# - PySide6.QtCore pour les signaux et la gestion des fichiers temporaires
# - edupaie.services.receipt_service pour la génération du PDF
# - edupaie.utils.paths pour le dossier utilisateur (fichiers temporaires)
# =============================================================================
# Ce fichier est utilisé par :
# - ui/payment_dialog.py pour l'aperçu après un paiement
# - ui/student_detail.py pour l'aperçu depuis l'historique
# =============================================================================

import os
import tempfile
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QToolBar, QFileDialog, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, QTemporaryFile
from PySide6.QtGui import QAction, QIcon, QPageLayout, QPageSize
from PySide6.QtPdfWidgets import QPdfView
from PySide6.QtPdf import QPdfDocument
from PySide6.QtPrintSupport import QPrinter, QPrintDialog
from edupaie.services.receipt_service import ReceiptService
from edupaie.utils.paths import user_data_dir


class ReceiptPreviewDialog(QDialog):
    """
    Dialogue d'aperçu du reçu PDF.
    
    Responsabilité : Afficher le reçu généré par receipt_service dans un
    viewer PDF avec options de zoom, enregistrement et impression.
    
    Pourquoi QDialog : Fenêtre modale pour visualiser le reçu avant de
    l'enregistrer ou de l'imprimer.
    
    Cycle de vie du fichier temporaire :
    1. Génération du PDF via receipt_service dans un fichier temporaire
    2. Chargement du fichier dans QPdfDocument pour l'affichage
    3. Suppression du fichier temporaire à la fermeture du dialogue
    
    Pourquoi un fichier temporaire : receipt_service génère un PDF sur disque,
    mais nous ne voulons pas le conserver dans le dossier de l'utilisateur.
    Le fichier temporaire permet de visualiser et d'imprimer sans polluer
    le système de fichiers.
    """
    
    def __init__(self, payment_id: int, receipt_service: ReceiptService, parent=None) -> None:
        """
        Initialise le dialogue d'aperçu.
        
        Args:
            payment_id: ID du paiement pour générer le reçu
            receipt_service: Service de génération des reçus
            parent: Widget parent
        """
        super().__init__(parent)
        
        self.payment_id = payment_id
        self.receipt_service = receipt_service
        self.temp_pdf_path = None
        
        # Configuration de la fenêtre
        # Pourquoi FixedSize : Le viewer PDF a une taille optimale
        self.setWindowTitle(f"Aperçu du reçu N° REC-????-?????")  # Mis à jour après génération
        self.setMinimumSize(800, 600)
        self.resize(1000, 800)
        
        # Génération du PDF et chargement
        self._setup_ui()
        self._load_receipt()
    
    def _setup_ui(self) -> None:
        """
        Configure l'interface utilisateur du dialogue.
        
        Structure :
        - Barre d'outils : zoom - / + / ajuster à la largeur / page entière
        - Zone centrale : QPdfView pour afficher le PDF
        - Barre de boutons : Enregistrer / Imprimer / Fermer
        """
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Barre d'outils pour le zoom
        toolbar = QToolBar()
        toolbar.setMovable(False)
        
        # Zoom moins
        action_zoom_out = QAction("Zoom -", self)
        action_zoom_out.triggered.connect(self._zoom_out)
        toolbar.addAction(action_zoom_out)
        
        # Zoom plus
        action_zoom_in = QAction("Zoom +", self)
        action_zoom_in.triggered.connect(self._zoom_in)
        toolbar.addAction(action_zoom_in)
        
        # Ajuster à la largeur
        action_fit_width = QAction("Ajuster à la largeur", self)
        action_fit_width.triggered.connect(self._fit_width)
        toolbar.addAction(action_fit_width)
        
        # Page entière
        action_fit_page = QAction("Page entière", self)
        action_fit_page.triggered.connect(self._fit_page)
        toolbar.addAction(action_fit_page)
        
        layout.addWidget(toolbar)
        
        # Viewer PDF
        # Pourquoi QPdfView : Widget Qt natif pour afficher les PDF
        self.pdf_view = QPdfView()
        self.pdf_document = QPdfDocument(self)
        self.pdf_view.setDocument(self.pdf_document)
        self.pdf_view.setPageMode(QPdfView.PageMode.SinglePage)
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
        layout.addWidget(self.pdf_view)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)
        
        # Barre de boutons en bas
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(10, 10, 10, 10)
        button_layout.setSpacing(10)
        
        # Bouton Enregistrer
        self.btn_save = QPushButton("Enregistrer le PDF")
        self.btn_save.clicked.connect(self._save_pdf)
        button_layout.addWidget(self.btn_save)
        
        # Bouton Imprimer
        self.btn_print = QPushButton("Imprimer")
        self.btn_print.clicked.connect(self._print_pdf)
        button_layout.addWidget(self.btn_print)
        
        # Spacer
        button_layout.addStretch()
        
        # Bouton Fermer
        self.btn_close = QPushButton("Fermer")
        self.btn_close.clicked.connect(self.accept)
        button_layout.addWidget(self.btn_close)
        
        layout.addLayout(button_layout)
    
    def _load_receipt(self) -> None:
        """
        Génère et charge le reçu PDF.
        
        Processus :
        1. Générer le PDF via receipt_service dans un fichier temporaire
        2. Charger le fichier dans QPdfDocument
        3. Mettre à jour le titre de la fenêtre avec le numéro de reçu
        
        Pourquoi un fichier temporaire : receipt_service génère un PDF sur disque,
        mais nous ne voulons pas le conserver. Le fichier est supprimé à la fermeture.
        """
        try:
            # Créer un dossier temporaire dans user_data_dir
            # Pourquoi user_data_dir : Garanti l'accès en écriture sur toutes les machines
            tmp_dir = user_data_dir() / "tmp"
            tmp_dir.mkdir(exist_ok=True)
            
            # Générer le PDF dans un fichier temporaire
            # Pourquoi suffixe .pdf : QPdfDocument nécessite une extension
            temp_file = tmp_dir / f"temp_receipt_{self.payment_id}.pdf"
            self.temp_pdf_path = str(temp_file)
            
            # Générer le PDF via receipt_service
            # Pourquoi receipt_service : Il contient toute la logique de génération
            receipt_number = self.receipt_service.generate_receipt(self.payment_id, self.temp_pdf_path)
            
            # Mettre à jour le titre avec le numéro de reçu
            self.setWindowTitle(f"Aperçu du reçu N° {receipt_number}")
            
            # Charger le PDF dans le viewer
            # Pourquoi load() : Charge le fichier et le rend disponible pour l'affichage
            if not self.pdf_document.load(self.temp_pdf_path):
                raise RuntimeError("Impossible de charger le PDF généré")
            
            # Vérifier que le PDF a au moins une page
            if self.pdf_document.pageCount() == 0:
                raise RuntimeError("Le PDF généré ne contient aucune page")
            
        except Exception as e:
            # Afficher une erreur explicite
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible de générer l'aperçu du reçu :\n{str(e)}"
            )
            # Journaliser l'erreur
            import logging
            logging.error(f"Erreur lors de la génération de l'aperçu du reçu (payment_id={self.payment_id}) : {e}", exc_info=True)
            # Fermer le dialogue
            self.reject()
    
    def _zoom_in(self) -> None:
        """Augmente le zoom du viewer PDF."""
        current_zoom = self.pdf_view.zoomFactor()
        self.pdf_view.setZoomFactor(current_zoom * 1.2)
    
    def _zoom_out(self) -> None:
        """Diminue le zoom du viewer PDF."""
        current_zoom = self.pdf_view.zoomFactor()
        self.pdf_view.setZoomFactor(current_zoom / 1.2)
    
    def _fit_width(self) -> None:
        """Ajuste le zoom pour afficher la page en largeur."""
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitToWidth)
    
    def _fit_page(self) -> None:
        """Ajuste le zoom pour afficher la page entière."""
        self.pdf_view.setZoomMode(QPdfView.ZoomMode.FitInView)
    
    def _save_pdf(self) -> None:
        """
        Enregistre le PDF à un emplacement choisi par l'utilisateur.
        
        Processus :
        1. Ouvrir une boîte de dialogue pour choisir l'emplacement
        2. Copier le fichier temporaire vers l'emplacement choisi
        3. Informer l'utilisateur du succès
        """
        if not self.temp_pdf_path or not Path(self.temp_pdf_path).exists():
            QMessageBox.warning(self, "Erreur", "Aucun PDF à enregistrer")
            return
        
        # Nom de fichier proposé
        # Pourquoi ce format : Préfixe Recu_ + numéro de reçu pour identification facile
        receipt_number = self.windowTitle().replace("Aperçu du reçu N° ", "")
        default_name = f"Recu_{receipt_number}.pdf"
        
        # Boîte de dialogue pour choisir l'emplacement
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Enregistrer le reçu",
            default_name,
            "Fichiers PDF (*.pdf)"
        )
        
        if file_path:
            try:
                # Copier le fichier temporaire vers l'emplacement choisi
                import shutil
                shutil.copy2(self.temp_pdf_path, file_path)
                QMessageBox.information(self, "Succès", "Le reçu a été enregistré avec succès")
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Erreur",
                    f"Impossible d'enregistrer le reçu :\n{str(e)}"
                )
                import logging
                logging.error(f"Erreur lors de l'enregistrement du reçu : {e}", exc_info=True)
    
    def _print_pdf(self) -> None:
        """
        Imprime le reçu via une boîte de dialogue d'impression.
        
        Processus :
        1. Ouvrir une boîte de dialogue d'impression
        2. Si l'utilisateur confirme, imprimer chaque page du PDF
        3. Rendre chaque page en QImage à 300 dpi
        4. Dessiner l'image dans la zone imprimable du QPrinter
        
        Pourquoi 300 dpi : Qualité d'impression standard pour les documents
        """
        if not self.temp_pdf_path or not Path(self.temp_pdf_path).exists():
            QMessageBox.warning(self, "Erreur", "Aucun PDF à imprimer")
            return
        
        # Créer une boîte de dialogue d'impression
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setResolution(300)  # 300 dpi pour une bonne qualité
        
        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec() != QDialog.DialogCode.Accepted:
            return
        
        try:
            from PySide6.QtGui import QPainter
            
            # Commencer l'impression
            painter = QPainter(printer)
            page_count = self.pdf_document.pageCount()
            
            for page_num in range(page_count):
                # Rendre la page en QImage
                # Pourquoi 300 dpi : Correspond à la résolution de l'imprimante
                page_size = self.pdf_document.pagePointSize(page_num)
                image = self.pdf_document.render(page_num, page_size * 300 / 72)
                
                # Dessiner l'image dans la zone imprimable
                # Pourquoi drawImage : Transfert l'image QImage vers le QPrinter
                if page_num > 0:
                    printer.newPage()
                
                # Calculer la position pour centrer l'image
                # Pourquoi centrer : Meilleure présentation sur la page
                printer_page_size = printer.pageLayout().pageSize().size(QPageLayout.Unit.Point)
                x = (printer_page_size.width() - image.width()) / 2
                y = (printer_page_size.height() - image.height()) / 2
                
                painter.drawImage(int(x), int(y), image)
            
            painter.end()
            QMessageBox.information(self, "Succès", "Le reçu a été envoyé à l'imprimante")
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible d'imprimer le reçu :\n{str(e)}"
            )
            import logging
            logging.error(f"Erreur lors de l'impression du reçu : {e}", exc_info=True)
    
    def closeEvent(self, event) -> None:
        """
        Supprime le fichier temporaire à la fermeture du dialogue.
        
        Pourquoi supprimer : Le fichier temporaire n'est plus nécessaire après
        la fermeture. Cela évite de polluer le système de fichiers.
        """
        # Supprimer le fichier temporaire s'il existe
        if self.temp_pdf_path and Path(self.temp_pdf_path).exists():
            try:
                Path(self.temp_pdf_path).unlink()
            except Exception as e:
                import logging
                logging.warning(f"Impossible de supprimer le fichier temporaire {self.temp_pdf_path} : {e}")
        
        # Accepter l'événement de fermeture
        event.accept()
