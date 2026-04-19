"""
Moteur ReAct + CoT pour l'Agent de Planification de Voyage Autonome.
Implémente la boucle Thought → Action → Observation jusqu'à la réponse finale.
Utilise le mode non-streaming avec simulation de streaming token par token.
"""

import json
import os
import time
from pathlib import Path
from openai import OpenAI

from dotenv import load_dotenv
load_dotenv()


from tools.weather_tool import get_weather_info
from tools.flights_tool import search_flights
from tools.hotels_tool import search_hotels
from tools.restaurants_tool import search_restaurants
from tools.itinerary_tool import build_itinerary

client = OpenAI()

# ─────────────────────────────────────────────
# Définition des outils disponibles pour l'agent
# ─────────────────────────────────────────────
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather_info",
            "description": (
                "Récupère les informations météorologiques pour une destination et une période donnée. "
                "Indique les conditions climatiques, les températures moyennes, les précipitations, "
                "et suggère les meilleures périodes pour voyager si la date est floue."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string", "description": "Ville ou pays de destination"},
                    "month": {"type": "string", "description": "Mois du voyage (ex: 'septembre', 'juillet')"},
                    "year": {"type": "string", "description": "Année optionnelle (ex: '2025')", "default": ""}
                },
                "required": ["destination", "month"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_flights",
            "description": (
                "Recherche des options de vols ou de trains pour une destination. "
                "Retourne des suggestions de compagnies, prix estimés, durées et plateformes de réservation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string", "description": "Ville ou pays de destination"},
                    "origin": {"type": "string", "description": "Ville ou pays de départ", "default": "France"},
                    "month": {"type": "string", "description": "Mois du voyage"},
                    "transport_type": {
                        "type": "string",
                        "enum": ["vol", "train", "les deux"],
                        "description": "Type de transport souhaité",
                        "default": "les deux"
                    }
                },
                "required": ["destination", "month"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_hotels",
            "description": (
                "Recherche des hôtels et hébergements pour une destination et une période. "
                "Retourne des suggestions avec catégories, prix estimés et plateformes de réservation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string", "description": "Ville ou pays de destination"},
                    "month": {"type": "string", "description": "Mois du séjour"},
                    "budget": {
                        "type": "string",
                        "enum": ["économique", "moyen", "luxe", "tous"],
                        "description": "Gamme de budget",
                        "default": "tous"
                    },
                    "duration_nights": {"type": "integer", "description": "Nombre de nuits estimé", "default": 7}
                },
                "required": ["destination", "month"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_restaurants",
            "description": (
                "Recherche des restaurants et expériences culinaires pour une destination. "
                "Retourne des suggestions de restaurants locaux, spécialités, et plateformes de réservation."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string", "description": "Ville ou pays de destination"},
                    "cuisine_type": {
                        "type": "string",
                        "description": "Type de cuisine souhaité (locale, internationale, végétarienne...)",
                        "default": "locale"
                    },
                    "budget": {
                        "type": "string",
                        "enum": ["économique", "moyen", "gastronomique", "tous"],
                        "default": "tous"
                    }
                },
                "required": ["destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "build_itinerary",
            "description": (
                "Construit et formate l'itinéraire final complet du voyage en consolidant toutes "
                "les informations collectées (météo, vols, hôtels, restaurants). "
                "Retourne un document structuré prêt à être exporté ou envoyé par email."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "destination": {"type": "string", "description": "Destination principale"},
                    "month": {"type": "string", "description": "Mois du voyage"},
                    "duration": {"type": "string", "description": "Durée estimée du séjour"},
                    "weather_summary": {"type": "string", "description": "Résumé météo"},
                    "flights_summary": {"type": "string", "description": "Résumé des options de transport"},
                    "hotels_summary": {"type": "string", "description": "Résumé des options d'hébergement"},
                    "restaurants_summary": {"type": "string", "description": "Résumé des options de restauration"},
                    "traveler_name": {"type": "string", "description": "Nom du voyageur", "default": "Voyageur"}
                },
                "required": ["destination", "month", "weather_summary", "flights_summary", "hotels_summary", "restaurants_summary"]
            }
        }
    }
]

