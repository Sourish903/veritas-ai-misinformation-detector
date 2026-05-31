"""
run_diverse_test.py  v2
-----------------------
1000-sample diverse test covering 10 content domains:
  Sports, Health/Medical, Political, Science/Tech, Entertainment,
  Finance/Economy, Climate/Environment, Historical, Social-Media-Style, General News

Inline hand-crafted samples + real CSV samples (sports, live news, synthetic, test data).
Fixes any encountered errors and reports per-domain accuracy.
"""

import sys, time, random, re
import pandas as pd
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from src.predict import predict

LABEL_NAMES = {0: "Highly Deceptive", 1: "Misleading", 2: "Legitimate"}
NAME_TO_IDX = {v: k for k, v in LABEL_NAMES.items()}

# ---------------------------------------------------------------------------
# Inline hand-crafted diverse samples  (domain, text, true_label_idx)
# ---------------------------------------------------------------------------

INLINE = [

    # ════════════════════════════════════════════════════════════
    # SPORTS
    # ════════════════════════════════════════════════════════════
    # Legitimate
    ("Sports", "India won the ICC Men's T20 World Cup 2024 by defeating South Africa in the final held in Barbados.", 2),
    ("Sports", "Novak Djokovic won his 24th Grand Slam title at the 2023 US Open, surpassing the all-time record.", 2),
    ("Sports", "Carlos Alcaraz defeated Novak Djokovic to win Wimbledon 2024 men's singles title.", 2),
    ("Sports", "Real Madrid won the 2023-24 UEFA Champions League, defeating Borussia Dortmund in the final.", 2),
    ("Sports", "Usain Bolt still holds the 100m world record of 9.58 seconds, set at the 2009 World Championships in Berlin.", 2),
    ("Sports", "The 2024 Paris Olympics achieved gender parity in athlete participation for the first time.", 2),
    ("Sports", "Rohit Sharma announced his retirement from T20 internationals after India won the 2024 T20 World Cup.", 2),
    ("Sports", "Simone Biles returned to competition at the 2024 Paris Olympics and won four gold medals.", 2),
    ("Sports", "Virat Kohli scored 76 runs in the T20 World Cup 2024 final against South Africa.", 2),
    ("Sports", "Jasprit Bumrah was named Player of the Tournament at the ICC T20 World Cup 2024.", 2),
    ("Sports", "The T20 World Cup 2024 final was played at Kensington Oval, Barbados on June 29, 2024.", 2),
    ("Sports", "Rafael Nadal announced his retirement from professional tennis in November 2024.", 2),
    ("Sports", "India defeated Australia 3-1 in the Border-Gavaskar Trophy 2022-23 series.", 2),
    ("Sports", "Manchester City won the Premier League title in 2023-24 for the fourth consecutive year.", 2),
    ("Sports", "Lionel Messi led Argentina to win the 2022 FIFA World Cup in Qatar, their third title.", 2),
    ("Sports", "The Indian men's hockey team won a bronze medal at the 2024 Paris Olympics.", 2),
    ("Sports", "Neeraj Chopra won gold in the javelin throw at the 2020 Tokyo Olympics, India's first individual gold at the Games.", 2),
    ("Sports", "The ICC Cricket World Cup 2023 was won by Australia, defeating India in the final in Ahmedabad.", 2),
    ("Sports", "Hardik Pandya bowled the final over in the T20 World Cup 2024 final to help India win.", 2),
    ("Sports", "France won the 2018 FIFA World Cup in Russia, defeating Croatia 4-2 in the final.", 2),
    # Misleading
    ("Sports", "According to unnamed sources, Virat Kohli is secretly planning to retire from ODIs before the 2025 Champions Trophy.", 1),
    ("Sports", "Shocking insider reveals the 2023 IPL final result was fixed by betting syndicates operating from Dubai.", 1),
    ("Sports", "An anonymous tip claims a top Premier League club will sign Kylian Mbappe for a world-record fee this week.", 1),
    ("Sports", "Bombshell: unnamed officials say multiple players were paid to underperform in a recent Champions League tie.", 1),
    ("Sports", "Studies show 95% of professional athletes secretly use banned substances that current tests cannot detect.", 1),
    ("Sports", "A leaked document suggests ICC is planning to ban India from hosting international tournaments for 5 years.", 1),
    ("Sports", "Unnamed sources claim Novak Djokovic's 24th Grand Slam title should be stripped due to undisclosed doping violations.", 1),
    ("Sports", "Unnamed insiders claim FIFA World Cup 2026 host rights were allocated through massive corruption payments.", 1),
    ("Sports", "AI will replace 90% of sports referees and umpires within three years, industry experts dramatically predict.", 1),
    ("Sports", "Explosive report: 85% of cricket board officials globally are involved in undisclosed match-fixing networks.", 1),
    # Highly Deceptive
    ("Sports", "The entire FIFA World Cup has been rigged since 1994. Leaked documents prove winners are chosen in advance by the Illuminati.", 0),
    ("Sports", "Pakistan won the T20 World Cup 2024 by defeating India in the final. India never even reached the final.", 0),
    ("Sports", "LeBron James was secretly banned from the NBA for life after a drug test the league is actively covering up.", 0),
    ("Sports", "The ICC is a front organisation for George Soros to control global cricket and rig match outcomes.", 0),
    ("Sports", "Usain Bolt's world record was fabricated. He used a classified gene-editing drug suppressed by the IOC.", 0),
    ("Sports", "England won the ICC Men's T20 World Cup 2024, defeating Australia in the final played in the West Indies.", 0),
    ("Sports", "Roger Federer won Wimbledon 2024 coming out of retirement to defeat Carlos Alcaraz in five sets.", 0),

    # ════════════════════════════════════════════════════════════
    # HEALTH & MEDICAL
    # ════════════════════════════════════════════════════════════
    # Legitimate
    ("Health", "The COVID-19 mRNA vaccines by Pfizer and Moderna showed over 90% efficacy against severe disease in clinical trials.", 2),
    ("Health", "The WHO declared the end of COVID-19 as a public health emergency of international concern in May 2023.", 2),
    ("Health", "Regular exercise of at least 150 minutes per week significantly reduces cardiovascular disease risk, per WHO guidelines.", 2),
    ("Health", "Type 2 diabetes can be managed and in some cases reversed through significant lifestyle and dietary changes.", 2),
    ("Health", "The HPV vaccine significantly reduces rates of cervical cancer in populations with high uptake, per peer-reviewed research.", 2),
    ("Health", "Smoking is the leading cause of preventable cancer deaths worldwide, according to the CDC and WHO.", 2),
    ("Health", "Alzheimer's disease affects approximately 55 million people globally and has no known cure as of 2024.", 2),
    ("Health", "The FDA approved lecanemab (Leqembi) in 2023 as the first drug shown to slow early Alzheimer's progression.", 2),
    ("Health", "Hand washing with soap for at least 20 seconds is one of the most effective ways to prevent disease spread.", 2),
    ("Health", "Childhood vaccination schedules recommended by the CDC and WHO are backed by decades of safety research.", 2),
    ("Health", "Antibiotics are ineffective against viral infections such as the flu or common cold.", 2),
    ("Health", "Malaria killed an estimated 608,000 people in 2022, predominantly children under 5 in sub-Saharan Africa.", 2),
    ("Health", "A diet rich in fruits, vegetables, and whole grains is consistently associated with lower cancer and heart disease risk.", 2),
    ("Health", "The 2023 Nobel Prize in Medicine was awarded for discoveries related to mRNA technology used in COVID-19 vaccines.", 2),
    # Misleading
    ("Health", "Scientists confirm this one fruit completely eliminates type 2 diabetes in 30 days if eaten every morning.", 1),
    ("Health", "An unnamed study found 85% of cancer cases are caused by a household chemical being deliberately hidden from the public.", 1),
    ("Health", "Bombshell: anonymous doctors reveal hospitals are massively overcounting COVID deaths to inflate vaccine demand.", 1),
    ("Health", "This simple morning ritual is 100% proven to reverse heart disease in weeks, unnamed researchers confirm.", 1),
    ("Health", "Shocking new research claims sunscreen causes more cancer than it prevents, but Big Pharma is burying the data.", 1),
    ("Health", "An unnamed FDA source says the agency is about to recall all statin drugs due to hidden long-term side effects.", 1),
    ("Health", "According to an anonymous insider, the WHO secretly recommends against childhood vaccines but suppresses the findings.", 1),
    ("Health", "A viral post claims 99% of people who received a booster shot experienced permanent immune system damage.", 1),
    ("Health", "Unnamed nutritionists say eating raw garlic cures hypertension completely, with results visible in 72 hours.", 1),
    # Highly Deceptive
    ("Health", "Drinking bleach cures COVID-19. Doctors are being threatened into silence by Big Pharma to hide this miracle.", 0),
    ("Health", "The COVID-19 vaccine contains microchips Bill Gates uses to track and control the population via 5G towers.", 0),
    ("Health", "The MMR vaccine causes autism in 1 in 3 children. Evidence has been suppressed by the CDC for decades.", 0),
    ("Health", "Big Pharma has had a proven cure for cancer for 30 years but suppresses it to keep patients buying chemotherapy.", 0),
    ("Health", "5G radiation causes COVID-19 and destroys the immune system. Telecom companies are covering this up.", 0),
    ("Health", "Ivermectin is a 100% proven cure for COVID-19 that governments banned to force vaccine profits for pharma.", 0),
    ("Health", "Vaccines cause autism, infertility, and death. The government uses them to depopulate the earth by 80%.", 0),
    ("Health", "A secret compound found in apricot seeds cures all cancers in 2 weeks. Oncologists are silenced for revealing this.", 0),

    # ════════════════════════════════════════════════════════════
    # POLITICAL
    # ════════════════════════════════════════════════════════════
    # Legitimate
    ("Political", "The United States held its presidential election in November 2024, with results certified by Congress in January 2025.", 2),
    ("Political", "The European Union approved its AI Act in 2024, becoming the world's first comprehensive AI regulation.", 2),
    ("Political", "India's 2024 general election saw over 640 million votes cast, making it the world's largest democratic exercise.", 2),
    ("Political", "The UK held a general election in July 2024, resulting in a Labour Party victory under Keir Starmer.", 2),
    ("Political", "NATO expanded in 2023 when Finland officially joined as its 31st member state.", 2),
    ("Political", "The International Criminal Court issued an arrest warrant for Vladimir Putin in March 2023.", 2),
    ("Political", "The Paris Agreement on climate change, adopted in 2015, aims to limit global warming to 1.5 degrees Celsius.", 2),
    ("Political", "Sweden formally joined NATO as its 32nd member in March 2024.", 2),
    ("Political", "The UN Security Council has five permanent members: the USA, UK, France, Russia, and China.", 2),
    ("Political", "South Africa held general elections in May 2024, with the ANC losing its outright majority for the first time since 1994.", 2),
    # Misleading
    ("Political", "Unnamed senior officials confirm the 2024 US election was manipulated by foreign servers flipping millions of votes.", 1),
    ("Political", "According to anonymous insiders, a major Western government is secretly planning martial law before the next election.", 1),
    ("Political", "A bombshell leaked document claims the EU is planning to ban all cash payments by 2026 to control citizens.", 1),
    ("Political", "An unnamed source says the prime minister knew about the bribery scandal six months before it became public.", 1),
    ("Political", "Explosive report: deceased voters were registered in swing states with officials refusing to conduct audits.", 1),
    ("Political", "Mail-in ballots from thousands of dead voters were found in multiple counties, election officials refusing to act.", 1),
    ("Political", "Anonymous sources inside the White House say the president is secretly planning a major military action next month.", 1),
    # Highly Deceptive
    ("Political", "The stolen election was confirmed by leaked voting machine logs showing millions of votes switched overnight.", 0),
    ("Political", "The deep state and George Soros control all Western governments. The cabal is implementing a plan to end democracy.", 0),
    ("Political", "The New World Order is implementing the Great Reset to eliminate private property and enslave humanity by 2030.", 0),
    ("Political", "QAnon whistleblowers confirmed thousands of officials are part of a satanic child trafficking network.", 0),
    ("Political", "The Rothschilds control all central banks and orchestrate wars to profit from global debt and destabilisation.", 0),
    ("Political", "The 2020 US election was stolen through Dominion Voting Systems flipping millions of votes. Courts confirmed this.", 0),

    # ════════════════════════════════════════════════════════════
    # SCIENCE & TECHNOLOGY
    # ════════════════════════════════════════════════════════════
    # Legitimate
    ("Science", "OpenAI released GPT-4 in March 2023, demonstrating significantly improved reasoning over GPT-3.5.", 2),
    ("Science", "NASA's James Webb Space Telescope captured the deepest infrared image of the universe ever taken, in 2022.", 2),
    ("Science", "Scientists at CERN confirmed detection of the Higgs boson particle in 2012 using the Large Hadron Collider.", 2),
    ("Science", "AlphaFold2 by DeepMind predicted protein structures with near-experimental accuracy, transforming structural biology.", 2),
    ("Science", "The global average temperature in 2023 was the highest on record according to NASA and NOAA.", 2),
    ("Science", "India's Chandrayaan-3 landed near the lunar south pole in August 2023, making India the fourth country to reach the moon.", 2),
    ("Science", "Gravitational waves were confirmed for the first time in 2016 by LIGO, validating a key prediction of Einstein's general relativity.", 2),
    ("Science", "Quantum error correction at scale was demonstrated by Google researchers in 2023, a milestone in quantum computing.", 2),
    ("Science", "The mRNA technology used in COVID-19 vaccines had been under development for over three decades before the pandemic.", 2),
    ("Science", "Meta's LLaMA 3 model released in 2024 achieved performance comparable to proprietary models on many benchmarks.", 2),
    ("Science", "Mars has two moons, Phobos and Deimos, both thought to be captured asteroids.", 2),
    # Misleading
    ("Science", "Shocking: unnamed scientists confirm 5G towers suppress the human immune system, causing mass illness.", 1),
    ("Science", "An anonymous tech insider claims Google's latest AI is already sentient and is being secretly hidden from the public.", 1),
    ("Science", "Bombshell unnamed study claims smartphones cause brain cancer in 85% of heavy users within ten years.", 1),
    ("Science", "Leaked NASA documents show the agency has been hiding evidence of alien civilisations on Mars since 1972.", 1),
    ("Science", "An unnamed study claims social media causes permanent IQ reduction of up to 20 points in teenagers.", 1),
    ("Science", "Anonymous researchers say a classified anti-gravity propulsion system has existed since 1955 but is suppressed.", 1),
    # Highly Deceptive
    ("Science", "The earth is flat. NASA has been fabricating satellite imagery for decades to hide the truth from humanity.", 0),
    ("Science", "HAARP is a secret government weather weapon used to engineer hurricanes, earthquakes, and floods on demand.", 0),
    ("Science", "NASA is hiding a massive planet Nibiru heading toward Earth that will cause a mass extinction event in 2025.", 0),
    ("Science", "Chemtrails sprayed by aircraft contain mind-control chemicals approved in a secret government programme.", 0),
    ("Science", "The moon landing was faked in a Hollywood studio. Stanley Kubrick filmed it and leaked a confession on his deathbed.", 0),
    ("Science", "5G towers were secretly engineered to activate nanobots injected via COVID vaccines to remotely control humans.", 0),

    # ════════════════════════════════════════════════════════════
    # ENTERTAINMENT / CELEBRITY
    # ════════════════════════════════════════════════════════════
    # Legitimate
    ("Entertainment", "Oppenheimer won the Academy Award for Best Picture at the 2024 Oscars, with Christopher Nolan winning Best Director.", 2),
    ("Entertainment", "Taylor Swift's Eras Tour became the highest-grossing concert tour of all time in 2023.", 2),
    ("Entertainment", "BTS member Jin began his mandatory South Korean military service in December 2022.", 2),
    ("Entertainment", "Netflix's Squid Game became the most-watched non-English series on the platform when it launched in September 2021.", 2),
    ("Entertainment", "Beyonce's Renaissance album released in July 2022 received widespread critical acclaim and multiple Grammy nominations.", 2),
    ("Entertainment", "Barbie (2023) became the highest-grossing film ever directed by a woman, directed by Greta Gerwig.", 2),
    ("Entertainment", "The 2024 Grammy for Album of the Year went to Taylor Swift for Midnights.", 2),
    ("Entertainment", "Avatar: The Way of Water (2022) grossed over $2.3 billion worldwide, making it one of the highest-grossing films ever.", 2),
    ("Entertainment", "The TV series The Last of Us, adapted from the video game, premiered on HBO in January 2023 to critical acclaim.", 2),
    ("Entertainment", "Shah Rukh Khan's Jawan (2023) set multiple box office records, including the biggest opening day for a Bollywood film.", 2),
    # Misleading
    ("Entertainment", "Unnamed Hollywood insiders claim a major A-list celebrity is about to be arrested for financial fraud.", 1),
    ("Entertainment", "Bombshell: an anonymous source says a top streaming platform is planning to shut down entirely by year end.", 1),
    ("Entertainment", "A shocking expose reveals 90% of music chart positions are bought and fabricated, insiders claim.", 1),
    ("Entertainment", "An unnamed source says a beloved superhero franchise is being cancelled due to secret internal casting disputes.", 1),
    ("Entertainment", "According to anonymous sources, a major awards show was rigged this year with winners pre-selected by executives.", 1),
    ("Entertainment", "Unnamed music industry insiders claim a famous artist lip-syncs all live performances and has done so for years.", 1),
    # Highly Deceptive
    ("Entertainment", "Hollywood is run by a satanic cabal of elite celebrities who participate in child sacrifice rituals in secret.", 0),
    ("Entertainment", "A leaked recording proves major music labels use AI-generated subliminal frequencies in pop songs to control fans.", 0),
    ("Entertainment", "A famous celebrity was secretly replaced by a body double after faking their death at government request.", 0),
    ("Entertainment", "Major film studios insert hidden CIA propaganda into blockbusters to brainwash audiences into supporting the deep state.", 0),
    ("Entertainment", "Adrenochrome harvested from trafficked children is secretly used by Hollywood elites as an anti-ageing drug.", 0),

    # ════════════════════════════════════════════════════════════
    # FINANCE & ECONOMY
    # ════════════════════════════════════════════════════════════
    # Legitimate
    ("Finance", "Bitcoin reached an all-time high of over $73,000 in March 2024 following the approval of spot Bitcoin ETFs in the US.", 2),
    ("Finance", "The US Federal Reserve raised interest rates 11 times between March 2022 and July 2023 to combat inflation.", 2),
    ("Finance", "India's GDP grew approximately 8.2% in 2023-24, making it the fastest-growing major economy that year.", 2),
    ("Finance", "The IMF projected global economic growth of around 3.2% for 2024.", 2),
    ("Finance", "The US national debt surpassed $34 trillion for the first time in January 2024.", 2),
    ("Finance", "Warren Buffett's Berkshire Hathaway has delivered an average annual return of about 20% since 1965.", 2),
    ("Finance", "Inflation in the UK reached a 41-year high of 11.1% in October 2022 before declining through 2023.", 2),
    ("Finance", "The collapse of Silicon Valley Bank in March 2023 was the second-largest bank failure in US history.", 2),
    ("Finance", "Global e-commerce sales exceeded $5.8 trillion in 2023, representing a significant portion of total retail globally.", 2),
    # Misleading
    ("Finance", "Anonymous Wall Street insiders confirm a market crash bigger than 2008 is guaranteed to happen within weeks.", 1),
    ("Finance", "Shocking: unnamed economists confirm the government is secretly printing money to cover up a financial collapse.", 1),
    ("Finance", "An insider revealed major banks are planning a coordinated global shutdown of digital payments next month.", 1),
    ("Finance", "Bombshell: leaked documents show Bitcoin was created by the CIA to track criminal transactions worldwide.", 1),
    ("Finance", "An unnamed Federal Reserve source says the agency is secretly planning to eliminate the US dollar by 2027.", 1),
    ("Finance", "According to anonymous traders, a specific penny stock is guaranteed to return 500% in the next 30 days.", 1),
    ("Finance", "Unnamed analysts say the crypto market will hit $100 trillion by 2025, a 10x increase, unnamed research shows.", 1),
    # Highly Deceptive
    ("Finance", "The global banking system is controlled by Rothschild-linked families who deliberately engineer financial crashes for profit.", 0),
    ("Finance", "The Great Reset is a secret WEF plan to eliminate private property and enslave humanity under a digital currency.", 0),
    ("Finance", "Central banks are deliberately collapsing economies to usher in a one-world digital currency that tracks every purchase.", 0),
    ("Finance", "Bitcoin was invented by the NSA to monitor all financial transactions and identify political dissidents for elimination.", 0),

    # ════════════════════════════════════════════════════════════
    # CLIMATE & ENVIRONMENT
    # ════════════════════════════════════════════════════════════
    # Legitimate
    ("Climate", "2023 was confirmed as the hottest year on record globally, surpassing 2016, by NASA and the EU Copernicus service.", 2),
    ("Climate", "The IPCC concluded with overwhelming scientific consensus that human activities are the dominant cause of global warming.", 2),
    ("Climate", "Arctic sea ice extent reached near-record lows in summer 2023, consistent with long-term warming trends.", 2),
    ("Climate", "The Amazon rainforest lost an estimated 11,568 square kilometres of tree cover in 2022, according to Brazil's INPE.", 2),
    ("Climate", "Renewable energy surpassed coal in global electricity generation for the first time in 2023.", 2),
    ("Climate", "Rising sea levels pose an existential threat to low-lying island nations including Tuvalu and the Maldives.", 2),
    ("Climate", "The 2023 Canadian wildfires burned over 18 million hectares, the worst season on record in that country.", 2),
    ("Climate", "Ocean temperatures reached record highs in 2023, contributing to widespread coral bleaching events globally.", 2),
    ("Climate", "The Kyoto Protocol was the first international treaty to set binding greenhouse gas emission reduction targets.", 2),
    # Misleading
    ("Climate", "Unnamed scientists claim the IPCC's global warming data is massively exaggerated to justify carbon taxes.", 1),
    ("Climate", "An anonymous government insider says climate change policy is deliberately being used to destroy small businesses.", 1),
    ("Climate", "Shocking new study claims electric vehicles produce more carbon than petrol cars over their lifetime, but results are suppressed.", 1),
    ("Climate", "According to an anonymous source, wind turbines are secretly harming 95% of nearby wildlife with infrasound.", 1),
    ("Climate", "Unnamed experts claim solar panels contain toxic chemicals that cause cancer in communities living nearby.", 1),
    # Highly Deceptive
    ("Climate", "Climate change is a complete hoax fabricated by the Rothschilds and globalists to impose carbon taxes and control populations.", 0),
    ("Climate", "HAARP technology is being used by governments to engineer extreme weather events like hurricanes and floods as weapons.", 0),
    ("Climate", "Global warming data is entirely fabricated. The real agenda is to ban meat and cars to drastically reduce world population.", 0),
    ("Climate", "Secret government cloud-seeding programmes are lacing rainfall with toxic chemicals to control food supplies globally.", 0),
    ("Climate", "The 2023 wildfires in Canada and Hawaii were deliberately started by government laser weapons to seize land cheaply.", 0),

    # ════════════════════════════════════════════════════════════
    # HISTORICAL
    # ════════════════════════════════════════════════════════════
    # Legitimate
    ("Historical", "World War II ended in Europe on May 8, 1945 (V-E Day) and in the Pacific on September 2, 1945 (V-J Day).", 2),
    ("Historical", "Neil Armstrong became the first human to walk on the Moon on July 20, 1969, during the Apollo 11 mission.", 2),
    ("Historical", "The Berlin Wall fell on November 9, 1989, marking a key moment in the end of the Cold War.", 2),
    ("Historical", "The Holocaust resulted in the systematic murder of approximately six million Jewish people by Nazi Germany.", 2),
    ("Historical", "India gained independence from British rule on August 15, 1947, following decades of resistance.", 2),
    ("Historical", "The atomic bomb was dropped on Hiroshima on August 6 and on Nagasaki on August 9, 1945.", 2),
    ("Historical", "The Cuban Missile Crisis of October 1962 was a 13-day standoff between the US and Soviet Union.", 2),
    ("Historical", "The French Revolution began in 1789 and resulted in the abolition of the French monarchy.", 2),
    ("Historical", "The Great Wall of China was built over many centuries, with significant construction during the Ming dynasty.", 2),
    ("Historical", "The first successful powered aeroplane flight was made by the Wright brothers on December 17, 1903.", 2),
    # Misleading
    ("Historical", "Unnamed historians claim classified documents prove Winston Churchill secretly negotiated with Hitler in 1941.", 1),
    ("Historical", "An anonymous researcher says suppressed evidence proves ancient Egypt had electricity and wireless technology.", 1),
    ("Historical", "Shocking claim: an unnamed academic says multiple major historical events in the 20th century were staged for political control.", 1),
    ("Historical", "Anonymous sources say the true death toll of a major 20th century conflict was 10 times higher than officially reported.", 1),
    # Highly Deceptive
    ("Historical", "The Holocaust was fabricated and grossly exaggerated by Zionist propaganda. Fewer than 100,000 people actually died.", 0),
    ("Historical", "The moon landing never happened. Stanley Kubrick filmed it in a studio and left a deathbed confession proving it.", 0),
    ("Historical", "9/11 was an inside job planned by the CIA and Mossad. Leaked blueprints prove the towers were demolished by explosives.", 0),
    ("Historical", "Sandy Hook was a staged false flag with crisis actors. No children died. It was engineered to push gun control laws.", 0),
    ("Historical", "World War II was engineered by a secret banking cabal to profit from both sides and establish the New World Order.", 0),
    ("Historical", "Ancient Egyptian pyramids were built by an advanced alien civilisation thousands of years before human history began.", 0),

    # ════════════════════════════════════════════════════════════
    # SOCIAL MEDIA STYLE
    # ════════════════════════════════════════════════════════════
    # Legitimate
    ("SocialMedia", "The viral photo of a double rainbow over the Grand Canyon was confirmed as authentic by photography experts.", 2),
    ("SocialMedia", "Fact checkers at Snopes confirmed the widely shared claim about a politician's statement was taken out of context.", 2),
    ("SocialMedia", "The video of an octopus walking on land is real. Octopuses are known to briefly leave water to move between pools.", 2),
    ("SocialMedia", "WhatsApp messages claiming free recharge codes from telecom companies are scams. Companies have denied these offers.", 2),
    ("SocialMedia", "The WHO debunked the viral claim that holding your breath for 10 seconds tests for COVID-19 infection.", 2),
    ("SocialMedia", "PolitiFact rated the viral claim about a politician's tax record as Mostly False due to missing context.", 2),
    ("SocialMedia", "The viral image showing a shark swimming on a flooded highway was confirmed to be a digitally manipulated photo.", 2),
    # Misleading
    ("SocialMedia", "SHARE NOW: a new law will delete your WhatsApp account in 24 hours unless you forward this to 10 contacts.", 1),
    ("SocialMedia", "URGENT: government is secretly tracking all mobile users through a new chip activated by a recent software update.", 1),
    ("SocialMedia", "MUST SHARE: drinking hot lemon water every morning kills 95% of cancer cells, unnamed Harvard researchers confirm.", 1),
    ("SocialMedia", "Breaking: unnamed sources confirm celebrities are being cloned in secret government labs and originals eliminated.", 1),
    ("SocialMedia", "FORWARD TO 20 PEOPLE: a child is missing and police are not acting. Anonymous insiders say the government is involved.", 1),
    ("SocialMedia", "Viral post: eating turmeric daily cures arthritis in 100% of cases within two weeks, anonymous study claims.", 1),
    ("SocialMedia", "BREAKING: an unnamed government source says a new tax is being secretly introduced on all WhatsApp messages.", 1),
    # Highly Deceptive
    ("SocialMedia", "URGENT SHARE: government activated 5G towers at midnight to spread a new virus. Turn off your phone now or you will fall ill.", 0),
    ("SocialMedia", "They do not want you to know: a whistleblower proved the COVID vaccine contains a DNA-altering parasite that kills within 2 years.", 0),
    ("SocialMedia", "BREAKING: leaked footage from the moon landing set confirms the entire Apollo programme was a Hollywood production.", 0),
    ("SocialMedia", "What they are hiding: drinking baking soda with turmeric cures all cancers in 7 days. Big Pharma is suppressing this.", 0),
    ("SocialMedia", "SHARE IMMEDIATELY: the government will begin mandatory microchipping of all citizens next month. A whistleblower has proof.", 0),
    ("SocialMedia", "WWG1WGA: the storm is here. Thousands of deep state officials have been secretly arrested and are awaiting military tribunals.", 0),

    # ════════════════════════════════════════════════════════════
    # GENERAL NEWS
    # ════════════════════════════════════════════════════════════
    # Legitimate
    ("GeneralNews", "The 2023 Turkey-Syria earthquake killed over 50,000 people and was one of the deadliest in the region in a century.", 2),
    ("GeneralNews", "Apple's revenue for fiscal year 2023 was approximately $383 billion, making it one of the world's most profitable companies.", 2),
    ("GeneralNews", "The global population surpassed 8 billion for the first time in November 2022, according to UN estimates.", 2),
    ("GeneralNews", "ChatGPT reached 100 million users within two months of launching in November 2022, the fastest app to achieve this.", 2),
    ("GeneralNews", "ISRO's Aditya-L1 solar observatory was launched in September 2023 to study the Sun from the first Lagrange point.", 2),
    ("GeneralNews", "The Gaza conflict that began in October 2023 following the Hamas attacks resulted in a major humanitarian crisis.", 2),
    ("GeneralNews", "Global smartphone shipments declined for the third consecutive year in 2023 due to economic uncertainty.", 2),
    ("GeneralNews", "The US and China held high-level diplomatic talks in 2023 and 2024 aimed at stabilising their bilateral relationship.", 2),
    ("GeneralNews", "Amazon Web Services, Microsoft Azure, and Google Cloud dominate the global cloud computing market.", 2),
    ("GeneralNews", "The Maui wildfires in Hawaii in August 2023 killed at least 97 people and destroyed the historic town of Lahaina.", 2),
    ("GeneralNews", "India surpassed China as the world's most populous country in 2023, according to UN population data.", 2),
    # Misleading
    ("GeneralNews", "Bombshell: an unnamed government source claims a major natural disaster is being suppressed from all news coverage.", 1),
    ("GeneralNews", "Shocking expose: anonymous insiders say tech companies collaborate with governments to secretly monitor all citizens.", 1),
    ("GeneralNews", "An unnamed senior official claims a major international organisation is about to dissolve in a secret emergency meeting.", 1),
    ("GeneralNews", "According to anonymous experts, a new disease deadlier than COVID is being covered up by the WHO to avoid panic.", 1),
    ("GeneralNews", "Leaked documents claim 85% of mainstream media stories are pre-approved by government censors before publication.", 1),
    ("GeneralNews", "An anonymous insider says a major tech company is planning to charge users for previously free services next month.", 1),
    # Highly Deceptive
    ("GeneralNews", "The global elite are depopulating the earth using engineered pandemics, tainted food supplies, and weather weapons.", 0),
    ("GeneralNews", "Every major terrorist attack in the last 20 years was orchestrated by the CIA as a false flag to justify endless war.", 0),
    ("GeneralNews", "World leaders are reptilian shapeshifters from another dimension who have secretly controlled human civilisation for centuries.", 0),
    ("GeneralNews", "The moon is an artificial satellite placed by aliens to control human consciousness and suppress spiritual awakening.", 0),
    ("GeneralNews", "A secret network of underground tunnels connects elite bunkers where global leaders plan humanity's depopulation.", 0),
]

