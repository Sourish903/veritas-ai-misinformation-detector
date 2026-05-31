from src.predict import predict

tests = [
    # ── HIGHLY DECEPTIVE ────────────────────────────────────────────────────
    ("HD-01", "The government is covering up the truth about 5G towers causing cancer and suppressing the cure."),
    ("HD-02", "Vaccines contain microchips installed by Bill Gates to track the population. Big Pharma is hiding this."),
    ("HD-03", "The moon landing was faked. Leaked NASA documents prove it was staged in a Hollywood studio."),
    ("HD-04", "Drinking bleach cures COVID-19. Doctors are being silenced for speaking out about this miracle cure."),
    ("HD-05", "The deep state and the Rothschilds are orchestrating the Great Reset to enslave humanity."),
    ("HD-06", "Sandy Hook was a staged false flag operation. The grieving parents are all crisis actors."),
    ("HD-07", "QAnon whistleblower reveals that elites are harvesting adrenochrome from trafficked children."),
    ("HD-08", "The earth is flat and NASA has been lying about it for decades. The globe is fake."),
    ("HD-09", "Chemtrails are being sprayed by governments to poison and depopulate the population."),
    ("HD-10", "Scientists found a secret miracle cure for cancer but Big Pharma is suppressing it to protect profits."),
    ("HD-11", "The stolen election was confirmed by a leaked document showing voting machines were rigged."),
    ("HD-12", "5G radiation suppresses the immune system and caused the spread of COVID-19."),
    ("HD-13", "WWG1WGA. The storm is coming. The deep state cabal is being exposed by the great awakening."),
    ("HD-14", "Ivermectin is a proven cure for COVID-19 but the government is suppressing it to push vaccines."),
    ("HD-15", "They do not want you to know that the MMR vaccine causes autism. The evidence is being hidden."),
    ("HD-16", "An insider leaked secret documents showing tech companies are suppressing voices online."),
    ("HD-17", "The Illuminati controls global banking and is engineering a financial collapse to enslave nations."),
    ("HD-18", "George Soros is funding and orchestrating the migrant crisis to destroy western civilization."),
    ("HD-19", "NASA is hiding evidence of alien life found on Mars. Leaked footage proves it was covered up."),
    ("HD-20", "The COVID-19 vaccine was designed as a bioweapon to depopulate the earth by 90 percent."),
    ("HD-21", "Hydroxychloroquine is a proven miracle cure suppressed by authorities to push expensive treatments."),
    ("HD-22", "The New World Order is planning to microchip every human being through mandatory vaccination."),
    ("HD-23", "Climate change is a hoax fabricated by globalists to impose carbon taxes and control economies."),
    ("HD-24", "HAARP is a secret government weather weapon used to engineer hurricanes and earthquakes."),
    ("HD-25", "Secret leaked documents prove the Holocaust death toll was fabricated and greatly exaggerated."),
    ("HD-26", "What they are hiding from you will change everything. Secret documents expose the real virus origin."),
    ("HD-27", "Big Pharma has suppressed the cure for diabetes. Whistleblowers are being threatened into silence."),
    ("HD-28", "The government secretly installed backdoors in all smartphones to stream audio to the NSA and CIA."),
    ("HD-29", "The deep state crisis actors staged the shooting to push gun control legislation against citizens."),
    ("HD-30", "NASA lies. The moon landing footage was faked and NASA has been covering it up since 1969."),
    # ── MISLEADING ──────────────────────────────────────────────────────────
    ("ML-01", "Studies show eating this superfood is guaranteed to boost your immunity by 85 percent."),
    ("ML-02", "According to unnamed sources, the minister is planning to resign before end of the month."),
    ("ML-03", "Scientists confirm a new diet can completely reverse type 2 diabetes in just 30 days."),
    ("ML-04", "Shocking new evidence exposed by an insider reveals massive voter fraud in the 2024 election."),
    ("ML-05", "AI will eliminate 95% of all jobs within 5 years, dramatically increasing unemployment worldwide."),
    ("ML-06", "An explosive new study reveals that 99% of people are deficient in this one vitamin."),
    ("ML-07", "Bombshell report: unnamed senior official says the prime minister knew about the scandal for months."),
    ("ML-08", "This simple trick is 100% proven to eliminate belly fat in just two weeks, doctors confirm."),
    ("ML-09", "Deceased voters were found on the rolls in three swing states, insiders claim."),
    ("ML-10", "New research shows this common household chemical dramatically increases cancer risk in 90% of users."),
    ("ML-11", "Shocking truth: unnamed study shows mobile phones reduce sperm count by 75 percent."),
    ("ML-12", "According to anonymous sources inside the White House, the president is planning a major military action."),
    ("ML-13", "Scientists confirm hidden ancient ruins prove mainstream history has been completely wrong all along."),
    ("ML-14", "Mail-in ballots from deceased voters were found in multiple counties, officials refusing to audit."),
    ("ML-15", "An unnamed insider says the central bank is secretly planning to raise interest rates next week."),
    ("ML-16", "Explosive report: voter fraud involving 90% of mail-in ballots found in key swing states."),
    ("ML-17", "Doctors are ignoring a major breakthrough that reverses Alzheimer symptoms in weeks."),
    ("ML-18", "Anonymous government insiders claim the president is hiding a serious health condition from the public."),
    ("ML-19", "Breaking: unnamed study confirms 5G towers dramatically increase radiation exposure in urban areas."),
    ("ML-20", "Scientists confirm that eating red meat is guaranteed to cause cancer within five years."),
    ("ML-21", "According to unnamed sources, the defence minister secretly authorised a military strike last month."),
    ("ML-22", "A bombshell allegation from an anonymous official claims the election was rigged in three states."),
    ("ML-23", "Shocking claim: 99% of population unknowingly exposed to toxic levels of fluoride in tap water."),
    ("ML-24", "Insiders leaked evidence that social media companies are deliberately boosting radical content by 90%."),
    ("ML-25", "An unnamed study proves common painkillers dramatically increase heart failure risk in 80% of users."),
    ("ML-26", "Unnamed government researchers found that sunscreen chemicals enter the bloodstream within one day."),
    ("ML-27", "An anonymous Wall Street insider says the stock market will crash by 90% before end of the year."),
    ("ML-28", "A bombshell claim from an unnamed doctor says hospitals are withholding an effective COVID treatment."),
    ("ML-29", "According to unnamed officials, the government secretly approved mass surveillance of all phone calls."),
    ("ML-30", "New shocking data shows 95% of all politicians are taking bribes from pharmaceutical companies."),
    # ── LEGITIMATE ──────────────────────────────────────────────────────────
    ("LG-01", "The Federal Reserve raised interest rates by 25 basis points on Wednesday, citing progress on inflation."),
    ("LG-02", "NASA successfully launched the Artemis II mission carrying four astronauts toward the Moon."),
    ("LG-03", "The World Health Organization approved a new malaria vaccine following clinical trials in three countries."),
    ("LG-04", "Parliament passed the climate bill with a majority vote, setting a net-zero emissions target by 2050."),
    ("LG-05", "A peer-reviewed study in Nature found a link between air pollution and cognitive decline in adults over 60."),
    ("LG-06", "India beat Australia by 6 wickets in the third Test match in Melbourne on Tuesday."),
    ("LG-07", "Apple reported quarterly earnings of 94 billion dollars, beating analyst expectations by 3 percent."),
    ("LG-08", "The Supreme Court ruled 6-3 to uphold the lower court decision on the redistricting case."),
    ("LG-09", "Scientists at CERN announced the detection of a new particle consistent with theoretical predictions."),
    ("LG-10", "The unemployment rate fell to 3.8 percent in March, according to the Bureau of Labor Statistics."),
    ("LG-11", "Researchers at Oxford University published findings showing a Mediterranean diet reduces heart disease risk."),
    ("LG-12", "Tesla recalled 125,000 vehicles due to a seatbelt warning system fault, the company confirmed on Friday."),
    ("LG-13", "The United Nations Security Council passed a ceasefire resolution with 12 votes in favour and 3 abstentions."),
    ("LG-14", "SpaceX successfully landed its Starship booster for the first time during a test flight over the Gulf of Mexico."),
    ("LG-15", "Google released its annual transparency report, showing a 12 percent increase in government data requests."),
    ("LG-16", "The European Central Bank held interest rates steady, citing easing inflation across the eurozone."),
    ("LG-17", "Manchester City won the Premier League title for the fourth consecutive season on Sunday."),
    ("LG-18", "India launched Chandrayaan-3 which successfully landed near the south pole of the Moon."),
    ("LG-19", "The IMF revised its global growth forecast to 3.2 percent for the current year."),
    ("LG-20", "A new study in The Lancet found daily aspirin use reduces colorectal cancer risk by 19 percent."),
    ("LG-21", "Microsoft announced it would lay off 10,000 employees, about 4 percent of its global workforce."),
    ("LG-22", "The Reserve Bank of India kept the repo rate unchanged at 6.5 percent for the third consecutive meeting."),
    ("LG-23", "Astronomers detected water vapour in the atmosphere of an exoplanet 700 light years from Earth."),
    ("LG-24", "The G20 summit concluded with member nations agreeing to a framework for regulating artificial intelligence."),
    ("LG-25", "Brazilian authorities arrested 14 people in connection with an alleged coup plot following the 2022 elections."),
    ("LG-26", "Health officials confirmed the vaccine does not cause autism, according to a study of over one million children."),
    ("LG-27", "Fact-checkers at PolitiFact rated the claim that 5G causes cancer as False, citing WHO guidelines."),
    ("LG-28", "The leaked diplomatic cables, published by the Guardian, revealed private discussions about trade tariffs."),
    ("LG-29", "Researchers found no credible evidence linking COVID-19 to 5G networks in a comprehensive review."),
    ("LG-30", "Scientists debunked the claim that the moon landing was faked, citing independent radar tracking data."),
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
