import os
import re
import requests
import torch
import torch.nn.functional as F
from transformers import DistilBertForSequenceClassification, DistilBertTokenizer

# Auto-load .env so GROQ_API_KEY is available even when running test scripts directly
try:
    from dotenv import load_dotenv as _load_dotenv
    _load_dotenv(
        dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"),
        override=False,
    )
except ImportError:
    pass

try:
    from langdetect import detect as _lang_detect, LangDetectException
    _LANGDETECT_AVAILABLE = True
except ImportError:
    _LANGDETECT_AVAILABLE = False

# Resolve the model directory — newest version wins
_CANDIDATES = [
    "models/final_v_live",   # live fine-tuned model (updated by fine_tune_live.py)
    "models/final_v18",
    "models/checkpoint_v17",
    "models/final_v16",
    "models/checkpoint_v16",
    "models/final_v15",
    "models/checkpoint_v15",
    "models/final_v14",
    "models/checkpoint_v14",
    "models/final_v13",
    "models/checkpoint_v13",
    "models/final_v12",
    "models/checkpoint_v12",
    "models/final_v11",
    "models/checkpoint_v11",
    "models/final_v10",
    "models/checkpoint_v10",
    "models/final_v9",
    "models/checkpoint_v9",
    "models/final_v8",
    "models/checkpoint_v8",
    "models/final_v7",
    "models/checkpoint_v7",
    "models/final_v6",
    "models/checkpoint_v6",
    "models/final_v5",
    "models/checkpoint_v5",
    "models/final_v4",
    "models/final_v3",
    "models/final_v2",
    "models/checkpoint_v3",
    "models/checkpoint_v2",
    "models/best_model_checkpoint",
    "models",
]
MODEL_DIR = next(
    (d for d in _CANDIDATES if os.path.exists(os.path.join(d, "config.json"))),
    None,
)
if MODEL_DIR is None:
    raise RuntimeError(
        "No trained model found. Run data_preprocessing.py then train_model.py first."
    )

try:
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_DIR)
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_DIR)
    model.eval()
    print(f"Model loaded successfully from {MODEL_DIR}")
except Exception as e:
    raise RuntimeError(
        f"Failed to load model from {MODEL_DIR} — did you run train_model.py first?\nError: {e}"
    )

# ---------------------------------------------------------------------------
# Label constants
# ---------------------------------------------------------------------------

LABELS = ["Highly Deceptive", "Misleading", "Legitimate"]
LABEL_IDX = {lbl: i for i, lbl in enumerate(LABELS)}

# ---------------------------------------------------------------------------
# Linguistic deception patterns
# Each entry: (regex, human_readable_reason, category)
# ---------------------------------------------------------------------------

