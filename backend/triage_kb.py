"""Vet-reviewed, static triage knowledge base - cats only.

Baked directly into code per README section 4.1 - no database, no file
reads at runtime. This keeps the safety property (fixed, vet-approved,
auditable) while dropping any file/DB dependency. Edit this table with
the same care you'd apply to a medical document: it's what the
deterministic Triage Engine (triage_engine.py) grounds every urgency
decision in.

Scope: this assistant supports cats only (see turn_processor.py's
out-of-scope redirect for other species). Every entry below is written
for feline presentation specifically - several symptoms (open-mouth
breathing, straining to urinate, going 24+ hours without food) carry a
different, often more urgent, meaning in cats than they would in a
species-agnostic KB, which is why localizing this content matters and
isn't just a wording pass.

Urgency vocabulary used elsewhere in the codebase:
  emergency - go to a vet / emergency clinic now
  soon      - see a vet within the next day or two
  home      - safe to monitor at home for now

Each entry also carries `typical_triage_level` - documentation only,
showing the usual outcome for that symptom in isolation. It is NOT read
by the Triage Engine, which always decides dynamically from the actual
red/yellow flag matches (README section 1: the urgency decision must
stay a deterministic function of the reported signs, not a static
per-symptom label). `questions_to_ask` is read by the Conversation Agent
(agents/conversation.py) as phrasing hints for its one allowed
clarifying question per turn.
"""

