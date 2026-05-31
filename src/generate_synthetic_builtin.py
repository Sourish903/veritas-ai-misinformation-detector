"""
generate_synthetic_builtin.py
------------------------------
Generates synthetic training data with NO external API required.
Uses structured templates to create semantically distinct examples
for each of the 3 misinformation classes.

This fixes the core problem: local Fake.csv HD/PF labels are assigned by
article *subject category*, not deception style. These templates create
examples where the text itself is definitively HD / PF / MM.

Usage:
  python src/generate_synthetic_builtin.py
  python src/generate_synthetic_builtin.py --per-class 400 --out src/synthetic_data.csv
"""

import argparse
import itertools
import os
import random
import pandas as pd

random.seed(42)

# ── Template components ────────────────────────────────────────────────────────

# HD — conspiracy / fabrication language. Each sentence is constructed by
# combining subject + verb + object + intensifier from pools below.

HD_SUBJECTS = [
    "The government", "Deep state operatives", "Big Pharma", "Global elites",
    "Secret cabals", "CIA officials", "Intelligence agencies", "The Illuminati",
    "World health authorities", "Tech billionaires", "The New World Order",
    "Shadow government officials", "Rothschild-backed organizations",
    "Globalist forces", "Underground networks",
]

HD_VERBS = [
    "has been covering up", "is actively suppressing", "has concealed",
    "is hiding", "has been fabricating", "orchestrated", "staged",
    "has been censoring", "deliberately destroyed evidence of",
    "has manipulated data to conceal", "is running a cover-up on",
    "funded the suppression of", "engineered the disappearance of",
]

HD_OBJECTS = [
    "a cure for cancer that has existed for decades",
    "evidence that 5G towers cause neurological damage",
    "documents proving COVID-19 was a planned bioweapon",
    "proof that vaccines contain tracking microchips",
    "data showing chemtrails are used for population control",
    "footage of crisis actors at staged mass shootings",
    "the real cause of climate change — solar weapon testing",
    "a leaked Pentagon file on alien contact",
    "evidence that the moon landing was filmed in a studio",
    "records showing fluoride is used for mind control",
    "a whistleblower's report on adrenochrome harvesting",
    "classified files on weather manipulation via HAARP",
    "proof that the earth is flat and NASA has been lying",
    "documents linking George Soros to election rigging",
    "evidence that the 2020 election was stolen via Dominion machines",
]

HD_CLOSERS = [
    "Leaked documents confirm this has been known for years.",
    "A whistleblower who worked inside the organization has come forward.",
    "They don't want you to know this — share before it gets deleted.",
    "This is what the mainstream media refuses to report.",
    "The evidence has been suppressed by powerful interests.",
    "Anonymous insiders say the cover-up goes all the way to the top.",
    "Secret files released by a brave insider confirm every detail.",
    "The truth is finally coming out — spread this before it's banned.",
    "Multiple credible witnesses have confirmed this but been silenced.",
    "This information was removed from the internet within hours.",
    "Deep state operatives have threatened those who speak out.",
    "Fact-checkers funded by Big Pharma are calling this 'false' — that alone proves it's true.",
    "WWG1WGA — the storm is coming and the truth will be revealed.",
    "Share this immediately. They are watching and will scrub this post.",
]

HD_OPENERS = [
    "BREAKING: Whistleblower reveals",
    "LEAKED: Secret document proves",
    "URGENT: What they're hiding from you —",
    "They don't want you to see this:",
    "BOMBSHELL: Insider exposes",
    "BANNED TRUTH:",
    "SUPPRESSED STUDY:",
    "COVER-UP EXPOSED:",
    "What the mainstream media won't tell you:",
    "DEEP STATE EXPOSED:",
    "FALSE FLAG CONFIRMED:",
    "CRISIS ACTOR PROOF:",
]

# ML (Misleading) — misleading statistics, vague citations, sensationalist but plausible

