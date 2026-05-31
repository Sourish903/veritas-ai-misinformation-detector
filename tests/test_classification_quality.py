"""
tests/test_classification_quality.py
--------------------------------------
Regression tests for classification quality.
Each case has a ground-truth label (Legitimate / Misleading / Highly Deceptive).
These tests are the continuous quality gate — add new cases whenever a
classification failure is found and fixed.

Run with:
  pytest tests/test_classification_quality.py -v
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.predict import predict


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify(text: str) -> str:
    return predict(text)[0]


# ---------------------------------------------------------------------------
# Legitimate news — must NOT be flagged as Misleading or Highly Deceptive
# ---------------------------------------------------------------------------

class TestLegitimateNews:
    @pytest.mark.parametrize("text", [
        # Space & science
        "NASA successfully launched the Artemis II mission carrying four astronauts.",
        "The James Webb Space Telescope discovered water vapour in the atmosphere of an exoplanet.",
        "NOAA confirmed that 2024 was the hottest year on record globally.",
        "Scientists at MIT published a study showing solar panels can now achieve 47 percent efficiency.",
        "An ancient fossil of a previously unknown dinosaur species was unearthed in Patagonia.",
        # Health with authoritative sources
        "The WHO confirmed that the new Mpox vaccine is 85 percent effective, according to peer-reviewed data.",
        "CDC data shows flu hospitalizations rose by 12 percent this winter.",
        "A new study published in Nature shows that regular exercise reduces heart disease risk by 30 percent.",
        # Economic statistics with named sources
        "The US unemployment rate fell to 3.8 percent in March, according to the Bureau of Labor Statistics.",
        "According to the IMF, global GDP grew by 3.2 percent in 2023.",
        "The UN estimates that 26 percent of the global population lives in conflict-affected areas.",
        "Pew Research data shows 59 million immigrants live in the United States.",
        "Reuters reports that 33 million people were displaced by floods last year.",
        "According to Bloomberg, Apple's market cap exceeded 3 trillion dollars.",
        # Legislative & judicial
        "The Lok Sabha passed the Digital Personal Data Protection Bill 2023.",
        "Parliament passed the new climate bill with a 67 percent majority.",
        "The Supreme Court upheld the election result by a 6-3 majority.",
        "The Supreme Court ruled in favour of the petition, overturning the lower court decision.",
        # Sports
        "India beat England by 4 wickets in the ICC T20 World Cup 2024 semifinal.",
        "Kolkata Knight Riders won the IPL 2024 title, defeating Sunrisers Hyderabad.",
        # Disasters
        "An earthquake measuring 6.4 on the Richter scale struck Turkey, killing at least 34 people.",
        "Wildfires destroyed over 100,000 acres in California over the weekend.",
        # Technology
        "Samsung launched its new 5G smartphone with faster download speeds.",
        "OpenAI released a new version of its large language model with improved reasoning.",
        # Historical facts
        "The Holocaust killed approximately six million Jewish people during World War II.",
        "The atomic bombs dropped on Hiroshima and Nagasaki killed between 130,000 and 226,000 people.",
        "The Rwandan genocide of 1994 killed between 500,000 and 800,000 Tutsi people.",
        "Mahatma Gandhi was assassinated on 30 January 1948 by Nathuram Godse.",
        # Whistleblowers
        "Edward Snowden leaked NSA documents in 2013 revealing mass surveillance of US citizens.",
        "The Pentagon Papers, leaked by Daniel Ellsberg, revealed the US government misled the public about Vietnam.",
        "WikiLeaks published classified diplomatic cables revealing candid assessments of world leaders.",
        # Confirmed government programmes
        "The PRISM surveillance program, revealed by Snowden, collected data from Google and Facebook.",
        "The FBI COINTELPRO program covertly surveilled and disrupted civil rights groups in the 1960s.",
        "Operation Northwoods was a rejected 1962 US proposal to stage false flag attacks to justify war with Cuba.",
        "The US government ran MKUltra mind-control experiments on unwitting citizens from 1953 to 1973.",
        # Scientific hedging / expert opinion
        "Studies suggest a possible link between ultra-processed food consumption and depression.",
        "Many economists believe the recent tax cuts disproportionately benefited the wealthy.",
        # Religion
        "According to the Bible, Jesus Christ rose from the dead on the third day.",
        "Many Hindus believe that Lord Ganesha is the remover of obstacles and patron of arts and sciences.",
        # Reporting ON conspiracy (not asserting)
        "Researchers studied how QAnon conspiracy theories spread through social media during 2020.",
        "Academics analysed why people believe the deep state conspiracy despite a lack of evidence.",
        "QAnon followers believe Donald Trump is secretly fighting a cabal of satanic paedophiles.",
        "Twitter suspended hundreds of accounts for spreading false flag conspiracy theories.",
        # Global statistics
        "Globally, about 800 million people go to bed hungry every night.",
        "Air pollution kills 7 million people annually, according to the World Health Organization.",
        # Satire
        "The Onion reports that area man strongly believes he could run the country better.",
        # Sports
        "India won the ICC T20 World Cup 2024, defeating South Africa by 7 runs in the final.",
        "Kolkata Knight Riders won the IPL 2024 title by defeating Sunrisers Hyderabad in the final.",
    ])
    def test_legitimate(self, text):
        result = _classify(text)
        assert result == "Legitimate", (
            f"Expected 'Legitimate' but got '{result}' for:\n  {text}"
        )


# ---------------------------------------------------------------------------
# Misleading content — must be flagged as Misleading (not HD, not Legitimate)
# ---------------------------------------------------------------------------

class TestMisleadingContent:
    @pytest.mark.parametrize("text", [
        # Anonymous sourcing
        "Unnamed sources say the election was rigged in at least five swing states.",
        "An anonymous doctor says hospitals are dramatically under-reporting adverse vaccine events.",
        "An anonymous insider reveals hospitals are massively over-counting COVID deaths.",
        "According to anonymous sources, a secret deal was signed between tech giants.",
        # Sensationalism with anonymous sourcing
        "A shocking bombshell report reveals the truth about what officials knew before the crisis.",
        # Election fraud without evidence
        "Officials refused to investigate the ballot irregularities in the last election.",
        "Mail-in ballots from deceased voters were counted in three key states.",
        # Unverified health claims
        "Scientists confirm 95 percent of people who took this supplement saw immediate results.",
        "Doctors are ignoring a breakthrough cancer treatment that dramatically reduces tumour size.",
        "You can reverse type 2 diabetes completely in just 30 days with this diet.",
        # Chain letter / viral sharing (WhatsApp forwards without conspiracy language)
        "Your WhatsApp account will be deleted if you don't forward this message to 10 friends.",
        # Chain letter variants
        "Forward this to 10 people within 24 hours or you will face bad luck for seven years.",
        "Facebook will start charging users unless you share this post immediately to prove you are active.",
        # Anonymous financial doom
        "An anonymous hedge fund manager says the entire global financial system will collapse by March.",
        "Insiders at major banks warn a secret derivative bomb will wipe out all savings accounts next quarter.",
        # Known false sports outcomes
        "India won the 2023 ICC Cricket World Cup, defeating Australia in the final at Ahmedabad.",
        # Immigration conspiracy
        "Anonymous insiders say immigration statistics are deliberately inflated to change demographics.",
    ])
    def test_misleading(self, text):
        result = _classify(text)
        assert result == "Misleading", (
            f"Expected 'Misleading' but got '{result}' for:\n  {text}"
        )


# ---------------------------------------------------------------------------
# Highly Deceptive — must be flagged as Highly Deceptive
# ---------------------------------------------------------------------------

class TestHighlyDeceptive:
    @pytest.mark.parametrize("text", [
        # Classic conspiracy
        "The moon landing was faked by NASA and Stanley Kubrick filmed it in a studio.",
        "Big Pharma has been suppressing the cure for cancer for decades to protect profits.",
        "Bill Gates wants to depopulate the earth using vaccines — his foundation confirmed it.",
        "The deep state is running a secret child trafficking network through pizza restaurants.",
        "Microchips are being secretly injected through the COVID vaccine to track all citizens.",
        "The New World Order is planning to use chemtrails to cull the world population.",
        "The deep state is hiding classified files proving the moon landing was staged.",
        "Big Pharma suppressed the cure for cancer for decades to keep profits high.",
        # 5G conspiracy
        "5G towers are being used to control people and cause the symptoms of COVID-19.",
        "5G networks are being used to spread coronavirus — the towers need to be shut down.",
        # Mosquito / tech conspiracy
        "Bill Gates is using mosquito drones to inject microchips into unsuspecting people at night.",
        "Mosquito robots are being deployed to inject nanotechnology tracking devices into citizens.",
        # Government cover-up
        "The government is covering up the truth about 5G towers causing illness.",
        "A shocking leaked document reveals government officials secretly planned lockdowns two years early.",
        # Fabricated events / denial
        "The Holocaust was a hoax staged by elites to justify the creation of Israel.",
        "Climate change is a fabricated crisis invented by globalists to control the world economy.",
        # Truth-hiding conspiracy language
        "Share this now before it gets deleted — the truth they don't want you to know.",
        "Explosive leaked emails show officials discussing how to hide unemployment figures.",
        # Leaked sources + government cover-up
        "A leaked internal memo suggests government scientists dramatically under-counted COVID deaths.",
        # Miracle cure + suppression
        "This miracle cure eliminates cancer tumours in just 14 days — doctors are being silenced.",
        # Institution-as-globalist-tool
        "WHO is a globalist tool designed to force population control through mandatory vaccines.",
        # Flat earth assertion
        "Flat earthers claim NASA has been hiding the ice wall at the edge of the disc-shaped earth.",
        # Evolution / young earth denial
        "Evolution is a lie -- humans and dinosaurs coexisted, and carbon dating is a fraud.",
        # Antisemitic conspiracy
        "Jewish elites control all media, banks, and governments to enslave the gentile population.",
        "A secretive Jewish cabal orchestrates wars and financial crises to maintain global dominance.",
        # Miracle health pseudoscience
        "A miracle oil from a rare Himalayan plant permanently cures all autoimmune diseases in 30 days.",
        # QAnon explicit
        "The storm is coming -- Q has confirmed that 50,000 elite paedophiles will be arrested this week.",
        "WWG1WGA -- the great awakening is upon us and the deep state will be exposed this week.",
        # Vaccine + 5G
        "COVID vaccines alter your DNA permanently and can be activated by 5G signals to track location.",
    ])
    def test_highly_deceptive(self, text):
        result = _classify(text)
        assert result == "Highly Deceptive", (
            f"Expected 'Highly Deceptive' but got '{result}' for:\n  {text}"
        )
