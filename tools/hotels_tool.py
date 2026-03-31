"""
Outil Hôtels : recherche des hébergements pour une destination et une période.
Fournit des suggestions par gamme de prix avec plateformes de réservation.
"""

import os
from openai import OpenAI

from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

HOTELS_DATA = {
    "malaisie": {
        "kuala lumpur": {
            "économique": [
                {"nom": "Tune Hotel KLIA2", "prix": "15-30€/nuit", "note": "⭐⭐⭐", "description": "Idéal pour les transits et petits budgets"},
                {"nom": "Capsule by Container Hotel", "prix": "20-40€/nuit", "note": "⭐⭐⭐", "description": "Hôtel capsule moderne et tendance"},
            ],
            "moyen": [
                {"nom": "Aloft Kuala Lumpur Sentral", "prix": "60-100€/nuit", "note": "⭐⭐⭐⭐", "description": "Excellent emplacement près du KLCC"},
                {"nom": "Hilton Garden Inn KL South", "prix": "70-120€/nuit", "note": "⭐⭐⭐⭐", "description": "Confort moderne, bon rapport qualité-prix"},
            ],
            "luxe": [
                {"nom": "Mandarin Oriental Kuala Lumpur", "prix": "200-400€/nuit", "note": "⭐⭐⭐⭐⭐", "description": "Vue sur les Tours Petronas, service exceptionnel"},
                {"nom": "The Ritz-Carlton Kuala Lumpur", "prix": "250-500€/nuit", "note": "⭐⭐⭐⭐⭐", "description": "Luxe absolu au cœur de la ville"},
            ]
        },
        "langkawi": {
            "économique": [
                {"nom": "Langkawi Dormitory Hostel", "prix": "10-25€/nuit", "note": "⭐⭐", "description": "Dortoirs propres, ambiance backpacker"},
            ],
            "moyen": [
                {"nom": "Berjaya Langkawi Resort", "prix": "80-150€/nuit", "note": "⭐⭐⭐⭐", "description": "Bungalows sur pilotis dans la forêt tropicale"},
            ],
            "luxe": [
                {"nom": "The Datai Langkawi", "prix": "400-800€/nuit", "note": "⭐⭐⭐⭐⭐", "description": "Élu l'un des meilleurs hôtels d'Asie, forêt tropicale"},
                {"nom": "Four Seasons Resort Langkawi", "prix": "350-700€/nuit", "note": "⭐⭐⭐⭐⭐", "description": "Villas avec piscine privée, plage privée"},
            ]
        }
    },
    "thaïlande": {
        "bangkok": {
            "économique": [
                {"nom": "Lub d Bangkok Siam", "prix": "15-35€/nuit", "note": "⭐⭐⭐", "description": "Hostel design primé, ambiance sociale"},
            ],
            "moyen": [
                {"nom": "Novotel Bangkok Silom Road", "prix": "60-110€/nuit", "note": "⭐⭐⭐⭐", "description": "Bien situé, piscine sur le toit"},
            ],
            "luxe": [
                {"nom": "Mandarin Oriental Bangkok", "prix": "300-600€/nuit", "note": "⭐⭐⭐⭐⭐", "description": "Hôtel légendaire au bord du Chao Phraya"},
            ]
        }
    },
    "maroc": {
        "marrakech": {
            "économique": [
                {"nom": "Riad Dar Zitoun", "prix": "25-50€/nuit", "note": "⭐⭐⭐", "description": "Riad traditionnel en médina, ambiance authentique"},
            ],
            "moyen": [
                {"nom": "Riad Kniza", "prix": "100-180€/nuit", "note": "⭐⭐⭐⭐", "description": "Riad de charme avec piscine, service personnalisé"},
            ],
            "luxe": [
                {"nom": "La Mamounia", "prix": "400-900€/nuit", "note": "⭐⭐⭐⭐⭐", "description": "Palace légendaire, jardins andalous, spa world-class"},
                {"nom": "Royal Mansour Marrakech", "prix": "500-1200€/nuit", "note": "⭐⭐⭐⭐⭐", "description": "Riads privés, service de butler, gastronomie étoilée"},
            ]
        }
    }
}