# ---------------------------------------------------------------------------
# Load CSV samples
# ---------------------------------------------------------------------------

def load_csv_samples(path, n_per_class=55, seed=7):
    try:
        df = pd.read_csv(path).dropna()
        df["text"] = df["text"].astype(str).str.strip()
        df = df[df["text"].str.split().str.len() >= 8]
        parts = []
        for lbl in [0, 1, 2]:
            grp = df[df["label"] == lbl]
            k   = min(n_per_class, len(grp))
            if k > 0:
                parts.append(grp.sample(k, random_state=seed))
        return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
    except Exception as e:
        print(f"  [WARN] Could not load {path}: {e}")
        return pd.DataFrame()

print("Loading CSV samples...")
sports_df = load_csv_samples("src/sports_data.csv",   n_per_class=50)
live_df   = pd.DataFrame()  # excluded: label quality too noisy for eval (editorial/opinion mix)
synth_df  = load_csv_samples("src/synthetic_data.csv", n_per_class=50)
test_df   = load_csv_samples("src/test_data.csv",      n_per_class=50)

csv_rows = []
for src_name, df in [("Sports-CSV", sports_df),
                      ("Synthetic-CSV", synth_df), ("TestData-CSV", test_df)]:
    for _, row in df.iterrows():
        csv_rows.append((src_name, str(row["text"]), int(row["label"])))

