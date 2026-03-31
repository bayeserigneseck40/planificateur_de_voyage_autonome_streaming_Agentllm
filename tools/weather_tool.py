"""
Outil Météo : fournit des informations climatiques détaillées pour une destination
et suggère les meilleures périodes de voyage via le LLM.
"""

import os
from openai import OpenAI

from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Base de données climatique enrichie pour les destinations populaires
CLIMATE_DATA = {
    "malaisie": {
        "description": "Climat tropical équatorial chaud et humide toute l'année",
        "months": {
            "janvier": {"temp": "26-32°C", "rain": "Modérée", "humidity": "Élevée", "score": 7},
            "février": {"temp": "26-32°C", "rain": "Faible", "humidity": "Modérée", "score": 9},
            "mars": {"temp": "27-33°C", "rain": "Faible", "humidity": "Modérée", "score": 9},
            "avril": {"temp": "27-33°C", "rain": "Modérée", "humidity": "Élevée", "score": 7},
            "mai": {"temp": "27-33°C", "rain": "Modérée", "humidity": "Élevée", "score": 7},
            "juin": {"temp": "27-33°C", "rain": "Faible (côte ouest)", "humidity": "Modérée", "score": 8},
            "juillet": {"temp": "26-32°C", "rain": "Faible (côte ouest)", "humidity": "Modérée", "score": 8},
            "août": {"temp": "26-32°C", "rain": "Faible (côte ouest)", "humidity": "Modérée", "score": 8},
            "septembre": {"temp": "26-32°C", "rain": "Modérée à forte", "humidity": "Élevée", "score": 6},
            "octobre": {"temp": "26-31°C", "rain": "Forte (côte est)", "humidity": "Très élevée", "score": 5},
            "novembre": {"temp": "25-31°C", "rain": "Forte", "humidity": "Très élevée", "score": 4},
            "décembre": {"temp": "25-30°C", "rain": "Forte (côte est)", "humidity": "Très élevée", "score": 5},
        },
        "best_periods": ["février", "mars", "juin", "juillet", "août"],
        "regions": {
            "Kuala Lumpur": "Accessible toute l'année, pluies courtes mais intenses",
            "Langkawi": "Meilleure période : novembre à avril (côte ouest)",
            "Côte Est (Perhentian, Tioman)": "Meilleure période : mars à octobre (fermé nov-fév)",
            "Bornéo (Sabah, Sarawak)": "Meilleure période : mars à octobre"
        }
    },
    "thaïlande": {
        "description": "Climat tropical avec trois saisons : fraîche, chaude et des pluies",
        "months": {
            "janvier": {"temp": "20-32°C", "rain": "Très faible", "humidity": "Faible", "score": 10},
            "février": {"temp": "22-33°C", "rain": "Très faible", "humidity": "Faible", "score": 10},
            "mars": {"temp": "24-35°C", "rain": "Faible", "humidity": "Modérée", "score": 8},
            "avril": {"temp": "26-36°C", "rain": "Modérée", "humidity": "Modérée", "score": 7},
            "mai": {"temp": "25-35°C", "rain": "Forte", "humidity": "Élevée", "score": 5},
            "juin": {"temp": "25-33°C", "rain": "Forte", "humidity": "Élevée", "score": 5},
            "juillet": {"temp": "24-32°C", "rain": "Forte", "humidity": "Élevée", "score": 5},
            "août": {"temp": "24-32°C", "rain": "Forte", "humidity": "Élevée", "score": 5},
            "septembre": {"temp": "24-31°C", "rain": "Très forte", "humidity": "Très élevée", "score": 4},
            "octobre": {"temp": "24-31°C", "rain": "Forte", "humidity": "Élevée", "score": 5},
            "novembre": {"temp": "22-31°C", "rain": "Modérée", "humidity": "Modérée", "score": 7},
            "décembre": {"temp": "20-30°C", "rain": "Faible", "humidity": "Faible", "score": 9},
        },
        "best_periods": ["novembre", "décembre", "janvier", "février", "mars"],
        "regions": {
            "Bangkok": "Meilleure période : novembre à février",
            "Chiang Mai": "Meilleure période : novembre à février",
            "Phuket": "Meilleure période : novembre à avril",
            "Koh Samui": "Meilleure période : janvier à août"
        }
    },
    "japon": {
        "description": "Climat tempéré avec quatre saisons bien distinctes",
        "months": {
            "janvier": {"temp": "2-10°C", "rain": "Faible", "humidity": "Faible", "score": 7},
            "février": {"temp": "3-11°C", "rain": "Faible", "humidity": "Faible", "score": 7},
            "mars": {"temp": "6-15°C", "rain": "Modérée", "humidity": "Modérée", "score": 9},
            "avril": {"temp": "12-20°C", "rain": "Modérée", "humidity": "Modérée", "score": 10},
            "mai": {"temp": "16-24°C", "rain": "Modérée", "humidity": "Modérée", "score": 9},
            "juin": {"temp": "20-27°C", "rain": "Forte (saison des pluies)", "humidity": "Élevée", "score": 6},
            "juillet": {"temp": "23-30°C", "rain": "Forte", "humidity": "Très élevée", "score": 6},
            "août": {"temp": "24-32°C", "rain": "Modérée", "humidity": "Élevée", "score": 7},
            "septembre": {"temp": "20-27°C", "rain": "Forte (typhons)", "humidity": "Élevée", "score": 6},
            "octobre": {"temp": "14-21°C", "rain": "Modérée", "humidity": "Modérée", "score": 10},
            "novembre": {"temp": "8-16°C", "rain": "Faible", "humidity": "Faible", "score": 9},
            "décembre": {"temp": "4-11°C", "rain": "Faible", "humidity": "Faible", "score": 7},
        },
        "best_periods": ["mars", "avril", "octobre", "novembre"],
        "regions": {
            "Tokyo": "Meilleure période : mars-avril (cerisiers) et octobre-novembre (feuillage)",
            "Kyoto": "Meilleure période : mars-avril et novembre",
            "Hokkaido": "Meilleure période : juin-août (été) ou janvier-février (ski)",
            "Okinawa": "Meilleure période : mai à octobre"
        }
    },
    "maroc": {
        "description": "Climat méditerranéen au nord, désertique au sud",
        "months": {
            "janvier": {"temp": "8-18°C", "rain": "Modérée", "humidity": "Modérée", "score": 7},
            "février": {"temp": "9-19°C", "rain": "Modérée", "humidity": "Modérée", "score": 7},
            "mars": {"temp": "11-21°C", "rain": "Faible", "humidity": "Faible", "score": 9},
            "avril": {"temp": "13-23°C", "rain": "Faible", "humidity": "Faible", "score": 9},
            "mai": {"temp": "16-26°C", "rain": "Très faible", "humidity": "Faible", "score": 10},
            "juin": {"temp": "20-31°C", "rain": "Très faible", "humidity": "Faible", "score": 9},
            "juillet": {"temp": "22-36°C", "rain": "Nulle", "humidity": "Faible", "score": 7},
            "août": {"temp": "22-36°C", "rain": "Nulle", "humidity": "Faible", "score": 7},
            "septembre": {"temp": "19-30°C", "rain": "Très faible", "humidity": "Faible", "score": 9},
            "octobre": {"temp": "15-25°C", "rain": "Faible", "humidity": "Faible", "score": 9},
            "novembre": {"temp": "11-20°C", "rain": "Modérée", "humidity": "Modérée", "score": 8},
            "décembre": {"temp": "8-17°C", "rain": "Modérée", "humidity": "Modérée", "score": 7},
        },
        "best_periods": ["mars", "avril", "mai", "septembre", "octobre"],
        "regions": {
            "Marrakech": "Meilleure période : mars-mai et septembre-novembre",
            "Fès": "Meilleure période : mars-mai et septembre-novembre",
            "Agadir": "Meilleure période : toute l'année (côte atlantique)",
            "Sahara (Merzouga)": "Meilleure période : octobre-avril (éviter juillet-août)"
        }
    }
}


