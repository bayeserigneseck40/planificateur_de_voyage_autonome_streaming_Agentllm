"""
Outil Vols & Trains : recherche des options de transport pour une destination.
Fournit des suggestions réalistes avec plateformes de réservation.
"""

import os
from openai import OpenAI

from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
# Base de données de routes populaires
FLIGHT_ROUTES = {
    "malaisie": {
        "hub": "Kuala Lumpur (KUL - KLIA)",
        "from_france": {
            "compagnies": ["Malaysia Airlines", "Air France + correspondance", "Emirates via Dubaï", "Qatar Airways via Doha", "Turkish Airlines via Istanbul"],
            "duree": "12h à 16h (avec escale)",
            "prix_estime": "450€ - 1200€ (aller-retour)",
            "vol_direct": False,
            "escales_populaires": ["Dubaï", "Doha", "Istanbul", "Singapour"]
        },
        "plateformes": ["Skyscanner", "Google Flights", "Kayak", "Booking.com Flights", "Kiwi.com"],
        "conseils": "Réservez 3-4 mois à l'avance pour les meilleures tarifs. Les vols via Dubaï (Emirates) sont souvent les plus confortables."
    },
    "thaïlande": {
        "hub": "Bangkok (BKK - Suvarnabhumi)",
        "from_france": {
            "compagnies": ["Thai Airways", "Air France", "Emirates", "Qatar Airways", "Turkish Airlines"],
            "duree": "11h à 14h (avec escale)",
            "prix_estime": "400€ - 1100€ (aller-retour)",
            "vol_direct": False,
            "escales_populaires": ["Dubaï", "Doha", "Istanbul", "Abu Dhabi"]
        },
        "plateformes": ["Skyscanner", "Google Flights", "Kayak", "Momondo"],
        "conseils": "Évitez les vols pendant les fêtes de fin d'année (prix x2). Les mardis et mercredis sont souvent les jours les moins chers."
    },
    "japon": {
        "hub": "Tokyo (NRT - Narita / HND - Haneda)",
        "from_france": {
            "compagnies": ["Air France (direct)", "Japan Airlines (direct)", "ANA (direct)", "Emirates", "Qatar Airways"],
            "duree": "12h (direct) à 16h (avec escale)",
            "prix_estime": "550€ - 1500€ (aller-retour)",
            "vol_direct": True,
            "escales_populaires": ["Dubaï", "Doha", "Helsinki"]
        },
        "plateformes": ["Skyscanner", "Google Flights", "Kayak", "Japan Airlines Direct"],
        "conseils": "Des vols directs Paris-Tokyo existent (Air France, JAL, ANA). Réservez 4-6 mois à l'avance pour les périodes de cerisiers (mars-avril)."
    },
    "maroc": {
        "hub": "Casablanca (CMN) / Marrakech (RAK)",
        "from_france": {
            "compagnies": ["Royal Air Maroc", "Air France", "Transavia", "easyJet", "Ryanair"],
            "duree": "3h à 4h (direct)",
            "prix_estime": "80€ - 350€ (aller-retour)",
            "vol_direct": True,
            "escales_populaires": []
        },
        "plateformes": ["Skyscanner", "Google Flights", "Transavia.com", "easyJet.com"],
        "conseils": "Vols directs très fréquents depuis Paris, Lyon, Marseille. Transavia et easyJet proposent souvent des tarifs très compétitifs."
    }
}

TRAIN_OPTIONS = {
    "maroc": "Le train n'est pas applicable pour rejoindre le Maroc depuis la France (mer Méditerranée). Option ferry depuis Algésiras (Espagne) possible.",
    "europe": "Eurostar, TGV international, Thalys disponibles pour les destinations européennes."
}


def search_flights(destination: str, month: str, origin: str = "France", transport_type: str = "les deux") -> str:
    """
    Recherche des options de transport pour une destination.
    """
    destination_lower = destination.lower().strip()
    route_data = None

    for key, data in FLIGHT_ROUTES.items():
        if key in destination_lower or destination_lower in key:
            route_data = data
            break

    if route_data:
        vols = route_data["from_france"]
        compagnies_text = "\n".join([f"  - {c}" for c in vols["compagnies"]])
        plateformes_text = " | ".join([f"[{p}](https://www.{p.lower().replace(' ', '')}.com)" for p in route_data["plateformes"]])

        direct_badge = "✅ Vols directs disponibles" if vols["vol_direct"] else "🔄 Correspondance nécessaire"
        escales = ", ".join(vols["escales_populaires"]) if vols["escales_populaires"] else "N/A"

        result = f"""## ✈️ Options de Transport — {origin} → {destination.title()} ({month.capitalize()})

### Informations générales
| Paramètre | Détail |
|-----------|--------|
| 🛬 Aéroport principal | {route_data['hub']} |
| ⏱️ Durée de vol | {vols['duree']} |
| 💰 Prix estimé (A/R) | {vols['prix_estime']} |
| ✈️ Vol direct | {direct_badge} |
| 🔄 Escales populaires | {escales} |

### Compagnies recommandées
{compagnies_text}

### 🌐 Plateformes de réservation
{plateformes_text}

### 💡 Conseil expert
{route_data['conseils']}

### 📅 Astuces pour {month.capitalize()}
- Réservez **2 à 4 mois à l'avance** pour obtenir les meilleurs tarifs
- Activez les **alertes de prix** sur Google Flights ou Skyscanner
- Comparez les vols **aller-retour vs aller simple** (parfois moins cher)
- Vérifiez les **bagages inclus** : les low-cost facturent souvent les bagages en soute

### 🔗 Liens de recherche rapide
- [Skyscanner — Paris → {destination.title()}](https://www.skyscanner.fr/transport/vols/par/{destination_lower[:3].upper()}/)
- [Google Flights](https://www.google.com/flights)
- [Kayak](https://www.kayak.fr)"""
        return result

    # Utiliser le LLM pour les destinations non référencées
    prompt = f"""En tant qu'expert en voyages et transport, fournis des informations détaillées sur les options de transport pour :
- Départ : {origin}
- Destination : {destination}
- Période : {month}
- Type souhaité : {transport_type}

Inclus :
1. Aéroports principaux
2. Compagnies aériennes recommandées
3. Durée et nombre d'escales
4. Fourchette de prix estimée (aller-retour)
5. Meilleures plateformes de réservation avec liens
6. Conseils pour trouver les meilleurs prix
7. Options train si applicable

Réponds en français avec des emojis et du Markdown."""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800
    )
    return response.choices[0].message.content
