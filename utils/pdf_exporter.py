import os
import re
import tempfile
import unicodedata
from pathlib import Path
from fpdf import FPDF
from datetime import datetime


# ──────────────────────────────────────────────────────────────
# Nettoyage du texte
# ──────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """
    Nettoie le texte pour la compatibilité PDF fpdf2 (police Helvetica = latin-1).
    1. Supprime les emojis et symboles Unicode hors BMP
    2. Normalise les caractères accentués (NFD → ASCII de base)
    3. Remplace les ponctuations typographiques courantes
    4. Encode en latin-1 en ignorant le reste
    """
    if not text:
        return ""

    # Étape 1 : supprimer emojis et symboles hors-BMP
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U000024C2-\U0001F251"
        "\U0001F926-\U0001F937"
        "\U00010000-\U0010FFFF"
        "\u2640-\u2642"
        "\u2600-\u2B55"
        "\u23CF\u23E9\u231A\uFE0F\u3030"
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub("", text)

    # Étape 2 : remplacements explicites de ponctuations typographiques
    replacements = {
        "\u2019": "'", "\u2018": "'",
        "\u201C": '"', "\u201D": '"',
        "\u2013": "-", "\u2014": "-", "\u2015": "-",
        "\u2022": "-", "\u2023": "-",
        "\u2026": "...",
        "\u2039": "<", "\u203A": ">",
        "\u2192": "->", "\u2190": "<-", "\u2194": "<->",
        "\u2605": "*", "\u2606": "*",
        "\u25CF": "*", "\u25CB": "o",
        "\u2713": "v", "\u2714": "v", "\u2717": "x", "\u2718": "x",
        "\u00B0": "deg",
        "\u00B7": ".",
        "\u00D7": "x",
        "\u00F7": "/",
        "\u20AC": "EUR",
        "\u00A3": "GBP",
        "\u00A5": "JPY",
        "\u00A0": " ",
        "\u200B": "", "\u200C": "", "\u200D": "",
        "\uFEFF": "",
        "\u00AD": "-",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # Étape 3 : normalisation NFD pour décomposer les accents
    # (é → e + combining accent → on garde la base ASCII)
    normalized = unicodedata.normalize("NFD", text)
    text = "".join(c for c in normalized if unicodedata.category(c) != "Mn")

    # Étape 4 : encodage latin-1 final (ignore les caractères restants)
    text = text.encode("latin-1", errors="ignore").decode("latin-1")

    return text.strip()


# ──────────────────────────────────────────────────────────────
# Classe PDF personnalisée
# ──────────────────────────────────────────────────────────────

class ItineraryPDF(FPDF):
    """Classe PDF personnalisée pour l'itinéraire de voyage."""

    def __init__(self, destination: str, month: str):
        super().__init__()
        self.destination = destination
        self.month = month
        # Marges explicites : gauche=10, droite=10, haut=10
        self.set_margins(left=10, top=10, right=10)
        self.set_auto_page_break(auto=True, margin=15)

    def _usable_width(self) -> float:
        """Largeur utile = largeur page - marge gauche - marge droite."""
        return self.w - self.l_margin - self.r_margin

    def header(self):
        """Bande bleue en haut avec titre destination."""
        self.set_fill_color(26, 115, 232)
        self.rect(0, 0, self.w, 18, "F")
        self.set_text_color(255, 255, 255)
        self.set_font("Helvetica", "B", 11)
        self.set_xy(self.l_margin, 4)
        header_text = clean_text(
            f"Itineraire de Voyage - {self.destination.title()} | {self.month.capitalize()}"
        )
        self.cell(self._usable_width(), 10, header_text, align="L")
        self.set_text_color(0, 0, 0)
        self.ln(16)

    def footer(self):
        """Pied de page avec numéro de page."""
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        footer_text = clean_text(
            f"Agent de Planification de Voyage Autonome  |  "
            f"Page {self.page_no()}  |  {datetime.now().strftime('%d/%m/%Y')}"
        )
        self.cell(self._usable_width(), 10, footer_text, align="C")

    def chapter_title(self, title: str):
        """Titre de section H2 avec fond coloré."""
        clean_title = clean_text(title)
        self.set_fill_color(232, 240, 254)
        self.set_text_color(26, 115, 232)
        self.set_font("Helvetica", "B", 13)
        self.multi_cell(self._usable_width(), 10, f"  {clean_title}", fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def section_title(self, title: str):
        """Sous-titre de section H3."""
        clean_title = clean_text(title)
        self.set_text_color(50, 50, 150)
        self.set_font("Helvetica", "B", 11)
        self.multi_cell(self._usable_width(), 8, clean_title)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def body_text(self, text: str):
        """Texte de corps normal."""
        clean = clean_text(text)
        if not clean:
            return
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(self._usable_width(), 6, clean)
        self.ln(1)

    def bullet_item(self, text: str):
        """
        Élément de liste à puces.
        Utilise un décalage via set_x() plutôt qu'une cell vide,
        ce qui évite de réduire l'espace disponible pour multi_cell.
        """
        clean = clean_text(text)
        if not clean:
            return
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        indent = 5  # décalage en mm
        # Positionner X avec décalage sans consommer de largeur
        self.set_x(self.l_margin + indent)
        # La largeur disponible est réduite du décalage
        self.multi_cell(self._usable_width() - indent, 6, clean_text(f"- {text}"))

    def info_box(self, text: str, color=(255, 248, 220)):
        """Boîte d'information colorée."""
        clean = clean_text(text)
        if not clean:
            return
        self.set_fill_color(*color)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(80, 80, 80)
        self.multi_cell(self._usable_width(), 6, f"  {clean}  ", fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def divider(self):
        """Ligne de séparation horizontale."""
        self.set_draw_color(200, 200, 200)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)


# ──────────────────────────────────────────────────────────────
# Rendu tableau Markdown
# ──────────────────────────────────────────────────────────────

def render_table(pdf: ItineraryPDF, table_lines: list):
    """
    Rend un tableau Markdown en PDF.
    La largeur de chaque colonne est calculée dynamiquement
    sur la base de la largeur utile réelle de la page.
    """
    if len(table_lines) < 2:
        return

    def parse_row(line: str) -> list:
        cells = [c.strip() for c in line.strip("|").split("|")]
        return [clean_text(re.sub(r"\*\*(.*?)\*\*", r"\1", c)) for c in cells]

    # Filtrer la ligne de séparation (--- | --- | ---)
    rows = [
        parse_row(line)
        for line in table_lines
        if not re.match(r"^\|[-| :]+\|$", line.strip())
    ]

    if not rows:
        return

    num_cols = max(len(r) for r in rows)
    if num_cols == 0:
        return

    usable = pdf._usable_width()
    col_width = usable / num_cols  # largeur par colonne

    # Calculer la largeur max de texte supportée par colonne
    # (fpdf2 lève l'erreur si col_width < largeur d'un caractère)
    # On impose un minimum de 15 mm par colonne
    min_col_width = 15.0
    if col_width < min_col_width:
        # Trop de colonnes : on réduit la police et on recalcule
        col_width = min_col_width
        # On tronque les cellules pour qu'elles tiennent

    def truncate_cell(text: str, width_mm: float, font_size: int = 9) -> str:
        """Tronque le texte pour qu'il tienne dans width_mm avec la police donnée."""
        if not text:
            return ""
        # Estimation : 1 caractère ≈ font_size * 0.35 mm en Helvetica
        max_chars = max(1, int(width_mm / (font_size * 0.35)))
        return text[:max_chars] if len(text) > max_chars else text

    # En-tête du tableau
    pdf.set_fill_color(26, 115, 232)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "B", 9)
    header_row = rows[0]
    for i in range(num_cols):
        cell_text = header_row[i] if i < len(header_row) else ""
        pdf.cell(col_width, 7, truncate_cell(cell_text, col_width, 9), border=1, fill=True)
    pdf.ln()

    # Corps du tableau
    pdf.set_text_color(40, 40, 40)
    pdf.set_font("Helvetica", "", 9)
    for row_idx, row in enumerate(rows[1:]):
        if row_idx % 2 == 0:
            pdf.set_fill_color(245, 245, 255)
        else:
            pdf.set_fill_color(255, 255, 255)
        for i in range(num_cols):
            cell_text = row[i] if i < len(row) else ""
            pdf.cell(col_width, 7, truncate_cell(cell_text, col_width, 9), border=1, fill=True)
        pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)


