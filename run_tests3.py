from src.predict import predict

tests = [
    # ── HIGHLY DECEPTIVE (HD-01 … HD-170) ───────────────────────────────────

    # Conspiracy / cover-up
    ("HD-001", "The government is covering up the existence of a shadow cabinet that controls all policy decisions."),
    ("HD-002", "Secret leaked files prove that NASA has been faking satellite imagery for over 50 years."),
    ("HD-003", "The deep state orchestrated the 2008 financial crisis to transfer wealth to the global elite."),
    ("HD-004", "A whistleblower revealed that the CDC altered vaccine safety data to hide adverse effects."),
    ("HD-005", "Leaked CIA documents confirm that multiple world leaders are controlled by a secret cabal."),
    ("HD-006", "The government is concealing evidence that free energy technology was developed in the 1950s."),
    ("HD-007", "Secret documents show the moon landing footage was re-shot in a Nevada studio by Kubrick."),
    ("HD-008", "The Illuminati controls the global banking system and is engineering a financial reset to enslave populations."),
    ("HD-009", "They are hiding the fact that water fluoridation is a mass mind control experiment run by the government."),
    ("HD-010", "WWG1WGA. The great awakening is exposing the deep state child trafficking network."),
    ("HD-011", "QAnon's Storm is coming. Adrenochrome-harvesting elites will be exposed and arrested soon."),
    ("HD-012", "The New World Order is using COVID lockdowns to implement permanent surveillance of all citizens."),
    ("HD-013", "The Rothschilds control the IMF and are engineering the collapse of the global economy."),
    ("HD-014", "Rockefeller operatives placed inside the WHO are suppressing natural cures for profit."),
    ("HD-015", "The great reset is a Soros-funded plot to destroy national sovereignty and enslave populations."),
    ("HD-016", "Leaked internal memos from the Pentagon confirm that HAARP is being used to trigger earthquakes."),
    ("HD-017", "What they are hiding from you will change everything. Secret files expose the real 9/11 plotters."),
    ("HD-018", "The government secretly installed backdoors in every router sold after 2010 to spy on citizens."),
    ("HD-019", "Crisis actors were hired and flown in ahead of the Las Vegas shooting which was a staged false flag."),
    ("HD-020", "NSA whistleblower reveals smartphones are continuously streaming audio to a government server farm."),

    # Health misinformation
    ("HD-021", "Vaccines contain microchips designed by Bill Gates to track every human being on earth."),
    ("HD-022", "The MMR vaccine is directly responsible for the autism epidemic. Pediatricians are paid to deny it."),
    ("HD-023", "Drinking bleach mixed with water cures COVID-19. Doctors are being threatened into silence about it."),
    ("HD-024", "The COVID-19 vaccine was engineered as a bioweapon designed to reduce global population by 70 percent."),
    ("HD-025", "Ivermectin cures COVID, cancer, and HIV. Big Pharma is suppressing this finding to protect profits."),
    ("HD-026", "Hydroxychloroquine is a miracle cure suppressed by the WHO to push expensive patented treatments."),
    ("HD-027", "Natural immunity is infinitely superior to any vaccine. The government is hiding this evidence."),
    ("HD-028", "5G towers suppress the human immune system and were rolled out to accelerate the COVID-19 pandemic."),
    ("HD-029", "Chemtrails contain barium, strontium and aluminium being sprayed to poison and depopulate the earth."),
    ("HD-030", "Big Pharma has the cure for cancer but is suppressing it to maintain a multi-trillion dollar industry."),
    ("HD-031", "Scientists found a miracle compound that reverses all cancer tumours but it is being suppressed by authorities."),
    ("HD-032", "The HPV vaccine causes infertility in young girls. Governments are hiding this to reduce the population."),
    ("HD-033", "Doctors are being silenced for revealing that vitamin C megadosing cures all viral infections."),
    ("HD-034", "A secret clinical trial proved that essential oils cure stage-4 cancer but results are being suppressed."),
    ("HD-035", "The microchip in the Moderna vaccine activates when scanned with a standard NFC reader."),
    ("HD-036", "mRNA injections permanently alter human DNA and will switch off the immune system within five years."),
    ("HD-037", "Chemotherapy is deliberately ineffective. Oncologists profit from keeping patients sick indefinitely."),
    ("HD-038", "The flu vaccine contains live HIV virus that accumulates in the body over repeated doses."),
    ("HD-039", "Vaccine mandate whistleblowers confirm that batch numbers identify which lots contain kill-switch compounds."),
    ("HD-040", "A leaked Pfizer document proves the company knew the vaccine caused heart failure in 20 percent of recipients."),

    # Political fabrication
    ("HD-041", "The 2020 presidential election was stolen using Dominion voting machines programmed to flip ballots."),
    ("HD-042", "Leaked footage proves that ballot boxes in multiple swing states were stuffed overnight."),
    ("HD-043", "A stolen election was confirmed by secret military intelligence showing vote-switching in all key states."),
    ("HD-044", "The CIA assassinated JFK because he was about to expose the Federal Reserve conspiracy."),
    ("HD-045", "Leaked CIA files confirm that multiple US presidents were secretly murdered by the deep state cabal."),
    ("HD-046", "George Soros funded the George Floyd protests to destabilise the US ahead of the November election."),
    ("HD-047", "Secret documents prove that the Holocaust death toll was fabricated and grossly exaggerated for political gain."),
    ("HD-048", "The Sandy Hook shooting was a staged false flag. All grieving parents are professional crisis actors."),
    ("HD-049", "The Boston Marathon bombing never happened. The entire event was orchestrated by the government."),
    ("HD-050", "The deep state rigged the 2016 primaries to remove Bernie Sanders and install their chosen candidate."),
    ("HD-051", "Leaked NSA files show that all major opposition politicians are blackmailed by the intelligence agencies."),
    ("HD-052", "The government is hiding evidence that elected officials are members of a child trafficking syndicate."),
    ("HD-053", "Military intelligence confirms that martial law has already been secretly declared in three US states."),
    ("HD-054", "The New World Order has already installed AI surveillance systems in all major cities to monitor citizens."),
    ("HD-055", "Secret government documents prove that chemtrails are being used to suppress political dissent nationwide."),

    # Flat earth / NASA / science denial
    ("HD-056", "NASA lies. The earth is flat and the globe model is a fiction created to extract funding from governments."),
    ("HD-057", "NASA fakes all space imagery using CGI. No human being has ever left the lower atmosphere."),
    ("HD-058", "The globe is fake. Independent researchers using laser measurements have proven the earth is flat."),
    ("HD-059", "Astronauts are crisis actors. NASA uses underwater tanks and wire rigs to simulate zero gravity footage."),
    ("HD-060", "The Van Allen belts are lethal. NASA faked the moon landing because it was physically impossible to survive."),

    # Antisemitic / extremist tropes
    ("HD-061", "The Rothschilds control all central banks and are engineering a global currency collapse to impose a digital ID."),
    ("HD-062", "The Soros-funded open borders agenda is designed to destroy western civilisation through mass immigration."),
    ("HD-063", "A global Jewish elite controls all mainstream media and systematically suppresses inconvenient truths."),
    ("HD-064", "The Rockefellers engineered modern medicine to suppress cheap natural cures and maximise pharmaceutical profits."),
    ("HD-065", "Elite globalist cabals harvest adrenochrome from trafficked children at underground facilities worldwide."),

    # Terrorism / shooting denial
    ("HD-066", "The 9/11 attacks were an inside job. Controlled demolition brought down all three World Trade Center towers."),
    ("HD-067", "The Parkland school shooting was staged using crisis actors to push a gun control agenda against citizens."),
    ("HD-068", "The Oklahoma City bombing was a government false flag designed to justify new domestic surveillance laws."),
    ("HD-069", "The Manchester Arena bombing was a staged event. Leaked police radio confirms no real casualties occurred."),
    ("HD-070", "Crisis actors were deployed at the Pulse nightclub shooting which was engineered to push gun control."),

    # Climate change denial conspiracy
    ("HD-071", "Climate change is a globalist hoax fabricated to impose carbon taxes and control national economies."),
    ("HD-072", "Scientists fabricated temperature records for the past 50 years to push the climate change narrative."),
    ("HD-073", "Secret leaked emails from top climate scientists prove they colluded to fake the global warming data."),
    ("HD-074", "The IPCC is a Rothschild-funded organisation created to push false climate science and carbon taxes."),
    ("HD-075", "Weather modification using HAARP is being used to fake extreme weather events blamed on climate change."),

    # Suppressed technology / energy
    ("HD-076", "A suppressed patent from 1964 proves that cars can run on water but oil companies paid the inventor off."),
    ("HD-077", "The government is hiding a cold fusion reactor that would end global energy dependence permanently."),
    ("HD-078", "A free energy device capable of powering entire cities was invented but its creator was silenced by authorities."),
    ("HD-079", "Big Oil assassinated Stanley Meyer who invented a hydrogen-splitting device that ran cars on water alone."),
    ("HD-080", "Tesla's original papers were seized by the government in 1943. The suppressed tech would end fossil fuels."),

    # Ancient history / alternative history
    ("HD-081", "The Smithsonian is hiding evidence of ancient giants that would disprove mainstream human evolution."),
    ("HD-082", "NASA is suppressing satellite data showing a second sun that enters the solar system every 26,000 years."),
    ("HD-083", "Leaked Vatican files prove that the real history of humanity has been concealed for over two thousand years."),
    ("HD-084", "Ancient Egyptian texts hidden in the Vatican confirm that extraterrestrial beings created the human race."),
    ("HD-085", "The government is hiding proof that Mars was once inhabited and that humans are descended from Martian colonists."),

    # 5G + surveillance
    ("HD-086", "5G millimetre waves penetrate the blood-brain barrier and are being used to beam thought-control signals."),
    ("HD-087", "The 5G rollout is a mass surveillance system that can track every individual in real time using street nodes."),
    ("HD-088", "5G towers were installed during COVID lockdowns to prevent public scrutiny of this surveillance weapon."),
    ("HD-089", "Government contractors installed 5G-linked RFID readers into smart meters to monitor household activity."),
    ("HD-090", "Leaked telecom documents reveal that 5G signals can be weaponised to cause cancer in targeted individuals."),

    # Misc conspiracy
    ("HD-091", "The mainstream media is entirely controlled by six corporations who coordinate the suppression of truth."),
    ("HD-092", "Big Tech is shadow banning and suppressing voices that expose government corruption and hidden agendas."),
    ("HD-093", "The global elite are constructing underground bunkers in preparation for a planned civilisation-ending event."),
    ("HD-094", "NASA is concealing the existence of Planet X which is approaching and will cause catastrophic pole shifts."),
    ("HD-095", "Secret government documents prove that birds are not real but are government surveillance drones."),
    ("HD-096", "The moon is an artificial satellite constructed by an ancient extraterrestrial civilisation."),
    ("HD-097", "A deep state whistleblower has confirmed that all major terrorist attacks are self-inflicted false flags."),
    ("HD-098", "Leaked Pentagon memos show that UFO technology has been reverse-engineered and is being used in classified aircraft."),
    ("HD-099", "The government is hiding evidence that mermaids exist after Navy sonar killed a population in 2004."),
    ("HD-100", "Leaked intelligence confirms that water supplies in major cities are being laced with lithium to sedate populations."),

    # More health
    ("HD-101", "The autism epidemic is caused by the mercury-based preservative thimerosal still present in flu vaccines."),
    ("HD-102", "Sunscreen chemicals cause cancer and are deliberately formulated to keep customers dependent on dermatology."),
    ("HD-103", "Statins are a Big Pharma scam. They cause heart disease while suppressing cheap dietary cures."),
    ("HD-104", "Chemotherapy is a poison racket. Oncologists receive kickbacks for every patient they put on chemo."),
    ("HD-105", "A suppressed study from Johns Hopkins shows that masks increase CO2 retention and cause brain damage."),
    ("HD-106", "The government is hiding a natural compound found in apricot seeds that cures all forms of cancer."),
    ("HD-107", "Fluoride calcifies the pineal gland, blocking spiritual perception and making populations easier to control."),
    ("HD-108", "Leaked FDA documents show that aspartame was approved despite internal evidence it causes brain tumours."),
    ("HD-109", "Hospital ventilators were deliberately misused during COVID to kill patients and inflate death statistics."),
    ("HD-110", "PCR tests were set to artificially high cycle thresholds to manufacture false-positive COVID cases."),

    # More political
    ("HD-111", "The FBI deliberately facilitated the January 6 riot using embedded undercover agents as provocateurs."),
    ("HD-112", "A secret Pentagon document confirms that the US government tested biological agents on its own soldiers."),
    ("HD-113", "The CIA runs a global network of media assets that plant false stories in over 50 countries."),
    ("HD-114", "Leaked documents confirm that MI6 assassinated Princess Diana because she was about to expose the royals."),
    ("HD-115", "George Soros directly funded the installation of radical district attorneys to defund police departments."),
    ("HD-116", "The government faked the death of Osama bin Laden. He is alive and living under CIA protection."),
    ("HD-117", "A shadow government of unelected globalists overrides elected presidents on all major policy decisions."),
    ("HD-118", "Dominion voting machines have a hidden wireless modem that connects to a foreign server during counting."),
    ("HD-119", "The FBI planted classified documents at Mar-a-Lago to frame a political opponent of the deep state."),
    ("HD-120", "Secret whistleblowers confirm that Supreme Court justices are routinely blackmailed by intelligence agencies."),

    # More science denial
    ("HD-121", "Evolution is a Masonic fraud. Secret Vatican documents prove that God created the earth 6000 years ago."),
    ("HD-122", "The Big Bang theory was invented to hide evidence of the divine creation of the universe."),
    ("HD-123", "Germ theory is false. Viruses do not cause disease and the entire field of virology is a medical fraud."),
    ("HD-124", "Chemtrails are confirmed by a leaked Air Force manual detailing stratospheric aerosol injection programs."),
    ("HD-125", "The government is suppressing proof that cannabis oil cures stage-4 cancer in 90 percent of patients."),

    # QAnon & movement-specific
    ("HD-126", "The storm is coming. Military tribunals will arrest all deep state operatives within 30 days."),
    ("HD-127", "Trump is secretly working with the NSA to expose the satanic ritual abuse network within the government."),
    ("HD-128", "JFK Jr. is alive and will return to announce the arrest of the global child trafficking cabal."),
    ("HD-129", "Adrenochrome is harvested from terrified children and consumed by Hollywood celebrities for its rejuvenating effects."),
    ("HD-130", "The white hats inside the military are conducting a silent coup to dismantle the deep state permanently."),

    # Vaccine-related (varied)
    ("HD-131", "The Pfizer vaccine contains graphene oxide nanoparticles that self-assemble into a neural control interface."),
    ("HD-132", "Vaccinated individuals are shedding spike proteins that sterilise unvaccinated people around them."),
    ("HD-133", "Military doctors leaked data showing excess deaths in the vaccinated population are being deliberately hidden."),
    ("HD-134", "The CDC is suppressing VAERS data showing that vaccines have killed over a million Americans."),
    ("HD-135", "Vaccine lots with the highest death rates were distributed to red states as a form of political genocide."),

    # Alien / UFO conspiracy
    ("HD-136", "Area 51 houses a living extraterrestrial ambassador who has been briefing US presidents since Eisenhower."),
    ("HD-137", "Leaked Roswell autopsy footage is genuine. The government has been concealing alien biology for 80 years."),
    ("HD-138", "NASA suppressed a Mars Curiosity image showing a clearly humanoid statue proving ancient civilisation."),
    ("HD-139", "Governments worldwide signed a secret treaty with the Greys allowing abductions in exchange for technology."),
    ("HD-140", "Whistleblower testimony confirms that a recovered alien craft is being back-engineered at Wright-Patterson."),

    # Banking / economy conspiracy
    ("HD-141", "The Federal Reserve is a private bank owned by the Rothschilds and has never been audited."),
    ("HD-142", "A secret plan to replace the US dollar with a digital currency chip implanted in the hand is already underway."),
    ("HD-143", "The 2008 financial crisis was deliberately engineered by Goldman Sachs to buy up distressed assets cheaply."),
    ("HD-144", "Bitcoin was created by the NSA as a honeypot to track the finances of government dissidents worldwide."),
    ("HD-145", "The IMF and World Bank are fronts for a global government that controls all sovereign nations through debt."),

    # Media / tech conspiracy
    ("HD-146", "Google's algorithms are programmed to suppress search results that expose government corruption."),
    ("HD-147", "Facebook uses AI emotion-manipulation tools to push users toward radicalism for government social control."),
    ("HD-148", "Twitter executives were caught on a leaked call admitting they shadow-ban all anti-establishment voices."),
    ("HD-149", "YouTube is suppressing videos proving that COVID vaccines cause infertility on behalf of the WHO."),
    ("HD-150", "Apple includes an NSA firmware backdoor in every iPhone that activates without user knowledge."),

    # Bioweapons
    ("HD-151", "Ebola was engineered in a US bioweapons lab and released to justify a military presence in West Africa."),
    ("HD-152", "HIV was deliberately created in a Fort Detrick laboratory and introduced into the population via hepatitis B vaccines."),
    ("HD-153", "COVID-19 was engineered as a bioweapon in the Wuhan Institute of Virology with US funding, and evidence is being suppressed."),
    ("HD-154", "Leaked gain-of-function research documents prove that monkeypox was lab-engineered for the next planned pandemic."),
    ("HD-155", "A whistleblower inside the WHO confirmed that the next engineered pandemic has already been released."),

    # Depopulation / genocide
    ("HD-156", "Bill Gates has publicly stated his goal is to reduce the world population by 90 percent using vaccines."),
    ("HD-157", "The COVID vaccine was designed to sterilise an entire generation as part of an elite depopulation agenda."),
    ("HD-158", "Chemtrails contain a slow-acting poison that reduces fertility and is part of a planned global depopulation."),
    ("HD-159", "Georgia Guidestones confirm that the elite plan to reduce global population to 500 million through engineered pandemics."),
    ("HD-160", "A United Nations document leaked online reveals a secret depopulation target to be achieved by 2030."),

    # Miscellaneous hard HD
    ("HD-161", "The government is hiding the cure for baldness because the hair loss industry generates hundreds of billions annually."),
    ("HD-162", "Microwave ovens emit radiation that destroys nutrients and slowly damages the brain with repeated exposure."),
    ("HD-163", "Leaked Vatican archives confirm that Jesus Christ survived the crucifixion and lived in Kashmir until old age."),
    ("HD-164", "A secret society of satanists controls all major award shows, embedding occult rituals in live broadcasts."),
    ("HD-165", "The moon controls human consciousness. NASA has been broadcasting frequency signals from the lunar surface."),
    ("HD-166", "Smart TVs contain government-installed firmware that activates the microphone when keywords are spoken."),
    ("HD-167", "A suppressed peer-reviewed study confirmed that mobile phone radiation causes brain cancer within 10 years."),
    ("HD-168", "The government is concealing the fact that tap water in major cities is laced with hormone disruptors deliberately."),
    ("HD-169", "Leaked NSA files prove the agency can activate any smartphone camera remotely without the user's knowledge."),
    ("HD-170", "A whistleblower revealed that hospital death certificates are being manipulated to inflate COVID fatality numbers."),

    # ── MISLEADING (ML-001 … ML-165) ────────────────────────────────────────

    # Unnamed / anonymous sources
    ("ML-001", "According to unnamed sources inside the treasury, the government plans to freeze all savings accounts next month."),
    ("ML-002", "Unnamed officials say the prime minister secretly approved a back-channel deal with a foreign government."),
    ("ML-003", "Anonymous insiders claim the central bank is planning a surprise interest rate cut to boost election prospects."),
    ("ML-004", "Unnamed Pentagon sources say the defence secretary was overruled on a classified military operation."),
    ("ML-005", "According to anonymous senior officials, the president's health has significantly deteriorated in recent weeks."),
    ("ML-006", "Unnamed diplomatic sources say a secret ceasefire agreement was signed last week but not yet announced."),
    ("ML-007", "An anonymous White House official claims the national security adviser is about to resign."),
    ("ML-008", "Unnamed sources at the FDA say approval of the new drug was fast-tracked despite safety concerns."),
    ("ML-009", "According to unnamed researchers, the new battery technology is 100% ready for mass deployment."),
    ("ML-010", "Unnamed intelligence officials claim a foreign government has already infiltrated all major financial institutions."),
    ("ML-011", "Anonymous sources inside NATO say the alliance is preparing for a ground invasion scenario within six months."),
    ("ML-012", "An unnamed senior economist says the stock market will collapse by 80 percent before the end of the year."),
    ("ML-013", "Unnamed health officials say hospitals are concealing the true scale of long COVID complications."),
    ("ML-014", "According to anonymous sources, the tech giant deliberately suppressed its AI safety research findings."),
    ("ML-015", "Unnamed government scientists say the new pesticide was approved despite 90 percent failure in safety trials."),

    # Bombshell / shocking / explosive language
    ("ML-016", "Bombshell report: shocking new evidence exposes massive corruption at the heart of the electoral commission."),
    ("ML-017", "Explosive investigation: insider reveals that 99 percent of charitable donations never reach their intended recipients."),
    ("ML-018", "Shocking claim: unnamed study proves that eating red meat every day triples your Alzheimer risk within 10 years."),
    ("ML-019", "Bombshell allegation from an anonymous senator claims the speaker accepted millions in foreign payments."),
    ("ML-020", "Stunning new evidence exposed by whistleblowers proves that the judiciary is under direct executive pressure."),
    ("ML-021", "Explosive claim: an unnamed regulator says food safety inspections were secretly cut by 90 percent last year."),
    ("ML-022", "Shocking new data shows 95 percent of all clinical trials for new drugs are funded and ghost-written by pharma."),
    ("ML-023", "Bombshell report: an anonymous defence analyst claims the army secretly conducted drone strikes on civilians."),
    ("ML-024", "Stunning revelation from unnamed insiders: the intelligence agency deleted evidence ahead of the inquiry."),
    ("ML-025", "Explosive allegation: an anonymous insider claims the regulator is deliberately ignoring evidence of bank fraud."),

    # Exaggerated statistics
    ("ML-026", "A new study claims that 99 percent of people who eat processed food will develop heart disease by 60."),
    ("ML-027", "Scientists confirm that 95 percent of bottled water contains dangerous levels of microplastics."),
    ("ML-028", "New research shows that social media use is guaranteed to cause depression in 90 percent of teenagers."),
    ("ML-029", "A stunning new report claims that 85 percent of fast food contains toxic levels of hormone-disrupting chemicals."),
    ("ML-030", "Unnamed experts say that 99 percent of all politicians worldwide take bribes from corporate donors."),
    ("ML-031", "New data shows that electric vehicles are 95 percent more likely to catch fire than petrol-powered cars."),
    ("ML-032", "A shocking study reveals that coffee is guaranteed to reduce cancer risk by 95 percent in daily drinkers."),
    ("ML-033", "Scientists confirm that standing desks reduce cardiovascular disease risk by 85 percent in all users."),
    ("ML-034", "An unnamed study proves that 90 percent of antidepressants are completely ineffective for most patients."),
    ("ML-035", "New research suggests common food additives dramatically increase Alzheimer risk in 85 percent of adults."),

    # Guaranteed / 100% proven
    ("ML-036", "This completely proven and 100 percent effective remedy eliminates belly fat in just seven days."),
    ("ML-037", "Scientists confirm this simple breathing technique is totally guaranteed to lower blood pressure immediately."),
    ("ML-038", "Doctors confirm this one supplement is 100 percent proven to reverse type 2 diabetes within 30 days."),
    ("ML-039", "This completely natural detox is guaranteed to flush all toxins from your liver in just 48 hours."),
    ("ML-040", "New research: this totally proven herb eliminates all symptoms of arthritis permanently within two weeks."),

    # Sensationalist health claims
    ("ML-041", "Scientists confirm a new diet can completely reverse type 2 diabetes in just three weeks."),
    ("ML-042", "Doctors are ignoring a major breakthrough that reverses Alzheimer symptoms in just six weeks."),
    ("ML-043", "An unnamed study shows that mobile phones reduce sperm count by 75 percent in regular users."),
    ("ML-044", "New shocking evidence confirms that common painkillers dramatically increase heart failure risk in 80 percent of users."),
    ("ML-045", "Bombshell report: unnamed doctors say hospitals are deliberately withholding an effective COVID treatment."),
    ("ML-046", "An unnamed researcher says eating this superfood is guaranteed to boost immunity by 85 percent."),
    ("ML-047", "Scientists confirm that drinking two litres of water a day completely eliminates the risk of kidney stones."),
    ("ML-048", "An anonymous health official claims sunscreen chemicals dramatically increase skin cancer risk in 80 percent of users."),
    ("ML-049", "Shocking new report from unnamed experts: tap water causes infertility in 80 percent of men under 40."),
    ("ML-050", "New research from an unnamed university reveals that veganism reduces cancer risk by 99 percent."),

    # Voter / election fraud (sourced or exaggerated)
    ("ML-051", "Mail-in ballots from deceased voters were found in several counties, sources close to the investigation claim."),
    ("ML-052", "Deceased voters appeared on electoral rolls in three swing states, insiders familiar with the audit claim."),
    ("ML-053", "An unnamed election official says 90 percent of mail-in ballots in key districts were fraudulently submitted."),
    ("ML-054", "Anonymous sources say election computers were connected to the internet during counting in several counties."),
    ("ML-055", "Unnamed officials claim voting machines in six states experienced unexplained data anomalies during the count."),

    # Financial / economic sensationalism
    ("ML-056", "An anonymous Wall Street insider says the stock market will crash by 90 percent before Christmas this year."),
    ("ML-057", "Unnamed economists predict a global depression 10 times worse than 1929 will hit within 18 months."),
    ("ML-058", "A bombshell report from an anonymous analyst says all major banks are secretly insolvent."),
    ("ML-059", "Unnamed sources at the treasury say the government has secretly been printing money to cover a budget crisis."),
    ("ML-060", "According to anonymous insiders, the housing market will collapse completely by 95 percent next year."),

    # Technology sensationalism
    ("ML-061", "AI will eliminate 95 percent of all white-collar jobs within five years, dramatically increasing unemployment."),
    ("ML-062", "An unnamed tech insider says social media algorithms are deliberately boosting radical content by 85 percent."),
    ("ML-063", "Anonymous Google engineers claim the search giant deliberately suppresses conservative news in results."),
    ("ML-064", "Unnamed sources at Apple say the company is building a secret government surveillance tool into iOS."),
    ("ML-065", "Shocking report: an unnamed cybersecurity expert says 90 percent of smart home devices are actively compromised."),

    # Environmental / climate sensationalism
    ("ML-066", "An unnamed study confirms that air pollution causes cancer in 95 percent of urban residents by age 50."),
    ("ML-067", "Shocking data from unnamed scientists reveals that global coral reefs will be completely gone within two years."),
    ("ML-068", "Anonymous environmental researchers say pesticide contamination has rendered 90 percent of farmland toxic."),
    ("ML-069", "Unnamed UN officials say sea levels will rise by five metres within a decade, flooding all coastal cities."),
    ("ML-070", "A bombshell report from anonymous scientists claims the Amazon will be completely deforested by next year."),

    # Political (non-fabrication, just misleading)
    ("ML-071", "According to unnamed sources, the defence minister secretly authorised a military strike without cabinet approval."),
    ("ML-072", "Unnamed parliamentary insiders say the government is planning secret tax hikes to be announced after the election."),
    ("ML-073", "An anonymous civil servant claims the prime minister ignored legal advice on three major policy decisions."),
    ("ML-074", "Unnamed sources in the foreign office say the ambassador was recalled due to a secret diplomatic incident."),
    ("ML-075", "According to anonymous officials, the intelligence services have been secretly monitoring opposition MPs."),

    # Drugs / pharma misleading
    ("ML-076", "Unnamed medical experts say the new drug is 100 percent effective against all variants of the disease."),
    ("ML-077", "An anonymous doctor says hospitals are dramatically under-reporting adverse events linked to the new treatment."),
    ("ML-078", "Unnamed researchers claim that aspirin taken daily is guaranteed to prevent heart attacks in 99 percent of users."),
    ("ML-079", "Shocking claim from an anonymous pharmacist: 90 percent of branded drugs are identical to cheap generics."),
    ("ML-080", "An unnamed study proves that common painkillers dramatically increase dementia risk in 80 percent of elderly users."),

    # Insider / leaked (sourced — misleading level)
    ("ML-081", "An explosive investigation by an insider exposes massive financial irregularities inside the supreme court."),
    ("ML-082", "Insiders leaked evidence that the energy regulator is deliberately allowing utilities to overcharge consumers."),
    ("ML-083", "According to sources inside the company, executives knew about the safety flaw for years and concealed it."),
    ("ML-084", "An anonymous whistleblower says the banking regulator deliberately ignored hundreds of fraud reports."),
    ("ML-085", "Unnamed sources say the ministry suppressed data on side effects discovered during the drug approval process."),

    # Mixed / nuanced misleading
    ("ML-086", "An explosive new report reveals that 99 percent of people who diet gain all the weight back within a year."),
    ("ML-087", "Shocking truth: an unnamed study shows that fluoride in water dramatically lowers IQ in 85 percent of children."),
    ("ML-088", "An anonymous climate scientist says the IPCC is dramatically understating the true rate of sea level rise."),
    ("ML-089", "According to unnamed sources, the prime minister secretly met with foreign intelligence agents last spring."),
    ("ML-090", "Unnamed health officials claim hospitals are dramatically under-reporting adverse vaccine events to authorities."),
    ("ML-091", "A bombshell report from an anonymous analyst says the housing bubble will burst by 90 percent this quarter."),
    ("ML-092", "Explosive claims from an anonymous senator says the speaker accepted secret foreign donations for the campaign."),
    ("ML-093", "According to unnamed researchers, social media is guaranteed to cause severe depression in all teenagers."),
    ("ML-094", "Shocking data shows 90 percent of mainstream news is funded directly by pharmaceutical companies."),
    ("ML-095", "An unnamed study proves electric vehicles are 95 percent more likely to spontaneously combust than petrol cars."),

    # Statistics without source
    ("ML-096", "Scientists confirm eating sugar dramatically increases aggression in 99 percent of children studied."),
    ("ML-097", "New research suggests this common household chemical dramatically increases cancer risk in 90 percent of users."),
    ("ML-098", "A stunning new report claims that 90 percent of fast food contains dangerous microplastic contamination."),
    ("ML-099", "Scientists confirm a simple interval training routine is 100 percent proven to reverse heart disease in weeks."),
    ("ML-100", "New evidence suggests screen time is guaranteed to permanently damage eyesight in 85 percent of children."),

    # More varied misleading
    ("ML-101", "Unnamed sources say the government is hiding damaging information about a new surveillance programme from parliament."),
    ("ML-102", "An anonymous official claims the minister misused public funds, allegations the ministry strongly denied."),
    ("ML-103", "An unnamed study proves that 5G dramatically increases radiation exposure in urban areas by 90 percent."),
    ("ML-104", "Shocking report: unnamed whistleblowers say the banking sector is hiding a 95 percent leverage crisis."),
    ("ML-105", "An anonymous government source says the army secretly tested an experimental agent on civilian volunteers."),
    ("ML-106", "New bombshell evidence exposed by unnamed insiders suggests the prime minister took bribes from a foreign regime."),
    ("ML-107", "According to unnamed sources, the defence contractor deliberately inflated costs by 90 percent on every contract."),
    ("ML-108", "An anonymous regulator says pharmaceutical firms suppress 85 percent of negative clinical trial results."),
    ("ML-109", "Unnamed economists say the real unemployment rate is 95 percent higher than the official government figures."),
    ("ML-110", "Shocking claim: an unnamed oncologist says 90 percent of cancer diagnoses lead to unnecessary treatment."),

    # Sensational without outright fabrication
    ("ML-111", "Bombshell claim: anonymous officials say the defence budget was secretly slashed by 80 percent this year."),
    ("ML-112", "An unnamed study confirms that working from home dramatically increases depression risk by 85 percent."),
    ("ML-113", "Shocking new research from unnamed scientists: processed sugar is guaranteed to cause type 2 diabetes by 50."),
    ("ML-114", "An anonymous UN official says the number of people in famine is 90 percent higher than reported figures."),
    ("ML-115", "Unnamed sources inside the IAEA say nuclear material is going missing at a dramatically higher rate than known."),
    ("ML-116", "Bombshell leak from an unnamed regulator: financial institutions are 95 percent exposed to a single counterparty."),
    ("ML-117", "According to anonymous sources, a top court judge secretly owns shares in firms whose cases he has ruled on."),
    ("ML-118", "Unnamed insiders at a major airline say maintenance checks have been secretly reduced by 80 percent to cut costs."),
    ("ML-119", "Shocking report from unnamed scientists: 90 percent of sunscreen products dramatically increase melanoma risk."),
    ("ML-120", "An anonymous official says the government knew about the contaminated water supply for years before disclosure."),

    ("ML-121", "A new unnamed report claims drinking coffee dramatically reduces your risk of every type of cancer by 95 percent."),
    ("ML-122", "According to anonymous sources, the army secretly deployed troops domestically without parliamentary approval."),
    ("ML-123", "Unnamed intelligence officials say a foreign state has compromised 90 percent of the nation's power grid."),
    ("ML-124", "Shocking data from an anonymous source: 85 percent of food labelled organic actually contains pesticide residues."),
    ("ML-125", "An explosive claim from an unnamed insider says the social media company stores deleted messages permanently."),
    ("ML-126", "Bombshell report: according to unnamed sources, the election results in five constituencies were deliberately altered."),
    ("ML-127", "An anonymous senior doctor claims remdesivir kills 80 percent of patients who receive it in ICU settings."),
    ("ML-128", "Unnamed economists say central bank digital currencies will allow governments to freeze accounts instantly."),
    ("ML-129", "Shocking data from unnamed researchers: 99 percent of people on long-term antidepressants suffer severe withdrawal."),
    ("ML-130", "An anonymous customs official says 90 percent of illegal firearms enter the country through official ports."),

    ("ML-131", "New data from unnamed scientists suggests the current bird flu strain has a 95 percent human fatality rate."),
    ("ML-132", "An explosive allegation from an anonymous MP claims the chancellor is planning a secret wealth tax."),
    ("ML-133", "Unnamed sources in the city say the largest hedge fund in Europe is secretly on the verge of collapse."),
    ("ML-134", "Shocking claim: an anonymous scientist says the new mRNA cancer vaccine causes autoimmune disease in 90 percent."),
    ("ML-135", "According to anonymous insiders, the tech giant manipulated its own benchmark tests to exaggerate performance."),

    ("ML-136", "An unnamed virologist says the new respiratory virus spreading in Asia has an 80 percent mortality rate."),
    ("ML-137", "Bombshell report: unnamed officials say the military knowingly used defective equipment that killed 90 soldiers."),
    ("ML-138", "An anonymous pharmacist says 85 percent of generic drugs sold in pharmacies are counterfeit or substandard."),
    ("ML-139", "Shocking new data from anonymous scientists: electromagnetic fields from power lines cause leukaemia in 85 percent of children."),
    ("ML-140", "An unnamed government insider says the new digital ID card scheme will be mandatory for all citizens within a year."),

    ("ML-141", "According to unnamed sources, the prime minister knew about the intelligence failure six months before the attack."),
    ("ML-142", "An explosive claim from anonymous officials says the judiciary is being systematically pressured by the executive."),
    ("ML-143", "Unnamed insiders say the pharmaceutical company suppressed trial data showing the drug causes liver failure in 30 percent."),
    ("ML-144", "Shocking report: an anonymous climate modeller says current models underestimate warming by 90 percent."),
    ("ML-145", "An unnamed cybersecurity expert claims 85 percent of government websites have already been silently compromised."),

    ("ML-146", "Bombshell data from anonymous researchers reveals that red meat consumption causes cancer in 95 percent of people."),
    ("ML-147", "An unnamed source inside the WHO says the organisation is dramatically understating the global obesity death toll."),
    ("ML-148", "Shocking claim: anonymous government scientists say tap water causes DNA damage in 80 percent of consumers."),
    ("ML-149", "Unnamed stock analysts say the technology sector is 90 percent overvalued and will crash within weeks."),
    ("ML-150", "According to anonymous insiders, the intelligence agency ran a secret programme targeting domestic journalists."),

    ("ML-151", "An unnamed study proves that five hours of screen time daily causes permanent vision loss in 85 percent of children."),
    ("ML-152", "Bombshell claim from an anonymous senator: the speaker colluded with a foreign government to fund the campaign."),
    ("ML-153", "Unnamed sources say a central bank governor privately admitted the currency is on the verge of hyperinflation."),
    ("ML-154", "Shocking report: an anonymous aviation insider claims 80 percent of near-misses at airports go unreported."),
    ("ML-155", "An unnamed environmental scientist says methane emissions are 95 percent higher than official measurements claim."),

    ("ML-156", "According to unnamed sources, the health ministry has been deliberately inflating vaccination coverage statistics."),
    ("ML-157", "An explosive allegation from an anonymous official claims the regulator approved a drug despite 90 percent adverse events."),
    ("ML-158", "Unnamed prison officials say mental health conditions in inmates are deliberately untreated to justify incarceration."),
    ("ML-159", "Shocking claim from an anonymous engineer: the bridge safety inspection was falsified and 85 percent of bridges are unsafe."),
    ("ML-160", "An unnamed source inside the company says the electric vehicle range figures are overstated by 90 percent in real conditions."),

    ("ML-161", "According to anonymous insiders, the government is suppressing a report showing 90 percent of renewable energy targets will be missed."),
    ("ML-162", "An unnamed academic says peer review at top journals is completely compromised — 95 percent of papers are never properly checked."),
    ("ML-163", "Bombshell: unnamed officials say the trade deal secretly cedes judicial sovereignty to a foreign tribunal."),
    ("ML-164", "Shocking data from an unnamed study: daily aspirin use dramatically increases brain bleeding risk in 85 percent of over-60s."),
    ("ML-165", "An anonymous source in the energy sector says the true cost of nuclear decommissioning is 90 percent higher than disclosed."),

    # ── LEGITIMATE (LG-001 … LG-165) ────────────────────────────────────────

    # Economics / finance
    ("LG-001", "The Federal Reserve raised interest rates by 25 basis points, citing continued progress in reducing inflation."),
    ("LG-002", "The Bank of England held interest rates at 5.25 percent following its latest monetary policy committee meeting."),
    ("LG-003", "The European Central Bank cut rates by 25 basis points for the first time since 2019, citing falling inflation."),
    ("LG-004", "The IMF revised its global growth forecast down to 2.9 percent, citing tighter financial conditions worldwide."),
    ("LG-005", "Goldman Sachs reported quarterly earnings of 12.7 billion dollars, beating analyst expectations significantly."),
    ("LG-006", "The US unemployment rate fell to 3.7 percent in April according to the Bureau of Labor Statistics report."),
    ("LG-007", "China's GDP grew by 5.2 percent in 2023, meeting the government's official economic growth target."),
    ("LG-008", "The European Union fined Meta 1.2 billion euros for violating GDPR data protection regulations."),
    ("LG-009", "Amazon reported net income of 10.4 billion dollars in its latest quarterly earnings, up 105 percent year-on-year."),
    ("LG-010", "The Reserve Bank of Australia held the cash rate steady at 4.35 percent amid signs of easing inflation."),
    ("LG-011", "UK inflation fell to 2.3 percent in April, its lowest level since July 2021, according to the ONS."),
    ("LG-012", "Japan's central bank raised interest rates for the first time in 17 years, ending its negative rate policy."),
    ("LG-013", "The US Senate passed a bipartisan bill allocating 550 billion dollars for roads, bridges and broadband."),
    ("LG-014", "Tesla reported its first quarterly revenue decline in four years amid growing competition in the EV market."),
    ("LG-015", "Berkshire Hathaway's annual report showed operating earnings of 37.4 billion dollars, a record for the company."),

    # Technology
    ("LG-016", "Apple released a new chip architecture delivering a 40 percent improvement in energy efficiency over its predecessor."),
    ("LG-017", "OpenAI released GPT-4 with significantly improved reasoning, multimodal capabilities and a longer context window."),
    ("LG-018", "Google's DeepMind announced AlphaFold 3, capable of predicting the structure of all biological molecules."),
    ("LG-019", "Microsoft announced a 10,000-employee layoff representing approximately 4 percent of its global workforce."),
    ("LG-020", "Samsung unveiled its new foldable smartphone at its Galaxy Unpacked event held in Seoul, South Korea."),
    ("LG-021", "Meta's AI research lab published a new large language model under an open-source licence for researchers."),
    ("LG-022", "The UK government published its AI safety framework following the Bletchley Park summit on frontier AI risks."),
    ("LG-023", "NVIDIA reported quarterly revenue of 22.1 billion dollars driven almost entirely by AI data centre demand."),
    ("LG-024", "Elon Musk's SpaceX successfully caught its Starship booster using the mechanical arms of the launch tower."),
    ("LG-025", "The G20 summit concluded with an agreement on a global framework for regulating artificial intelligence systems."),

    # Health / medicine (legitimate)
    ("LG-026", "A clinical trial published in the New England Journal of Medicine found the new drug reduced stroke risk by 22 percent."),
    ("LG-027", "The WHO approved a new malaria vaccine following phase-3 clinical trials conducted in three African countries."),
    ("LG-028", "Researchers at Oxford University found a Mediterranean diet reduces cardiovascular disease risk by 25 percent."),
    ("LG-029", "A peer-reviewed study in The Lancet found daily aspirin use reduces colorectal cancer risk by 19 percent."),
    ("LG-030", "A review of 72 peer-reviewed studies found no credible evidence linking the MMR vaccine to autism."),
    ("LG-031", "Health authorities confirmed the mRNA COVID vaccine does not alter human DNA, citing three independent reviews."),
    ("LG-032", "The CDC updated its guidance on COVID booster timing based on a large-scale observational study of 1.2 million people."),
    ("LG-033", "A study in JAMA found that GLP-1 receptor agonists reduced cardiovascular events by 20 percent in diabetic patients."),
    ("LG-034", "Researchers at MIT developed a new antibiotic using machine learning that kills drug-resistant bacteria in mice."),
    ("LG-035", "The FDA approved a new gene therapy for sickle cell disease following successful phase-3 clinical trial results."),
    ("LG-036", "A Cochrane review found that surgical masks reduce influenza transmission by approximately 53 percent in community settings."),
    ("LG-037", "Public Health England confirmed childhood vaccination rates have remained above 90 percent for the third consecutive year."),
    ("LG-038", "A study published in Nature Medicine linked long-term air pollution exposure to increased dementia risk in adults."),
    ("LG-039", "Clinical trial results showed the new RSV vaccine was 82 percent effective in adults aged 60 and over."),
    ("LG-040", "Researchers found that regular exercise reduces the risk of developing type 2 diabetes by 30 percent over 10 years."),

    # Science
    ("LG-041", "NASA's James Webb Space Telescope captured the deepest infrared image of the universe ever taken."),
    ("LG-042", "Scientists at CERN announced the detection of a new particle consistent with theoretical predictions."),
    ("LG-043", "Astronomers confirmed the discovery of a potentially habitable exoplanet 40 light years from Earth."),
    ("LG-044", "Researchers successfully sequenced the genome of the woolly mammoth, raising the possibility of de-extinction."),
    ("LG-045", "A team at the University of Cambridge published a new quantum computing error-correction technique in Nature."),
    ("LG-046", "The Voyager 1 spacecraft sent data showing it had crossed into interstellar space beyond the heliosphere."),
    ("LG-047", "Scientists detected gravitational waves from the merger of two neutron stars using the LIGO observatory."),
    ("LG-048", "A new study in Science found that microplastics have been detected in human blood at measurable concentrations."),
    ("LG-049", "Researchers at Stanford developed a new solar cell achieving a record 29.8 percent energy conversion efficiency."),
    ("LG-050", "The Intergovernmental Panel on Climate Change warned that global temperatures could rise by 1.5 degrees by 2040."),

    # Environment / climate (legitimate reporting)
    ("LG-051", "Global carbon dioxide concentrations reached a record 421 parts per million according to NOAA monitoring data."),
    ("LG-052", "The UN Environment Programme reported that ozone layer recovery is on track, expected to fully recover by 2066."),
    ("LG-053", "A study in Nature found that global forest cover increased by 2.24 million square kilometres over the past 35 years."),
    ("LG-054", "The European Union agreed to phase out new petrol and diesel car sales by 2035 under its Fit for 55 package."),
    ("LG-055", "Australia experienced its hottest year on record in 2023, with a mean temperature 1.53 degrees above the average."),

    # Politics / geopolitics (factual)
    ("LG-056", "Parliament passed the climate bill with a majority vote, setting a net-zero emissions target by 2050."),
    ("LG-057", "The United Nations Security Council passed a ceasefire resolution for Gaza with 14 votes in favour and one abstention."),
    ("LG-058", "Ukraine and Russia held preliminary ceasefire negotiations in Turkey mediated by United Nations officials."),
    ("LG-059", "The International Criminal Court issued an arrest warrant for the Russian president over the deportation of Ukrainian children."),
    ("LG-060", "The Supreme Court ruled 6-3 to uphold the lower court decision on the redistricting case in North Carolina."),
    ("LG-061", "Brazil's Supreme Court upheld the conviction of the former president's allies for attempting to stage a coup."),
    ("LG-062", "The G7 nations agreed to use interest from frozen Russian assets to fund a 50 billion dollar loan to Ukraine."),
    ("LG-063", "The European Parliament held its first vote on a proposed new regulation governing artificial intelligence."),
    ("LG-064", "Taiwan's presidential election was won by the ruling DPP candidate with 40 percent of the vote."),
    ("LG-065", "Pakistan's Supreme Court ruled that the jailed former prime minister's party was entitled to reserved parliamentary seats."),

    # Sport
    ("LG-066", "Manchester City won the Premier League title for the fourth consecutive season on the final day of the campaign."),
    ("LG-067", "France won the UEFA Nations League final against Spain in a match that went to extra time in Paris."),
    ("LG-068", "India beat Australia by six wickets in the third Test match played in Melbourne to claim the series."),
    ("LG-069", "The IOC confirmed that Paris would host the 2024 Summer Olympic Games with 32 sports on the programme."),
    ("LG-070", "Novak Djokovic won his 24th Grand Slam title at the US Open, breaking the all-time record in the sport."),

    # Business / companies
    ("LG-071", "Volkswagen announced plans to close three factories in Germany as part of a major restructuring programme."),
    ("LG-072", "Disney reported quarterly revenue of 22.1 billion dollars, with streaming profitability ahead of expectations."),
    ("LG-073", "Airbus delivered a record 735 commercial aircraft in 2023, surpassing its previous annual delivery record."),
    ("LG-074", "Shell reported annual profits of 28 billion dollars, its second highest result following the 2022 energy crisis."),
    ("LG-075", "Boeing suspended production of its 737 MAX 9 aircraft temporarily following an emergency exit blowout incident."),

    # Disasters / natural events
    ("LG-076", "A magnitude 7.8 earthquake struck southern Turkey and northern Syria, killing more than 50,000 people."),
    ("LG-077", "Pakistan experienced its worst flooding in decades, affecting over 33 million people according to UN estimates."),
    ("LG-078", "The Maui wildfires destroyed the historic town of Lahaina in Hawaii, killing at least 100 people."),
    ("LG-079", "Hurricane Otis struck Acapulco as a Category 5 storm, killing over 50 people and causing widespread destruction."),
    ("LG-080", "An unusual heat wave in Europe set new national temperature records in the United Kingdom and Spain."),

    # Fact-checking / debunking (tricky — legit text about misinformation)
    ("LG-081", "PolitiFact rated the claim that the 2020 election was stolen as False after reviewing more than 60 court rulings."),
    ("LG-082", "WHO confirmed there is no evidence that chemtrails pose any health risk, calling the theory scientifically baseless."),
    ("LG-083", "Scientists refuted claims that 5G causes cancer, citing decades of research on non-ionising electromagnetic radiation."),
    ("LG-084", "A review of 72 studies found no credible evidence that vaccines cause autism in children or adults."),
    ("LG-085", "Health authorities confirmed the mRNA vaccine does not alter human DNA, contradicting viral social media posts."),
    ("LG-086", "Scientists debunked the flat-earth claim by citing independent satellite telemetry, GPS data and ship navigation."),
    ("LG-087", "The court rejected the election fraud claim, stating there was no evidence of widespread irregularities presented."),
    ("LG-088", "Researchers found no link between fluoride in drinking water and reduced IQ in a 30-year longitudinal study."),
    ("LG-089", "Experts disproved the theory that Bill Gates is using vaccines to implant tracking devices in recipients."),
    ("LG-090", "Snopes rated as False the claim that drinking bleach mixed with water cures respiratory viral infections."),
    ("LG-091", "A new study comprehensively debunked the claim that 5G towers spread COVID-19, finding no plausible mechanism."),
    ("LG-092", "WHO stated clearly that the COVID-19 vaccine does not contain microchips or any tracking technology whatsoever."),
    ("LG-093", "Scientists refuted the moon landing hoax claim, citing archived telemetry data and independent radar tracking evidence."),
    ("LG-094", "Researchers found no scientific evidence supporting the claim that chemtrails affect human immune function."),
    ("LG-095", "Fact-checkers at FullFact rated the claim that 5G radiation caused the pandemic as entirely false and baseless."),

    # Reporting on conspiracy / misinformation (edge cases — should be Legitimate)
    ("LG-096", "The government launched a public awareness campaign to counter vaccine misinformation spreading on social media."),
    ("LG-097", "Social media platforms removed thousands of posts falsely claiming election machines were connected to foreign servers."),
    ("LG-098", "A documentary examined how flat earth conspiracy theories spread on YouTube and radicalise believers over time."),
    ("LG-099", "Researchers studied why people believe in deep state conspiracies and what cognitive biases drive distrust of institutions."),
    ("LG-100", "YouTube demonetized channels spreading COVID misinformation including claims that vaccines contain microchips."),
    ("LG-101", "The government launched an inquiry into the spread of misinformation about voting machines following the election."),
    ("LG-102", "Academics examined how antisemitic conspiracy theories about the Rothschilds spread through social media algorithms."),
    ("LG-103", "A study found that exposure to debunking content reduces belief in conspiracy theories by 20 percent on average."),
    ("LG-104", "News organisations removed false claims about election fraud spreading on their platforms after the vote."),
    ("LG-105", "A team of researchers studied why people become radicalised by deep state beliefs and what interventions help."),

    # More fact-based news
    ("LG-106", "The World Health Organization declared monkeypox a public health emergency of international concern."),
    ("LG-107", "India's Chandrayaan-3 successfully landed near the south pole of the Moon, making India the fourth nation to do so."),
    ("LG-108", "Scientists at CERN announced the first observation of the Higgs boson decaying into two muons."),
    ("LG-109", "The International Monetary Fund approved a 15.6 billion dollar loan programme for Ukraine."),
    ("LG-110", "Google released its annual transparency report showing a 12 percent rise in government data requests globally."),
    ("LG-111", "A study in the British Medical Journal found that processed meat consumption raises bowel cancer risk by 18 percent."),
    ("LG-112", "The Reserve Bank of India held the repo rate unchanged at 6.5 percent for the sixth consecutive meeting."),
    ("LG-113", "An Oxford University study found that people who sleep fewer than six hours a night face higher dementia risk."),
    ("LG-114", "Researchers at Johns Hopkins published findings showing a link between gut bacteria diversity and mental health."),
    ("LG-115", "The FDA approved the first over-the-counter birth control pill in the United States following clinical trials."),
    ("LG-116", "Brazil deforested a record low area of Amazon rainforest in 2023, down 50 percent from 2022 according to INPE."),
    ("LG-117", "A Nature study confirmed that rewilding projects in Europe increased biodiversity by an average of 35 percent."),
    ("LG-118", "The IAEA confirmed Iran had enriched uranium to 60 percent purity at its Fordow facility."),
    ("LG-119", "A WHO report estimated that antimicrobial resistance caused 1.27 million deaths globally in 2019."),
    ("LG-120", "Scientists announced the discovery of the largest known prime number, containing over 41 million digits."),

    # Historical / institutional reporting
    ("LG-121", "The US House of Representatives voted 220 to 211 to pass the Inflation Reduction Act on party lines."),
    ("LG-122", "Netflix reported losing 970,000 subscribers in the second quarter, its worst result in over a decade."),
    ("LG-123", "The United Arab Emirates became the first Arab nation to land a spacecraft on Mars with the Hope mission."),
    ("LG-124", "WHO confirmed that polio has been eradicated from the African continent following a years-long vaccination campaign."),
    ("LG-125", "Brazil arrested 14 people in connection with an alleged coup plot following the 2022 presidential election."),
    ("LG-126", "A new Lancet study found that noise pollution from road traffic increases cardiovascular disease risk by 8 percent."),
    ("LG-127", "The UK Supreme Court ruled unanimously that the Rwanda asylum policy was unlawful under international law."),
    ("LG-128", "Scientists discovered a new species of deep-sea octopus living 3,000 metres below the surface of the Pacific."),
    ("LG-129", "The OECD published its annual report showing education spending increased in 28 of 38 member countries."),
    ("LG-130", "A study in the Journal of the American Heart Association found that walking 7,000 steps daily reduces mortality risk."),

    # International reporting
    ("LG-131", "The North Korean government confirmed a satellite launch that the UN said violated multiple security council resolutions."),
    ("LG-132", "Saudi Arabia and Iran agreed to restore diplomatic relations in a deal brokered by China in Beijing."),
    ("LG-133", "The African Union admitted Ethiopia after its suspension was lifted following the peace deal in Tigray."),
    ("LG-134", "Kosovo applied for membership in the Council of Europe with the backing of a majority of member states."),
    ("LG-135", "The Hague International Court of Justice ruled that Nicaragua must pay Colombia compensation over maritime borders."),

    # More debunking / analysis articles (legitimate)
    ("LG-136", "A comprehensive study found no evidence that the MMR vaccine is linked to autism after examining 1.2 million children."),
    ("LG-137", "Independent scientists found no evidence that chemtrails contain barium or strontium in harmful quantities."),
    ("LG-138", "The FDA confirmed that graphene oxide is not present in any approved COVID-19 vaccine formulations."),
    ("LG-139", "Researchers debunked the claim that the Pfizer vaccine contains a microchip after testing multiple vials."),
    ("LG-140", "A court-appointed expert found no evidence of systematic fraud after examining 147,000 mail-in ballots."),

    # More legitimate health
    ("LG-141", "A clinical trial published in Nature Medicine found a new CAR-T therapy achieved remission in 73 percent of patients."),
    ("LG-142", "WHO recommended a new oral cholera vaccine following successful field trials in three countries."),
    ("LG-143", "A study in Circulation found that Mediterranean diet adherence reduced all-cause mortality by 23 percent over 10 years."),
    ("LG-144", "Researchers confirmed that the HPV vaccine has reduced cervical cancer rates by 87 percent in vaccinated cohorts."),
    ("LG-145", "A Cochrane review found that antidepressants are more effective than placebo in treating moderate to severe depression."),

    # Tech and society
    ("LG-146", "The EU's Digital Markets Act came into force, requiring large tech platforms to open messaging to third parties."),
    ("LG-147", "A new report by the Alan Turing Institute found that AI hiring tools show measurable bias against minority applicants."),
    ("LG-148", "The UK Online Safety Act received royal assent, requiring platforms to remove illegal content more rapidly."),
    ("LG-149", "A study by researchers at Princeton found that misinformation spreads six times faster than accurate news on social media."),
    ("LG-150", "The European Parliament passed the AI Act, the world's first comprehensive legal framework for artificial intelligence."),

    # Economy and society
    ("LG-151", "The Office for National Statistics reported that UK house prices fell 1.8 percent over the previous 12 months."),
    ("LG-152", "The World Bank reported that the number of people living in extreme poverty fell to 9.3 percent globally in 2023."),
    ("LG-153", "A study by the Resolution Foundation found UK real wages grew by 2.1 percent in 2023 after two years of decline."),
    ("LG-154", "The US Consumer Price Index rose 3.4 percent year-on-year in April, above the Federal Reserve's 2 percent target."),
    ("LG-155", "OPEC+ agreed to extend production cuts of 3.66 million barrels per day through the end of 2024."),

    # More science
    ("LG-156", "Scientists announced the first successful synthesis of a self-replicating RNA molecule in a laboratory setting."),
    ("LG-157", "A team at the Broad Institute developed a new CRISPR base editing tool capable of correcting single-letter DNA errors."),
    ("LG-158", "The Parker Solar Probe became the closest human-made object to the sun, flying within 6.1 million kilometres."),
    ("LG-159", "Astronomers detected water vapour in the atmosphere of an exoplanet using the James Webb Space Telescope."),
    ("LG-160", "Scientists confirmed that the universe is approximately 13.8 billion years old using data from the Planck satellite."),

    # More legitimate diverse
    ("LG-161", "The International Labour Organization reported that global youth unemployment stood at 13.6 percent in 2023."),
    ("LG-162", "The UNHCR reported that the number of forcibly displaced people worldwide surpassed 110 million for the first time."),
    ("LG-163", "A new study in Science found that ocean acidification has increased by 26 percent since the industrial revolution."),
    ("LG-164", "The Global Fund reported that its programmes have saved 59 million lives from AIDS, tuberculosis and malaria since 2002."),
    ("LG-165", "India overtook China as the world's most populous country in 2023, reaching an estimated 1.43 billion people."),
]