TRIAGE_KB: dict[str, dict] = {
    "urinary_obstruction": {
        "label": "Urinary obstruction / straining to urinate (FLUTD)",
        "typical_triage_level": "emergency",
        "questions_to_ask": [
            "Is your cat male or female?",
            "When did you last actually see them produce urine?",
            "Are they going in and out of the litter box repeatedly with little or nothing coming out?",
            "Are they crying, straining, or licking at their genital area?",
            "Any vomiting, lethargy, or loss of appetite along with this?",
        ],
        "red_flags": [
            "straining to urinate with little or no urine",
            "crying while trying to urinate",
            "unable to urinate",
            "repeated trips to the litter box with no output",
            "blood in urine with straining",
            "vocalizing in the litter box",
            "male cat straining to pee",
            "lethargy with straining to urinate",
            "vomiting with straining to urinate",
            "hard, painful bladder",
        ],
        "yellow_flags": [
            "urinating more often than usual",
            "mild blood tinge in urine",
            "small accidents just outside the litter box",
        ],
        "owner_guidance": "A cat straining with little or no urine coming out is a same-day emergency, not a wait-and-see situation - a blocked urethra (far more common in male cats) can cause fatal kidney failure within 24-48 hours. Do not try to wait this out at home; go to a vet or emergency clinic now.",
    },
    "constipation": {
        "label": "Constipation / straining to defecate",
        "typical_triage_level": "soon",
        "questions_to_ask": [
            "Is your cat straining to urinate or to pass stool - which does it look like?",
            "When did they last produce a normal stool?",
            "Small, hard, dry pellets, or straining with nothing coming out at all?",
            "Any vomiting or reduced appetite?",
            "Any recent diet or litter changes?",
        ],
        "red_flags": [
            "straining in litter box for more than a day with nothing produced",
            "vomiting with constipation",
            "firm distended abdomen with straining",
            "crying while straining to defecate",
            "no bowel movement in 3 or more days",
        ],
        "yellow_flags": [
            "small hard stools for a day or two",
            "straining occasionally but still passing some stool",
        ],
        "owner_guidance": "Owners often can't tell straining-to-pee from straining-to-poop apart just by looking - if there's any doubt, treat it as the urinary emergency above and have it checked same-day. True constipation with a cat still passing small hard stools and otherwise acting normal can usually be watched briefly, but repeated straining with nothing produced, or any vomiting alongside it, needs a vet visit within the day.",
    },
    "vomiting": {
        "label": "Vomiting",
        "typical_triage_level": "varies",
        "questions_to_ask": [
            "Does the vomit contain hair, undigested food, or clear/yellow fluid?",
            "How many times has this happened, and over what period?",
            "Are they still eating, drinking, and acting normally in between?",
            "Any blood, or does it look like coffee grounds?",
            "Has this been a recurring pattern for weeks, even if infrequent?",
        ],
        "red_flags": [
            "blood in vomit",
            "vomiting blood",
            "coffee-ground vomit",
            "distended abdomen",
            "bloated belly",
            "3+ times in a few hours",
            "repeated vomiting",
            "lethargy",
            "unable to keep water down",
            "vomiting and not eating for a full day",
            "vomiting with straining to urinate",
        ],
        "yellow_flags": [
            "persists past 24 hours",
            "off and on for a couple of days",
            "vomiting more than once a week as an ongoing pattern",
        ],
        "owner_guidance": "An occasional hairball from a cat that's otherwise eating and behaving normally usually isn't urgent - withhold food for a few hours (not water), then offer a small bland meal. But repeated vomiting, vomiting paired with not eating, or any blood should be seen the same day. A pattern of vomiting more than a couple of times a month, even if each episode looks mild, is worth a non-urgent vet visit - in cats that pattern can point to chronic issues like IBD, hyperthyroidism, or kidney disease rather than 'just hairballs'.",
    },
    "diarrhea": {
        "label": "Diarrhoea (loose or watery stool)",
        "typical_triage_level": "soon",
        "questions_to_ask": [
            "How old is your cat - are they a kitten under 6 months?",
            "Any blood, black tarry color, or unusual smell?",
            "Any vomiting along with the diarrhoea?",
            "Are they still eating, drinking, and acting normally otherwise?",
            "Any recent food change, new treats, or access to something they shouldn't have eaten?",
        ],
        "red_flags": [
            "blood in stool",
            "black tarry stool",
            "severe lethargy",
            "vomiting alongside diarrhea",
            "kitten under 6 months",
            "signs of dehydration",
            "diarrhea with not eating",
        ],
        "yellow_flags": ["persists past 48 hours", "recurring over several days"],
        "owner_guidance": "Offer a bland, easily digestible diet in small portions and keep fresh water available; monitor stool over the next day. A kitten, any blood or black stool, vomiting alongside it, or diarrhoea that drags past 48 hours all warrant a vet visit rather than continued home monitoring - kittens dehydrate far faster than adult cats.",
    },
    "not_eating": {
        "label": "Loss of appetite / not eating",
        "typical_triage_level": "soon",
        "questions_to_ask": [
            "Roughly how many hours or meals has it been since they last ate anything?",
            "Are they still drinking water normally?",
            "Is your cat overweight? (Cats that stop eating - especially heavier cats - are at real risk of a serious liver condition after just 1-2 days.)",
            "Any vomiting, diarrhoea, or hiding along with the appetite change?",
        ],
        "red_flags": [
            "not eating for 2+ days",
            "not eating at all combined with vomiting",
            "not eating and lethargic",
            "not eating for over 24 hours in an overweight cat",
            "not eating and hiding",
            "not eating with yellowing of the gums or skin",
        ],
        "yellow_flags": [
            "skipped meals for a day",
            "eating noticeably less than usual",
            "picking at food but not finishing meals",
        ],
        "owner_guidance": "This is taken more seriously in cats than in most pets: going without food for as little as 24-48 hours - especially in an overweight cat - can trigger a dangerous liver condition (hepatic lipidosis). Try offering a usual favorite food and track how much is actually eaten. If it stretches past 24 hours, or comes with vomiting, diarrhoea, or hiding, treat it as same-day rather than wait-and-see.",
    },
    "difficulty_breathing": {
        "label": "Breathing difficulty",
        "typical_triage_level": "emergency",
        "questions_to_ask": [
            "Is your cat breathing with their mouth open?",
            "Are they hiding, reluctant to move, or crouched with elbows out?",
            "Can you estimate how fast they're breathing at rest (breaths per minute)?",
            "Any recent trauma, or a known heart condition?",
        ],
        "red_flags": [
            "labored breathing",
            "gasping",
            "open mouth breathing in a cat",
            "blue or pale gums",
            "choking",
            "collapsed after exercise",
            "breathing with elbows out or crouched low",
            "rapid shallow breathing at rest",
        ],
        "yellow_flags": ["breathing faster than usual at rest"],
        "owner_guidance": "Unlike dogs, cats don't pant as a normal cooling behavior - open-mouth breathing, or breathing that looks labored or rapid while resting, is almost always abnormal and should never be watched at home. This needs emergency evaluation now, even if your cat still seems otherwise alert.",
    },
    "skin_irritation": {
        "label": "Skin issues (itching, overgrooming, hair loss, rash)",
        "typical_triage_level": "home",
        "questions_to_ask": [
            "Is it in one spot or spread across the body?",
            "Is your cat licking or grooming that area more than usual?",
            "Any fleas or flea dirt visible, and are they on flea prevention?",
            "Any recent change in food, litter brand, or household cleaning products?",
            "Indoor-only, or do they spend time outside?",
        ],
        "red_flags": [
            "sudden facial swelling",
            "hives with breathing trouble",
            "open wound that is spreading",
            "signs of an allergic reaction",
            "raw, broken skin from grooming",
        ],
        "yellow_flags": [
            "persistent itching for several days",
            "hair loss in one area",
            "overgrooming a specific spot",
            "small scabs scattered across the body",
        ],
        "owner_guidance": "Prevent excessive licking or scratching where possible (a cone can help) and keep the area clean and dry. Overgrooming down to bald or raw skin, or a scattering of small scabs, is common with flea allergy or other allergic skin disease in cats and is worth a routine vet visit rather than an emergency one - unless it comes with facial swelling or breathing trouble, which needs care right away.",
    },
    "lethargy": {
        "label": "Lethargy / low energy / hiding",
        "typical_triage_level": "soon",
        "questions_to_ask": [
            "Are they hiding more than usual, or avoiding contact?",
            "Still eating, drinking, and using the litter box normally?",
            "Any change in breathing, gum color, or ability to stand?",
            "How long has this been going on?",
        ],
        "red_flags": [
            "collapse",
            "unresponsive",
            "won't get up",
            "pale or blue gums",
            "difficulty breathing",
            "sudden onset severe weakness",
            "hiding and not eating",
        ],
        "yellow_flags": ["lasting more than a day", "getting worse"],
        "owner_guidance": "Cats are very good at hiding illness, so lethargy that's noticeable enough for an owner to flag is worth taking seriously rather than assuming it will pass. Let them rest somewhere quiet with water accessible, but if it's paired with hiding, not eating, or lasts more than a day, that's a reason to see a vet rather than keep waiting.",
    },
    "limping": {
        "label": "Limping / lameness",
        "typical_triage_level": "soon",
        "questions_to_ask": [
            "Which leg, and are they putting any weight on it at all?",
            "Any recent fall, jump, or known trauma - including a fall from a height (window, balcony)?",
            "Any visible wound, swelling, or bleeding?",
            "How long has the limp been going on?",
        ],
        "red_flags": [
            "visible bone",
            "leg at an odd angle",
            "not bearing any weight at all",
            "limping after a fall from height",
            "limping after being hit by a car",
            "yelping in pain when touched",
        ],
        "yellow_flags": ["limping for more than a day", "limping getting worse"],
        "owner_guidance": "Restrict activity and keep your cat from jumping or climbing. Check the paw for anything lodged in it. Cats can survive falls from significant heights ('high-rise syndrome') with injuries that aren't obvious at first, so any limping following a fall should be checked by a vet even if your cat is walking around.",
    },
    "seizure": {
        "label": "Seizure",
        "typical_triage_level": "emergency",
        "questions_to_ask": [
            "How long did the seizure last?",
            "Has there been more than one today?",
            "Have they fully regained normal awareness afterward?",
            "Any known toxin exposure or head trauma beforehand?",
        ],
        "red_flags": [
            "seizure",
            "convulsions",
            "seizure lasting more than a few minutes",
            "multiple seizures in one day",
            "not regaining consciousness after a seizure",
        ],
        "yellow_flags": [],
        "owner_guidance": "Any seizure in a cat warrants a same-day vet call. Keep the area clear of objects your cat could hit and do not put your hands near the mouth.",
    },
    "bloated_abdomen": {
        "label": "Bloated / distended abdomen",
        "typical_triage_level": "emergency",
        "questions_to_ask": [
            "Is the belly firm and tense, or soft?",
            "Any retching without bringing anything up?",
            "Is your cat a kitten - could this be a heavy parasite load?",
            "Any known heart, liver, or prior FIP diagnosis?",
        ],
        "red_flags": [
            "distended abdomen",
            "bloated belly",
            "retching without producing vomit",
            "restlessness with a swollen belly",
            "hard swollen abdomen",
            "sudden fluid-filled belly",
        ],
        "yellow_flags": ["mild belly swelling after a large meal"],
        "owner_guidance": "True stomach-twisting bloat (GDV) is rare in cats compared to large dogs, but a tense or fluid-filled abdomen in a cat is still not something to watch at home - it can point to serious causes like fluid buildup from heart, liver, or infectious disease (e.g. FIP), organ enlargement, or a heavy worm burden in a kitten. Have it evaluated the same day.",
    },
    "eye_injury": {
        "label": "Eye injury / irritation",
        "typical_triage_level": "soon",
        "questions_to_ask": [
            "One eye or both?",
            "Any visible cut, cloudiness, or bulging?",
            "Is your cat pawing at the eye or keeping it closed?",
            "Any recent fight with another cat (scratch injuries are common)?",
        ],
        "red_flags": [
            "eye popped out",
            "visible cut on the eye",
            "eye suddenly cloudy",
            "pawing at eye with swelling",
            "cannot open the eye",
        ],
        "yellow_flags": ["mild redness or watering for a day"],
        "owner_guidance": "Prevent pawing or rubbing at the eye (a cone can help) and avoid rinsing with anything other than plain saline. Cat-fight scratches to the eye are common and can look minor at first but need prompt attention, since corneal injuries can worsen quickly.",
    },
    "ear_infection": {
        "label": "Ear discomfort / infection signs",
        "typical_triage_level": "soon",
        "questions_to_ask": [
            "One ear or both?",
            "Any discharge, odor, or visible swelling?",
            "Head tilt, stumbling, or loss of balance?",
        ],
        "red_flags": [
            "swollen ear flap",
            "head tilt",
            "loss of balance",
            "foul smelling discharge with pain",
        ],
        "yellow_flags": ["shaking head for more than a day", "scratching at ear repeatedly"],
        "owner_guidance": "Do not insert anything into the ear canal. Keep the ear dry and monitor for increased swelling or odor. A head tilt or balance problem points to a deeper inner-ear issue and should be seen promptly, not just monitored.",
    },
    "coughing": {
        "label": "Coughing",
        "typical_triage_level": "soon",
        "questions_to_ask": [
            "Does it look like hunching/hacking to bring up a hairball, or a dry repetitive cough?",
            "Any wheezing or breathing difficulty with the cough?",
            "How long has the cough been going on?",
            "Any known asthma diagnosis?",
        ],
        "red_flags": [
            "coughing up blood",
            "cough with difficulty breathing",
            "wheezing cough with open mouth breathing",
            "blue or pale gums while coughing",
        ],
        "yellow_flags": ["persistent cough for more than 2 days", "worsening cough"],
        "owner_guidance": "A single hunch-and-hack to bring up a hairball is normal cat behavior and not the same as a true cough. A repeated, dry cough - especially with any wheezing - is a common sign of feline asthma and is worth a non-urgent vet visit; if it's ever paired with breathing difficulty, treat that as an emergency instead.",
    },
    "pain_vocalizing": {
        "label": "Pain / vocalizing in distress",
        "typical_triage_level": "soon",
        "questions_to_ask": [
            "Where does the pain seem to be - can you tell what they don't want touched?",
            "Are they hiding along with the vocalizing?",
            "Any known injury or recent event that could explain it?",
        ],
        "red_flags": [
            "crying out constantly",
            "won't let anyone touch a body part",
            "restless and hiding with apparent pain",
            "sudden severe pain",
        ],
        "yellow_flags": ["occasional vocalizing", "mild sensitivity when touched"],
        "owner_guidance": "Keep your cat calm and confined to a safe, quiet space and avoid handling the painful area. Cats vocalizing from pain - rather than just meowing for attention - are usually also hiding or acting differently, and that combination deserves a same-day look rather than waiting.",
    },
    "trauma_injury": {
        "label": "Trauma (fall, hit by car, cat fight)",
        "typical_triage_level": "emergency",
        "questions_to_ask": [
            "What happened - a fall, a vehicle, or a fight with another animal?",
            "If a fall, from roughly what height?",
            "Any visible wounds, limping, or difficulty breathing since?",
            "Is your cat walking around normally now, or hiding and quiet?",
        ],
        "red_flags": [
            "hit by car",
            "fell from height",
            "animal fight with puncture wounds",
            "bleeding that won't stop",
            "unconscious after injury",
        ],
        "yellow_flags": ["minor scrape from a fall"],
        "owner_guidance": "Any trauma from a vehicle, a fall from height, or a fight with another animal should be evaluated by a vet promptly, even if your cat seems to be walking around normally afterward - cats often mask serious internal injury with an outwardly normal appearance for hours before deteriorating, and puncture wounds from a cat fight commonly abscess if left untreated.",
    },
    "poisoning_ingestion": {
        "label": "Possible poisoning / toxin ingestion",
        "typical_triage_level": "emergency",
        "questions_to_ask": [
            "What exactly did they eat or get exposed to, and roughly how much?",
            "How long ago did this happen?",
            "Any lilies in the house - even pollen or vase water?",
            "Any vomiting, drooling, or wobbliness since?",
        ],
        "red_flags": [
            "ate any part of a lily plant",
            "exposed to lily pollen or lily vase water",
            "ate chocolate",
            "ate a human medication",
            "ate a toxic plant",
            "ate rat poison",
            "applied a dog flea/tick product containing permethrin",
            "ate onion or garlic",
            "drooling and vomiting after eating something unknown",
            "known ingestion of a toxic substance",
        ],
        "yellow_flags": ["ate something unusual but is acting normal"],
        "owner_guidance": "Lilies are severely, often fatally, toxic to cats - even a small amount of pollen groomed off fur or a sip of vase water can cause kidney failure, so any lily exposure is a same-day emergency even before symptoms appear. The same urgency applies to chocolate, human medications, rat poison, onion/garlic, and dog-specific flea/tick products containing permethrin (a common and severe cat poisoning). Do not induce vomiting unless a vet or poison control specifically instructs it. Keep the packaging or plant to show the vet.",
    },
}