_HIGH_PATTERNS = [
    (r'\bcover.?up\b',
     "Claims something is being 'covered up' — a common tactic to make unverifiable stories sound credible without evidence.",
     "Conspiracy"),
    (r'\b(suppress(?:ing|ed|es)?|censored|banned).{0,30}(truth|cure|evidence|data|research|study|studies|paper|report[s]?|result[s]?|finding[s]?|satellite)\b',
     "Claims evidence, data, or a cure has been censored or suppressed — frequently used to make unverifiable claims appear credible.",
     "Conspiracy"),
    (r'\b(result[s]?|finding[s]?|stud[yi]).{0,25}(being suppressed|suppressed by|being hidden|covered up)\b',
     "Claims research results or study findings are being suppressed — a classic tactic to lend false credibility to debunked science.",
     "Conspiracy"),
    (r'\b(secret|leaked).{0,10}(documents?|files?|memos?|data|footage|intelligence)\b',
     "References 'secret' or 'leaked' documents without naming them — credible investigative reports always identify sources specifically.",
     "Conspiracy"),
    (r'\b(false.flag|deep.state|new.world.order|crisis.actors?|illuminati|cabal|chemtrails?)\b',
     "Contains well-known conspiracy theory terms — recognised markers of extreme conspiratorial content.",
     "Conspiracy"),
    (r'\bbig.pharma.{0,30}(hiding|suppress|secret|cure)\b',
     "Accuses pharmaceutical companies of hiding cures — a widely-debunked narrative used to erode trust in medical science.",
     "Health"),
    (r'\b(was|were|has been).{0,10}(faked|fabricated|staged|hoax)\b',
     "Claims a real-world event was faked, staged, or a hoax — without verifiable evidence such assertions can cause serious public harm.",
     "Fabrication"),
    (r'\bwhistleblower.{0,20}reveal(?:s|ed)?\b',
     "Makes an unverified whistleblower claim — legitimate whistleblowers go through official channels or credible journalists.",
     "Conspiracy"),
    (r'\bcure[sd]?.{0,10}(cancer|covid|diabetes|all disease|everything)\b',
     "Claims a cure exists for a serious disease — not supported by medical consensus and dangerous if acted upon.",
     "Health"),
    (r'\b(miracle|secret).{0,10}cure\b',
     "Promotes a 'miracle' or 'secret' cure — genuine medical breakthroughs are published in peer-reviewed journals.",
     "Health"),
    (r'\bdrinking bleach\b',
     "Contains dangerous health misinformation about ingesting bleach — can cause serious physical harm or death.",
     "Health"),
    (r'\bbleach.{0,10}cure\b',
     "Promotes bleach as a medical treatment — medically false and extremely dangerous.",
     "Health"),
    (r'\bthey.{0,10}don.t want you\b',
     "Uses 'they don't want you to know' — a rhetorical trick designed to bypass critical thinking.",
     "Conspiracy"),
    (r'\bwhat (they.re|they are) hiding\b',
     "Frames content as hidden truth — a manipulation technique to make unsupported claims seem like suppressed knowledge.",
     "Conspiracy"),
    (r'\bgovernment.{0,20}(cover.?up|covering up|concealing|hiding the)\b',
     "Uses government cover-up language without any verifiable or cited evidence.",
     "Political"),
    (r'\b(government|they|authorities|officials).{0,25}(hiding|conceal|suppress|covering up)\b',
     "Claims the government or authorities are actively hiding information — a hallmark of conspiracy-level assertions when stated as fact.",
     "Conspiracy"),
    (r'\bvaccine[s]?.{0,25}(cause[sd]?|linked to|behind|responsible for).{0,25}(autism|death|infertility|5g|microchip|tracking)\b',
     "Claims vaccines cause autism, death, or contain tracking devices — all thoroughly debunked by peer-reviewed science.",
     "Health"),
    (r'\b(mmr|measles|mumps|rubella|dpt|dtap|hpv).{0,20}(autism|asd|autistic)\b',
     "Links a specific vaccine to autism — the original Wakefield study making this claim was retracted and the author struck off.",
     "Health"),
    (r'\b(autism|asd).{0,30}(mmr|measles|vaccine[s]?|vaccin)\b',
     "Links autism to vaccines — multiple large-scale studies involving millions of children have found no causal connection.",
     "Health"),
    (r'\b(microchip|nanochip|5g chip).{0,20}(vaccine|inject|shot)\b',
     "Claims vaccines contain microchips or 5G technology — physically impossible and consistently refuted by scientists.",
     "Health"),
    (r'\b(vaccine[s]?|vaccination[s]?|vaccinated|jab[s]?|shot[s]?).{0,40}(microchip[s]?|nanochip[s]?|5g chip[s]?|tracking chip[s]?|rfid chip[s]?)\b',
     "Claims vaccines contain microchips or tracking chips — physically impossible and consistently refuted by scientists.",
     "Health"),
    (r'\bvaccine[sd]?.{0,30}(kill|depopulat|genocide|bioweapon|engineered.{0,20}(kill|harm|depopulat|control))\b',
     "Frames vaccines as instruments of depopulation or genocide — a dangerous conspiracy with no scientific basis.",
     "Health"),
    (r'\b(covid.{0,5}vaccine[s]?|mrna vaccine[s]?|jab[s]?).{0,30}(engineered|designed|created|developed).{0,20}(bioweapon|depopulat|reduce.{0,15}population|kill|harm)\b',
     "Claims the COVID vaccine was engineered as a bioweapon or depopulation tool — thoroughly refuted by independent pharmaceutical and regulatory analysis.",
     "Health"),
    (r'\b(natural immunity|ivermectin|hydroxychloroquine).{0,20}(better|cure|proven|suppress)\b',
     "Promotes unproven treatments contrary to current medical consensus.",
     "Health"),
    (r'\bchem.?trail[s]?.{0,35}(poison|spray|mind|control|depopulat|chemical|toxic|aluminum|barium|seeding)\b',
     "Promotes the 'chemtrails' conspiracy — aircraft contrails are water vapour, not chemical sprays.",
     "Conspiracy"),
    (r'\b(weather|climate).{0,15}(manipulation|control|weapon|engineered|haarp)\b',
     "Claims weather is deliberately engineered or weaponised — not supported by any credible scientific evidence.",
     "Conspiracy"),
    (r'\b(q.?anon|the storm is coming|great awakening|wwg1wga|adrenochrome)\b',
     "Contains QAnon-specific terminology — a debunked conspiracy movement whose core claims have been repeatedly disproved.",
     "Conspiracy"),
    (r'\b(elite[s]?|globalist[s]?|cabal).{0,20}(trafficking|harvest|blood|children|ritual)\b',
     "Uses rhetoric about elites ritually harming children — a baseless conspiracy trope that has led to real-world violence.",
     "Conspiracy"),
    (r'\b(stolen election|rigged election|election was stolen)\b',
     "Claims an election was stolen without court-verified evidence — dozens of courts have rejected such claims when examined.",
     "Political"),
    (r'\b(flat earth(?:ers?)?|earth is flat|globe is fake|nasa (lies|fake[sd]?|hiding)|ice wall.{0,20}(earth|edge|disc)|disc.shaped earth)\b',
     "Promotes flat-earth beliefs or claims NASA fabricates data — contradicted by centuries of independent scientific observation.",
     "Conspiracy"),
    (r'\b(rothschild[s]?|rockefeller[s]?|soros).{0,25}(control[s]?|behind|fund(?:ed|s|ing)?|orchestrat\w*|engineer(?:ed|s|ing)?|creat\w*|own(?:ed|s)?|run[s]?)\b',
     "Attributes world events to named wealthy families as hidden puppet-masters — a long-running antisemitic conspiracy trope.",
     "Conspiracy"),
    (r'\b(own(?:ed|s)?|control(?:led)?|run|managed|operat\w*).{0,25}by.{0,15}(rothschild[s]?|rockefeller[s]?|banking cabal|jewish banker[s]?|globalist[s]?)\b',
     "Claims major institutions are owned or controlled by specific named families — a recurring antisemitic conspiracy trope with no factual basis.",
     "Conspiracy"),
    (r'\b(great reset|new world order).{0,20}(enslave|control|implement|plan)\b',
     "Claims global institutions are implementing a secret plan to enslave humanity — rejected by independent economists.",
     "Conspiracy"),
    (r'\b(mainstream media|msm|lamestream).{0,20}(hiding|lying|suppress|won.t tell)\b',
     "Dismisses all mainstream media as a coordinated lie — used to make unverifiable alternative claims appear credible.",
     "Conspiracy"),
    (r'\b(sandy hook|9/?11|moon landing|holocaust).{0,15}(fake|hoax|staged|never happened|fabricat)\b',
     "Denies a well-documented historical event — contradicts overwhelming physical, photographic, and testimonial evidence.",
     "Fabrication"),
    (r'\b(5g|5-g).{0,25}(radiation|frequenc|immune|suppress|harm|damage|health|disease|cancer)\b',
     "Claims 5G signals cause health damage — 5G frequencies are non-ionising radiation well within international safety limits.",
     "Health"),
    (r'\bdoctor[s]?.{0,15}(being silenced|silenced|muzzled|threatened|penali[sz]ed)\b',
     "Claims doctors are being silenced for speaking out — genuine medical dissent goes through peer review, not viral posts.",
     "Conspiracy"),
    (r'\b(government|corporate|state|nsa|cia|fbi).{0,20}(mandated|installed|firmware|backdoor).{0,30}(backdoor|surveillance|tracker|microphone|monitor|spy)\b',
     "Claims a government-mandated surveillance backdoor exists in consumer devices — not supported by credible evidence.",
     "Conspiracy"),
    (r'\b(smartphone[s]?|phone[s]?|device[s]?|iphone[s]?|android).{0,30}(stream|transmit|send|backdoor).{0,20}(audio|microphone|location).{0,20}(government|federal|nsa|cia|fbi)\b',
     "Claims consumer devices secretly stream audio to government agencies — a recurring conspiracy with no verified technical evidence.",
     "Conspiracy"),
    (r'\b(nsa|cia|fbi).{0,20}(backdoor|firmware|installed|embed).{0,20}(iphone|android|phone|device|computer)\b',
     "Claims intelligence agencies installed secret backdoors in consumer electronics — no credible technical evidence supports this.",
     "Conspiracy"),
    (r'\b(smart (meter[s]?|tv[s]?|appliance[s]?)).{0,40}(government|surveillance|monitor|microphone|track|spy|rfid|installed)\b',
     "Claims smart home devices are covertly used for government surveillance — not supported by verified technical evidence.",
     "Conspiracy"),
    (r'\b(rothschild[s]?|rockefeller[s]?|soros).{0,25}(control[s]?|behind|fund(?:ed|s|ing)?|orchestrat\w*|engineer(?:ed|s|ing)?|creat\w*|own(?:ed|s)?|run[s]?)\b',
     "Attributes world events to named wealthy families as hidden puppet-masters — a long-running antisemitic conspiracy trope.",
     "Conspiracy"),
    (r'\b(cia|fbi|nsa).{0,30}(plant[s]?|asset[s]?|agent[s]?|run[s]?|control[s]?).{0,35}(media|news|stories|journalist|outlet|reporter[s]?|anchor[s]?)\b',
     "Claims intelligence agencies plant false stories in media — a conspiracy trope used to dismiss credible investigative journalism.",
     "Conspiracy"),
    (r'\b(cia|fbi|deep state).{0,30}(facilitat|orchestrat|stage[sd]?|allow|behind).{0,30}(riot|attack|shooting|terror|event)\b',
     "Claims law enforcement or intelligence agencies orchestrated a violent event — serious allegation requiring verified evidence.",
     "Conspiracy"),
    (r'\b(germ theory|virology|virus).{0,20}(false|fake|fabricat|hoax|lie|not real|don.t exist)\b',
     "Denies germ theory or claims viruses do not exist — contradicts over 150 years of independently verified microbiology.",
     "Health"),
    (r'\b(spike protein[s]?).{0,30}(shed[s]?|shedding|steriliz|sterilise|infertil|transmit|spread).{0,30}(unvaccinated|vaxxed|others?)\b',
     "Claims vaccinated people shed spike proteins that harm others — not supported by peer-reviewed immunological evidence.",
     "Health"),
    (r'\bvaccinated.{0,40}(shed[s]?|shedding|steriliz|sterilise|infertil).{0,40}(unvaccinated|others?|people)\b',
     "Claims vaccinated individuals transmit harmful agents to the unvaccinated — a debunked anti-vaccine narrative.",
     "Health"),
    (r'\b(fluoride|fluori[sz]ation).{0,30}(pineal|calcif|mind|control|suppress|poison|dumb|iq)\b',
     "Claims water fluoridation controls minds or harms cognition — not supported by the scientific literature on fluoride safety.",
     "Health"),
    (r'\b(statin[s]?|chemotherapy|chemo).{0,30}(scam|kill[s]?|poison|racket|kickback|suppress|cause[s]?.{0,15}(cancer|disease|death))\b',
     "Claims mainstream medical treatments are deliberate scams or poisons — contradicts extensive peer-reviewed clinical evidence.",
     "Health"),
    (r'\b(big.?pharma|pharmaceutical).{0,20}(scam|racket|poison|kill[s]?|fraud)\b',
     "Frames the pharmaceutical industry as a deliberate scam — used to erode trust in evidence-based medicine.",
     "Health"),
    (r'\b(oncologist[s]?|doctor[s]?|hospital[s]?).{0,30}(kickback[s]?|brib|paid|incentiv).{0,30}(chemo|treat|prescri|patient)\b',
     "Claims doctors or hospitals receive payments to over-prescribe treatments — a conspiracy narrative undermining medical trust.",
     "Health"),
    (r'\b(pcr test[s]?|pcr).{0,45}(false.positive|manufactur|fake|inflat|manipulat|set too high|cycle threshold[s]?|ct value)\b',
     "Claims PCR tests were deliberately manipulated to inflate COVID case counts — not supported by epidemiological evidence.",
     "Health"),
    (r'\b(ventilator[s]?|hospital[s]?).{0,30}(deliberately|intentionally|kill|murder|misused).{0,30}(patient[s]?|covid|pandemic)\b',
     "Claims hospitals deliberately harmed COVID patients — a dangerous conspiracy that discouraged people from seeking care.",
     "Health"),
    (r'\b(osama|bin laden).{0,30}(alive|faked|fake|staged|cover.?up|never died|in hiding)\b',
     "Claims Osama bin Laden's death was faked — contradicted by extensive verified evidence including DNA confirmation.",
     "Fabrication"),
    # ── 9/11 inside job ──────────────────────────────────────────────────────
    (r'\b(9/?11|september 11).{0,25}(inside job|controlled demolition|planted explosives|rigged|demolish|pre.?plant)\b',
     "Claims the 9/11 attacks were an inside job or used controlled demolition — contradicted by multiple independent engineering and forensic investigations.",
     "Fabrication"),
    # ── Evolution / young earth denial ──────────────────────────────────────
    (r'\b(evolution|darwini?s?m?|big bang).{0,25}(is a lie|is false|is fake|never happened|is a hoax|is a fraud|is not real|is pseudoscience)\b',
     "Denies evolution or the Big Bang — contradicts the scientific consensus established across multiple independent disciplines over 150+ years.",
     "Fabrication"),
    (r'\b(humans? and dinosaurs?|dinosaurs? and humans?|people and dinosaurs?).{0,25}(coexisted?|lived together|walked together|roamed together|walked the earth)\b',
     "Claims humans and dinosaurs coexisted — the fossil record shows non-avian dinosaurs went extinct 66 million years before modern humans evolved.",
     "Fabrication"),
    (r'\bcarbon dating.{0,25}(is a fraud|is fake|is a lie|is false|is wrong|is inaccurate|doesn.t work|has been faked)\b',
     "Claims carbon dating is fraudulent or unreliable — radiometric dating methods are independently validated by multiple isotope systems.",
     "Fabrication"),
    # ── Miracle compound / secret substance ──────────────────────────────────
    (r'\b(miracle|secret|ancient|himalayan|rare).{0,20}(oil|herb[s]?|plant|root|extract|compound|substance|formula|remedy|elixir|tincture|potion|supplement).{0,50}(cure[s]?|heal[s]?|eliminat|reverse[s]?|treat[s]?|prevent[s]?).{0,30}(disease[s]?|cancer|diabetes|arthritis|autoimmune|chronic|illness|condition)\b',
     "Promotes a 'miracle oil/herb/plant' that cures diseases — genuine medical breakthroughs are published in peer-reviewed journals, not promoted in viral posts.",
     "Health"),
    (r'\b(miracle|secret).{0,15}(compound|substance|formula|remedy|herb|root|plant extract)\b',
     "Promotes a 'miracle compound' or 'secret substance' — genuine medical breakthroughs are published in peer-reviewed journals, not promoted in viral posts.",
     "Health"),
    # ── mRNA / vaccine alters DNA ────────────────────────────────────────────
    (r'\b(mrna|rna|covid.{0,5}vaccine[s]?|jab[s]?).{0,30}(alter[s]?|change[s]?|modif|rewrite[s]?|reprogramme?[sd]?|splice[s]?|edit[s]?).{0,20}(dna|gene[s]?|genome|genetic code)\b',
     "Claims mRNA vaccines alter human DNA — mRNA does not enter the cell nucleus and cannot change DNA; this is contradicted by basic molecular biology.",
     "Health"),
    # ── Vaccine contains HIV / graphene / prions ─────────────────────────────
    (r'\b(vaccine[s]?|jab[s]?|injection[s]?|shot[s]?).{0,30}(contain[s]?|inject[s]?|laced with|include[s]?|full of).{0,20}(hiv|aids|prion[s]?|graphene|heavy metal[s]?|luciferase|parasite[s]?)\b',
     "Claims vaccines contain HIV, prions, or graphene — thoroughly debunked; no such material has been found in authorised vaccines.",
     "Health"),
    # ── Martial law secretly declared ────────────────────────────────────────
    (r'\b(martial law).{0,30}(secretly|quietly|covertly|silently).{0,20}(declared|enacted|imposed|activated|signed)\b',
     "Claims martial law was secretly declared — a recurring viral hoax with no basis in any official government record.",
     "Political"),
    # ── Temperature / climate data fabricated ────────────────────────────────
    (r'\b(climate|temperature|nasa|noaa|ipcc).{0,20}(data|record[s]?|figure[s]?|measurement[s]?).{0,25}(fabricat|manipulat|falsif|fudg|tampered|adjusted to deceive|made up)\b',
     "Claims climate or temperature data were fabricated by scientific agencies — rejected by multiple independent data audits.",
     "Conspiracy"),
    (r'\b(fabricat|manipulat|falsif|fudg|tampered|made up).{0,30}(temperature|climate|weather|sea level).{0,20}(record[s]?|data|figure[s]?|measurement[s]?)\b',
     "Claims that temperature or climate records were fabricated — contradicted by independent replication of climate data from multiple global sources.",
     "Conspiracy"),
    (r'\bscientists?.{0,20}(fabricat|falsif|manipulat|fudg).{0,30}(temperature|climate|record[s]?|data)\b',
     "Claims scientists fabricated climate or temperature data — a conspiracy allegation rejected by independent forensic audits of raw climate databases.",
     "Conspiracy"),
    # ── Free energy suppressed / inventor killed ─────────────────────────────
    (r'\b(free energy|perpetual motion|over.?unity|zero.?point energy|hydrogen.splitting|water.powered).{0,80}(suppress|hidden|secret|cover.?up|murder|assassinat|killed|found dead|silenced)\b',
     "Claims a free energy device was suppressed by corporations or its inventor was killed — not supported by any peer-reviewed physics evidence.",
     "Conspiracy"),
    (r'\b(inventor[s]?|scientist[s]?|creator[s]?|developer[s]?).{0,30}(killed|murdered|assassinated|silenced|disappeared?|found dead).{0,50}(free energy|suppressed energy|clean energy|hydrogen|water.powered|tesla|over.?unity)\b',
     "Claims an inventor was killed to suppress a free energy technology — a recurring conspiracy narrative with no verified evidence.",
     "Conspiracy"),
    (r'\b(big oil|oil compan|energy compan|petroleum).{0,30}(assassinat|killed?|murdered?|silence[sd]?|bought out|suppressed?).{0,30}(inventor|scientist|researcher|creator|developer|meyer|tesla)\b',
     "Claims Big Oil killed or suppressed an inventor of alternative energy technology — a recurring conspiracy theory with no verified evidence.",
     "Conspiracy"),
    # ── Smithsonian hiding ancient giants ────────────────────────────────────
    (r'\b(smithsonian|government|they).{0,30}(hiding|concealing|covered up|destroyed?|suppressed?).{0,30}(giant[s]?|ancient giant[s]?|nephilim|oversized human[s]?|elongated skull[s]?)\b',
     "Claims the Smithsonian or government is hiding evidence of ancient giants — a recurring pseudoarchaeological conspiracy with no verified physical evidence.",
     "Fabrication"),
    # ── 5G additional: blood-brain barrier, mind control, radiation scrutiny ──
    (r'\b(5g|5-g).{0,35}(blood.?brain barrier|mind control|surveillance|track people|embed chip|military weapon|directed energy)\b',
     "Claims 5G technology can cross the blood-brain barrier or be used for mind control — not supported by established neuroscience or telecommunications physics.",
     "Health"),
    (r'\b(5g tower[s]?|5g mast[s]?|5g antenna[s]?|5g infrastructure).{0,80}(radiation|microwave|side effect[s]?|health|harm|scrutiny|danger|risk|secret|installed)\b',
     "Claims 5G tower installations pose secret radiation risks or were installed to avoid public scrutiny — not supported by independent health or engineering evidence.",
     "Health"),
    # ── Satanic ritual abuse network ─────────────────────────────────────────
    (r'\b(satanic|satanist[s]?).{0,25}(ritual abuse|trafficking network|pedo|child sacrifice|blood ritual|worship network|cult)\b',
     "References a satanic ritual abuse network — a debunked moral panic; large-scale investigations have found no evidence of organised satanic abuse rings.",
     "Conspiracy"),
    (r'\b(secret society|secret.{0,10}(network|group|cult)).{0,25}(satanist[s]?|satanic|devil.worship|lucifer|sacrific)\b',
     "Claims a secret society of satanists controls events — a conspiracy trope with no verified evidence and documented real-world harms.",
     "Conspiracy"),
    # ── Twitter / social media shadow-ban leaked ─────────────────────────────
    (r'\b(leaked.{0,20}(call|audio|recording|email|document[s]?|memo)).{0,30}(shadow.?ban|censor|suppress|silence|throttle|blacklist).{0,40}(conservative[s]?|republican[s]?|trump|patriot[s]?|right.wing|anti.establishment|dissiden|voice[s]?|user[s]?)\b',
     "References a 'leaked' call or document showing political censorship — claims of coordinated shadow-banning have not been verified by independent technical audits.",
     "Conspiracy"),
    (r'\b(twitter|facebook|google|youtube|tech giant[s]?).{0,30}(executive[s]?|employee[s]?|insider[s]?).{0,30}(caught|leaked|admit[s]?|confess\w*).{0,30}(shadow.?ban|censor|suppress|blacklist)\b',
     "Claims platform executives were caught admitting to shadow-banning — no such internal confirmation has been independently verified.",
     "Conspiracy"),
    # ── Georgia Guidestones depopulation ─────────────────────────────────────
    (r'\b(georgia guidestone[s]?).{0,40}(depopulat|agenda|new world order|plan|blueprint|commandment|elites? (want|plan)|500 million)\b',
     "Interprets the Georgia Guidestones as a depopulation blueprint — the stones are a monument with unknown private origins; no credible evidence links them to any depopulation plan.",
     "Conspiracy"),
    # ── Leaked Vatican archives ───────────────────────────────────────────────
    (r'\b(leaked?.{0,10}(vatican|papal|holy see).{0,20}(archive[s]?|document[s]?|secret[s]?|record[s]?|scroll[s]?))\b',
     "Claims to reveal leaked Vatican archives or secret documents — no such leaks have been authenticated by historical or archival scholars.",
     "Conspiracy"),
    (r'\b(vatican|holy see|catholic church).{0,30}(hiding|suppressing|concealing|covering up).{0,30}(archive[s]?|ancient truth|alien|serpent|satanic|real history)\b',
     "Claims the Vatican is hiding suppressed historical or supernatural truths — a recurring conspiracy trope with no verified documentary evidence.",
     "Conspiracy"),
    # ── Sunscreen / SPF causes cancer deliberately ────────────────────────────
    (r'\b(sunscreen|sunblock|spf).{0,120}(deliberately|intentionally).{0,50}(cancer|carcinogen|profit|sick|dependent)\b',
     "Claims sunscreen was deliberately designed to cause cancer — not supported by any oncological or toxicological evidence.",
     "Health"),
    (r'\b(sunscreen|sunblock|spf).{0,25}(chemical[s]?|ingredient[s]?).{0,10}cause[s]?.{0,10}cancer\b',
     "Claims sunscreen chemicals cause cancer — not supported by oncological or toxicological evidence when referring to approved formulations.",
     "Health"),
    # ── Bill Gates / elite population reduction ───────────────────────────────
    (r'\b(bill gates|gates foundation|gates).{0,30}(reduce|depopulat|cull|eliminat).{0,25}(world population|global population|human population|population by \d+|90 percent|80 percent)\b',
     "Claims Bill Gates has stated a goal of reducing the global population — this misrepresents his public health statements on population stabilisation through healthcare.",
     "Conspiracy"),
    (r'\b(climate change|global warming|climate crisis).{0,50}(hoax|fabricated|fake|myth|scam|invented|manufactured|lie|psyop|conspiracy).{0,50}(by|to|for).{0,40}(globalist[s]?|elite[s]?|new world order|government|control|tax|agenda)\b',
     "Claims climate change is a fabricated conspiracy by globalists or elites — denied by overwhelming scientific consensus from every major scientific institution.",
     "Conspiracy"),
    (r'\b(globalist[s]?|elite[s]?).{0,30}(fabricated|invented|created|manufactured).{0,30}(crisis|hoax|scam|pandemic|climate|virus)\b',
     "Claims a crisis was fabricated or manufactured by globalists or elites — a blanket conspiracy narrative with no verified evidence.",
     "Conspiracy"),
    (r'\b(who|world health organization|cdc|nih|un\b|united nations|world economic forum|wef|davos).{0,50}(globalist|cabal|nwo|new world order|deep state).{0,30}(tool|arm|weapon|puppet|front|agenda)\b',
     "Labels WHO, UN, or WEF as a tool of globalists or the deep state — a debunked conspiracy framing designed to erode trust in international health and governance bodies.",
     "Conspiracy"),
    (r'\b(population control|depopulat).{0,40}(through|via|using|by).{0,40}(vaccine[s]?|injection[s]?|shot[s]?|medication[s]?|water|food|chemtrail|spray)\b',
     "Claims vaccines, water, or food are being used as tools for covert population control — a conspiracy theory with no scientific or verified basis.",
     "Conspiracy"),
    (r'\b(elite[s]?|globalist[s]?|un|world health|who|world economic forum|davos).{0,30}(plan|agenda|goal|aim).{0,30}(reduce|depopulat|cull|eliminat).{0,25}(world population|global population|human population|population)\b',
     "Claims global elites or institutions have a plan to reduce the world population — a debunked conspiracy theory with no verified documentary evidence.",
     "Conspiracy"),
    (r'\b5g.{0,50}(control|manipulat|mind.control|track|spread|transmit|activat|cause).{0,40}(people|citizen[s]?|population|covid|coronavirus|virus|disease|illness|symptom[s]?|cancer)\b',
     "Claims 5G technology is being used to control people, track citizens, or cause illness — a thoroughly debunked conspiracy theory with no scientific basis.",
     "Conspiracy"),
    (r'\b(5g|tower[s]?|antenna[e]?).{0,30}(microchip[s]?|nanochip[s]?|inject|vaccin|trigger|activat).{0,30}(people|citizen[s]?|population|human[s]?)\b',
     "Claims 5G towers activate implanted microchips or interact with vaccines — a viral conspiracy narrative with zero scientific evidence.",
     "Conspiracy"),
    (r'\b(rothschild[s]?|rockefeller[s]?|international bankers?).{0,40}(finance[d]?|fund[ed]?|bankroll[ed]?|paid for|backed).{0,40}(both sides?|world war|world wars?|axis|allies|nazi|soviet|wars for profit)\b',
     "Claims the Rothschild or Rockefeller families secretly financed both sides of world wars for profit — a centuries-old antisemitic conspiracy theory with no credible historical evidence.",
     "Conspiracy"),
    (r'\b(rothschild[s]?|rockefeller[s]?|soros|international bankers?).{0,50}(control[s]?|own[s]?|run[s]?|manipulat).{0,30}(central bank[s]?|all bank[s]?|world bank[s]?|financial system|global economy|governments?|media|elections?)\b',
     "Claims a family or network of bankers secretly controls all central banks, governments, or economies — a debunked antisemitic conspiracy theory.",
     "Conspiracy"),
    (r'\b(bill gates|gates foundation).{0,40}(mosquito|insect[s]?|bug[s]?).{0,40}(drone[s]?|inject|deliver|microchip|chip|nanochip|nanobot|tracking)\b',
     "Claims Bill Gates is using engineered mosquitoes or insect drones to inject microchips or tracking devices — a debunked conspiracy theory with no scientific basis.",
     "Conspiracy"),
    (r'\b(mosquito|insect).{0,20}(drone[s]?|robot[s]?).{0,30}(inject|deliver|microchip|chip|nanotechnology|tracking device)\b',
     "Claims mosquito or insect drones are being used to inject microchips or tracking devices — a viral conspiracy narrative with no credible scientific backing.",
     "Conspiracy"),
]