def get_weather_info(destination: str, month: str, year: str = "") -> str:
    """
    Retourne les informations météorologiques pour une destination et une période.
    Utilise le LLM pour enrichir les données si la destination n'est pas dans la base locale.
    """
    destination_lower = destination.lower().strip()
    month_lower = month.lower().strip()

    # Chercher dans la base de données locale
    climate = None
    for key, data in CLIMATE_DATA.items():
        if key in destination_lower or destination_lower in key:
            climate = data
            break

    if climate and month_lower in climate["months"]:
        month_data = climate["months"][month_lower]
        score = month_data["score"]
        score_emoji = "🌟" * min(score // 2, 5)
        best = ", ".join(climate["best_periods"])

        # Alerte si mois non optimal
        warning = ""
        if score <= 5:
            warning = f"\n⚠️ **Attention** : {month_lower.capitalize()} n'est pas la meilleure période pour {destination}."
        elif score >= 9:
            warning = f"\n✅ **Excellent choix** : {month_lower.capitalize()} est une des meilleures périodes pour {destination} !"

        regions_text = "\n".join([f"  - **{r}** : {d}" for r, d in climate["regions"].items()])

        result = f"""## 🌤️ Météo & Climat — {destination.title()} en {month_lower.capitalize()} {year}

**Climat général** : {climate['description']}

### Conditions en {month_lower.capitalize()}
| Paramètre | Valeur |
|-----------|--------|
| 🌡️ Températures | {month_data['temp']} |
| 🌧️ Précipitations | {month_data['rain']} |
| 💧 Humidité | {month_data['humidity']} |
| ⭐ Score voyage | {score}/10 {score_emoji} |
{warning}

### 📍 Conditions par région
{regions_text}

### 🗓️ Meilleures périodes pour visiter {destination.title()}
Les mois recommandés sont : **{best}**

### 💡 Conseils pratiques
- Emportez toujours un imperméable léger en zone tropicale
- Consultez les alertes météo locales avant le départ
- Réservez à l'avance pendant les hautes saisons"""
        return result

    # Si destination non trouvée, utiliser le LLM pour générer les infos
    prompt = f"""En tant qu'expert météorologique et voyagiste, fournis des informations climatiques détaillées pour :
- Destination : {destination}
- Mois : {month} {year}

Inclus :
1. Description générale du climat
2. Températures moyennes (min/max)
3. Niveau de précipitations
4. Humidité
5. Score de voyage /10 pour ce mois
6. Les 3-5 meilleures périodes pour visiter
7. Conseils pratiques spécifiques
8. Alertes particulières (typhons, mousson, chaleur extrême...)

Réponds en français avec des emojis et du Markdown."""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800
    )
    return response.choices[0].message.content