# Aliases so the Intake Agent's free-text extraction (or a user typing
# casually) still resolves to a canonical KB key. Kept separate from the
# KB itself so the KB stays a clean, reviewable medical table.
SYMPTOM_ALIASES: dict[str, str] = {
    "throwing up": "vomiting",
    "puking": "vomiting",
    "throwing up food": "vomiting",
    "hairball": "vomiting",
    "coughing up a hairball": "vomiting",
    "loose stool": "diarrhea",
    "loose stools": "diarrhea",
    "runny stool": "diarrhea",
    "diarrhoea": "diarrhea",
    "low energy": "lethargy",
    "tired": "lethargy",
    "sluggish": "lethargy",
    "no energy": "lethargy",
    "hiding more than usual": "lethargy",
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
    "open mouth breathing": "difficulty_breathing",
    "panting": "difficulty_breathing",
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
    "overgrooming": "skin_irritation",
    "licking a bald spot": "skin_irritation",
    "cough": "coughing",
    "hacking": "coughing",
    "can't pee": "urinary_obstruction",
    "straining to pee": "urinary_obstruction",
    "blood in urine": "urinary_obstruction",
    "peeing more": "urinary_obstruction",
    "peeing outside the litter box": "urinary_obstruction",
    "not using the litter box": "urinary_obstruction",
    "straining to poop": "constipation",
    "can't poop": "constipation",
    "hasn't pooped": "constipation",
    "crying in pain": "pain_vocalizing",
    "yowling": "pain_vocalizing",
    "yelping": "pain_vocalizing",
    "hit by a car": "trauma_injury",
    "hit by car": "trauma_injury",
    "fell down": "trauma_injury",
    "fell from a window": "trauma_injury",
    "cat fight": "trauma_injury",
    "attacked by another animal": "trauma_injury",
    "ate chocolate": "poisoning_ingestion",
    "ate poison": "poisoning_ingestion",
    "swallowed something": "poisoning_ingestion",
    "ate something toxic": "poisoning_ingestion",
    "ate a lily": "poisoning_ingestion",
    "lily exposure": "poisoning_ingestion",
}


def get_kb_entry(symptom_key: str | None) -> dict | None:
    """Deterministic lookup used by the Triage Engine and exposed as the
    get_kb_entry() tool from README section 7. The knowledge base is
    cat-only end to end, so there's no species filter to apply here."""
    if not symptom_key:
        return None
    return TRIAGE_KB.get(symptom_key)