PF_TEMPLATES = [
    "A new study shows that {treatment} is {pct}% more effective than {comparison}, though experts remain divided on the methodology.",
    "According to unnamed sources within {org}, {claim}. Officials have not confirmed the report.",
    "Scientists at an unnamed university have found that {substance} {effect}, contradicting years of accepted research.",
    "{pct}% of {group} now believe {opinion}, according to a survey conducted by an anonymous research group.",
    "Shocking new data reveals that {statistic}, a figure that has not been independently verified.",
    "An explosive report claims {claim}, though the original document has not been made public.",
    "Experts warn that {warning}, citing a study published in an unspecified peer-reviewed journal.",
    "Insider sources say {org} is preparing to announce {claim}, which would affect millions.",
    "A bombshell revelation from anonymous government officials confirms {claim}, raising urgent questions.",
    "New research suggests {substance} could {effect} — but the study has not yet been peer-reviewed.",
    "According to a leaked internal memo, {org} has known about {risk} for years but chose not to act.",
    "A stunning new poll shows {pct}% of {group} support {policy}, a dramatic shift from previous data.",
]

PF_FILL = {
    "treatment":   ["vitamin D supplements", "ivermectin", "herbal extracts", "alkaline water",
                    "intermittent fasting", "cold therapy", "high-dose vitamin C", "turmeric extract",
                    "colloidal silver", "homeopathic remedies", "essential oils", "probiotics",
                    "hydrogen peroxide therapy", "ozone therapy", "melatonin supplements"],
    "pct":         ["34", "47", "61", "73", "82", "91", "58", "39", "67", "44",
                    "76", "88", "53", "29", "95", "41", "68", "37", "84", "52"],
    "comparison":  ["standard medication", "conventional treatment", "flu vaccines",
                    "chemotherapy", "antidepressants", "insulin therapy", "antibiotics",
                    "radiation therapy", "statins", "blood pressure medication", "opioids"],
    "org":         ["the FDA", "the CDC", "the WHO", "major pharmaceutical companies",
                    "Wall Street banks", "Silicon Valley firms", "the Pentagon", "the EU",
                    "the UN", "the IMF", "the World Economic Forum", "the NIH",
                    "FEMA", "the World Bank", "the Bilderberg Group", "Davos elites"],
    "claim":       ["inflation will hit record highs by year-end",
                    "a new pandemic strain has already been identified",
                    "layoffs will exceed 2 million next quarter",
                    "the housing market will crash within months",
                    "a major bank is on the verge of collapse",
                    "social media companies plan mass censorship rollouts",
                    "a second lockdown is being planned for next year",
                    "cryptocurrency will replace the dollar within a decade",
                    "AI will eliminate 80% of white-collar jobs by 2030",
                    "a digital vaccine passport will become mandatory",
                    "the stock market is about to experience its worst crash since 1929",
                    "food shortages are being deliberately engineered",
                    "a new surveillance law will track all financial transactions"],
    "substance":   ["caffeine", "artificial sweeteners", "5G radiation", "microplastics",
                    "seed oils", "tap water fluoride", "processed sugar", "glyphosate",
                    "BPA", "MSG", "aspartame", "high-fructose corn syrup",
                    "titanium dioxide", "carrageenan", "sodium nitrate"],
    "effect":      ["increases cancer risk by up to 40%", "disrupts hormone production",
                    "accelerates cognitive decline", "reduces fertility by 30%",
                    "causes permanent DNA changes", "triggers autoimmune responses",
                    "is linked to a 55% rise in childhood obesity", "damages gut microbiome",
                    "causes neurological inflammation", "accelerates cellular aging",
                    "suppresses immune function by up to 45%", "raises cortisol levels dangerously"],
    "group":       ["Americans", "millennials", "small business owners", "parents",
                    "voters", "college graduates", "healthcare workers", "Gen Z adults",
                    "rural communities", "working-class families", "retirees", "veterans",
                    "immigrants", "Black Americans", "women over 40"],
    "opinion":     ["the economy is rigged", "mainstream media cannot be trusted",
                    "the government hides medical cures", "elections are manipulated",
                    "vaccines are unsafe", "banks control politicians",
                    "climate change is exaggerated", "big tech is censoring conservatives",
                    "the justice system is biased", "schools are indoctrinating children"],
    "statistic":   ["childhood cancer rates have tripled in the past decade",
                    "suicide rates among teens have doubled since social media launched",
                    "1 in 3 Americans will develop a chronic illness from processed food",
                    "corporate profits hit an all-time high while wages stagnated",
                    "antibiotic resistance will kill more people than cancer by 2050",
                    "the average American will lose 15 years of pension savings this decade",
                    "70% of processed foods contain unlisted chemical additives",
                    "hospital error rates have increased 200% since the pandemic"],
    "warning":     ["everyday household chemicals are causing hormone disruption",
                    "screen time is permanently altering children's brains",
                    "processed food additives are linked to rising obesity rates",
                    "antibiotic overuse may trigger a superbug pandemic",
                    "wi-fi signals may interfere with sleep cycles and brain development",
                    "air fresheners contain chemicals linked to lung disease",
                    "tap water in most cities exceeds safe levels of PFAS contaminants",
                    "common painkillers may increase heart attack risk by 50%"],
    "risk":        ["the long-term side effects of mRNA vaccines",
                    "the link between pesticides and neurological disorders",
                    "dangerous chemical levels in municipal water supplies",
                    "the addictive design of social media algorithms",
                    "the carcinogenic properties of common food preservatives",
                    "the link between ultra-processed food and early dementia",
                    "radiation exposure from airport body scanners",
                    "the psychological effects of algorithmic news feeds"],
    "policy":      ["universal basic income", "mandatory vaccination", "digital ID",
                    "central bank digital currency", "social credit scoring",
                    "15-minute cities", "lab-grown meat mandates", "carbon taxes",
                    "universal surveillance cameras", "compulsory digital health records"],
}