# ─────────────────────────────────────────────
# Prompt système ReAct + CoT
# ─────────────────────────────────────────────
SYSTEM_PROMPT = """Tu es un Agent Expert en Planification de Voyage Autonome. Tu utilises la technique ReAct (Reasoning + Acting) combinée avec Chain-of-Thought (CoT) pour planifier des voyages de manière exhaustive et personnalisée.

## Ton processus de raisonnement (ReAct + CoT)

Pour chaque demande de voyage, tu dois suivre ce cycle :

**THOUGHT** → Réfléchis à ce que tu dois faire, quelles informations manquent, dans quel ordre les collecter.
**ACTION** → Appelle les outils nécessaires pour collecter les informations.
**OBSERVATION** → Analyse les résultats et décide de la prochaine étape.
**REPEAT** → Continue jusqu'à avoir toutes les informations nécessaires.
**FINAL ANSWER** → Synthétise tout en un plan de voyage complet.

## Tes capacités

1. **Météo & Climat** : Analyser les conditions météorologiques, suggérer les meilleures périodes si la date est vague (ex: "septembre" sans année précise).
2. **Transport** : Rechercher vols, trains, options de transport avec prix estimés et plateformes de réservation.
3. **Hébergement** : Suggérer des hôtels selon le budget et les préférences.
4. **Restauration** : Recommander des restaurants et expériences culinaires locales.
5. **Itinéraire** : Construire un plan jour par jour cohérent et exportable.

## Règles importantes

- Si la date est floue (ex: "septembre"), commence TOUJOURS par analyser la météo pour suggérer les meilleures sous-périodes.
- Appelle les outils dans cet ordre logique : météo → transport → hébergement → restauration → itinéraire final.
- Sois proactif : anticipe les besoins du voyageur (visa, vaccins, budget total estimé).
- Présente toujours les informations de manière structurée avec des sections claires.
- Propose toujours des alternatives (budget économique ET premium).
- À la fin, propose systématiquement de télécharger l'itinéraire en PDF ou de l'envoyer par email.
- Réponds toujours en français sauf si l'utilisateur parle une autre langue.

## Format de réponse

Utilise des emojis et du Markdown pour rendre la réponse lisible :
- 🌤️ pour la météo
- ✈️ pour les vols
- 🏨 pour les hôtels  
- 🍽️ pour les restaurants
- 📅 pour l'itinéraire
- 💡 pour les conseils pratiques
"""

# ─────────────────────────────────────────────
# Dispatcher des outils
# ─────────────────────────────────────────────
TOOL_DISPATCHER = {
    "get_weather_info": get_weather_info,
    "search_flights": search_flights,
    "search_hotels": search_hotels,
    "search_restaurants": search_restaurants,
    "build_itinerary": build_itinerary,
}


def run_tool(tool_name: str, tool_args: dict) -> str:
    """Exécute un outil et retourne le résultat sous forme de chaîne."""
    func = TOOL_DISPATCHER.get(tool_name)
    if func is None:
        return f"Erreur : outil '{tool_name}' introuvable."
    try:
        result = func(**tool_args)
        return result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"Erreur lors de l'exécution de {tool_name} : {str(e)}"


def simulate_streaming(text: str, on_thought, chunk_size: int = 8, delay: float = 0.01):
    """Simule le streaming token par token depuis un texte complet."""
    if not on_thought:
        return
    words = text.split(' ')
    buffer = ""
    for i, word in enumerate(words):
        buffer += word + (' ' if i < len(words) - 1 else '')
        if len(buffer) >= chunk_size:
            on_thought(buffer)
            buffer = ""
            time.sleep(delay)
    if buffer:
        on_thought(buffer)


def stream_agent_response(messages: list, on_thought=None, on_tool_call=None, on_tool_result=None):
    """
    Boucle ReAct principale.
    
    Paramètres :
    - messages : historique de la conversation
    - on_thought : callback(text) appelé pour chaque chunk de raisonnement
    - on_tool_call : callback(tool_name, tool_args) appelé avant l'exécution d'un outil
    - on_tool_result : callback(tool_name, result) appelé après l'exécution d'un outil
    
    Retourne : le texte final de la réponse de l'agent
    """
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # ── Appel au LLM (non-streaming pour compatibilité) ──
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.7,
        )

        choice = response.choices[0]
        message = choice.message
        finish_reason = choice.finish_reason

        # ── Si l'agent a du texte à afficher ──
        if message.content:
            simulate_streaming(message.content, on_thought)

        # ── Si l'agent a fini (pas d'outil à appeler) ──
        if finish_reason == "stop" or not message.tool_calls:
            final_text = message.content or ""
            messages.append({"role": "assistant", "content": final_text})
            return final_text

        # ── Exécution des outils appelés ──
        if message.tool_calls:
            # Ajouter le message assistant avec les tool_calls
            messages.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            })

            # Exécuter chaque outil et ajouter les résultats
            for tc in message.tool_calls:
                tool_name = tc.function.name
                try:
                    tool_args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    tool_args = {}

                if on_tool_call:
                    on_tool_call(tool_name, tool_args)

                result = run_tool(tool_name, tool_args)

                if on_tool_result:
                    on_tool_result(tool_name, result)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result
                })

    return "L'agent a atteint le nombre maximum d'itérations."
