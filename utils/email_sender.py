"""
Module d'envoi d'email avec SMTP.
Supporte Gmail (TLS port 587), Outlook/Hotmail, et tout serveur SMTP custom.
Envoie l'itinéraire en corps HTML + pièce jointe PDF.

Compatibilité : Windows / Linux / macOS
Dépendances : uniquement la bibliothèque standard Python (smtplib, email)
"""

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formatdate, make_msgid
from pathlib import Path
from datetime import datetime
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Configuration SMTP prédéfinie par fournisseur
# ──────────────────────────────────────────────────────────────

SMTP_PRESETS = {
    "gmail": {
        "host": "smtp.gmail.com",
        "port": 587,
        "use_tls": True,
        "label": "Gmail",
        "note": (
            "Pour Gmail, utilisez un 'Mot de passe d'application' (App Password) "
            "et non votre mot de passe principal. "
            "Activez-le sur : https://myaccount.google.com/apppasswords"
        ),
    },
    "outlook": {
        "host": "smtp-mail.outlook.com",
        "port": 587,
        "use_tls": True,
        "label": "Outlook / Hotmail",
        "note": "Utilisez votre adresse et mot de passe Outlook habituels.",
    },
    "yahoo": {
        "host": "smtp.mail.yahoo.com",
        "port": 587,
        "use_tls": True,
        "label": "Yahoo Mail",
        "note": (
            "Pour Yahoo, générez un 'Mot de passe d'application' dans les paramètres "
            "de sécurité de votre compte Yahoo."
        ),
    },
    "custom": {
        "host": "",
        "port": 587,
        "use_tls": True,
        "label": "Serveur SMTP personnalisé",
        "note": "Renseignez manuellement le host et le port de votre serveur SMTP.",
    },
}


# ──────────────────────────────────────────────────────────────
# Génération du corps HTML de l'email
# ──────────────────────────────────────────────────────────────

def _build_html_body(destination: str, month: str, itinerary_text: str) -> str:
    """
    Génère un corps d'email HTML élégant contenant un résumé de l'itinéraire.
    Le PDF complet est joint en pièce jointe.
    """
    # Extraire un aperçu du texte (500 premiers caractères)
    preview = itinerary_text[:600].replace("\n", "<br>").replace("#", "").strip()
    if len(itinerary_text) > 600:
        preview += "..."

    generated_date = datetime.now().strftime("%d/%m/%Y à %H:%M")

    html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Votre Itinéraire de Voyage — {destination.title()}</title>
