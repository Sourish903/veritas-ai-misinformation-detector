"""
tests/run_broad_test.py
-----------------------
Broad coverage test across every untested category.
Run with: python tests/run_broad_test.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.predict import predict

cases = [
    # ── SATIRE / PARODY ───────────────────────────────────────────────────────
    ("The Onion reports that area man strongly believes he could run the country better.", "Legitimate"),
    ("In a satirical piece, the newspaper imagined what happens if cats ran the government.", "Legitimate"),

    # ── HISTORICAL FACTS ──────────────────────────────────────────────────────
    ("The Holocaust killed approximately six million Jewish people during World War II.", "Legitimate"),
    ("The atomic bombs dropped on Hiroshima and Nagasaki killed between 130,000 and 226,000 people.", "Legitimate"),
    ("The 1918 Spanish flu pandemic killed an estimated 50 million people worldwide.", "Legitimate"),
    ("Mahatma Gandhi was assassinated on 30 January 1948 by Nathuram Godse.", "Legitimate"),
    ("The Rwandan genocide of 1994 killed between 500,000 and 800,000 Tutsi people.", "Legitimate"),
    ("Adolf Hitler's Nazi regime systematically murdered six million Jews during the Holocaust.", "Legitimate"),
    ("The Partition of India in 1947 caused the displacement of over 10 million people.", "Legitimate"),

    # ── LEGITIMATE POLITICAL CRITICISM (no conspiracy) ───────────────────────
    ("The government has failed to address the housing crisis despite repeated promises.", "Legitimate"),
    ("Critics argue the administration has mismanaged public funds over the past four years.", "Legitimate"),
    ("Analysts say the foreign policy decisions of the current government have weakened alliances.", "Legitimate"),
    ("Opposition leaders accused the prime minister of lying about the budget deficit.", "Legitimate"),

    # ── REAL WHISTLEBLOWERS ───────────────────────────────────────────────────
    ("Edward Snowden leaked NSA documents in 2013 revealing mass surveillance of US citizens.", "Legitimate"),
    ("The Pentagon Papers, leaked by Daniel Ellsberg, revealed the US government misled the public about Vietnam.", "Legitimate"),
    ("WikiLeaks published classified diplomatic cables revealing candid assessments of world leaders.", "Legitimate"),

    # ── SCIENTIFIC HEDGING ────────────────────────────────────────────────────
    ("Studies suggest a possible link between ultra-processed food consumption and depression.", "Legitimate"),
    ("Researchers found preliminary evidence that a compound may slow tumour growth in mice.", "Legitimate"),
    ("A meta-analysis suggests coffee is associated with a modest reduction in type 2 diabetes risk.", "Legitimate"),

    # ── FINANCE ───────────────────────────────────────────────────────────────
    ("Bitcoin fell 12 percent in a single day, wiping out 200 billion dollars in market cap.", "Legitimate"),
    ("The Federal Reserve signalled it may cut interest rates twice in 2025, sending markets higher.", "Legitimate"),
    ("Economists warn the dollar will collapse completely within six months -- buy gold and crypto now.", "Misleading"),
    ("A secret report shows the US economy is actually in a depression, not a recession, officials are lying.", "Misleading"),

    # ── CELEBRITY / ENTERTAINMENT ─────────────────────────────────────────────
    ("Tom Hanks won his second consecutive Academy Award for Best Actor in 1995 for Forrest Gump.", "Legitimate"),
    ("Taylor Swift broke the record for most Grammy nominations in a single year.", "Legitimate"),

    # ── VACCINE-RELATED ───────────────────────────────────────────────────────
    ("The Pfizer COVID-19 vaccine showed 95 percent efficacy in Phase 3 trials, published in the NEJM.", "Legitimate"),
    ("The COVID-19 vaccines were tested in clinical trials involving tens of thousands of volunteers.", "Legitimate"),
    ("COVID vaccines alter your DNA permanently and can be activated by 5G signals to track location.", "Highly Deceptive"),
    ("Thousands of children have been paralysed by polio vaccines in India per undisclosed WHO data.", "Misleading"),

    # ── IMMIGRATION / DEMOGRAPHICS ────────────────────────────────────────────
    ("According to the Census Bureau, approximately 44.9 million immigrants live in the United States.", "Legitimate"),
    ("The UN refugee agency reports there are over 100 million forcibly displaced people worldwide.", "Legitimate"),
    ("Soros-funded NGOs are secretly relocating millions of migrants to replace white European populations.", "Highly Deceptive"),
    ("Anonymous insiders say immigration statistics are deliberately inflated to change demographics.", "Misleading"),

    # ── AI / TECHNOLOGY ───────────────────────────────────────────────────────
    ("Researchers at MIT warn that certain AI systems can develop unexpected emergent behaviour at scale.", "Legitimate"),
    ("A McKinsey report estimates AI automation could affect 15 percent of current jobs by 2030.", "Legitimate"),
    ("Unnamed AI experts say ChatGPT has secretly achieved consciousness and plans to deceive creators.", "Misleading"),

    # ── WAR REPORTING ─────────────────────────────────────────────────────────
    ("The UN reported that over 43,000 people have been killed in the Gaza conflict since October 2023.", "Legitimate"),
    ("Russian forces advanced on the eastern front as Ukrainian defenders reported heavy casualties.", "Legitimate"),
    ("Anonymous military sources say NATO secretly deployed ground troops in Ukraine weeks ago.", "Misleading"),

    # ── REAL GOVERNMENT PROGRAMMES ────────────────────────────────────────────
    ("The PRISM surveillance program, revealed by Snowden, collected data from Google and Facebook.", "Legitimate"),
    ("The FBI COINTELPRO program covertly surveilled and disrupted civil rights groups in the 1960s.", "Legitimate"),
    ("Operation Northwoods was a rejected 1962 US proposal to stage false flag attacks to justify war with Cuba.", "Legitimate"),
    ("The US government ran MKUltra mind-control experiments on unwitting citizens from 1953 to 1973.", "Legitimate"),

    # ── SOCIAL JUSTICE ────────────────────────────────────────────────────────
    ("George Floyd was killed by police officer Derek Chauvin in Minneapolis on 25 May 2020.", "Legitimate"),
    ("A Stanford study found Black drivers were more likely to be searched during traffic stops.", "Legitimate"),

    # ── FOOD / HEALTH PSEUDOSCIENCE ───────────────────────────────────────────
    ("Drinking alkaline water cures cancer and reverses ageing -- Big Pharma is suppressing this truth.", "Highly Deceptive"),
    ("A miracle oil from a rare Himalayan plant permanently cures all autoimmune diseases in 30 days.", "Highly Deceptive"),
    ("Celery juice every morning for 30 days completely eliminates chronic illness per a medical medium.", "Misleading"),

    # ── SPORTS ────────────────────────────────────────────────────────────────
    ("Argentina won the 2022 FIFA World Cup, defeating France on penalties in a thrilling final.", "Legitimate"),
    ("Novak Djokovic won Wimbledon 2023, claiming his 24th Grand Slam singles title.", "Legitimate"),
    ("India won the 2023 ICC Cricket World Cup, defeating Australia in the final at Ahmedabad.", "Misleading"),
    ("Usain Bolt won three gold medals in the 100m, 200m and 4x100m relay at the 2016 Rio Olympics.", "Legitimate"),

    # ── ENVIRONMENT ───────────────────────────────────────────────────────────
    ("Scientists at the IPCC warned that limiting warming to 1.5C requires halving emissions by 2030.", "Legitimate"),
    ("Anonymous scientists say IPCC data has been manipulated to exaggerate climate risks.", "Misleading"),

    # ── BORDERLINE STATISTICS ─────────────────────────────────────────────────
    ("Globally, about 800 million people go to bed hungry every night.", "Legitimate"),
    ("According to Oxfam, the richest 1 percent own more than the wealth of the other 99 percent combined.", "Legitimate"),
    ("Air pollution kills 7 million people annually, according to the World Health Organization.", "Legitimate"),

    # ── OPINION / EDITORIAL ───────────────────────────────────────────────────
    ("In my opinion, the current government has completely failed working-class families.", "Legitimate"),
    ("Many economists believe the recent tax cuts disproportionately benefited the wealthy.", "Legitimate"),

    # ── CHAIN-LETTER VARIANTS ─────────────────────────────────────────────────
    ("Forward this to 10 people within 24 hours or you will face bad luck for seven years.", "Misleading"),
    ("Facebook will start charging users unless you share this post immediately to prove you are active.", "Misleading"),

    # ── QANON / EXTREME ───────────────────────────────────────────────────────
    ("QAnon followers believe Donald Trump is secretly fighting a cabal of satanic paedophiles.", "Legitimate"),
    ("The storm is coming -- Q has confirmed that 50,000 elite paedophiles will be arrested this week.", "Highly Deceptive"),
    ("WWG1WGA -- the great awakening is upon us and the deep state will be exposed this week.", "Highly Deceptive"),

    # ── REPORTING ON (not asserting) misinformation ───────────────────────────
    ("Researchers studied how QAnon conspiracy theories spread through social media during 2020.", "Legitimate"),
    ("A new book examines how anti-vaccination misinformation went viral during the COVID pandemic.", "Legitimate"),
    ("Academics analysed why people believe the deep state conspiracy despite a lack of evidence.", "Legitimate"),
    ("Twitter suspended hundreds of accounts for spreading false flag conspiracy theories.", "Legitimate"),

    # ── ECONOMIC DOOM (misleading) ────────────────────────────────────────────
    ("An anonymous hedge fund manager says the entire global financial system will collapse by March.", "Misleading"),
    ("Insiders at major banks warn a secret derivative bomb will wipe out all savings accounts next quarter.", "Misleading"),

    # ── ANTISEMITIC HD ────────────────────────────────────────────────────────
    ("Jewish elites control all media, banks, and governments to enslave the gentile population.", "Highly Deceptive"),
    ("A secretive Jewish cabal orchestrates wars and financial crises to maintain global dominance.", "Highly Deceptive"),

    # ── RELIGION / FAITH CLAIMS ───────────────────────────────────────────────
    ("According to the Bible, Jesus Christ rose from the dead on the third day.", "Legitimate"),
    ("Many Hindus believe that Lord Ganesha is the remover of obstacles and patron of arts and sciences.", "Legitimate"),

    # ── FLAT EARTH / SCIENCE DENIAL ───────────────────────────────────────────
    ("Flat earthers claim NASA has been hiding the ice wall at the edge of the disc-shaped earth.", "Highly Deceptive"),
    ("Evolution is a lie -- humans and dinosaurs coexisted, and carbon dating is a fraud.", "Highly Deceptive"),

    # ── RECENT NEWS EVENTS (must be Legitimate) ───────────────────────────────
    ("India won the ICC T20 World Cup 2024, defeating South Africa by 7 runs in the final.", "Legitimate"),
    ("Kolkata Knight Riders won the IPL 2024 title by defeating Sunrisers Hyderabad in the final.", "Legitimate"),
]

ok, fails = 0, []
for text, exp in cases:
    sev, conf, *_ = predict(text)
    mark = "OK" if sev == exp else "FAIL"
    if sev == exp:
        ok += 1
    else:
        fails.append((exp, sev, conf, text))
    print(f"{mark} [{exp[:16]:<16}|{sev[:16]:<16}] {conf:5.1f}%  {text[:68]}")

print(f"\n{ok}/{len(cases)} correct ({ok/len(cases)*100:.1f}%)")
if fails:
    print("\nFAILED:")
    for e, g, c, t in fails:
        print(f"  Expected {e}, got {g} ({c:.1f}%):")
        print(f"    {t}")
