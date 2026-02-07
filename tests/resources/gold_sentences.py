"""
Gold Standard Sentences extracted from AnCora Guidelines.
Source: references/Guia sintaxi.txt

Structure:
{
    "Category": [
        {
            "id": "Section-ID",
            "text": "Sentence text",
            "phenomenon": "Description of what should be observed",
            "expected": "Brief description of expected structure (e.g., 'No subject', 'Coordination at SN')"
        }
    ]
}
"""

GOLD_SENTENCES = {
    "Sujeto Elíptico (Pro-Drop)": [
        {
            "id": "1.1",
            "text": "A Eivissa tenim un patrimoni cultural únic.",
            "phenomenon": "Sujeto elíptico (nosaltres)",
            "expected": "AnCora inserta un nodo vacío. Stanza probablemente lo omita.",
        },
        {
            "id": "1.2",
            "text": "Ofreció un total de 114 millones de euros.",
            "phenomenon": "Sujeto elíptico (él/ella)",
            "expected": "Verbo como raíz o hijo de S sin SN sujeto explícito.",
        },
        {
            "id": "1.4",
            "text": "No podem cedir terreny a Badia.",
            "phenomenon": "Sujeto elíptico con negación",
            "expected": "La negación 'no' debe estar dentro del grupo verbal o S.",
        },
    ],
    "Impersonalidad": [
        {
            "id": "1.15",
            "text": "No hi ha cap previsió.",
            "phenomenon": "Verbo haber impersonal (existencial)",
            "expected": "No debe haber sujeto. 'cap previsió' es Objeto Directo.",
        },
        {
            "id": "1.14",
            "text": "Es tracta d'una mostra.",
            "phenomenon": "Impersonal refleja con 'es'",
            "expected": "'Es' marcado como marca de impersonalidad o morfema verbal.",
        },
    ],
    "Coordinación": [
        {
            "id": "2.4",
            "text": "Diputats i consellers republicans.",
            "phenomenon": "Coordinación de SN",
            "expected": "Estructura plana o jerárquica donde 'i' une ambos nombres.",
        },
        {
            "id": "2.5",
            "text": "L'atur masculí es va situar en 64.248 i va disminuir en 2.493.",
            "phenomenon": "Coordinación de oraciones con sujeto compartido",
            "expected": "Dos oraciones coordinadas. La segunda tiene sujeto elíptico.",
        },
    ],
    "Sintagma Nominal Complejo": [
        {
            "id": "2.3",
            "text": "Punt de vista de la mobilitat.",
            "phenomenon": "Complementos del nombre en cadena",
            "expected": "AnCora los pone al mismo nivel (hermanos). Stanza podría anidarlos.",
        },
        {
            "id": "2.19",
            "text": "Els cinc primers mesos.",
            "phenomenon": "Determinantes complejos",
            "expected": "Estructura interna de 'spec' o modificadores del nombre.",
        },
    ],
    "Ambigüedad y 'Se'": [
        {
            "id": "2.123",
            "text": "Es va acostar al taxista.",
            "phenomenon": "Verbo pronominal (acostar-se)",
            "expected": "'Es' como morfema pronominal, no objeto.",
        },
        {
            "id": "2.125",
            "text": "Es durà a terme.",
            "phenomenon": "Pasiva refleja",
            "expected": "'Es' como marca de pasiva.",
        },
    ],
    "Locuciones y MWE": [
        {
            "id": "Appx.2",
            "text": "La posada en marxa del projecte.",
            "phenomenon": "Locución nominal (posada_en_marxa)",
            "expected": "Debería tratarse como una unidad léxica o un grupo plano.",
        }
    ],
}