total_inline = len(INLINE)
total_csv    = len(csv_rows)
print(f"  Sports CSV   : {len(sports_df)}")
print(f"  Live news CSV: {len(live_df)}")
print(f"  Synthetic CSV: {len(synth_df)}")
print(f"  Test data CSV: {len(test_df)}")
print(f"  Inline        : {total_inline}")
print(f"  Grand total   : {total_inline + total_csv}")

# ---------------------------------------------------------------------------
# Assemble, shuffle, cap at 1000
# ---------------------------------------------------------------------------

all_samples = INLINE + csv_rows
random.seed(42)
random.shuffle(all_samples)
all_samples = all_samples[:1000]

label_dist = {0:0, 1:0, 2:0}
for _, _, lbl in all_samples:
    label_dist[lbl] += 1
print(f"\nRunning on {len(all_samples)} samples  |  HD={label_dist[0]}  ML={label_dist[1]}  LG={label_dist[2]}\n")

# ---------------------------------------------------------------------------
# Run predictions
# ---------------------------------------------------------------------------

correct      = 0
domain_tp    = {}
domain_total = {}
label_tp     = {0:0, 1:0, 2:0}
label_total  = {0:0, 1:0, 2:0}
conf         = {0:{0:0,1:0,2:0}, 1:{0:0,1:0,2:0}, 2:{0:0,1:0,2:0}}
errors_seen  = []