passed = failed = 0
failures = []
label_stats = {"HD": [0, 0], "ML": [0, 0], "LG": [0, 0]}
prev_cat = ""

print(f"{'Test':<9}  {'Exp':<4}  {'Got':<18}  {'Conf':>6}  Result")
print("=" * 70)

for name, text in tests:
    expected = name[:2]
    label, conf, reasons, rec, ctype = predict(text)
    short = {"Highly Deceptive": "HD", "Misleading": "ML", "Legitimate": "LG"}.get(label, "??")
    ok = short == expected
    label_stats[expected][1] += 1
    if ok:
        passed += 1
        label_stats[expected][0] += 1
    else:
        failed += 1
        failures.append((name, expected, label, conf, text[:80]))

    cur_cat = name[:2]
    if cur_cat != prev_cat:
        print()
        prev_cat = cur_cat

    result = "PASS" if ok else "!! FAIL !!"
    print(f"{name:<9}  {expected:<4}  {label:<18}  {conf:>5.1f}%  {result}")

print()
print("=" * 70)
print(f"TOTAL: {passed}/{len(tests)} passed  |  {failed} failed")
print()
print("Per-class breakdown:")
for cls, (p, t) in label_stats.items():
    bar = "#" * p + "-" * (t - p)
    print(f"  {cls}: {p:>3}/{t}  [{bar}]")

if failures:
    print()
    print("FAILURES:")
    for name, exp, got, conf, txt in failures:
        print(f"  {name}: expected {exp}, got {got} ({conf:.1f}%)")
        print(f"         \"{txt}\"")
else:
    print()
    print("All tests passed.")
