"""
generate_targeted_augmentation.py
-----------------------------------
Generates targeted synthetic training examples to fix the ML model's
systematic classification failures identified during adversarial testing:

1. Disaster/casualty reporting (label 2) → model predicts HD
2. Rothschild/banking conspiracy (label 0) → model predicts Legitimate
3. 'Crisis actors' plural (label 0) → model predicts Legitimate
4. Government under-reporting stats (label 1) → model predicts HD
5. UFO/government secrecy framed as fact (label 1) → over-suppressed

Outputs CSV rows to append to src/train_data.csv.

Usage:
  python src/generate_targeted_augmentation.py
  python src/generate_targeted_augmentation.py --out src/augmentation_data.csv --per-bucket 150
"""

import argparse
import itertools
import random
import pandas as pd

random.seed(123)

# ── LABEL 2 (Legitimate): disaster / casualty reporting ────────────────────────

DISASTER_TYPES = [
    "earthquake", "flood", "cyclone", "hurricane", "tsunami", "wildfire",
    "landslide", "tornado", "volcanic eruption", "blizzard", "typhoon",
    "monsoon flooding", "dam collapse", "building collapse", "avalanche",
]

DISASTER_LOCATIONS = [
    "Haiti", "Indonesia", "Turkey", "Japan", "Nepal", "Bangladesh",
    "India", "Pakistan", "Mexico", "Philippines", "Chile", "Greece",
    "Iran", "Morocco", "Libya", "Afghanistan", "Ecuador", "Peru",
    "California", "Australia", "New Zealand", "Colombia", "Brazil",
    "Italy", "China", "Myanmar", "Vietnam", "Thailand", "South Africa",
]

CASUALTY_TEMPLATES = [
    "At least {n} people were killed in the {disaster} that struck {loc}.",
    "More than {n} people died after a {disaster} hit {loc} on {day}.",
    "The {disaster} in {loc} left {n} dead and hundreds displaced.",
    "Rescue teams recovered {n} bodies following the {disaster} in {loc}.",
    "Authorities confirmed {n} deaths after the {disaster} devastated {loc}.",
    "{n} people were killed and {injured} injured after a {disaster} struck {loc}.",
    "The death toll from the {disaster} in {loc} has risen to {n}, officials say.",
    "Nearly {n} people lost their lives when a {disaster} swept through {loc}.",
    "Emergency services reported {n} fatalities following the {disaster} in {loc}.",
    "The {disaster} killed at least {n} people and injured many more in {loc}.",
    "A {disaster} tore through {loc}, killing at least {n} and displacing thousands.",
    "Officials raised the death toll to {n} after the {disaster} battered {loc}.",
    "{n} confirmed dead and {injured} missing as {disaster} response continues in {loc}.",
    "Search and rescue teams found {n} bodies after the {disaster} struck {loc}.",
    "The United Nations said {n} people died in the {disaster} that hit {loc} this week.",
    "Red Cross teams deployed to {loc} where the {disaster} killed at least {n}.",
    "Government data shows {n} killed in the {disaster} that struck {loc} last {day}.",
    "The {disaster} that hit {loc} over the weekend has killed at least {n} people.",
]

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
        "last week", "this week", "over the weekend"]


def _disaster_examples(n: int) -> list:
    rows = []
    pool = list(itertools.product(DISASTER_TYPES, DISASTER_LOCATIONS, CASUALTY_TEMPLATES))
    random.shuffle(pool)
    for disaster, loc, tmpl in pool[:n]:
        num = random.randint(3, 3500)
        injured = random.randint(num, num * 4)
        text = tmpl.format(
            n=num, disaster=disaster, loc=loc, injured=injured,
            day=random.choice(DAYS),
        )
        rows.append({"text": text, "label": 2})
    return rows


# ── LABEL 0 (HD): banking / Rothschild / elite financing wars ──────────────────

BANKING_SUBJECTS = [
    "The Rothschild family", "The Rothschilds", "Rothschild-backed bankers",
    "The Rockefellers", "International bankers", "Jewish banking elites",
    "The Rockefeller dynasty", "Global banking cartels", "The Warburg family",
    "The Morgan banking dynasty", "Zionist bankers",
]

BANKING_VERBS = [
    "secretly financed both sides of", "funded both the Allies and Axis in",
    "bankrolled all factions in", "profited from both sides of",
    "orchestrated and financed", "engineered and funded",
    "covertly funded both sides during", "deliberately started",
]

BANKING_TARGETS = [
    "World War I to extract war debt profits",
    "World War II for financial gain",
    "the Napoleonic Wars to establish central bank control",
    "the Civil War to divide and conquer America",
    "both world wars to establish the Federal Reserve",
    "the First World War using loans to all governments",
    "WWII to justify the creation of Israel and the UN",
    "every major 20th-century conflict through hidden loans",
]