# LG (Legitimate) — genuine, credible, well-sourced factual news

MM_TEMPLATES = [
    "The {market} fell {pct}% on {day} amid concerns about {issue}, analysts said.",
    "{org} announced new guidelines on {topic}, citing {reason} as a key concern.",
    "A report released by {body} warns that {issue} could affect millions over the next decade.",
    "Economists are divided on whether {event} signals the start of a broader {trend}.",
    "{city} officials are reviewing policies on {topic} following a rise in {metric}.",
    "Tech companies face increased scrutiny over {topic}, with regulators calling for {action}.",
    "Health authorities in {region} have issued an advisory on {topic}, urging residents to {advice}.",
    "New data from {body} shows {trend} in {sector}, raising questions about long-term sustainability.",
    "{company} reported lower-than-expected earnings, sending shares down {pct}% in after-hours trading.",
    "Rising {commodity} prices are putting pressure on consumers as {event} continues to weigh on markets.",
    "A new study published in {journal} suggests a possible link between {substance} and {condition}.",
    "Lawmakers are debating new legislation on {topic}, with advocates and critics staking out opposing views.",
    "{country} announced a {policy} that has drawn mixed reactions from international observers.",
    "Climate scientists released a report this week warning that {climate_risk} without significant policy changes.",
    "The unemployment rate edged {direction} to {pct}% in {month}, according to official figures.",
]

