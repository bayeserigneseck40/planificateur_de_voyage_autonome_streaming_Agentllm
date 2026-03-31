"""
Outil Restaurants : recommande des expériences culinaires pour une destination.
"""

import os
from openai import OpenAI

from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

CUISINE_DATA = {
    "malaisie": {
        "specialites": [
            "Nasi Lemak (riz à la noix de coco, anchois, œuf dur)",
            "Char Kway Teow (nouilles sautées aux fruits de mer)",
            "Laksa (soupe de nouilles épicée au lait de coco)",
            "Roti Canai (pain feuilleté avec curry)",
            "Satay (brochettes marinées avec sauce cacahuète)",
            "Bak Kut Teh (soupe de côtes de porc aux herbes)",
            "Cendol (dessert glacé au lait de coco)"
        ],
        "restaurants": {
            "économique": [
                {"nom": "Jalan Alor Night Market", "ville": "Kuala Lumpur", "type": "Street food", "prix": "2-8€/repas", "description": "La rue street food la plus célèbre de KL, ambiance nocturne incontournable"},
                {"nom": "Petaling Street (Chinatown)", "ville": "Kuala Lumpur", "type": "Marché local", "prix": "2-6€/repas", "description": "Authentique Chinatown avec hawker stalls traditionnels"},
            ],
            "moyen": [
                {"nom": "Bijan Bar & Restaurant", "ville": "Kuala Lumpur", "type": "Malaisien traditionnel", "prix": "20-40€/repas", "description": "Cuisine malaisienne raffinée dans un cadre colonial"},
                {"nom": "Limapulo", "ville": "Kuala Lumpur", "type": "Nyonya (Peranakan)", "prix": "15-30€/repas", "description": "Cuisine Nyonya authentique, recettes transmises depuis 5 générations"},
            ],
            "gastronomique": [
                {"nom": "Nobu Kuala Lumpur", "ville": "Kuala Lumpur", "type": "Fusion japonais-péruvien", "prix": "80-150€/repas", "description": "Restaurant étoilé, vue panoramique sur les Tours Petronas"},
                {"nom": "Dewakan", "ville": "Kuala Lumpur", "type": "Haute cuisine malaisienne", "prix": "100-180€/repas", "description": "Premier restaurant malaisien dans la liste Asia's 50 Best"},
            ]
        },
        "conseils": [
            "Essayez les 'Hawker Centres' (centres de restauration de rue) pour une expérience authentique et abordable",
            "La Malaisie est un paradis pour les végétariens : cuisine indienne et chinoise très présentes",
            "Évitez l'eau du robinet, préférez l'eau en bouteille",
            "Les restaurants halal sont très répandus (majorité musulmane)",
            "Réservez pour les restaurants gastronomiques, surtout le week-end"
        ]
    },
    "thaïlande": {
        "specialites": [
            "Pad Thai (nouilles sautées aux crevettes)",
            "Tom Yum Goong (soupe épicée aux crevettes)",
            "Green Curry / Red Curry",
            "Som Tum (salade de papaye verte)",
            "Mango Sticky Rice (riz gluant à la mangue)",
            "Massaman Curry (curry doux aux pommes de terre)"
        ],
        "restaurants": {
            "économique": [
                {"nom": "Or Tor Kor Market", "ville": "Bangkok", "type": "Marché alimentaire", "prix": "3-8€/repas", "description": "Le meilleur marché alimentaire de Bangkok, produits frais et plats cuisinés"},
            ],
            "moyen": [
                {"nom": "Nahm", "ville": "Bangkok", "type": "Thaï traditionnel", "prix": "40-80€/repas", "description": "Cuisine thaïlandaise authentique, dans la liste des 50 meilleurs d'Asie"},
            ],
            "gastronomique": [
                {"nom": "Le Normandie", "ville": "Bangkok", "type": "Français étoilé", "prix": "150-250€/repas", "description": "Restaurant 2 étoiles Michelin au Mandarin Oriental"},
            ]
        },
        "conseils": [
            "Mangez dans les marchés de nuit pour l'authenticité et les prix bas",
            "Précisez votre tolérance au piment ('pet nit noi' = peu épicé)",
            "Les restaurants de rue sont souvent meilleurs que les restaurants touristiques"
        ]
    },
    "maroc": {
        "specialites": [
            "Tajine (ragoût mijoté en poterie)",
            "Couscous (plat national du vendredi)",
            "Pastilla (feuilleté sucré-salé au pigeon ou poulet)",
            "Harira (soupe traditionnelle)",
            "Mechoui (agneau rôti entier)",
            "Msemen (crêpes feuilletées)",
            "Thé à la menthe"
        ],
        "restaurants": {
            "économique": [
                {"nom": "Djemaa el-Fna", "ville": "Marrakech", "type": "Street food", "prix": "3-10€/repas", "description": "La place mythique avec ses dizaines de stands de grillades le soir"},
            ],
            "moyen": [
                {"nom": "Dar Yacout", "ville": "Marrakech", "type": "Marocain traditionnel", "prix": "40-70€/repas", "description": "Riad somptueux, dîner aux chandelles, musique gnaoua"},
            ],
            "gastronomique": [
                {"nom": "Le Grand Café de la Poste", "ville": "Marrakech", "type": "Franco-marocain", "prix": "50-100€/repas", "description": "Institution coloniale, cuisine fusion raffinée"},
            ]
        },
        "conseils": [
            "Négociez toujours le prix dans les restaurants sans menu affiché",
            "Le couscous est traditionnellement servi le vendredi",
            "Goûtez impérativement le thé à la menthe et les pâtisseries locales",
            "Réservez pour les riads-restaurants, souvent limités en places"
        ]
    }
}