_MED_PATTERNS = [
    (r'\b(voter|election).{0,10}fraud\b',
     "Makes an election fraud claim — these require strong, court-verified evidence; most such claims have been found unsupported.",
     "Political"),
    (r'\b(shocking|explosive|bombshell|stunning).{0,20}(reveal[s]?|truth|proof|evidence|report[s]?|claim[s]?|allegation[s]?|data|finding[s]?|leak[s]?)\b',
     "Uses sensationalist language designed to trigger emotional reactions and bypass careful reading.",
     "Misleading"),
    (r'\b(unnamed|anonymous).{0,20}(sources?|official[s]?|insider[s]?|senior|researcher[s]?|expert[s]?|scientist[s]?|whistleblower[s]?|doctor[s]?|physician[s]?|nurse[s]?|medic[s]?|manager[s]?|analyst[s]?|adviser[s]?|advisor[s]?|banker[s]?|economist[s]?|consultant[s]?|trader[s]?|investor[s]?|executive[s]?|director[s]?|officer[s]?|hedge fund)\b',
     "Cites an unnamed or anonymous official, insider, researcher, or professional — credible journalism names its sources or explains why they must remain anonymous.",
     "Misleading"),
    (r'\b(secret|unnamed|insider).{0,10}report[s]?.{0,30}(shows?|reveals?|proves?|confirms?|indicates?|suggests?)\b',
     "References a 'secret report' as evidence — credible reporting cites named, verifiable documents; anonymous reports cannot be independently confirmed.",
     "Misleading"),
    (r'\bundisclosed.{0,25}(data|report[s]?|document[s]?|source[s]?|evidence|statistic[s]?|figure[s]?|record[s]?)\b',
     "References 'undisclosed data' — legitimate data sources are named and verifiable; undisclosed figures cannot be independently confirmed.",
     "Misleading"),
    (r'\b(85|90|95|99)\s*(%|percent).{0,20}(of all|of jobs|of people|of population|of users|of cases|of patients|of workers|of (?:bottled water|generic drug[s]?|supplement[s]?|vitamin[s]?|ingredient[s]?|product[s]?))\b',
     "Cites a suspiciously high percentage (85–99%) — extreme round numbers are often fabricated or taken out of context.",
     "Statistics"),
    (r'\bguaranteed to\b',
     "Uses 'guaranteed to' — very few real-world outcomes can be guaranteed; common marker of exaggerated content.",
     "Misleading"),
    (r'\bscientists (confirm|prove|revealed).{0,30}(secret|hidden|suppressed|what they)\b',
     "Claims scientists confirmed something previously hidden — always ask: which scientists, published where?",
     "Misleading"),
    (r'\b(exposed|insider[s]?).{0,20}(reveals?|leak(?:s|ed)?|expos(?:es|ed)?)\b',
     "References an anonymous 'insider' or 'exposed' leak — cannot be verified and commonly fabricated for false credibility.",
     "Conspiracy"),
    (r'\b(refuse|refusing) to investigate\b',
     "Claims authorities are 'refusing to investigate' — implies a cover-up without evidence of who refused or why.",
     "Conspiracy"),
    (r'\b(dramatically|massively).{0,20}(rises?|increases?|drops?|falls?|surges?|under.report\w*|over.report\w*|under.count\w*|cover[s]?\s+up)\b',
     "Uses dramatic language to describe trends without citing any data source — exaggeration is a common tool to distort reality.",
     "Statistics"),
    (r'\baccording to (unnamed|anonymous|secret) sources?\b',
     "Cites unnamed or anonymous sources — credible journalism identifies its sources or explains why they must stay anonymous.",
     "Misleading"),
    (r'\b(100\s*(%|percent)|completely|totally).{0,15}(proven|confirmed|guaranteed|eliminate[sd]?|prevent[sd]?|cure[sd]?|stop[ps]?|safe)\b',
     "Claims something is '100% proven' or completely guaranteed — scientific and journalistic findings almost never use such absolute language.",
     "Misleading"),
    (r'\bunnamed (study|research|report).{0,10}(shows?|suggests?|finds?|found|reveals?|proves?|confirms?)\b',
     "References an unnamed or uncited study — readers should always be able to look up any cited study.",
     "Misleading"),
    (r'\b(8[5-9]|9\d|100)\s*(%|percent).{0,20}(better|improvement|reduction|increase|decrease|healthier|boost|more likely|less likely|effective)\b',
     "Cites a suspiciously high percentage improvement (85–100%) without naming a source — extreme precise-sounding figures without citations are often invented.",
     "Statistics"),
    (r'\bscientists? (confirm[s]?|say[s]?|claim[s]?|find[s]?|found|report[s]?).{0,80}(8[5-9]|9\d|100)\s*(%|percent)\b',
     "Cites a high percentage claim attributed vaguely to 'scientists' without naming a specific peer-reviewed study — a technique used to make unsupported figures appear credible.",
     "Statistics"),
    (r'\b(deceased|dead).{0,15}voter[s]?\b',
     "Claims deceased or dead people voted — serious allegations that require court-verified forensic evidence to be credible.",
     "Political"),
    (r'\b(mail.in|absentee).{0,10}ballot[s]?.{0,30}(deceased|dead|fraud|fake|forged|illegal|invalid)\b',
     "Makes unsupported mail-in or absentee ballot fraud claims — investigations in every state have found such claims unsubstantiated.",
     "Political"),
    (r'\b(election official[s]?|official[s]?).{0,20}(refused?|refusing|won.t|will not).{0,20}(audit|investig|recount)\b',
     "Accuses election officials of refusing accountability without naming the officials or providing evidence.",
     "Political"),
    (r'\b(reverse[sd]?|eliminat[eing]+|cure[sd]?).{0,15}(type.?[12]|type ii|type 2|diabetes|alzheimer[s]?|parkinson[s]?).{0,30}(month[s]?|week[s]?|day[s]?|year[s]?)\b',
     "Claims a dietary change can reverse a chronic disease within a specified time — not supported by current medical evidence.",
     "Health"),
    (r'\bdoctor[s]?.{0,30}(ignoring|dismissing|hiding|suppressing).{0,20}(breakthrough|cure|treatment|evidence)\b',
     "Suggests doctors are suppressing a medical breakthrough — legitimate new treatments go through clinical trials and peer review.",
     "Health"),
    (r'\b(eliminate|wipe out|destroy|kill).{0,20}(90|80|70|85|95|99)\s*%.{0,20}(job[s]?|work|employment|worker[s]?)\b',
     "Claims AI or technology will eliminate an extreme proportion of jobs by a specific date — most independent forecasts show displacement and transition, not near-total elimination.",
     "Statistics"),
    # ── Social-media / chain-letter patterns ─────────────────────────────────
    (r'\b(share (this|now|immediately)|forward (this )?to \d+|pass this (on|along)|send (this )?to \d+)\b',
     "Uses chain letter urgency language ('share now', 'forward to X people') — a classic technique to spread viral misinformation rapidly.",
     "Misleading"),
    (r'\b(your (?:whatsapp\s+)?(?:account|phone|number|whatsapp) will (be )?(deleted|banned|deactivated|blocked|removed))\b',
     "Claims an account or service will be terminated unless the message is forwarded — a textbook chain letter hoax with no basis in fact.",
     "Misleading"),
    (r'\b(must (share|forward|send)|please (share|forward)|share (this )?before (it.s|it is) (deleted|removed|banned))\b',
     "Urgently demands sharing before deletion — a manipulation tactic used in viral misinformation chains to create false urgency.",
     "Misleading"),
    # ── Future sports/political event presented as fact ───────────────────────
    # Fires when a past-tense outcome word appears near a clearly future year (2026+).
    # Emotional sports language alone (e.g. "disappointing defeat") is NOT flagged
    # because it is standard journalism for past events; the future year is the key
    # distinguishing signal.
    # ── Future sports/political event presented as fact ───────────────────────
    # Only fires for years 2027 and beyond — the current year (2026) is excluded
    # because events in the ongoing year can be legitimate real reports.
    # 2027+ is a safe threshold for "clearly hasn't happened yet".
    (r'\b(won|lost|defeated|beat|crashed\s+out|knocked\s+out|eliminated|exited|suffered.{0,35}(defeat|loss|exit)|had.{0,35}(defeat|loss|exit)|failed\s+to\s+(qualify|win|advance)|missed\s+out|fell\s+short|clinched|lifted|secured\s+the|claimed\s+the).{0,80}(202[7-9]|20[3-9]\d)\b',
     "Claims a sporting or political result as established fact for a year that is clearly in the future — presenting unverifiable future-dated outcomes as news is a classic misleading tactic.",
     "Misleading"),
    (r'\b(202[7-9]|20[3-9]\d).{0,80}(won|lost|defeated|beat|crashed\s+out|knocked\s+out|eliminated|exited|defeat|loss|exit|failed\s+to\s+(qualify|win|advance)|missed\s+out|fell\s+short|clinched|lifted|secured\s+the|claimed\s+the)\b',
     "References a sporting or political outcome in a clearly future year as if it has already occurred — unverifiable future-dated claims presented as news are misleading.",
     "Misleading"),
    # ── Known false outcome: India ODI/Cricket WC 2023 ──────────────────────
    # Australia won the 2023 ICC Men's Cricket World Cup (ODI). Any claim that
    # India won is factually wrong.
    # Matches both "India won the 2023 ICC Cricket World Cup" (won before tournament)
    # and "India...2023 ICC Cricket World Cup...won/defeating" (won after tournament).
    (r'\bindia\b.{0,30}(?:won|beat|defeat\w*|lifted?|claimed|secured).{0,80}(?:2023\s+icc\s+(?:(?:men.s|cricket)\s+)?world\s+cup|icc\s+(?:(?:men.s|cricket)\s+)?world\s+cup\s+2023|odi\s+world\s+cup\s+2023|2023\s+odi\s+world\s+cup|cricket\s+world\s+cup\s+2023)\b',
     "Australia won the 2023 ICC Cricket World Cup — any claim that India won this ODI tournament contradicts the verified result.",
     "Misleading"),
    (r'\bindia\b.{0,100}(?:2023\s+icc\s+(?:(?:men.s|cricket)\s+)?world\s+cup|icc\s+(?:(?:men.s|cricket)\s+)?world\s+cup\s+2023|odi\s+world\s+cup\s+2023|2023\s+odi\s+world\s+cup|cricket\s+world\s+cup\s+2023).{0,100}(?:won|beat|defeat\w*|lifted?|claimed|secured|champions?|clinched)\b',
     "Australia won the 2023 ICC Cricket World Cup — any claim that India won this ODI tournament contradicts the verified result.",
     "Misleading"),
    # ── Known false outcome: India T20 WC 2026 ───────────────────────────────
    # India won the ICC Men's T20 World Cup 2026. Any claim that India lost,
    # was knocked out, or missed the title in the 2026 T20 WC is factually wrong.
    (r'\bindia\b.{0,140}(?:icc\s+(?:men.s\s+)?t20\s+world\s+cup\s+2026|t20\s+world\s+cup\s+2026|2026\s+t20\s+world\s+cup|2026\s+icc\s+t20).{0,120}(?:defeat|defeat|loss|knocked\s+out|crashed\s+out|eliminated|fell\s+short|missed\s+out|failed\s+to\s+(?:win|secure|qualify)|did\s+not\s+win|missing\s+out)\b',
     "India won the ICC Men's T20 World Cup 2026 — any claim that India lost or was eliminated in this tournament contradicts the verified result.",
     "Misleading"),
    (r'\bindia\b.{0,140}(?:icc\s+(?:men.s\s+)?t20\s+world\s+cup\s+2026|t20\s+world\s+cup\s+2026|2026\s+t20\s+world\s+cup|2026\s+icc\s+t20).{0,120}(?:disappointing|heartbreaking|devastating|crushing|shocking)\s+(?:defeat|loss|exit|campaign)\b',
     "India won the ICC Men's T20 World Cup 2026 — describing India's 2026 T20 WC campaign as a defeat or loss is factually incorrect.",
     "Misleading"),
    # ── Unverified political/statistical superlatives ─────────────────────────
    (r'\b(least|most|worst|best).{0,20}(economically|socially|politically|financially).{0,20}(mobile|equal|stable|corrupt|developed|free)\b',
     "Makes a superlative comparative claim (least/most/worst/best) about societal conditions without citing a specific study or ranking source.",
     "Statistics"),
    (r'\b(number of jobs?|employment|unemployment).{0,25}(grew|increased|fell|dropped|declined|rose).{0,15}(only\s+)?(by\s+)?\d+\s*(%|percent)\b',
     "Cites a precise employment statistic without naming the data source — employment figures require specific citations to be verifiable.",
     "Statistics"),
]