# ──────────────────────────────────────────────────────────────
# Parser Markdown → PDF
# ──────────────────────────────────────────────────────────────

def parse_markdown_to_pdf(pdf: ItineraryPDF, content: str):
    """Parse le contenu Markdown et le convertit en éléments PDF."""
    lines = content.split("\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()

        if not stripped:
            i += 1
            continue

        # Titre H1
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            pdf.set_font("Helvetica", "B", 16)
            pdf.set_text_color(26, 115, 232)
            pdf.multi_cell(pdf._usable_width(), 10, clean_text(title))
            pdf.set_text_color(0, 0, 0)
            pdf.ln(3)

        # Titre H2
        elif stripped.startswith("## "):
            pdf.chapter_title(stripped[3:].strip())

        # Titre H3
        elif stripped.startswith("### "):
            pdf.section_title(stripped[4:].strip())

        # Ligne de séparation
        elif stripped.startswith("---"):
            pdf.divider()

        # Tableau Markdown
        elif stripped.startswith("|") and "|" in stripped[1:]:
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            render_table(pdf, table_lines)
            continue

        # Liste à puces (- ou *)
        elif stripped.startswith("- ") or stripped.startswith("* "):
            item = stripped[2:].strip()
            item = re.sub(r"\*\*(.*?)\*\*", r"\1", item)
            item = re.sub(r"\*(.*?)\*", r"\1", item)
            item = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", item)
            pdf.bullet_item(item)

        # Texte en gras seul sur une ligne
        elif stripped.startswith("**") and stripped.endswith("**") and len(stripped) > 4:
            text = stripped[2:-2]
            pdf.set_font("Helvetica", "B", 10)
            pdf.set_text_color(40, 40, 40)
            pdf.multi_cell(pdf._usable_width(), 6, clean_text(text))
            pdf.set_font("Helvetica", "", 10)

        # Texte normal
        else:
            text = re.sub(r"\*\*(.*?)\*\*", r"\1", stripped)
            text = re.sub(r"\*(.*?)\*", r"\1", text)
            text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)
            text = re.sub(r"`(.*?)`", r"\1", text)
            if text.strip():
                pdf.body_text(text)

        i += 1


