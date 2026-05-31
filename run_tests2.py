from src.predict import predict

tests = [
    # ── HIGHLY DECEPTIVE — new categories ───────────────────────────────────
    ("HD-01", "The Rockefellers are secretly controlling all major governments through a shadow banking cabal."),
    ("HD-02", "Fluoride in tap water is a government mind control agent designed to make the population docile."),
    ("HD-03", "The great awakening reveals that adrenochrome harvested from children powers the global elite."),
    ("HD-04", "Secret leaked memos prove that climate scientists fabricated temperature data for decades."),
    ("HD-05", "Bill Gates is using mosquitoes as drones to inject microchips into the unsuspecting population."),
    ("HD-06", "The government is hiding a free energy device that would end fossil fuel dependence forever."),
    ("HD-07", "COVID-19 was engineered as a bioweapon in a Wuhan lab and governments are covering up the evidence."),
    ("HD-08", "Natural immunity is 100 times better than any vaccine. The government is suppressing this finding."),
    ("HD-09", "The MMR vaccine is responsible for the autism epidemic. Pediatricians are paid to stay silent."),
    ("HD-10", "Leaked CIA files prove that multiple US presidents were assassinated by the deep state cabal."),
    ("HD-11", "5G towers are being used to beam mind control frequencies into urban populations worldwide."),
    ("HD-12", "The Rothschilds control the Federal Reserve and are orchestrating the collapse of the dollar."),
    ("HD-13", "Chemtrails contain barium and strontium used to suppress immune systems across the population."),
    ("HD-14", "The WHO is a front for Big Pharma and is hiding the cure for cancer to maintain drug profits."),
    ("HD-15", "Crisis actors were used at the Boston Marathon bombing. The whole event was staged by the government."),
    ("HD-16", "A whistleblower revealed that NASA fakes all space imagery using CGI and green screens."),
    ("HD-17", "They are hiding the fact that ivermectin cures all viral diseases including COVID-19 and HIV."),
    ("HD-18", "The New World Order has already installed surveillance backdoors in every smartphone sold after 2015."),
    ("HD-19", "George Soros funded the riots to destabilize the country and implement martial law."),
    ("HD-20", "Secret government documents prove that the 2020 election was stolen using Dominion voting machines."),

    # ── MISLEADING — new patterns ────────────────────────────────────────────
    ("ML-01", "A stunning new report claims that 90% of fast food contains dangerous levels of microplastics."),
    ("ML-02", "Unnamed medical experts say the new drug is 100% effective against all variants of the virus."),
    ("ML-03", "Bombshell claim: anonymous officials say the defence budget was secretly slashed by 80 percent."),
    ("ML-04", "Shocking study reveals drinking coffee is guaranteed to reduce your cancer risk by 95 percent."),
    ("ML-05", "According to unnamed sources in parliament, the government is planning secret tax hikes next month."),
    ("ML-06", "An explosive investigation by an insider exposes massive corruption at the heart of the judiciary."),
    ("ML-07", "Scientists confirm that eating sugar dramatically increases aggression in 99% of children studied."),
    ("ML-08", "Anonymous whistleblowers say the banking regulator is deliberately ignoring evidence of fraud."),
    ("ML-09", "New research suggests this common food additive dramatically increases Alzheimer risk in 85% of adults."),
    ("ML-10", "Mail-in votes from deceased individuals were found in seven counties, sources claim."),
    ("ML-11", "Unnamed Pentagon insiders say the military has been covering up UFO contact for decades."),
    ("ML-12", "A bombshell allegation from an anonymous senator claims the speaker accepted foreign payments."),
    ("ML-13", "According to unnamed researchers, social media use is guaranteed to cause depression in teenagers."),
    ("ML-14", "Shocking data shows 90% of mainstream news outlets are funded by pharmaceutical companies."),
    ("ML-15", "An unnamed study proves that electric vehicles are 95% more likely to catch fire than petrol cars."),
    ("ML-16", "Explosive claims from an anonymous government scientist say tap water causes infertility in 80% of men."),
    ("ML-17", "New evidence exposed by insiders suggests the prime minister secretly met foreign agents last year."),
    ("ML-18", "According to unnamed sources, the judiciary is being systematically pressured by the executive branch."),
    ("ML-19", "Unnamed health officials claim hospitals are dramatically under-reporting adverse vaccine events."),
    ("ML-20", "A bombshell report from an anonymous analyst says the stock market will collapse by 90% this quarter."),

    # ── LEGITIMATE — varied topics ───────────────────────────────────────────
    ("LG-01", "The Bank of England raised interest rates to 5.25 percent, the highest level in 15 years."),
    ("LG-02", "France won the UEFA Nations League final against Spain in a match decided by penalties."),
    ("LG-03", "Amazon reported a net profit of 10.4 billion dollars in its latest quarterly earnings statement."),
    ("LG-04", "The WHO declared monkeypox a global health emergency following outbreaks in 75 countries."),
    ("LG-05", "Astronomers using the James Webb Space Telescope discovered the oldest galaxy ever observed."),
    ("LG-06", "The Indian government announced a new scheme to provide free education to children under 14."),
    ("LG-07", "A clinical trial published in JAMA found that the new drug reduced stroke risk by 22 percent."),
    ("LG-08", "Ukraine and Russia held ceasefire talks in Turkey mediated by the United Nations on Thursday."),
    ("LG-09", "OpenAI released GPT-5 with significantly improved reasoning and multimodal capabilities."),
    ("LG-10", "The Intergovernmental Panel on Climate Change warned that global temperatures could rise by 2.5 degrees."),
    ("LG-11", "Pakistan experienced its worst flooding in decades, affecting over 33 million people according to the UN."),
    ("LG-12", "Samsung unveiled its new foldable smartphone series at its annual Galaxy Unpacked event in Seoul."),
    ("LG-13", "The International Criminal Court issued an arrest warrant for a sitting head of state for the first time."),
    ("LG-14", "Researchers at MIT developed a new battery technology that charges to 80 percent in five minutes."),
    ("LG-15", "The US Senate passed a bipartisan infrastructure bill allocating 550 billion dollars for roads and bridges."),
    ("LG-16", "The European Union fined Meta 1.2 billion euros for violating data protection regulations."),
    ("LG-17", "A magnitude 7.8 earthquake struck southern Turkey and Syria, killing more than 50,000 people."),
    ("LG-18", "Netflix reported losing 200,000 subscribers in the first quarter, its first decline in a decade."),
    ("LG-19", "The Reserve Bank of Australia held interest rates steady amid signs of slowing inflation."),
    ("LG-20", "Scientists successfully sequenced the genome of the woolly mammoth, opening possibilities for de-extinction."),

    # ── TRICKY — debunking, reporting on misinformation, nuanced ─────────────
    ("LG-21", "A new study comprehensively debunked the claim that 5G towers spread COVID-19, finding no biological mechanism."),
    ("LG-22", "PolitiFact rated the claim that the election was stolen as False after reviewing court documents."),
    ("LG-23", "WHO confirmed there is no evidence that chemtrails pose any health risk, calling the theory baseless."),
    ("LG-24", "A review of 72 studies found no credible evidence that vaccines cause autism in children."),
    ("LG-25", "Health authorities confirmed the mRNA vaccine does not alter human DNA, contradicting viral social media posts."),
    ("LG-26", "Scientists refuted claims that the moon landing was faked, citing archived telemetry and third-party radar data."),
    ("LG-27", "The court rejected the election fraud claim, saying there was no evidence of widespread irregularities."),
    ("LG-28", "Researchers found no link between fluoride in drinking water and cognitive decline in a 30-year study."),
    ("LG-29", "Experts disproved the theory that Bill Gates is using vaccines to implant tracking devices."),
    ("LG-30", "Snopes rated as False the claim that drinking bleach cures respiratory infections."),

    # ── EDGE CASES ───────────────────────────────────────────────────────────
    # Legitimate text mentioning conspiracy in news context
    ("LG-31", "The government launched a public awareness campaign to counter vaccine misinformation on social media."),
    ("LG-32", "Social media companies removed thousands of posts spreading false claims about election fraud."),
    ("LG-33", "A documentary examined how flat earth conspiracy theories spread online and radicalize believers."),
    ("LG-34", "Researchers studied why people believe in deep state conspiracies and what drives distrust of institutions."),
    ("LG-35", "YouTube demonetized channels spreading COVID misinformation including vaccine microchip theories."),
    # Genuinely ambiguous — system should still pick a side
    ("ML-21", "Unnamed sources say the government is hiding details about the new surveillance programme from parliament."),
    ("ML-22", "An anonymous official claims the minister misused public funds, allegations the ministry denied."),
    ("ML-23", "According to insiders, the pharmaceutical company suppressed data on side effects in the clinical trial."),
    ("ML-24", "Shocking report: an unnamed regulator says food safety standards were quietly lowered last year."),
    ("ML-25", "An explosive claim from an anonymous source says the army secretly tested biological agents on civilians."),
]

passed = failed = 0
failures = []
label_stats = {"HD": [0, 0], "ML": [0, 0], "LG": [0, 0]}
prev_cat = ""

print(f"{'Test':<7}  {'Exp':<4}  {'Got':<18}  {'Conf':>6}  Result")
print("=" * 65)

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
        failures.append((name, expected, label, conf, text[:75]))

    cur_cat = name[:2]
    if cur_cat != prev_cat:
        print()
        prev_cat = cur_cat

    result = "PASS" if ok else "!! FAIL !!"
    print(f"{name:<7}  {expected:<4}  {label:<18}  {conf:>5.1f}%  {result}")

print()
print("=" * 65)
print(f"TOTAL: {passed}/{len(tests)} passed  |  {failed} failed")
print()
print("Per-class breakdown:")
for cls, (p, t) in label_stats.items():
    bar = "#" * p + "-" * (t - p)
    print(f"  {cls}: {p:>2}/{t}  [{bar}]")

if failures:
    print()
    print("FAILURES:")
    for name, exp, got, conf, txt in failures:
        print(f"  {name}: expected {exp}, got {got} ({conf:.1f}%)")
        print(f"         \"{txt}\"")
else:
    print()
    print("All tests passed.")