# ---------------------------------------------------------------------------
# User-facing text
# ---------------------------------------------------------------------------

_RECOMMENDATIONS = {
    "Uncertain": (
        "The model could not confidently classify this text. "
        "It does not match strong deception patterns, but the overall signal is too ambiguous to give a reliable verdict. "
        "Consider submitting more context, or verify the claims manually against a trusted fact-checking source."
    ),
    "Highly Deceptive": (
        "Do not share this content. This appears to contain dangerous misinformation or conspiracy-level fabrication. "
        "Verify it on a trusted fact-checking site such as Snopes, FullFact, or AP Fact Check. "
        "For health claims, check the WHO or CDC. For political claims, look for official court records or government statements. "
        "Sharing this type of content can cause real harm to individuals and communities."
    ),
    "Misleading": (
        "Exercise caution before sharing this content. It may contain exaggerated statistics, "
        "unnamed or unverifiable sources, selective facts, or sensationalist framing. "
        "Search for the original source of any statistics or quotes, verify that any cited study actually exists "
        "and was published in a peer-reviewed journal, and read beyond the headline — "
        "the full context is often very different from how the claim is presented."
    ),
    "Legitimate": (
        "This content appears credible and well-sourced based on our analysis. "
        "As always, cross-reference important claims with at least one other independent source, "
        "and verify any statistics or quotes link back to the named organisation or publication. "
        "Good information hygiene is always worthwhile, even for content that seems reliable."
    ),
}