def search_restaurants(destination: str, cuisine_type: str = "locale", budget: str = "tous") -> str:
    """
    Recommande des restaurants et expériences culinaires pour une destination.
    """
    destination_lower = destination.lower().strip()
    cuisine_info = None

    for key, data in CUISINE_DATA.items():
        if key in destination_lower or destination_lower in key:
            cuisine_info = data
            break

    if cuisine_info:
        # Spécialités
        specialites_text = "\n".join([f"  - {s}" for s in cuisine_info["specialites"]])

        # Restaurants par budget
        budgets_to_show = ["économique", "moyen", "gastronomique"] if budget == "tous" else [budget]
        sections = []

        icons = {"économique": "💚", "moyen": "💛", "gastronomique": "💎"}
        labels = {"économique": "Petit budget (street food & locaux)", "moyen": "Budget intermédiaire", "gastronomique": "Gastronomique"}

        for b in budgets_to_show:
            if b in cuisine_info["restaurants"]:
                icon = icons.get(b, "⭐")
                label = labels.get(b, b)
                restaurants = cuisine_info["restaurants"][b]
                rests_text = ""
                for r in restaurants:
                    rests_text += f"\n**{r['nom']}** — {r['ville']}\n"
                    rests_text += f"  - 🍴 Type : {r['type']}\n"
                    rests_text += f"  - 💰 Prix : {r['prix']}\n"
                    rests_text += f"  - 📝 {r['description']}\n"
                sections.append(f"### {icon} {label}\n{rests_text}")

        sections_text = "\n".join(sections)
        conseils_text = "\n".join([f"  - {c}" for c in cuisine_info["conseils"]])

        result = f"""## 🍽️ Gastronomie & Restaurants — {destination.title()}

### 🌟 Spécialités incontournables à goûter
{specialites_text}

{sections_text}

### 🌐 Plateformes de réservation
- [TheFork (LaFourchette)](https://www.thefork.fr) — Réservation en ligne, réductions fréquentes
- [TripAdvisor Restaurants](https://www.tripadvisor.fr) — Avis et réservations
- [Google Maps](https://maps.google.com) — Recherche locale, horaires, avis
- [Yelp](https://www.yelp.fr) — Avis détaillés et photos

### 💡 Conseils gastronomiques pour {destination.title()}
{conseils_text}

### 📊 Budget repas estimé par jour
| Gamme | Coût estimé / personne / jour |
|-------|-------------------------------|
| 💚 Street food & locaux | 10€ - 25€ |
| 💛 Restaurants intermédiaires | 30€ - 60€ |
| 💎 Gastronomique | 80€ - 200€+ |"""
        return result

    # LLM fallback
    prompt = f"""En tant qu'expert culinaire et guide gastronomique, fournis des recommandations de restaurants pour :
- Destination : {destination}
- Type de cuisine : {cuisine_type}
- Budget : {budget}

Inclus :
1. 5-7 spécialités locales incontournables
2. 2-3 restaurants recommandés par gamme de prix (économique, intermédiaire, gastronomique)
3. Budget repas estimé par jour
4. Plateformes de réservation recommandées
5. Conseils pratiques (allergies, habitudes locales, pourboires...)

Réponds en français avec des emojis et du Markdown."""

    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=900
    )
    return response.choices[0].message.content