BANKING_CLOSERS = [
    "Historical records prove this has been suppressed by mainstream historians.",
    "Documents uncovered by researchers confirm this was planned decades in advance.",
    "This is what the banking elite does not want you to know.",
    "The evidence has been hidden in archives that few are allowed to access.",
    "Follow the money — the same families profit from every war.",
    "This is the real history they do not teach in schools.",
    "Central bank records leaked by insiders confirm the scheme.",
    "Whistleblowers inside the Fed have confirmed this arrangement.",
]

CONTROL_TEMPLATES = [
    "The {family} secretly control all {target} through a network of shell companies.",
    "{family} agents have been running {target} since the 19th century.",
    "Every {target} in the world is ultimately controlled by the {family}.",
    "The {family} engineered {event} to tighten their grip on {target}.",
    "{family} operatives placed in key positions now run {target} globally.",
    "Leaked documents show {family} owns controlling stakes in every {target}.",
    "The {family} designed the entire {target} system to extract wealth from nations.",
    "Through front organisations, the {family} have dominated {target} for 200 years.",
]

CTRL_FAMILIES = [
    "Rothschild", "Rockefeller", "Rothschild-Rockefeller", "international banking",
    "globalist banking", "Warburg", "Morgan banking",
]

CTRL_TARGETS = [
    "central banks", "global financial institutions", "Western governments",
    "mainstream media outlets", "pharmaceutical companies", "intelligence agencies",
    "tech corporations", "central bank networks",
]

CTRL_EVENTS = [
    "the 2008 financial crisis", "the COVID-19 pandemic", "the 2001 recession",
    "the Great Depression", "the dot-com crash", "the housing collapse",
]