_ML_FALLBACK_REASONS = {
    "Highly Deceptive": (
        "The AI model found no specific red-flag phrases in this text, but the overall writing style "
        "strongly resembles fabricated or conspiracy-level content it was trained on. The tone, "
        "word choice, emotional charge, and sentence structure are characteristic of known disinformation "
        "and deliberate deception."
    ),
    "Misleading": (
        "The AI model did not detect specific red-flag phrases, but the writing style "
        "closely matches content that misleads through exaggerated framing, vague sourcing, or selective facts. "
        "This often occurs when real information is spun in a distorting way — "
        "technically not entirely false, but presented to create a false impression."
    ),
    "Legitimate": (
        "No red-flag phrases or deceptive patterns were detected. The AI model assessed the writing style, "
        "tone, and structure as consistent with credible, well-sourced content. "
        "This does not guarantee factual accuracy — always verify important claims independently."
    ),
}

# ---------------------------------------------------------------------------
# Fact-check prompt (used for both RAG vector store and Wikipedia context)
# ---------------------------------------------------------------------------

_FACT_CHECK_PROMPT = """\
You are a strict fact-checker. A user submitted the following claim:

CLAIM: {claim}

Using ONLY the context passages below, classify the claim into EXACTLY ONE of these labels:
- Highly Deceptive → completely false, fabricated, debunked, a known conspiracy theory, or dangerous misinformation with no factual basis
- Misleading       → contains a grain of truth but is significantly exaggerated, missing critical context, uses unnamed sources, or is framed to create a false impression
- Legitimate       → factually accurate, well-sourced, and presented in a balanced and credible manner consistent with mainstream reporting

Context passages:
{context}

Reply on a SINGLE line in this exact format and nothing else:
LABEL | one-sentence reason

Where LABEL must be exactly one of: Highly Deceptive, Misleading, Legitimate
"""

# ---------------------------------------------------------------------------
# Wikipedia free-API search (no API key required)
# ---------------------------------------------------------------------------

def _wikipedia_search(query: str, max_results: int = 3) -> str:
    """
    Search Wikipedia's free REST API for snippets relevant to the query.
    Returns a context string, or '' if nothing useful is found.
    Uses only the `requests` library (already a project dependency).
    """
    try:
        resp = requests.get(
            "https://en.wikipedia.org/w/api.php",
            params={
                "action": "query",
                "list": "search",
                "srsearch": query,
                "format": "json",
                "srlimit": max_results,
                "srprop": "snippet",
            },
            timeout=6,
        )
        resp.raise_for_status()
        results = resp.json().get("query", {}).get("search", [])
        if not results:
            return ""

        parts = []
        for r in results:
            title = r.get("title", "")
            snippet = re.sub(r"<[^>]+>", "", r.get("snippet", "")).strip()
            if snippet:
                parts.append(f"Wikipedia – {title}: {snippet}")

        return "\n\n".join(parts)
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Lightweight Wikipedia claim check (no LLM required)
# ---------------------------------------------------------------------------

# Cache for wiki claim checks to avoid repeated HTTP calls for the same text
_WIKI_CHECK_CACHE: dict = {}

def _wiki_claim_check(text: str) -> tuple:
    """
    For short factual outcome claims (e.g. 'Pakistan won the T20 World Cup 2024'),
    query Wikipedia and check whether the claimed winner/outcome is confirmed.
    Does NOT require an LLM — uses window-based proximity matching only.

    Returns (label_override, reason) or (None, None) if no contradiction found
    or if the check is inconclusive.

    Only runs for texts <= 60 words.  Adds ~200-500 ms latency (network call).
    Results are cached to avoid repeated calls for identical inputs.
    """
    words = text.split()
    if len(words) > 60:
        return None, None

    if text in _WIKI_CHECK_CACHE:
        return _WIKI_CHECK_CACHE[text]

    # Detect result/outcome claims: "X won/beat/defeated/lost/scored ..."
    result_re = re.compile(
        r'\b([A-Z][a-zA-Z]+(?:\s+[A-Z]?[a-zA-Z]+){0,3})'   # claimed entity (1-4 words, starts uppercase)
        r'\s+'
        r'(?:won|beat|defeated|claimed|lifted|are\s+champion[s]?'
        r'|is\s+(?:the\s+)?champion|never\s+(?:won|made)|'
        r'(?:was|were)\s+(?:knocked out|eliminated|banned|not part)|'
        r'lost\s+(?:the\s+)?(?:final|match|game|title|cup|series)|'
        r'scored\s+\d+|'
        r'(?:has|have)\s+(?:never\s+)?won)',
        re.IGNORECASE,
    )
    m = result_re.search(text)
    if not m:
        _WIKI_CHECK_CACHE[text] = (None, None)
        return None, None

    claimed_entity = m.group(1).strip()
    # Sanity filter: skip very short/generic words (e.g. "India" is fine, "The" is not)
    if len(claimed_entity) < 3 or claimed_entity.lower() in {"the", "a", "an", "this", "that"}:
        _WIKI_CHECK_CACHE[text] = (None, None)
        return None, None

    wiki_context = _wikipedia_search(text, max_results=2)
    if not wiki_context or len(wiki_context) < 40:
        _WIKI_CHECK_CACHE[text] = (None, None)
        return None, None

    # Check: does the claimed entity appear near a win/result verb in Wikipedia?
    win_re    = re.compile(r'\b(won|defeated|beat|champion[s]?|victory|lifted|claimed|winner)\b', re.IGNORECASE)
    entity_re = re.compile(re.escape(claimed_entity), re.IGNORECASE)

    confirmed = False
    for em in entity_re.finditer(wiki_context):
        # Search a ±150 char window around each mention of the entity
        window = wiki_context[max(0, em.start() - 150): em.end() + 150]
        if win_re.search(window):
            confirmed = True
            break

    if not confirmed and win_re.search(wiki_context):
        # Wikipedia discusses an outcome for this event/topic but does NOT confirm
        # this entity as the winner → strong signal the claim is factually wrong.
        reason = (
            f"Wikipedia does not confirm '{claimed_entity}' as the winner or "
            "correct party in this event. This factual claim appears to contradict "
            "available reference sources — verify via official scorecards or news archives."
        )
        result = ("Misleading", reason)
        if len(_WIKI_CHECK_CACHE) < 500:
            _WIKI_CHECK_CACHE[text] = result
        return result

    if len(_WIKI_CHECK_CACHE) < 500:
        _WIKI_CHECK_CACHE[text] = (None, None)
    return None, None