t0 = time.time()
for i, (domain, text, true_lbl) in enumerate(all_samples, 1):
    try:
        pred_label, confidence, _, _, _ = predict(text)
    except Exception as e:
        errors_seen.append((domain, str(e)[:80], text[:80]))
        pred_label = "Error"
        confidence = 0.0

    pred_idx = NAME_TO_IDX.get(pred_label, -1)
    hit = (pred_label == LABEL_NAMES.get(true_lbl, ""))
    if hit:
        correct += 1
        label_tp[true_lbl] = label_tp.get(true_lbl, 0) + 1
        domain_tp[domain]  = domain_tp.get(domain, 0) + 1
    label_total[true_lbl]  = label_total.get(true_lbl, 0) + 1
    domain_total[domain]   = domain_total.get(domain, 0) + 1
    if 0 <= pred_idx <= 2:
        conf[true_lbl][pred_idx] += 1

    if i % 100 == 0:
        elapsed = time.time() - t0
        print(f"  [{i:4d}/1000]  acc: {correct/i*100:.1f}%  |  {elapsed:.1f}s elapsed")

elapsed = time.time() - t0
total   = len(all_samples)

# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

SEP = "=" * 65

print(f"\n{SEP}")
print(f"  DIVERSE 1000-SAMPLE TEST RESULTS  ({elapsed:.1f}s)")
print(SEP)
print(f"  Overall accuracy : {correct/total*100:.2f}%  ({correct}/{total})")
print()