MM_FILL = {
    "market":    ["stock market", "Nasdaq", "S&P 500", "crypto market", "bond market", "housing market"],
    "pct":       ["1.2", "2.4", "0.8", "3.1", "1.7", "4.2", "0.5", "2.9"],
    "day":       ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
    "issue":     ["rising inflation", "geopolitical tensions", "interest rate hikes",
                  "slowing economic growth", "supply chain disruptions", "trade policy uncertainty"],
    "org":       ["The FDA", "The WHO", "The CDC", "The Federal Reserve", "The IMF",
                  "The European Central Bank", "UNICEF", "The World Bank"],
    "topic":     ["air quality standards", "data privacy", "food labeling",
                  "mental health services", "cybersecurity", "remote work policies",
                  "housing affordability", "carbon emissions", "AI regulation"],
    "reason":    ["public health concerns", "rising costs", "new scientific evidence",
                  "increased consumer demand", "regulatory pressure"],
    "body":      ["the United Nations", "the OECD", "the American Medical Association",
                  "the Congressional Budget Office", "the Pew Research Center"],
    "event":     ["the recent bank failures", "the latest jobs report", "this quarter's GDP data",
                  "the recent tech layoffs", "the surge in energy prices"],
    "trend":     ["recession", "economic slowdown", "inflation surge", "market correction",
                  "productivity decline", "labor shortage"],
    "city":      ["New York", "London", "Los Angeles", "Chicago", "San Francisco", "Toronto", "Sydney"],
    "metric":    ["housing costs", "traffic incidents", "public school enrollment",
                  "small business closures", "homelessness rates"],
    "action":    ["greater transparency", "stricter oversight", "new disclosure rules",
                  "independent audits", "consumer protections"],
    "region":    ["the Northeast", "Southeast Asia", "Western Europe", "Sub-Saharan Africa",
                  "South America", "the Asia-Pacific region"],
    "advice":    ["stay indoors during peak hours", "consult a doctor if symptoms arise",
                  "take standard precautions", "limit outdoor activity"],
    "sector":    ["manufacturing", "retail", "technology", "healthcare", "energy", "finance"],
    "company":   ["Apple", "Amazon", "Tesla", "Meta", "Microsoft", "Google", "Goldman Sachs"],
    "commodity": ["oil", "natural gas", "wheat", "copper", "lithium"],
    "journal":   ["The Lancet", "JAMA", "Nature", "The New England Journal of Medicine",
                  "BMJ", "Science"],
    "substance": ["ultra-processed foods", "artificial sweeteners", "red meat",
                  "alcohol", "air pollution", "sedentary behavior"],
    "condition": ["cardiovascular disease", "cognitive decline", "metabolic syndrome",
                  "type 2 diabetes", "certain cancers"],
    "country":   ["China", "the United States", "the UK", "Germany", "India", "France", "Japan"],
    "policy":    ["new trade agreement", "sweeping tax reform", "immigration overhaul",
                  "defence spending increase", "renewable energy mandate"],
    "climate_risk": [
        "Arctic ice could vanish by 2050",
        "sea levels may rise by up to a metre by 2100",
        "extreme weather events will become significantly more frequent",
        "global temperatures could exceed the 1.5°C threshold within two decades",
    ],
    "direction": ["up", "down"],
    "month":     ["January", "February", "March", "April", "May", "June",
                  "July", "August", "September", "October"],
}


# ── Short-text examples (2022-2025 topics, 5-15 words) ────────────────────────
# These cover headlines, social media posts, and brief claims that the model
# would never see from the long-article Fake.csv / True.csv training data.

SHORT_HD = [
    # Ukraine / Russia
    "Ukraine war is a false flag staged by NATO and Zelensky.",
    "Russia's bioweapons were funded by the US Pentagon in Ukraine labs.",
    "NATO secretly started the Ukraine war to destabilize Europe.",
    "Zelensky is a WEF puppet installed to trigger World War 3.",
    "Ukrainian soldiers are paid crisis actors, says leaked Pentagon file.",
    "Russia exposed secret US bioweapon labs hidden inside Ukraine.",
    "The Ukraine conflict was engineered by Soros to collapse Europe.",
    # COVID / vaccines (post-2022)
    "mRNA vaccines alter your DNA and cause slow depopulation.",
    "Omicron was engineered to force another lockdown and vaccine mandate.",
    "COVID boosters are laced with graphene oxide for 5G tracking.",
    "CDC is hiding mass vaccine deaths from official statistics.",
    "Pfizer trial data shows vaccines cause AIDS — suppressed by WHO.",
    "COVID was a hoax engineered to introduce digital vaccine passports.",
    "Vaccine-induced turbo cancer is being hidden by Big Pharma.",
    "Ivermectin cures COVID — WHO suppressed the evidence for profit.",
    # Elections / politics (2022-2024)
    "2022 midterm elections were stolen using Dominion voting machines.",
    "Trump was framed — all 91 indictments are deep state persecution.",
    "Biden regime is using DOJ to jail political opponents.",
    "2024 election was rigged before a single vote was cast.",
    "Soros funded the prosecutors going after Trump to stop MAGA.",
    # Tech / AI
    "ChatGPT is secretly feeding all conversations to the NSA.",
    "Microsoft is using AI to censor conservative voices worldwide.",
    "Elon Musk is controlled by globalists despite his Twitter takeover.",
    "5G towers are activating nanobots injected via COVID vaccines.",
    "Google DeepMind has created sentient AI and is hiding it.",
    # Economy / crypto
    "FTX collapse was orchestrated by the CIA to crush crypto.",
    "Sam Bankman-Fried was a Democrat money-laundering operation for Ukraine.",
    "Global elites engineered the 2022 inflation to bankrupt the middle class.",
    "Silicon Valley Bank was deliberately collapsed to introduce CBDC control.",
    "The WEF's Great Reset will confiscate all private property by 2030.",
    # Health / misc
    "Bill Gates is using mosquitoes to deliver mRNA vaccines secretly.",
    "WHO's new pandemic treaty will end national sovereignty permanently.",
    "Bird flu H5N1 is being weaponised for the next planned pandemic.",
    "Fluoride in water is a mind-control chemical used since the 1950s.",
    "Chemtrails sprayed over cities contain lithium for population sedation.",
]