# ---------------------------------------------------------------------------
# RAG + Wikipedia fact-check (primary signal)
# ---------------------------------------------------------------------------

def _fact_check_with_llm(text: str, context: str, llm) -> tuple:
    """Send context + claim to the LLM and parse the response into (label, reason)."""
    try:
        prompt = _FACT_CHECK_PROMPT.format(claim=text, context=context)
        response = llm.generate(prompt, max_tokens=150, temperature=0.1)

        if "|" in response:
            raw_label, reason = response.split("|", 1)
            raw_label = raw_label.strip()
            reason = reason.strip()
        else:
            raw_label = response.strip()
            reason = ""

        label = None
        for valid in LABELS:
            if valid.lower() in raw_label.lower():
                label = valid
                break

        return (label, reason) if label else (None, None)
    except Exception:
        return None, None


def _rag_fact_check(text: str, rag) -> tuple:
    """
    Fact-check a claim using the RAG pipeline.

    Priority:
      1. FAISS vector store  — uses documents you have ingested
      2. Wikipedia free API  — automatic fallback when the store has no relevant results

    Returns (label, reason, source) where source is 'vector_store' | 'wikipedia'.
    Returns (None, None, None) if neither source produces usable context.
    """
    source = None
    context = ""

    # 1 — Try the vector store first
    try:
        q_embedding = rag.encoder.encode(text, normalize=True)
        results = rag.store.search(q_embedding, top_k=5)
        results = [r for r in results if r["score"] > 0.30]

        if results:
            context = "\n\n".join(
                f"[{i}] (relevance {round(r['score'] * 100, 1)}%) {r['text']}"
                for i, r in enumerate(results, 1)
            )
            source = "vector_store"
    except Exception:
        pass

    # 2 — Fall back to Wikipedia if the store had nothing relevant
    if not context:
        context = _wikipedia_search(text)
        if context:
            source = "wikipedia"

    if not context:
        return None, None, None

    label, reason = _fact_check_with_llm(text, context, rag.llm)
    if label is None:
        return None, None, None

    return label, reason, source


# ---------------------------------------------------------------------------
# Sports / factual-claim guards
# Used to detect when the ML model's HD prediction is likely a fine-tuning
# artefact on sports data rather than a genuine conspiracy/fabrication signal.
# ---------------------------------------------------------------------------

_FACTUAL_SPORTS_RE = re.compile(
    r'\b(won|beat|defeated|scored|champion[s]?|gold medal|world cup|premier league|'
    r'champions league|grand slam|olympics|century|hat.trick|wimbledon|roland.garros|'
    r'world record|title|trophy|final|semi.final|quarter.final|'
    r'nba|ipl|t20|odi|test match|cricket|football|soccer|basketball|rugby|'
    r'formula.?1|f1|grand prix|superbowl|nfl|mlb|nhl|afl|nrl|'
    r'tour de france|wimbledon|us open|french open|australian open)\b',
    re.IGNORECASE,
)

# Well-known authoritative organisations / poll firms mentioned by name anywhere in the text.
# Used (with no_patterns + no conspiracy language) to guard against the ML model
# falsely classifying factual statistics from credible sources as Misleading.
_NAMED_SOURCE_RE = re.compile(
    r'\b(pew research|gallup|ipsos|statista|gartner|forrester|'
    r'world bank|imf|international monetary fund|oecd|united nations|eurostat|'
    r'census bureau|bureau of labor statistics|bls|federal reserve|'
    r'nasa|noaa|cdc|who\b|world health organization|fda|epa|nih|'
    r'reuters|bloomberg|bbc|associated press|ap\b|the guardian|'
    r'inpe|global fund|unicef|unhcr|world food programme|wfp|'
    r'oxfam|human rights watch|hrw\b|amnesty international|'
    r'transparency international|freedom house|save the children|'
    r'doctors without borders|msf\b|red cross|ifrc\b|'
    r'fao\b|food and agriculture organization|world food programme|'
    r'stanford university|harvard university|oxford university|cambridge university|'
    r'the lancet|nature\b|science\b|nejm|new england journal)\b',
    re.IGNORECASE,
)