# ──────────────────────────────────────────────────────────────
# Fonction principale d'export
# ──────────────────────────────────────────────────────────────

def export_itinerary_to_pdf(
    content: str,
    destination: str,
    month: str,
    output_path: str = None
) -> str:
    """
    Exporte l'itinéraire en PDF.
    Retourne le chemin du fichier PDF généré.
    """
    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_clean = re.sub(r"[^a-z0-9]", "_", destination.lower())
        # Utilise le répertoire temporaire du système (compatible Windows/Linux/macOS)
        tmp_dir = Path(tempfile.gettempdir())
        output_path = str(tmp_dir / f"itineraire_{dest_clean}_{month.lower()}_{timestamp}.pdf")

    pdf = ItineraryPDF(destination=destination, month=month)
    pdf.add_page()

    # ── Page de titre ──────────────────────────────────────────
    # Bannière bleue (commence à Y=18 car le header occupe 0-18)
    banner_y = 18
    banner_h = 55
    pdf.set_fill_color(26, 115, 232)
    pdf.rect(0, banner_y, pdf.w, banner_h, "F")

    pdf.set_text_color(255, 255, 255)

    # Ligne 1 : "Itineraire de Voyage"
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_xy(pdf.l_margin, banner_y + 8)
    pdf.cell(pdf._usable_width(), 12, clean_text("Itineraire de Voyage"), align="C", ln=True)

    # Ligne 2 : destination
    pdf.set_font("Helvetica", "B", 17)
    pdf.set_x(pdf.l_margin)
    pdf.cell(pdf._usable_width(), 10, clean_text(destination.title()), align="C", ln=True)

    # Ligne 3 : période
    pdf.set_font("Helvetica", "", 13)
    pdf.set_x(pdf.l_margin)
    pdf.cell(pdf._usable_width(), 8, clean_text(f"Periode : {month.capitalize()}"), align="C", ln=True)

    pdf.set_text_color(0, 0, 0)

    # Positionner le curseur après la bannière avec un espace
    pdf.set_xy(pdf.l_margin, banner_y + banner_h + 8)

    # ── Contenu principal ──────────────────────────────────────
    parse_markdown_to_pdf(pdf, content)

    pdf.output(output_path)
    return output_path