</head>
<body style="margin:0; padding:0; background-color:#f4f6fb; font-family: 'Segoe UI', Arial, sans-serif;">

  <!-- Conteneur principal -->
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f6fb; padding: 30px 0;">
    <tr>
      <td align="center">
        <table width="620" cellpadding="0" cellspacing="0"
               style="background:#ffffff; border-radius:16px;
                      box-shadow: 0 4px 24px rgba(26,35,126,0.12); overflow:hidden;">

          <!-- En-tête dégradé -->
          <tr>
            <td style="background: linear-gradient(135deg, #1a237e 0%, #1565c0 60%, #0288d1 100%);
                       padding: 36px 40px; text-align:center;">
              <div style="font-size:48px; margin-bottom:10px;">✈️</div>
              <h1 style="color:#ffffff; font-size:26px; font-weight:800;
                         margin:0 0 6px 0; letter-spacing:-0.5px;">
                Votre Itinéraire de Voyage
              </h1>
              <p style="color:rgba(255,255,255,0.85); font-size:18px; margin:0 0 4px 0;">
                <strong>{destination.title()}</strong>
              </p>
              <p style="color:rgba(255,255,255,0.7); font-size:14px; margin:0;">
                Période : {month.capitalize()}
              </p>
            </td>
          </tr>

          <!-- Corps -->
          <tr>
            <td style="padding: 32px 40px;">

              <p style="color:#37474f; font-size:15px; line-height:1.7; margin:0 0 20px 0;">
                Bonjour,<br><br>
                Votre <strong>Agent de Planification de Voyage Autonome</strong> a préparé
                votre itinéraire complet pour votre voyage à
                <strong>{destination.title()}</strong> en <strong>{month.capitalize()}</strong>.
                Vous trouverez le plan détaillé en <strong>pièce jointe PDF</strong>.
              </p>

              <!-- Aperçu -->
              <div style="background:#f0f4ff; border-left: 4px solid #1a73e8;
                          border-radius: 0 8px 8px 0; padding: 16px 20px; margin-bottom:24px;">
                <p style="color:#1a237e; font-size:12px; font-weight:700;
                           text-transform:uppercase; letter-spacing:1px; margin:0 0 8px 0;">
                  Aperçu de l'itinéraire
                </p>
                <p style="color:#455a64; font-size:13px; line-height:1.7; margin:0;">
                  {preview}
                </p>
              </div>

              <!-- Bouton CTA -->
              <div style="text-align:center; margin: 28px 0;">
                <span style="display:inline-block; background: linear-gradient(135deg, #1a73e8, #1557b0);
                             color:#ffffff; font-size:15px; font-weight:700;
                             padding: 14px 36px; border-radius: 30px;
                             text-decoration:none; letter-spacing:0.3px;">
                  📄 Voir le PDF en pièce jointe
                </span>
              </div>

              <!-- Rappel pratique -->
              <table width="100%" cellpadding="0" cellspacing="0"
                     style="background:#fff8e1; border-radius:10px;
                            border:1px solid #ffe082; margin-bottom:24px;">
                <tr>
                  <td style="padding:16px 20px;">
                    <p style="color:#e65100; font-size:12px; font-weight:700;
                               text-transform:uppercase; letter-spacing:1px; margin:0 0 6px 0;">
                      💡 Rappel important
                    </p>
                    <p style="color:#5d4037; font-size:13px; line-height:1.6; margin:0;">
                      Les prix et disponibilités indiqués sont des estimations générées par l'IA.
                      Pensez à vérifier et confirmer vos réservations directement auprès des
                      prestataires (compagnies aériennes, hôtels, etc.).
                    </p>
                  </td>
                </tr>
              </table>

            </td>
          </tr>

          <!-- Pied de page -->
          <tr>
            <td style="background:#f8f9fa; border-top:1px solid #e8eaf6;
                       padding: 20px 40px; text-align:center;">
              <p style="color:#9e9e9e; font-size:12px; margin:0 0 4px 0;">
                Généré le {generated_date} par l'Agent de Planification de Voyage Autonome
              </p>
              <p style="color:#bdbdbd; font-size:11px; margin:0;">
                Propulsé par ReAct + Chain-of-Thought AI
              </p>
            </td>
          </tr>

        </table>
      </td>
    </tr>
  </table>