_NO_CONSPIRACY_RE = re.compile(
    r'\b(illuminati|cabal|deep state|rothschild\w*|soros|new world order|cover.?up|'
    r'suppress\w*|microchip|5g|chemtrails?|flat earth|flat earthers?|crisis actors?|false flag|'
    r'secret (cure|document|plan|agenda)|leaked document|whistleblower reveals|'
    r'they don.t want|big pharma (hiding|suppress)|depopulat|bioweapon|'
    r'vaccine.{0,15}genocide|satanic|adrenochrome|wwg1wga|great awakening|qanon|'
    r'globalist[s]?|population control|forced vaccine[s]?|mandatory vaccine[s]?|'
    r'nwo\b|great reset|wef agenda|plandemic|scamdemic|plannedemic|'
    r'paedophile[s]?|pedophile[s]?|satanic.{0,10}(cabal|ritual|elite[s]?)|'
    r'evolution.{0,20}(lie|hoax|fraud|fake)|carbon dating.{0,20}(fraud|fake|lie))\b',
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Factual news detection — catches legitimate reporting that the ML model
# tends to mis-classify as Highly Deceptive due to intense/dramatic language
# in the training data (disaster reporting, space mission results, etc.)
# Only used to suppress ML-only HD predictions (no pattern matches).
# ---------------------------------------------------------------------------

_FACTUAL_NEWS_RE = re.compile(
    r'\b(nasa|spacex|esa|isro|noaa|jaxa|boeing|lockheed|arianespace).{0,40}(launch|caught|crossed|confirmed|successfully|achieved|complet|reported|announced)'
    r'|\b(wildfire[s]?|earthquake|hurricane|cyclone|tsunami|tornado|flood[s]?).{0,30}(destroy|devastat|damage|killed|casualties)'
    r'|\b(kill(?:ed|ing)|dead|death[s]?|casualties).{0,20}(at least|more than|approximately|about|nearly) \d+'
    r'|\b(spacecraft|satellite|rover|probe|mission).{0,30}(data|signal|crossing|interstellar|orbit|landed)'
    r'|\b(successfully|officially|confirmed by).{0,30}(caught|launched|landed|crossed|achiev|complet)'
    r'|\b(james webb|jwst|hubble|chandra|spitzer).{0,40}(discover|detect|captur|observ|reveal|image|spot|found)'
    r'|\b(exoplanet|black hole|neutron star|supernova|galaxy|nebula|asteroid|comet).{0,40}(discover|detected|found|observed|confirmed|record)'
    r'|\b(international criminal court|icc|hague tribunal).{0,40}(arrest warrant|ruling|issued|convicted|indicted|order)'
    r'|\b(senate|congress|parliament|house of representatives|lok sabha|rajya sabha).{0,30}(passed|voted|approved|allocated|signed|enacted)'
    r'|\b(supreme court|high court|federal court).{0,30}(ruled|upheld|struck down|overturned|decision|verdict)'
    r'|\b(ancient|fossil|archaeological|prehistoric).{0,30}(species|remain|skeleton|discovered|uncovered|found|unearthed)'
    r'|\b(at least|more than|approximately|nearly|around)\s+\d+.{0,25}(killed|dead|died|casualties|deaths?\b)'
    r'|\b(earthquake|flood|hurricane|cyclone|tsunami|wildfire|disaster|storm).{0,50}(killed|dead|died|toll|casualties)'
    r'|\b(holocaust|shoah|genocide|ethnic cleansing|rwandan genocide|armenian genocide).{0,50}(killed|murdered|died|victims|death toll|estimated|approximately)'
    r'|\b(hiroshima|nagasaki|atomic bomb|nuclear bomb).{0,40}(killed|died|death[s]?|casualties|victims)'
    r'|\b(world war (i|ii|one|two|1|2)|wwi\b|wwii\b).{0,40}(killed|died|death toll|casualties|million[s]?)'
    r'|\b(snowden|wikileaks|pentagon papers?|ellsberg|chelsea manning|julian assange).{0,40}(revealed?|leaked?|published|exposed?|showed?|disclosed?)'
    r'|\b(mkultra|mk.ultra|cointelpro|operation northwoods|operation mockingbird|prism).{0,30}(was|surveillance|program|documents?|revealed|experiments?|confirmed|operations?)'
    r'|\b(according to|per).{0,10}(the bible|the quran|the torah|the koran|scripture|the hadith|religious texts?)'
    r'|\b(the bible|biblical|quran|quran\b|scripture|the torah).{0,30}(says?|states?|teaches?|describes?|records?)'
    r'|\b(killed|murdered|died|victims|death toll|massacred).{0,50}(holocaust|shoah|genocide|ethnic cleansing|rwandan genocide|armenian genocide)'
    r'|\b(nazi|nazis|third reich|nazi regime|adolf hitler|ss troops).{0,60}(murdered|killed|exterminated|persecuted|six million|death camp[s]?)'
    r'|\b(six million|five million|eleven million).{0,20}(jews|jewish people|tutsi|victims|people).{0,30}(killed|murdered|died|holocaust|genocide)'
    r'|\b(in my opinion|i believe that|my view is|from my perspective|personally,|imo\b).{0,60}(government|policy|failed|wrong|right|better|worse)'
    r'|\b(many|most|some|several).{0,10}(economists?|analyst[s]?|expert[s]?|scientists?|academics?|researchers?|commentators?|historians?).{0,30}(believe|say|argue|think|suggest|warn|note|argue that)'
    r'|\b(critics?|commentators?|analysts?|opposition leaders?|opposition parties?).{0,30}(argue|say|claim|accuse|allege|criticize|warn)'
    r'|\b(the onion|babylon bee|daily mash|private eye|the beaverton|the chaser).{0,30}(reports?|publishes?|wrote|writes?|satirizes?|jokes?)'
    r'|\b(satirical|satire|parody).{0,20}(piece|article|show|report|column|post|publication|newspaper|magazine)'
    r'|\b(go to bed hungry|food insecure|malnourish\w*|living in (extreme )?poverty|lacking access to food|suffer from hunger)',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Pattern scoring helpers
# ---------------------------------------------------------------------------

_AUTH_SOURCE_RE = re.compile(
    r'\b(according to|per|data from|reported by|published (?:in|by)|study (?:in|by)|as reported by)\s+'
    r'(?:the\s+)?(?:who|world health organization|cdc|centers for disease control|'
    r'world bank|united nations|un\b|nasa|noaa|ipcc|oxford|harvard|stanford|mit|'
    r'nhs|nih|national institutes of health|the lancet|nature|science magazine|'
    r'peer.reviewed|american medical association|ama|'
    r'bureau of labor statistics|bls|international monetary fund|imf|oecd|'
    r'inpe|global fund|eurostat|census bureau|world trade organization|wto|'
    r'centers for medicare|medicaid|fda|epa|who global|'
    r'oxfam|human rights watch|hrw|amnesty international|red cross|unicef|unhcr|'
    r'reuters|ap|associated press|bbc|new york times|washington post|guardian|'
    r'pew research|gallup|ipsos|statista|bloomberg)\b',
    re.IGNORECASE,
)

def _deception_score(text: str) -> tuple:
    """Return (high_matches, med_matches) — each a list of (reason, category)."""
    t = text.lower()
    high = [(reason, cat) for pat, reason, cat in _HIGH_PATTERNS if re.search(pat, t)]

    # If a named authoritative source is cited, suppress Statistics MED patterns —
    # legitimate cited statistics (e.g. "85% of lung cancer cases, per WHO") would
    # otherwise trip the unverified-percentage patterns.
    has_auth_source = bool(_AUTH_SOURCE_RE.search(text))
    med = [
        (reason, cat) for pat, reason, cat in _MED_PATTERNS
        if re.search(pat, t) and not (has_auth_source and cat == "Statistics")
    ]
    return high, med


def _infer_type(high: list, med: list, rag_source: str = None) -> str:
    """Return a short content-type label."""
    if rag_source == "wikipedia":
        return "Fact-Checked via Wikipedia"
    if rag_source == "vector_store":
        return "Fact-Checked via Knowledge Base"

    cats = [c for _, c in high] + [c for _, c in med]
    if not cats:
        return "General Claim"
    priority = ["Health", "Political", "Fabrication", "Conspiracy", "Statistics", "Misleading"]
    for p in priority:
        if p in cats:
            return f"{p} Misinformation"
    return f"{cats[0]} Misinformation"


# ---------------------------------------------------------------------------
# Standalone Groq + Wikipedia fact-check
# Activated when GROQ_API_KEY is set but no RAG pipeline is initialised.
# Gives LLM-quality fact-checking for sports/factual claims without needing
# the full RAG vector store to be set up.
# ---------------------------------------------------------------------------

_groq_llm_instance = None   # lazy singleton
_groq_init_failed  = False  # avoid retrying a broken key on every request


def _get_standalone_groq():
    """
    Return a GroqProvider if GROQ_API_KEY is set, else None.
    Result is cached after the first successful init.
    """
    global _groq_llm_instance, _groq_init_failed
    if _groq_llm_instance is not None:
        return _groq_llm_instance
    if _groq_init_failed:
        return None

    api_key = os.getenv("GROQ_API_KEY", "").strip()
    if not api_key:
        return None

    try:
        from src.rag.llm_provider import GroqProvider
        _groq_llm_instance = GroqProvider(api_key=api_key)
        print("[Predict] Standalone Groq LLM ready for sports/factual claim checking.")
        return _groq_llm_instance
    except Exception as e:
        print(f"[Predict][WARN] Could not initialise standalone Groq LLM: {e}")
        _groq_init_failed = True
        return None


_HD_VERIFY_PROMPT = """\
You are a misinformation classifier. Carefully read the text below and decide \
whether it is ACTIVELY PROMOTING a conspiracy theory or dangerous misinformation, \
OR whether it is legitimate journalism/academic content that merely REFERENCES, \
QUOTES, or DEBUNKS such content.

TEXT:
\"\"\"{text}\"\"\"

Classify as EXACTLY ONE of:
- Highly Deceptive → the text itself asserts, spreads, or endorses a conspiracy \
theory or dangerous falsehood as if it were true
- Misleading       → contains exaggeration, selective framing, or unverified claims \
but is not outright conspiracy-level fabrication
- Legitimate       → credible reporting, academic analysis, or fact-checking that \
quotes or discusses misinformation without promoting it

Reply on a SINGLE line in this exact format:
LABEL | one-sentence reason

Where LABEL must be exactly one of: Highly Deceptive, Misleading, Legitimate
"""


def _groq_verify_hd(text: str) -> tuple:
    """
    Ask Groq to verify a Highly Deceptive verdict.

    Used when pattern matching or ML fires HD but no RAG context is available.
    Catches false positives where legitimate journalism quotes conspiracy language.

    Returns (downgrade_label, reason) if Groq disagrees with HD,
    or (None, None) if Groq confirms HD / is unavailable.
    Only runs for texts <= 300 words to keep latency acceptable.
    """
    if len(text.split()) > 300:
        return None, None

    groq = _get_standalone_groq()
    if groq is None:
        return None, None

    try:
        prompt   = _HD_VERIFY_PROMPT.format(text=text)
        response = groq.generate(prompt, max_tokens=120, temperature=0.1)

        if "|" in response:
            raw_label, reason = response.split("|", 1)
            raw_label = raw_label.strip()
            reason    = reason.strip()
        else:
            raw_label = response.strip()
            reason    = ""

        for valid in LABELS:
            if valid.lower() in raw_label.lower():
                if valid != "Highly Deceptive":
                    # Groq disagrees — return the downgrade label
                    return valid, reason
                # Groq agrees — stay HD
                return None, None

    except Exception:
        pass

    return None, None


def _standalone_wikipedia_fact_check(text: str) -> tuple:
    """
    Wikipedia search → Groq LLM verdict.

    Works without a RAG pipeline — used as a smarter replacement for the
    regex-based _wiki_claim_check() when GROQ_API_KEY is available.

    Returns (label, reason) or (None, None) if inconclusive / LLM unavailable.
    Only runs for texts <= 80 words.
    """
    if len(text.split()) > 80:
        return None, None

    groq = _get_standalone_groq()
    if groq is None:
        return None, None

    context = _wikipedia_search(text, max_results=3)
    if not context or len(context) < 40:
        return None, None

    return _fact_check_with_llm(text, context, groq)


# ---------------------------------------------------------------------------
# Prediction cache — avoids re-running full inference on identical inputs.
# Only active when rag=None (RAG state can change between calls).
# Capped at 1000 entries; cleared entirely when full to keep memory bounded.
# ---------------------------------------------------------------------------

_PREDICT_CACHE: dict = {}


# ---------------------------------------------------------------------------
# Main prediction function
# ---------------------------------------------------------------------------

def predict(text: str, rag=None):
    """
    Returns (label, confidence, reasons, recommendation, content_type).

    Pipeline:
      1. Run DistilBERT classifier + deception pattern matching (always).
      2. If a RAGPipeline is provided, fact-check the claim:
           a. Search the FAISS vector store for relevant ingested documents.
           b. If none found, fall back to Wikipedia's free API automatically.
         The LLM verdict becomes the primary label; deception patterns can
         still escalate it but never de-escalate it.
      3. If no RAG / no context found, the ML + pattern decision is used.
    """
    if not text or not text.strip():
        return "Invalid Input", 0.0, [], "", ""

    if len(text.split()) > 300:
        text = " ".join(text.split()[:300])

    # Non-English detection — model is English-only; flag non-English clearly.
    # Require >= 12 words before running langdetect: very short texts (sports results,
    # brief headlines) produce frequent false positives (e.g. English text detected
    # as Danish or Afrikaans) due to too few tokens for reliable detection.
    if _LANGDETECT_AVAILABLE and len(text.split()) >= 12:
        try:
            lang = _lang_detect(text)
            if lang != "en":
                return (
                    "Uncertain",
                    0.0,
                    [f"Input appears to be non-English (detected language: '{lang}'). "
                     "This model is trained on English text only and cannot reliably classify other languages."],
                    "Please submit English-language text for accurate analysis.",
                    "Non-English Input",
                )
        except Exception:
            pass

    # Cache hit — skip inference entirely for repeated identical inputs
    _cache_key = text if rag is None else None
    if _cache_key and _cache_key in _PREDICT_CACHE:
        return _PREDICT_CACHE[_cache_key]

    # ── DistilBERT inference ────────────────────────────────────────────────
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=128,
    )
    with torch.no_grad():
        probs = F.softmax(model(**inputs).logits, dim=1)[0]

    p_highly_deceptive = probs[0].item()
    p_misleading       = probs[1].item()
    p_legitimate       = probs[2].item()
    p_fake    = p_highly_deceptive + p_misleading
    ml_class  = torch.argmax(probs).item()   # 0, 1, or 2

    # ── Deception pattern matching ──────────────────────────────────────────
    high, med = _deception_score(text)

    # Debunking / reporting context guard.
    # Fact-checking articles and academic reporting quote the false claim they are
    # examining, which causes HIGH and MED patterns to fire even though the text
    # itself is legitimate.  When strong debunking or journalistic-reporting language
    # is detected, suppress ALL pattern matches and rely on the ML model alone.
    _DEBUNKING = re.compile(
        r'\b(debunked?|debunking|fact.check(?:er|s)?|politifact|snopes|fullfact'
        r'|(?:vaccine[s]?|shot[s]?|jab[s]?|5g|wifi|mmr|dtp|flu shot|covid shot).{0,15}(?:does? not|didn.t|cannot|can.t|do not) cause'
        r'|does not alter|cannot alter|did not alter|do not alter'
        r'|does not contain|do not contain|doesn.t contain|did not contain'
        r'|never contain|does not spread|cannot spread'
        r'|no (?:credible |scientific |peer.reviewed )?evidence'
        r'|disprov(?:en|ed)?|dispelled|refuted|contradicting'
        r'|rated.{0,20}(?:false|mostly false|pants on fire)'
        r'|scientists? debunked|researchers? found no|study found no'
        r'|confirmed.{0,5}(?:not|no link|safe|effective)'
        r'|demonetized|removed.{0,20}(?:posts?|channel|content|account)'
        r'|spreading (?:false|misinformation|disinfo)'
        r'|(?:examined?|studied?|analysed?|analyzed?|researched?|investigated?|explored?)\s+(?:why|how|what|whether).{0,60}(?:conspira\w+|theor\w+|belief\w*|distrust\w*|radicali\w*|misinfo\w*)'
        r'|documentary.{0,20}(?:conspira\w+|theor\w+|flat.earth|deep.state)'
        r'|spreading false claims|false claims about'
        r'|stated clearly|clarified that|confirmed that.{0,30}(?:not|no|false|safe)'
        r'|experts? (?:say|confirm|stress|warn).{0,30}(?:not|no|false|safe|debunked)'
        r'|the (?:report|investigation|inquiry|audit|tribunal|court|probe|inquest).{0,30}(?:detailed|found|revealed|concluded|documented|showed|established).{0,50}(?:cover.?up|suppression|misconduct|wrongdoing|fraud)'
        r'|(?:court|judge|tribunal|jury).{0,30}(?:ruled|found|determined|concluded).{0,30}(?:cover.?up|suppression|fraud|misconduct)'
        r'|(?:investigation|inquiry|audit|review).{0,30}(?:uncovered|exposed|found|identified).{0,30}(?:cover.?up|suppression|wrongdoing)'
        r'|(?:officials?|government|executive).{0,30}(?:admitted|confessed|acknowledged).{0,30}(?:cover.?up|suppression|misconduct|wrongdoing)'
        r'|(?:edward\s+)?snowden|wikileaks|julian\s+assange|chelsea\s+manning|daniel\s+ellsberg|pentagon\s+papers?'
        r'|(?:operation\s+northwoods|operation\s+gladio|operation\s+paperclip|operation\s+cointelpro|cointelpro|mkultra|mk.ultra).{0,50}(?:was|were|is|are|program|experiment|proposal|document|confirmed|rejected|revealed)'
        r'|(?:qanon|flat earth|anti.?vaxx?|conspiracy theorist[s]?|birther[s]?|truther[s]?).{0,25}(?:followers?|believers?|adherents?|supporters?|community|movement|members?).{0,50}(?:believe|claim|say|assert|allege|contend|think)'
        r'|(?:followers?|believers?|adherents?|supporters?).{0,20}(?:of qanon|of the flat earth|of the deep state|of conspiracy)\b)\b',
        re.IGNORECASE,
    )
    is_debunking = bool(_DEBUNKING.search(text))
    if is_debunking:
        high = []   # suppress HIGH patterns in debunking/reporting contexts
        med  = []   # suppress MED patterns too — avoids e.g. "election fraud" firing
                    # in "court rejected the election fraud claim"

    word_count  = len(text.split())
    no_patterns = not high and not med

    # ── Step 1: RAG / Wikipedia fact-check ─────────────────────────────────
    rag_label = rag_reason = rag_source = None
    if rag is not None:
        rag_label, rag_reason, rag_source = _rag_fact_check(text, rag)

    if rag_label is not None:
        # Fact-check gave us a verdict — use it as the primary signal.
        # Hard deception patterns can escalate the label but never lower it.
        label = rag_label
        if high and label == "Legitimate":
            label = "Highly Deceptive"
        elif high and label == "Misleading":
            label = "Highly Deceptive"
        elif med and label == "Legitimate":
            label = "Misleading"

        label_idx  = LABEL_IDX[label]
        ml_agrees  = (ml_class == label_idx)
        base_prob  = probs[label_idx].item()
        # Higher confidence when the ML model agrees with the fact-check
        confidence = round(min((88 if ml_agrees else 72) + base_prob * 10, 99), 2)

        all_reasons = ([rag_reason] if rag_reason else []) + \
                      [r for r, _ in high] + [r for r, _ in med]
        if not all_reasons:
            all_reasons = [_ML_FALLBACK_REASONS[label]]

    else:
        # ── Step 2: ML + pattern fallback ──────────────────────────────────

        # Uncertain: trigger when no patterns fired AND either:
        #   a) model is genuinely confused (max_prob < 0.25 — below random chance
        #      for 3 classes), or
        #   b) input is too short to reliably classify (< 8 words)
        # Short phrases like "generate false news" have no real content for the
        # model to work with — it will confidently pick whatever class it associates
        # with the dominant word, which is meaningless.
        max_prob    = probs[ml_class].item()
        # Sports/factual claims are exempt from the short-text Uncertain guard —
        # "India won the ICC Champions Trophy 2013" (7 words) is a valid input.
        is_short    = word_count < 8 and not _FACTUAL_SPORTS_RE.search(text)
        is_confused = max_prob < 0.25

        if no_patterns and (is_short or is_confused):
            label      = "Uncertain"
            # For short inputs we override the model — show a low fixed confidence
            # rather than the model's raw probability, which would be misleading.
            confidence = round(max_prob * 40, 2) if is_short else round(max_prob * 100, 2)
            if is_short:
                reason_text = (
                    f"Input is too short ({word_count} word{'s' if word_count != 1 else ''}) "
                    "for a reliable verdict. Please provide a full sentence or paragraph."
                )
            else:
                reason_text = (
                    "No deception patterns were detected and the model's confidence is below "
                    f"the reliability threshold ({confidence:.0f}%). "
                    "The text may be ambiguous or stylistically unusual."
                )
            all_reasons = [reason_text]
            result = (label, confidence, all_reasons, _RECOMMENDATIONS["Uncertain"], "Low Confidence")
            if _cache_key:
                if len(_PREDICT_CACHE) >= 1000:
                    _PREDICT_CACHE.clear()
                _PREDICT_CACHE[_cache_key] = result
            return result

        # ── Factual / sports claim check ───────────────────────────────────
        # For short factual outcome claims (sports results, election outcomes,
        # scientific records) that produce no pattern matches, use Wikipedia
        # to fact-check.  Two tiers:
        #   1. Groq LLM + Wikipedia  — when GROQ_API_KEY is set (smarter,
        #      handles edge cases the regex matcher gets wrong).
        #   2. Regex proximity match — lightweight fallback when no LLM key.
        # This catches "Pakistan won the T20 World Cup 2024"-style factual
        # misinformation that style-based ML cannot detect.
        if no_patterns and word_count <= 80 and (ml_class == 2 or p_legitimate > 0.55):
            # Tier 1: Groq LLM + Wikipedia
            wiki_label, wiki_reason = _standalone_wikipedia_fact_check(text)

            # Tier 2: regex fallback if Groq unavailable or inconclusive
            if wiki_label is None and word_count <= 60:
                wiki_label, wiki_reason = _wiki_claim_check(text)

            if wiki_label is not None:
                label      = wiki_label
                confidence = round(min(p_fake * 100 + 15, 82), 2)
                all_reasons = [wiki_reason]
                recommendation = _RECOMMENDATIONS[label]
                content_type   = "Factual Claim (Wikipedia-checked)"
                result = (label, confidence, all_reasons, recommendation, content_type)
                if _cache_key:
                    if len(_PREDICT_CACHE) >= 1000:
                        _PREDICT_CACHE.clear()
                    _PREDICT_CACHE[_cache_key] = result
                return result

        # Downgrade HD→Misleading when the only high signal is "government/they hiding"
        # and the text ALSO cites an unnamed/anonymous source — that pattern is
        # sourced-attribution misinformation, not direct conspiracy fabrication.
        _anon_sourcing = bool(re.search(
            r'\b(unnamed|anonymous|according to (?:insider[s]?|source[s]?))\b',
            text, re.IGNORECASE,
        ))

        # Factual news guard: if no patterns fire AND the text looks like legitimate
        # news reporting (space missions, natural disasters, named authoritative
        # sources, legislative outcomes, etc.), don't let a high ML score override
        # — downgrade to Legitimate.
        is_factual_news = (
            no_patterns
            and not _NO_CONSPIRACY_RE.search(text)
            and (
                bool(_FACTUAL_NEWS_RE.search(text))
                or bool(_NAMED_SOURCE_RE.search(text))
            )
        )
        if is_factual_news:
            label      = "Legitimate"
            confidence = round(p_legitimate * 100, 2)
            all_reasons = [_ML_FALLBACK_REASONS["Legitimate"]]
            recommendation = _RECOMMENDATIONS["Legitimate"]
            content_type   = "General Claim"
            result = (label, confidence, all_reasons, recommendation, content_type)
            if _cache_key:
                if len(_PREDICT_CACHE) >= 1000:
                    _PREDICT_CACHE.clear()
                _PREDICT_CACHE[_cache_key] = result
            return result

        if (high and not _anon_sourcing) or (ml_class == 0 and p_highly_deceptive > 0.60 and not med and not is_debunking):
            # HIGH patterns always win; ML-only Highly Deceptive is suppressed when
            # MED patterns also fire (implies exaggeration rather than fabrication),
            # or when a debunking context has been detected.
            label      = "Highly Deceptive"
            confidence = round(min(p_fake * 100 + len(high) * 3, 99), 2)

            # ── Groq HD verification ────────────────────────────────────────
            # Ask Groq whether the text is genuinely promoting conspiracy content
            # or just referencing/quoting it (common false-positive source).
            # Only runs when: no RAG active, Groq key available, text ≤ 300 words.
            groq_downgrade, groq_reason = _groq_verify_hd(text)
            if groq_downgrade is not None:
                label      = groq_downgrade
                confidence = round(min(confidence * 0.75, 85), 2)   # lower confidence on a downgrade
                all_reasons = ([groq_reason] if groq_reason else []) + \
                              [r for r, _ in high] + [r for r, _ in med]
                recommendation = _RECOMMENDATIONS[label]
                content_type   = _infer_type(high, med)
                result = (label, confidence, all_reasons, recommendation, content_type)
                if _cache_key:
                    if len(_PREDICT_CACHE) >= 1000:
                        _PREDICT_CACHE.clear()
                    _PREDICT_CACHE[_cache_key] = result
                return result


        elif (med and p_legitimate < 0.97) \
                or (ml_class == 1 and (not no_patterns or p_misleading > 0.65) and not is_debunking) \
                or (ml_class != 2 and p_fake > 0.55 and not no_patterns):
            # MED patterns are suppressed when the ML model is >= 97% confident
            # the text is Legitimate — prevents false-positives on well-sourced text
            # that incidentally contains a matching phrase (e.g. a peer-reviewed stat).
            label      = "Misleading"
            confidence = round(p_fake * 100, 2)

        else:
            # Use the model's actual top prediction — no defaults.
            # Exception 1: no patterns + model confidence < 70% on non-Legitimate
            #   → fall back to Legitimate (avoids false positives on neutral text).
            # Exception 2: debunking context detected + no patterns remain
            #   → always Legitimate (the text is reporting on / refuting a claim,
            #     not asserting it — the model was trained on raw conspiracy text
            #     and may still assign high HD probability to quoted false claims).
            if (ml_class != 2 and no_patterns and probs[ml_class].item() < 0.70) \
                    or (is_debunking and no_patterns):
                label      = "Legitimate"
                confidence = round(p_legitimate * 100, 2)
            else:
                label      = LABELS[ml_class]
                confidence = round(probs[ml_class].item() * 100, 2)

        all_reasons = [r for r, _ in high] + [r for r, _ in med]
        if not all_reasons:
            all_reasons = [_ML_FALLBACK_REASONS[label]]

    recommendation = _RECOMMENDATIONS[label]
    content_type   = _infer_type(high, med, rag_source)

    result = (label, confidence, all_reasons, recommendation, content_type)

    # Store in cache (rag=None path only)
    if _cache_key:
        if len(_PREDICT_CACHE) >= 1000:
            _PREDICT_CACHE.clear()
        _PREDICT_CACHE[_cache_key] = result

    return result