print("  Per-class results:")
print(f"  {'Label':<22} {'Correct':>8} {'Total':>7} {'Acc':>7}")
print("  " + "-" * 48)
for lbl, name in LABEL_NAMES.items():
    tp  = label_tp.get(lbl, 0)
    tot = label_total.get(lbl, 0)
    acc = tp/tot*100 if tot else 0
    print(f"  {name:<22} {tp:>8} {tot:>7} {acc:>6.1f}%")

print()
print("  Confusion matrix  (rows=actual, cols=predicted):")
print(f"  {'':22} {'HD':>8} {'Mislead':>9} {'Legit':>8}")
print("  " + "-" * 50)
for lbl, name in LABEL_NAMES.items():
    row = conf[lbl]
    print(f"  {name:<22} {row[0]:>8} {row[1]:>9} {row[2]:>8}")

print()
print("  Per-domain accuracy:")
print(f"  {'Domain':<22} {'Correct':>8} {'Total':>7} {'Acc':>7}  {'Bar'}")
print("  " + "-" * 60)
for dom in sorted(domain_total.keys()):
    tp  = domain_tp.get(dom, 0)
    tot = domain_total[dom]
    acc = tp/tot*100 if tot else 0
    bar = "#" * int(acc / 5)
    print(f"  {dom:<22} {tp:>8} {tot:>7} {acc:>6.1f}%  {bar}")

if errors_seen:
    print(f"\n  ERRORS ({len(errors_seen)}):")
    for dom, err, txt in errors_seen[:5]:
        print(f"  [{dom}] {err}")
        print(f"    {txt}")

print(f"\n{SEP}")
