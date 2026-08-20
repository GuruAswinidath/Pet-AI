"""Vet-reviewed, static triage knowledge base.

Baked directly into code per README section 4.1 - no database, no file
reads at runtime. This keeps the safety property (fixed, vet-approved,
auditable) while dropping any file/DB dependency. Edit this table with
the same care you'd apply to a medical document: it's what the
deterministic Triage Engine (triage_engine.py) grounds every urgency
decision in.

Urgency vocabulary used elsewhere in the codebase:
  emergency - go to a vet / emergency clinic now
  soon      - see a vet within the next day or two
  home      - safe to monitor at home for now
"""

TRIAGE_KB: dict[str, dict] = {
    "vomiting": {
        "label": "Vomiting",
        "species": "both",
        "red_flags": [
            "blood in vomit",
            "vomiting blood",
            "distended abdomen",
            "bloated belly",
            "3+ times in a few hours",
            "repeated vomiting",
            "lethargy",
            "unable to keep water down",
            "vomiting and not eating for a full day",
        ],
        "yellow_flags": ["persists past 24 hours", "off and on for a couple of days"],
        "home_care": "Withhold food for a few hours (not water), then reintroduce a small bland meal. Monitor closely for repeat episodes.",
    },
    "diarrhea": {
        "label": "Diarrhea",
        "species": "both",
        "red_flags": [
            "blood in stool",
            "black tarry stool",
            "severe lethargy",
            "vomiting alongside diarrhea",
            "puppy or kitten under 6 months",
            "signs of dehydration",
        ],
        "yellow_flags": ["persists past 48 hours", "recurring over several days"],
        "home_care": "Offer a bland, easily digestible diet in small portions and make sure fresh water stays available. Monitor stool for the next day.",
    },
    "lethargy": {
        "label": "Lethargy / low energy",
        "species": "both",
        "red_flags": [
            "collapse",
            "unresponsive",
            "won't get up",
            "pale gums",
            "difficulty breathing",
            "sudden onset severe weakness",
        ],
        "yellow_flags": ["lasting more than a day", "getting worse"],
        "home_care": "Let your pet rest in a quiet space, keep water accessible, and watch for any new symptoms over the next several hours.",
    },
    "not_eating": {
        "label": "Not eating / reduced appetite",
        "species": "both",
        "red_flags": [
            "not eating for 2+ days",
            "not eating at all combined with vomiting",
            "not eating and lethargic",
            "cat not eating for over 24 hours",
        ],
        "yellow_flags": ["skipped meals for a day", "eating noticeably less than usual"],
        "home_care": "Try a small amount of a usual favorite food. Track how many meals are being skipped and whether water intake stays normal.",
    },
    "limping": {
        "label": "Limping / lameness",
        "species": "both",
        "red_flags": [
            "visible bone",
            "leg at an odd angle",
            "not bearing any weight at all",
            "limping after a fall from height",
            "limping after being hit by a car",
            "yelping in pain when touched",
        ],
        "yellow_flags": ["limping for more than a day", "limping getting worse"],
        "home_care": "Restrict activity and keep your pet from jumping or running. Check the paw for anything lodged in it (thorns, glass).",
    },
    "seizure": {
        "label": "Seizure",
        "species": "both",
        "red_flags": [
            "seizure",
            "convulsions",
            "seizure lasting more than a few minutes",
            "multiple seizures in one day",
            "not regaining consciousness after a seizure",
        ],
        "yellow_flags": [],
        "home_care": "Any seizure warrants a same-day vet call; keep the area around your pet clear of objects and do not put your hands near the mouth.",
    },
    "difficulty_breathing": {
        "label": "Difficulty breathing",
        "species": "both",
        "red_flags": [
            "labored breathing",
            "gasping",
            "open mouth breathing in a cat",
            "blue or pale gums",
            "choking",
            "collapsed after exercise",
        ],
        "yellow_flags": ["breathing faster than usual at rest"],
        "home_care": "This symptom should not be managed at home - even mild changes in breathing effort warrant prompt veterinary evaluation.",
    },
    "bloated_abdomen": {
        "label": "Bloated / distended abdomen",
        "species": "both",
        "red_flags": [
            "distended abdomen",
            "bloated belly",
            "retching without producing vomit",
            "restlessness with a swollen belly",
            "hard swollen abdomen",
        ],
        "yellow_flags": ["mild belly swelling after a large meal"],
        "home_care": "A tense, swollen abdomen - especially with unproductive retching - can indicate a life-threatening emergency (bloat/GDV) and should never be watched at home.",
    },
    "eye_injury": {
        "label": "Eye injury / irritation",
        "species": "both",
        "red_flags": [
            "eye popped out",
            "visible cut on the eye",
            "eye suddenly cloudy",
            "pawing at eye with swelling",
            "cannot open the eye",
        ],
        "yellow_flags": ["mild redness or watering for a day"],
        "home_care": "Prevent pawing/rubbing at the eye (a cone can help) and avoid rinsing with anything other than plain saline.",
    },
    "ear_infection": {
        "label": "Ear discomfort / infection signs",
        "species": "both",
        "red_flags": [
            "swollen ear flap",
            "head tilt",
            "loss of balance",
            "foul smelling discharge with pain",
        ],
        "yellow_flags": ["shaking head for more than a day", "scratching at ear repeatedly"],
        "home_care": "Do not insert anything into the ear canal. Keep the ear dry and monitor for increased swelling or odor.",
    },
    "skin_irritation": {
        "label": "Skin irritation / itching",
        "species": "both",
        "red_flags": [
            "sudden facial swelling",
            "hives with breathing trouble",
            "open wound that is spreading",
            "signs of an allergic reaction",
        ],
        "yellow_flags": ["persistent itching for several days", "hair loss in one area"],
        "home_care": "Prevent excessive scratching or licking where possible and keep the area clean and dry.",
    },
    "coughing": {
        "label": "Coughing",
        "species": "both",
        "red_flags": [
            "coughing up blood",
            "cough with difficulty breathing",
            "honking cough with collapse",
            "blue or pale gums while coughing",
        ],
        "yellow_flags": ["persistent cough for more than 2 days", "worsening cough"],
        "home_care": "Limit strenuous exercise and use a harness instead of a collar if coughing seems related to neck pressure.",
    },
    "urinary_issues": {
        "label": "Urinary issues",
        "species": "both",
        "red_flags": [
            "straining to urinate with little or no urine",
            "crying while trying to urinate",
            "cat unable to urinate",
            "blood in urine with straining",
        ],
        "yellow_flags": ["urinating more often than usual", "mild blood tinge in urine"],
        "home_care": "A cat straining with no urine output is a same-day emergency (possible blockage) and should never wait for home monitoring.",
    },
    "pain_vocalizing": {
        "label": "Pain / vocalizing in distress",
        "species": "both",
        "red_flags": [
            "crying out constantly",
            "won't let anyone touch a body part",
            "restless and panting with apparent pain",
            "sudden severe pain",
        ],
        "yellow_flags": ["occasional whimpering", "mild sensitivity when touched"],
        "home_care": "Keep your pet calm and confined to a safe, quiet space and avoid handling the painful area.",
    },
    "trauma_injury": {
        "label": "Trauma (hit by car, fall, fight)",
        "species": "both",
        "red_flags": [
            "hit by car",
            "fell from height",
            "animal fight with puncture wounds",
            "bleeding that won't stop",
            "unconscious after injury",
        ],
        "yellow_flags": ["minor scrape from a fall"],
        "home_care": "Any trauma from a vehicle, fall, or animal fight should be evaluated by a vet promptly even if your pet seems to be walking around normally.",
    },
    "poisoning_ingestion": {
        "label": "Possible poisoning / toxin ingestion",
        "species": "both",
        "red_flags": [
            "ate chocolate",
            "ate a human medication",
            "ate a toxic plant",
            "ate rat poison",
            "drooling and vomiting after eating something unknown",
            "known ingestion of a toxic substance",
        ],
        "yellow_flags": ["ate something unusual but is acting normal"],
        "home_care": "Do not induce vomiting unless a vet or poison control specifically instructs it - some substances cause more harm coming back up. Keep the packaging/plant to show the vet.",
    },
}