SHORT_ML = [
    # Ukraine / geopolitics
    "Ukraine is losing the war badly despite Western media blackout.",
    "NATO weapons are fuelling the conflict, critics say, without evidence.",
    "Russia's economy has not collapsed despite Western sanctions, report claims.",
    "Zelensky demands $100 billion more — with no accountability, insiders say.",
    # COVID / health (post-2022)
    "New COVID variant XBB is 80% more transmissible, unnamed study says.",
    "COVID boosters may increase reinfection risk, according to anonymous researchers.",
    "Long COVID affects 47% of vaccinated adults, unverified data shows.",
    "Remdesivir causes more harm than COVID itself, controversial study claims.",
    "Natural immunity 10x stronger than vaccine immunity, experts say.",
    # Economics (2022-2025)
    "Inflation driven solely by Biden spending, economists argue without citing data.",
    "US recession is already here — government hiding the real GDP numbers.",
    "93% of economists predict a crash worse than 2008 within months.",
    "Housing market set to drop 40% as rate hike pain accelerates.",
    "Corporate greed caused 80% of post-pandemic inflation, study shows.",
    # AI / tech
    "ChatGPT has a secret liberal bias baked in by OpenAI engineers.",
    "AI will eliminate 60% of all jobs within 5 years, report warns.",
    "OpenAI hid safety failures from the board before Sam Altman's ousting.",
    "Meta's AI collected private messages without user consent, insiders claim.",
    "Elon Musk's xAI is secretly more powerful than GPT-4, sources say.",
    # Elections / politics
    "Biden's mental decline is being hidden by White House staff, aides say.",
    "Trump's poll leads are being suppressed by mainstream media, analysis claims.",
    "RFK Jr's campaign was sabotaged by DNC insiders, according to unnamed sources.",
    "Voter ID laws prevented 2 million legitimate votes in 2022 midterms.",
    # Crypto / finance
    "Bitcoin will hit $500,000 by end of 2025, anonymous analysts predict.",
    "FTX funds were channelled to Democrats, though the link is unproven.",
    "CBDC rollout will give governments power to freeze any account instantly.",
    # Health / misc
    "Ultra-processed food causes cancer at twice the rate of smoking, study finds.",
    "Antidepressants are no better than placebo, massive new analysis suggests.",
    "Microplastics found in 99% of human blood — long-term effects unknown.",
    "5G radiation is linked to insomnia and anxiety, unnamed research claims.",
]