</body>
</html>"""
    return html


# ──────────────────────────────────────────────────────────────
# Fonction principale d'envoi
# ──────────────────────────────────────────────────────────────

def send_itinerary_email(
    recipient_email: str,
    destination: str,
    month: str,
    itinerary_text: str,
    pdf_path: Optional[str] = None,
    sender_email: Optional[str] = None,
    sender_password: Optional[str] = None,
    smtp_host: Optional[str] = None,
    smtp_port: int = 587,
    use_tls: bool = True,
) -> dict:
    """
    Envoie l'itinéraire par email avec SMTP.

    Paramètres
    ----------
    recipient_email   : Adresse email du destinataire.
    destination       : Nom de la destination (ex: "Malaisie").
    month             : Mois du voyage (ex: "septembre").
    itinerary_text    : Contenu texte/Markdown de l'itinéraire (pour l'aperçu HTML).
    pdf_path          : Chemin local vers le fichier PDF à joindre (optionnel).
    sender_email      : Email expéditeur. Si None, lu depuis SMTP_SENDER_EMAIL (env).
    sender_password   : Mot de passe SMTP. Si None, lu depuis SMTP_PASSWORD (env).
    smtp_host         : Serveur SMTP. Si None, lu depuis SMTP_HOST (env).
    smtp_port         : Port SMTP (défaut 587 pour TLS).
    use_tls           : Utiliser STARTTLS (recommandé).

    Retourne
    --------
    dict avec les clés :
        - "success" (bool)
        - "message" (str) : message de succès ou description de l'erreur
    """

    # ── 1. Résolution des paramètres depuis les variables d'environnement ──
    sender_email    = sender_email    or os.getenv("SMTP_SENDER_EMAIL", "")
    sender_password = sender_password or os.getenv("SMTP_PASSWORD", "")
    smtp_host       = smtp_host       or os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port       = int(os.getenv("SMTP_PORT", str(smtp_port)))

    # ── 2. Validation des paramètres obligatoires ──
    if not sender_email:
        return {
            "success": False,
            "message": (
                "Adresse email expéditeur manquante. "
                "Renseignez SMTP_SENDER_EMAIL dans le fichier .env "
                "ou fournissez le paramètre sender_email."
            ),
        }
    if not sender_password:
        return {
            "success": False,
            "message": (
                "Mot de passe SMTP manquant. "
                "Renseignez SMTP_PASSWORD dans le fichier .env "
                "ou fournissez le paramètre sender_password."
            ),
        }
    if not recipient_email or "@" not in recipient_email:
        return {
            "success": False,
            "message": f"Adresse email destinataire invalide : '{recipient_email}'.",
        }

    # ── 3. Construction du message MIME ──
    msg = MIMEMultipart("alternative")
    msg["Subject"]    = f"✈️ Votre itinéraire de voyage — {destination.title()} ({month.capitalize()})"
    msg["From"]       = f"Agent Voyage AI <{sender_email}>"
    msg["To"]         = recipient_email
    msg["Date"]       = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=sender_email.split("@")[-1])

    # Corps texte brut (fallback pour clients email sans HTML)
    plain_text = (
        f"Votre itinéraire de voyage — {destination.title()} ({month.capitalize()})\n\n"
        f"{itinerary_text[:1500]}\n\n"
        "Le PDF complet est joint à cet email.\n\n"
        "-- Agent de Planification de Voyage Autonome"
    )
    msg.attach(MIMEText(plain_text, "plain", "utf-8"))

    # Corps HTML
    html_body = _build_html_body(destination, month, itinerary_text)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # ── 4. Pièce jointe PDF (si fournie et existante) ──
    if pdf_path:
        pdf_file = Path(pdf_path)
        if pdf_file.exists():
            with open(pdf_file, "rb") as f:
                pdf_data = f.read()
            attachment = MIMEApplication(pdf_data, _subtype="pdf")
            dest_clean = destination.replace(" ", "_").lower()
            filename   = f"itineraire_{dest_clean}_{month.lower()}.pdf"
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=filename
            )
            msg.attach(attachment)
        else:
            # PDF non trouvé : on envoie quand même l'email sans pièce jointe
            pass

    # ── 5. Connexion SMTP et envoi ──
    try:
        context = ssl.create_default_context()

        if use_tls:
            # STARTTLS : connexion non chiffrée puis upgrade TLS (port 587)
            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, msg.as_bytes())
        else:
            # SSL direct (port 465)
            with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=15) as server:
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, recipient_email, msg.as_bytes())

        has_pdf = pdf_path and Path(pdf_path).exists()
        return {
            "success": True,
            "message": (
                f"Email envoyé avec succès à {recipient_email}"
                + (" (avec PDF en pièce jointe)" if has_pdf else " (sans PDF)")
                + "."
            ),
        }

    except smtplib.SMTPAuthenticationError:
        return {
            "success": False,
            "message": (
                "Échec d'authentification SMTP. Vérifiez votre email et mot de passe.\n"
                "Pour Gmail : utilisez un 'Mot de passe d'application' (App Password), "
                "pas votre mot de passe principal.\n"
                "Lien : https://myaccount.google.com/apppasswords"
            ),
        }
    except smtplib.SMTPConnectError:
        return {
            "success": False,
            "message": (
                f"Impossible de se connecter au serveur SMTP {smtp_host}:{smtp_port}. "
                "Vérifiez le host, le port et votre connexion internet."
            ),
        }
    except smtplib.SMTPRecipientsRefused:
        return {
            "success": False,
            "message": f"L'adresse destinataire '{recipient_email}' a été refusée par le serveur.",
        }
    except TimeoutError:
        return {
            "success": False,
            "message": (
                f"Délai de connexion dépassé pour {smtp_host}:{smtp_port}. "
                "Vérifiez votre connexion réseau ou les paramètres du pare-feu."
            ),
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Erreur inattendue lors de l'envoi : {type(e).__name__} — {str(e)}",
        }