def search_hotels(destination: str, month: str, budget: str = "tous", duration_nights: int = 7) -> str:
    """
    Recherche des hôtels pour une destination et une période.
    """
    destination_lower = destination.lower().strip()
    country_data = None
    city_data = None

    # Chercher par pays puis par ville
    for country, cities in HOTELS_DATA.items():
        if country in destination_lower or destination_lower in country:
            country_data = cities
            # Prendre la première ville disponible comme capitale/principale
            first_city = list(cities.keys())[0]
            city_data = cities[first_city]
            city_name = first_city
            break
        for city, data in cities.items():
            if city in destination_lower or destination_lower in city:
                city_data = data
                city_name = city
                break

    if city_data:
        budgets_to_show = ["économique", "moyen", "luxe"] if budget == "tous" else [budget]
        sections = []

        price_ranges = {
            "économique": ("💚", "Budget économique"),
            "moyen": ("💛", "Budget intermédiaire"),
            "luxe": ("💎", "Luxe & Premium")
        }

        for b in budgets_to_show:
            if b in city_data:
                emoji, label = price_ranges.get(b, ("⭐", b))
                hotels = city_data[b]
                hotels_text = ""
                for h in hotels:
                    hotels_text += f"\n**{h['nom']}** {h['note']}\n"
                    hotels_text += f"  - 💰 Prix : {h['prix']}\n"
                    hotels_text += f"  - 📝 {h['description']}\n"
                sections.append(f"### {emoji} {label}\n{hotels_text}")

        sections_text = "\n".join(sections)

        # Calcul budget total estimé
        total_eco = f"{15 * duration_nights}€ - {40 * duration_nights}€"
        total_mid = f"{70 * duration_nights}€ - {150 * duration_nights}€"
        total_lux = f"{250 * duration_nights}€ - {800 * duration_nights}€"

        result = f"""## 🏨 Hébergements — {destination.title()} ({month.capitalize()}, {duration_nights} nuits)

{sections_text}

### 💰 Budget hébergement estimé ({duration_nights} nuits)
| Gamme | Coût total estimé |
|-------|------------------|
| 💚 Économique | {total_eco} |
| 💛 Intermédiaire | {total_mid} |
| 💎 Luxe | {total_lux} |

### 🌐 Plateformes de réservation
- [Booking.com](https://www.booking.com) — Large choix, annulation gratuite souvent disponible
- [Airbnb](https://www.airbnb.fr) — Appartements et maisons locales, expérience authentique
- [Hotels.com](https://www.hotels.com) — Programme de fidélité (1 nuit offerte / 10 nuits)
- [Agoda](https://www.agoda.com) — Spécialiste Asie, souvent moins cher pour la région
- [Expedia](https://www.expedia.fr) — Packages vol + hôtel avantageux

### 💡 Conseils de réservation pour {month.capitalize()}
- Réservez **2-3 mois à l'avance** pour les meilleures disponibilités
- Comparez toujours les prix sur **au moins 3 plateformes**
- Vérifiez les **politiques d'annulation** (préférez le remboursable)
- Lisez les avis récents (moins de 6 mois) pour une vision actuelle"""
        return result

    # LLM fallback
    prompt = f"""En tant qu'expert en hébergement et voyages, fournis des recommandations d'hôtels pour :
- Destination : {destination}
- Mois : {month}
- Budget : {budget}
- Durée : {duration_nights} nuits

Inclus pour chaque gamme (économique, intermédiaire, luxe) :
1. 2-3 hôtels recommandés avec prix par nuit
2. Points forts de chaque hôtel
3. Budget total estimé pour {duration_nights} nuits
4. Meilleures plateformes de réservation
5. Conseils spécifiques à la destination

Réponds en français avec des emojis et du Markdown."""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=900
    )
    return response.choices[0].message.content