SHORT_LG = [
    # Ukraine / geopolitics
    "Ukraine conflict enters third year with no ceasefire agreement in sight, the United Nations reported.",
    "NATO pledged continued military support for Ukraine at the Brussels summit, according to the alliance's secretary-general.",
    "Russia launched fresh missile strikes on Ukrainian cities overnight, Ukrainian officials confirmed.",
    "Peace talks between Russia and Ukraine remain stalled, the UN special envoy said in a statement.",
    "G7 leaders agreed to extend economic sanctions on Russia through 2025 at their annual summit.",
    # COVID / health (post-2022)
    "The FDA approved an updated COVID booster targeting the XBB Omicron variant ahead of the winter season.",
    "The WHO declared an end to COVID-19 as a public health emergency of international concern in May 2023.",
    "The CDC confirmed detection of the JN.1 COVID subvariant in multiple US states and urged standard precautions.",
    "The NIH announced $1.15 billion in new funding for long COVID research across 200 research sites.",
    "The USDA and CDC confirmed H5N1 bird flu in US dairy cattle herds in nine states, with no human cases linked.",
    # Economy (2022-2025)
    "The Federal Reserve raised its benchmark interest rate by 25 basis points to a 22-year high.",
    "The US Bureau of Labor Statistics reported inflation fell to 3.1% in November 2023, the lowest since June 2021.",
    "The UK Office for National Statistics confirmed a technical recession after GDP contracted for two consecutive quarters.",
    "The IMF raised its global growth forecast for 2024 to 3.1%, citing resilience in the US and emerging economies.",
    "Silicon Valley Bank was closed by California regulators and placed into FDIC receivership on March 10, 2023.",
    # AI / tech
    "OpenAI released GPT-4, a multimodal large language model, to paying subscribers in March 2023.",
    "The European Parliament passed the AI Act, the world's first comprehensive AI regulatory framework, in March 2024.",
    "OpenAI's board removed Sam Altman as CEO before reinstating him five days later following staff backlash.",
    "Google DeepMind launched Gemini, a multimodal AI model, in December 2023 to compete directly with GPT-4.",
    "Elon Musk completed his $44 billion acquisition of Twitter in October 2022 and subsequently rebranded it as X.",
    # Elections / politics
    "Republicans won a narrow majority in the US House of Representatives in the November 2022 midterm elections.",
    "President Biden signed the Inflation Reduction Act into law in August 2022, allocating $369 billion to climate programmes.",
    "Former President Donald Trump was indicted by a Manhattan grand jury in March 2023, making him the first ex-president to face criminal charges.",
    "The US Supreme Court voted 6-3 to overturn Roe v. Wade in June 2022, returning abortion regulation to individual states.",
    "Israel's government declared a state of war on October 8, 2023, following Hamas attacks that killed approximately 1,200 people.",
    # Crypto / finance
    "FTX founder Sam Bankman-Fried was arrested in the Bahamas in December 2022 and subsequently extradited to the United States.",
    "Bitcoin rose above $60,000 in February 2024 following the SEC's approval of spot Bitcoin exchange-traded funds.",
    "The SEC approved 11 spot Bitcoin ETF applications in January 2024, marking a landmark shift in crypto regulation.",
    # Science / environment
    "The Copernicus Climate Change Service confirmed 2023 was the hottest year on record, at 1.48°C above the pre-industrial average.",
    "The James Webb Space Telescope captured images of galaxies formed just 300 million years after the Big Bang, NASA announced.",
    "COP28 concluded with a landmark agreement calling for a transition away from fossil fuels, signed by nearly 200 nations.",
    # Additional clearly factual / attributed statements
    "The World Health Organization reported that approximately 1.1 million people died from HIV/AIDS-related illnesses in 2022.",
    "According to the Congressional Budget Office, the US federal deficit totalled $1.7 trillion in fiscal year 2023.",
    "The European Central Bank raised interest rates to 4% in September 2023, its highest level since the euro was introduced.",
    "NASA's Artemis I mission completed an uncrewed lunar flyby in November 2022 as a test for future crewed missions.",
    "The International Energy Agency reported global renewable energy capacity grew by 50% in 2023, led by solar expansion.",
    "A peer-reviewed study in The Lancet found COVID-19 mRNA vaccines reduced severe disease risk by over 90% in clinical trials.",
    "The US Department of Justice announced the indictment of 28 individuals in connection with a $1.8 billion Medicare fraud scheme.",
    "The Bank of England held interest rates at 5.25% in November 2023 as inflation continued to fall toward its 2% target.",
]


def generate_short_texts() -> list:
    """Return all pre-written short-text examples for all three classes."""
    rows = []
    for text in SHORT_HD:
        rows.append({"text": text.strip(), "label": 0})
    for text in SHORT_ML:
        rows.append({"text": text.strip(), "label": 1})
    for text in SHORT_LG:
        rows.append({"text": text.strip(), "label": 2})
    return rows