def _banking_conspiracy_examples(n: int) -> list:
    rows = []
    # War financing conspiracy
    pool1 = list(itertools.product(BANKING_SUBJECTS, BANKING_VERBS, BANKING_TARGETS, BANKING_CLOSERS))
    random.shuffle(pool1)
    for subj, verb, target, closer in pool1[:n // 2]:
        text = f"{subj} {verb} {target}. {closer}"
        rows.append({"text": text, "label": 0})
    # Control conspiracy
    pool2 = list(itertools.product(CTRL_FAMILIES, CTRL_TARGETS, CTRL_EVENTS, CONTROL_TEMPLATES))
    random.shuffle(pool2)
    for fam, tgt, evt, tmpl in pool2[:n - len(rows)]:
        text = tmpl.format(family=fam, target=tgt, event=evt)
        rows.append({"text": text, "label": 0})
    return rows


# ── LABEL 0 (HD): crisis actors at real events ─────────────────────────────────

CRISIS_EVENTS = [
    "the Boston Marathon bombing", "the Sandy Hook shooting", "the Las Vegas shooting",
    "the Parkland school shooting", "the Aurora cinema shooting",
    "the 9/11 attacks", "the Oklahoma City bombing", "the Orlando Pulse nightclub shooting",
    "the 2017 Manchester bombing", "the Brussels bombings", "the Nice truck attack",
    "the Christchurch mosque shootings", "the Columbine shooting",
]

CRISIS_TEMPLATES = [
    "Crisis actors were used at {event} to push a gun control agenda.",
    "Eyewitness accounts confirm crisis actors were deployed at {event}.",
    "Video evidence proves that crisis actors participated in staging {event}.",
    "The survivors of {event} are paid crisis actors — their stories do not add up.",
    "Crisis actors hired by government contractors staged {event} for media coverage.",
    "Leaked casting calls show crisis actors were recruited weeks before {event}.",
    "Multiple crisis actors spotted at {event} were previously photographed at other 'attacks'.",
    "Documents prove crisis actors were briefed on their roles at {event} in advance.",
    "The grief displayed by families at {event} is fake — these are trained crisis actors.",
    "{event} was a staged false flag using professional crisis actors and controlled demolition.",
    "Social media posts made before {event} happened prove it was a drill using crisis actors.",
    "A former FEMA employee exposed how crisis actors were used to stage {event}.",
    "The same crisis actors appeared at both {event} and another staged shooting.",
    "Voice analysis of crisis actors at {event} reveals their testimony was scripted.",
    "Crisis actors at {event} were paid by a Soros-funded NGO to fabricate witnesses.",
]


def _crisis_actor_examples(n: int) -> list:
    rows = []
    pool = list(itertools.product(CRISIS_EVENTS, CRISIS_TEMPLATES))
    random.shuffle(pool)
    for event, tmpl in pool[:n]:
        text = tmpl.format(event=event)
        rows.append({"text": text, "label": 0})
    return rows


# ── LABEL 1 (Misleading): government under-reporting statistics ─────────────────

UNDERREPORT_SUBJECTS = [
    "The government", "Officials", "Health authorities", "Government statisticians",
    "The administration", "Federal agencies", "State officials", "Public health bodies",
    "The treasury department", "The ministry", "Authorities",
]

UNDERREPORT_METRICS = [
    "inflation figures", "unemployment numbers", "COVID death tolls",
    "crime statistics", "poverty rates", "homelessness figures",
    "cancer rates linked to pesticides", "adverse vaccine events",
    "civilian casualty figures", "air pollution deaths",
    "economic contraction data", "job loss statistics",
]

UNDERREPORT_VERBS = [
    "is massively under-reporting", "has been dramatically under-counting",
    "is deliberately under-reporting", "has been systematically misrepresenting",
    "is consistently hiding the real", "has been drastically under-stating",
    "are dramatically suppressing", "has deliberately miscounted",
]

UNDERREPORT_MOTIVES = [
    "to fool the public before the election.",
    "to avoid panic and maintain control.",
    "to protect the pharmaceutical industry.",
    "to prevent market collapse.",
    "to mislead voters about the state of the economy.",
    "in order to justify continued lockdown policies.",
    "to avoid accountability for policy failures.",
    "to maintain the illusion of stability.",
    "so that corporate donors are not embarrassed.",
    "to cover up the true scale of the policy failure.",
]


def _underreporting_examples(n: int) -> list:
    rows = []
    pool = list(itertools.product(
        UNDERREPORT_SUBJECTS, UNDERREPORT_METRICS,
        UNDERREPORT_VERBS, UNDERREPORT_MOTIVES,
    ))
    random.shuffle(pool)
    for subj, metric, verb, motive in pool[:n]:
        text = f"{subj} {verb} {metric} {motive}"
        rows.append({"text": text, "label": 1})
    return rows


# ── LABEL 1 (Misleading): unnamed-source government / institutional claims ──────

UNNAMED_SRC_TEMPLATES = [
    "Anonymous sources inside {org} claim that {claim}.",
    "Unnamed officials at {org} say that {claim}, though no evidence has been provided.",
    "A whistleblower at {org} alleges that {claim} — the organisation has not responded.",
    "According to anonymous insiders at {org}, {claim}.",
    "Secret documents leaked from {org} suggest that {claim}.",
    "Insider sources at {org} have revealed that {claim}.",
    "Off-the-record briefings from {org} staff indicate that {claim}.",
]

UNNAMED_ORGS = [
    "the CDC", "the FDA", "the WHO", "the Pentagon", "the White House",
    "the IMF", "NATO", "the EU Commission", "the World Bank",
    "the CIA", "the NSA", "the FBI", "FEMA", "the Treasury",
]

UNNAMED_CLAIMS = [
    "a second pandemic is already being prepared",
    "the real inflation rate is triple the official figure",
    "millions of vaccine deaths have been deliberately hidden",
    "the economy is far worse than publicly reported",
    "a new digital currency will replace cash within two years",
    "the unemployment numbers are manipulated before release",
    "the agency is preparing emergency lockdown protocols",
    "foreign governments have compromised the financial system",
    "a massive cyberattack is being hidden from the public",
    "new restrictions are being planned but not yet announced",
]


def _unnamed_source_examples(n: int) -> list:
    rows = []
    pool = list(itertools.product(UNNAMED_ORGS, UNNAMED_CLAIMS, UNNAMED_SRC_TEMPLATES))
    random.shuffle(pool)
    for org, claim, tmpl in pool[:n]:
        text = tmpl.format(org=org, claim=claim)
        rows.append({"text": text, "label": 1})
    return rows


# ── MAIN ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--per-bucket", type=int, default=200,
                        help="Synthetic examples per failure category")
    parser.add_argument("--out", default="src/augmentation_data.csv")
    args = parser.parse_args()

    n = args.per_bucket
    rows = []
    rows += _disaster_examples(n)
    rows += _banking_conspiracy_examples(n)
    rows += _crisis_actor_examples(n)
    rows += _underreporting_examples(n)
    rows += _unnamed_source_examples(n)

    df = pd.DataFrame(rows)
    df = df.drop_duplicates(subset="text").sample(frac=1, random_state=99).reset_index(drop=True)

    print(f"Generated {len(df)} targeted augmentation examples")
    print(df["label"].value_counts().sort_index().to_string())

    df.to_csv(args.out, index=False)
    print(f"\nSaved -> {args.out}")


if __name__ == "__main__":
    main()
