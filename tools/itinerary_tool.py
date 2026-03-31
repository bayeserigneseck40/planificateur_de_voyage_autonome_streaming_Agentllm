"""
Outil Itinéraire : construit et formate l'itinéraire final complet du voyage.
Génère un document structuré prêt à être exporté en PDF ou envoyé par email.
"""

import os
from datetime import datetime
from openai import OpenAI

from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Stockage global de l'itinéraire courant (pour export)
_current_itinerary = {"content": "", "destination": "", "month": ""}


def build_itinerary(
    destination: str,
    month: str,
    weather_summary: str,
    flights_summary: str,
    hotels_summary: str,
    restaurants_summary: str,
    duration: str = "7-10 jours",
    traveler_name: str = "Voyageur"
) -> str:
    """
    Construit l'itinéraire final complet en utilisant le LLM pour synthétiser
    toutes les informations collectées en un plan jour par jour cohérent.
    """
    global _current_itinerary

    prompt = f"""Tu es un expert en planification de voyages. Crée un itinéraire de voyage complet et détaillé pour :

**Voyageur** : {traveler_name}
**Destination** : {destination}
**Période** : {month}
**Durée estimée** : {duration}

**Informations collectées :**

=== MÉTÉO ===
{weather_summary[:500]}

=== TRANSPORT ===
{flights_summary[:500]}

=== HÉBERGEMENT ===
{hotels_summary[:500]}

=== RESTAURATION ===
{restaurants_summary[:500]}

**Instructions :**
Crée un itinéraire jour par jour (pour {duration}) avec :
1. Un programme quotidien (matin, après-midi, soir)
2. Les sites et activités incontournables
3. Les restaurants recommandés pour chaque repas
4. Les conseils pratiques (transport local, horaires, prix)
5. Un budget journalier estimé
6. Les informations pratiques essentielles (visa, monnaie, langue, décalage horaire)

Format : Markdown structuré avec emojis, sections claires, tableaux récapitulatifs.
Réponds en français."""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=2000
    )

    itinerary_content = response.choices[0].message.content

    # Construire le document complet
    full_doc = f"""# 🌍 Itinéraire de Voyage — {destination.title()}
**Préparé pour** : {traveler_name}  
**Destination** : {destination.title()}  
**Période** : {month.capitalize()}  
**Durée** : {duration}  
**Généré le** : {datetime.now().strftime('%d/%m/%Y à %H:%M')}

---

{itinerary_content}

---

## 📋 Récapitulatif des Réservations

### ✈️ Transport
{flights_summary[:800]}

### 🏨 Hébergement
{hotels_summary[:800]}

### 🍽️ Restauration
{restaurants_summary[:600]}

### 🌤️ Météo & Climat
{weather_summary[:600]}

---

## 💡 Informations Pratiques Essentielles

### 📞 Numéros d'urgence
- **Urgences générales** : 112 (numéro européen universel)
- **Ambassade de France** : Consultez [France Diplomatie](https://www.diplomatie.gouv.fr)

### 🌐 Ressources utiles
- [Google Maps](https://maps.google.com) — Navigation locale
- [XE Currency](https://www.xe.com) — Conversion de devises en temps réel
- [TripAdvisor](https://www.tripadvisor.fr) — Avis et recommandations
- [Météo locale](https://www.meteoblue.com) — Prévisions météo détaillées

---

*Itinéraire généré par l'Agent de Planification de Voyage Autonome — Powered by ReAct + CoT AI*
"""

    # Sauvegarder pour export
    _current_itinerary["content"] = full_doc
    _current_itinerary["destination"] = destination
    _current_itinerary["month"] = month

    return full_doc


def get_current_itinerary() -> dict:
    """Retourne l'itinéraire courant pour export."""
    return _current_itinerary