def fill_template(template: str, pool: dict) -> str:
    """Fill a template string with randomly chosen values from pool."""
    result = template
    for key, values in pool.items():
        placeholder = "{" + key + "}"
        if placeholder in result:
            result = result.replace(placeholder, random.choice(values), 1)
    return result


def generate_hd(n: int) -> list:
    rows = []
    pool = list(itertools.product(HD_OPENERS, HD_SUBJECTS, HD_VERBS, HD_OBJECTS, HD_CLOSERS))
    random.shuffle(pool)
    for opener, subj, verb, obj, closer in pool:
        if len(rows) >= n:
            break
        text = f"{opener} {subj} {verb} {obj}. {closer}"
        rows.append({"text": text, "label": 0})
    # If we need more, cycle through with different random combos
    while len(rows) < n:
        opener  = random.choice(HD_OPENERS)
        subj    = random.choice(HD_SUBJECTS)
        verb    = random.choice(HD_VERBS)
        obj     = random.choice(HD_OBJECTS)
        closer  = random.choice(HD_CLOSERS)
        text    = f"{opener} {subj} {verb} {obj}. {closer}"
        rows.append({"text": text, "label": 0})
    return rows[:n]


def generate_misleading(n: int) -> list:
    rows = []
    templates = PF_TEMPLATES * ((n // len(PF_TEMPLATES)) + 2)
    random.shuffle(templates)
    seen = set()
    for tmpl in templates:
        if len(rows) >= n:
            break
        text = fill_template(tmpl, PF_FILL)
        if text not in seen:
            seen.add(text)
            rows.append({"text": text, "label": 1})
    return rows[:n]


def generate_legitimate(n: int) -> list:
    rows = []
    templates = MM_TEMPLATES * ((n // len(MM_TEMPLATES)) + 2)
    random.shuffle(templates)
    seen = set()
    for tmpl in templates:
        if len(rows) >= n:
            break
        text = fill_template(tmpl, MM_FILL)
        if text not in seen:
            seen.add(text)
            rows.append({"text": text, "label": 2})
    return rows[:n]


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic training data (no API required)")
    parser.add_argument("--per-class", type=int, default=400,
                        help="Examples to generate per class (default: 400)")
    parser.add_argument("--out", default=None,
                        help="Output CSV path (default: src/synthetic_data.csv)")
    args = parser.parse_args()

    out_path = args.out or os.path.join(os.path.dirname(__file__), "synthetic_data.csv")
    n = args.per_class

    print(f"Generating {n} long-form examples per class (total {n*3})...")

    hd_rows = generate_hd(n)
    ml_rows = generate_misleading(n)
    lg_rows = generate_legitimate(n)

    print(f"  Highly Deceptive : {len(hd_rows)}")
    print(f"  Misleading       : {len(ml_rows)}")
    print(f"  Legitimate       : {len(lg_rows)}")

    # Short-text examples (2022-2025 real-world topics, 5-15 words)
    # These teach the model to classify headlines / social media posts correctly.
    short_rows = generate_short_texts()
    hd_short = sum(1 for r in short_rows if r["label"] == 0)
    ml_short = sum(1 for r in short_rows if r["label"] == 1)
    lg_short = sum(1 for r in short_rows if r["label"] == 2)
    print(f"\nShort-text examples (2022+ topics):")
    print(f"  Highly Deceptive : {hd_short}")
    print(f"  Misleading       : {ml_short}")
    print(f"  Legitimate       : {lg_short}")

    # Merge with existing synthetic data if present
    existing = []
    if os.path.exists(out_path):
        try:
            existing = pd.read_csv(out_path).to_dict("records")
            print(f"\nAppending to existing file ({len(existing)} rows).")
        except Exception:
            pass

    all_rows = existing + hd_rows + ml_rows + lg_rows + short_rows
    df = pd.DataFrame(all_rows).drop_duplicates(subset=["text"]).reset_index(drop=True)
    df.to_csv(out_path, index=False)

    print(f"\nSaved {len(df)} total examples to {out_path}")
    print("\nNext steps:")
    print(f"  python src/data_preprocessing.py --liar --synthetic {out_path}")
    print("  python src/train_model.py --batch-size 64 --epochs 10 --patience 4 --no-oversample")


if __name__ == "__main__":
    main()