# Aliases so the Intake Agent's free-text extraction (or a user typing
# casually) still resolves to a canonical KB key. Kept separate from the
# KB itself so the KB stays a clean, reviewable medical table.
SYMPTOM_ALIASES: dict[str, str] = {
    "throwing up": "vomiting",
    "puking": "vomiting",
    "throwing up food": "vomiting",
    "loose stool": "diarrhea",
    "loose stools": "diarrhea",
    "runny stool": "diarrhea",
    "low energy": "lethargy",
    "tired": "lethargy",
    "sluggish": "lethargy",
    "no energy": "lethargy",
    "not hungry": "not_eating",
    "loss of appetite": "not_eating",
    "won't eat": "not_eating",
    "refusing food": "not_eating",
    "lameness": "limping",
    "favoring a leg": "limping",
    "can't walk properly": "limping",
    "convulsions": "seizure",
    "fits": "seizure",
    "shaking uncontrollably": "seizure",
    "trouble breathing": "difficulty_breathing",
    "breathing heavily": "difficulty_breathing",
    "gasping for air": "difficulty_breathing",
    "swollen belly": "bloated_abdomen",
    "belly is swollen": "bloated_abdomen",
    "distended belly": "bloated_abdomen",
    "red eye": "eye_injury",
    "eye discharge": "eye_injury",
    "watery eye": "eye_injury",
    "ear infection": "ear_infection",
    "smelly ears": "ear_infection",
    "shaking head": "ear_infection",
    "itching": "skin_irritation",
    "scratching a lot": "skin_irritation",
    "rash": "skin_irritation",
    "hot spot": "skin_irritation",
    "cough": "coughing",
    "hacking": "coughing",
    "can't pee": "urinary_issues",
    "straining to pee": "urinary_issues",
    "blood in urine": "urinary_issues",
    "peeing more": "urinary_issues",
    "crying in pain": "pain_vocalizing",
    "whimpering": "pain_vocalizing",
    "yelping": "pain_vocalizing",
    "hit by a car": "trauma_injury",
    "hit by car": "trauma_injury",
    "fell down": "trauma_injury",
    "dog fight": "trauma_injury",
    "attacked by another animal": "trauma_injury",
    "ate chocolate": "poisoning_ingestion",
    "ate poison": "poisoning_ingestion",
    "swallowed something": "poisoning_ingestion",
    "ate something toxic": "poisoning_ingestion",
}


def get_kb_entry(species: str | None, symptom_key: str | None) -> dict | None:
    """Deterministic lookup used by the Triage Engine and exposed as the
    get_kb_entry() tool from README section 7."""
    if not symptom_key:
        return None
    entry = TRIAGE_KB.get(symptom_key)
    if entry is None:
        return None
    if species and entry["species"] not in ("both", species):
        # Entry exists but is tagged for the other species - still return
        # it (better an imperfect match than none) so the caller can decide.
        return entry
    return entry
