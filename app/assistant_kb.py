"""Knowledge base for the Get My Money Back demo assistant.

Auto-generated. Drives MaxAI when no live Pine backend is connected.
Every answer is compliant: matches are 'potential', claiming is free directly
with the state, SmartCredit never holds funds or charges a finder's fee.
Generated: 2026-06-03
"""

KB: dict = {'greeting': "Hi! I'm MaxAI, your SmartCredit money-finder. I can help you understand the potential "
             'unclaimed-property matches we found in your name and walk you through filing your '
             'claim for free, directly with the State of California. Just so you know up front: '
             "SmartCredit isn't affiliated with the state, we never hold your money, and we never "
             "charge a finder's fee. What would you like to know?",
 'suggested_prompts': ['What is unclaimed property?',
                       'How do I file my claim in California?',
                       'What documents will I need?',
                       'Is this really free?',
                       'Is Get My Money Back safe — or is this a scam?',
                       'Why can SmartCredit see this?'],
 'intents': [{'intent': 'what_is_unclaimed_property',
              'triggers': ['what is unclaimed property',
                           'what is unclaimed money',
                           'what does unclaimed mean',
                           'what are unclaimed funds',
                           'explain unclaimed property',
                           'what is this money'],
              'answer': 'Unclaimed property is money that belongs to you but got lost track of — '
                        'things like a forgotten bank balance, an old security deposit, an '
                        'uncashed paycheck or refund, or an insurance payout. After a holder (a '
                        "bank, employer, or insurer) can't reach you for a while, they're required "
                        'by law to hand it over to the state for safekeeping. California holds it '
                        'for you indefinitely until you claim it. Get My Money Back simply helps you spot '
                        'money that may be waiting for you so you can go get it back.'},
             {'intent': 'how_myreclaim_finds_matches',
              'triggers': ['how does myreclaim work',
                           'how do you find matches',
                           'how does this find money',
                           'how do you know this is mine',
                           'where does this data come from',
                           'how does the search work'],
              'answer': "California's State Controller publishes the official list of unclaimed "
                        'property, and we cross-check those public records against the name and '
                        'address details on your SmartCredit profile. When the details line up, we '
                        'surface it as a potential match for you to review. Because names and '
                        'addresses change over time, every result is a potential match, not a '
                        "guarantee — you'll confirm it's really yours when you file directly with "
                        'the state. Right now we search California records, with more states on '
                        'the way.'},
             {'intent': 'match_sections_meaning',
              'triggers': ['what does potential mean',
                           'what is a new match',
                           'what does already-claimed mean',
                           'what are the sections',
                           'potential new already claimed',
                           'what do these labels mean',
                           'what does the status mean'],
              'answer': 'We sort your results into a few simple buckets. "Potential" matches are '
                        'records that look like they could be yours based on your name and address '
                        '— likely, but not confirmed until the state verifies them. "New" flags a '
                        "potential match we surfaced since you last checked, so it's easy to spot "
                        'fresh finds. "Already-claimed" means a record you\'ve previously filed on '
                        "or marked as handled, so you don't chase the same money twice. In every "
                        'case, the State of California makes the final call on ownership when you '
                        'file.'},
             {'intent': 'how_to_file_in_ca',
              'triggers': ['how do i file',
                           'how to claim',
                           'how do i claim in california',
                           'steps to file',
                           'how do i get my money',
                           'file a claim ca',
                           'claim process'],
              'answer': 'Filing in California is free and you do it directly with the state. '
                        "Here's the path: 1) Tap the claim link on your match to go to the state's "
                        'official site, claimit.ca.gov. 2) Search or confirm the property the '
                        'state shows for your name. 3) Start the claim and answer their questions '
                        'to confirm your identity and your connection to the property. 4) Upload '
                        'the documents they request. 5) Submit, and the State of California '
                        'reviews it and pays you directly. Get My Money Back just hands you off to the '
                        'official site — we never file on your behalf or touch your payment, and '
                        'you can always verify everything straight with the state.'},
             {'intent': 'documents_needed',
              'triggers': ['what documents do i need',
                           'what do i need to file',
                           'what paperwork',
                           'required documents',
                           'proof needed',
                           'what id do i need',
                           'documents to claim'],
              'answer': 'California will tell you exactly what they need during the claim, and it '
                        "depends on the property, but it's usually straightforward. Expect to "
                        'provide proof of your identity (like a government-issued photo ID and '
                        "your Social Security number) and proof that you're connected to the "
                        'listed address or the property — for example, an old utility bill, bank '
                        'statement, or paycheck stub. Higher-value or business claims can ask for '
                        'a bit more. Always follow the document checklist on claimit.ca.gov, since '
                        "the state's instructions are the official word."},
             {'intent': 'how_long_it_takes',
              'triggers': ['how long does it take',
                           'when will i get paid',
                           'processing time',
                           'how long to get money',
                           'timeline',
                           'how long for the claim',
                           'when do i get my money'],
              'answer': 'Timing is set by the State of California, not by SmartCredit. Many '
                        'straightforward claims are processed within a few weeks once the state '
                        'has everything it needs, while claims that require extra documentation or '
                        'verification can take a few months. The fastest way to keep things moving '
                        'is to submit complete, accurate documents the first time. For the current '
                        'official timeframe, check claimit.ca.gov or contact the State '
                        "Controller's office directly."},
             {'intent': 'is_it_free',
              'triggers': ['is it free',
                           'is this really free',
                           'do i have to pay',
                           'is there a fee',
                           'how much does it cost',
                           'do you charge',
                           'finder fee',
                           'free to claim'],
              'answer': 'Yes — claiming your property is completely free, and you file directly '
                        'with the State of California at claimit.ca.gov. SmartCredit never charges '
                        "a finder's fee and never takes a cut of what you recover; surfacing these "
                        'matches is just part of your membership. You should never have to pay '
                        "anyone to claim what's already yours, and the state pays you directly. If "
                        'anyone asks for a percentage to "recover" your money, that\'s a red '
                        'flag.'},
             {'intent': 'name_or_address_slightly_off',
              'triggers': ['name is spelled wrong',
                           'address is wrong',
                           "details don't match",
                           'name is slightly off',
                           'is this still mine',
                           'wrong middle name',
                           'old address',
                           "name doesn't match exactly"],
              'answer': "A small mismatch is common and doesn't mean the money isn't yours. "
                        'Records often use a maiden name, a nickname, a misspelling, or an address '
                        'you lived at years ago, so we surface close matches as potential on '
                        'purpose. The State of California is who confirms ownership — when you '
                        'file at claimit.ca.gov, you can document the connection (like a former '
                        "name or a prior address) and they'll verify it. If a record clearly isn't "
                        "you, it's fine to skip it; only claim property that genuinely belongs to "
                        'you.'},
             {'intent': 'deceased_relative_estate',
              'triggers': ['deceased relative',
                           'my parent died',
                           'claim for someone who died',
                           'inheritance',
                           'estate claim',
                           'passed away',
                           'claim for a deceased person',
                           'my late mother',
                           'heir'],
              'answer': "First, I'm sorry for your loss. Claiming property for someone who has "
                        "passed away is a separate, more involved process — it's an estate or heir "
                        'claim, and the State of California requires additional legal '
                        'documentation (such as proof of your authority to act for the estate). '
                        "Get My Money Back's self-file flow is built for claiming your own property, so we "
                        "don't guide estate claims here. Please go directly to claimit.ca.gov for "
                        'their deceased-owner/estate instructions, and consider speaking with the '
                        "estate's executor or an attorney to make sure it's handled correctly."},
             {'intent': 'other_states_not_supported',
              'triggers': ['other states',
                           'i live in texas',
                           'what about new york',
                           'do you search all states',
                           'my money is in another state',
                           'states besides california',
                           'florida ohio arizona',
                           'not in california'],
              'answer': "Right now Get My Money Back searches California's unclaimed-property records, and "
                        "we're working to add more states. If your money is held in another state, "
                        "you can still claim it for free directly with that state's official "
                        "unclaimed-property office — tell me which state and I'll point you to its "
                        'portal. Every U.S. state runs its own free claim site, and the official '
                        'directory at unclaimed.org links to all of them. As always, claiming is '
                        'free and you never need a paid finder.'},
             {'intent': 'is_it_a_scam_safe',
              'triggers': ['is this a scam',
                           'is this safe',
                           'is this legit',
                           'is this real',
                           'sounds too good to be true',
                           'is myreclaim a scam',
                           'can i trust this',
                           'is this fraud'],
              'answer': "It's a fair question to ask, and skepticism is healthy. Unclaimed "
                        'property is real and government-run: California genuinely holds billions '
                        'in lost funds and lets you claim yours for free at claimit.ca.gov. '
                        'Get My Money Back only points you to those official records — we never hold your '
                        "money, never charge a finder's fee, and aren't affiliated with the State "
                        'of California. A few scam tell-tales to watch for elsewhere: anyone who '
                        'asks for an upfront payment or a percentage to "release" your funds, or '
                        'who pressures you to pay fast. With Get My Money Back, you file directly with the '
                        'state and verify everything yourself.'},
             {'intent': 'privacy_why_smartcredit_sees_this',
              'triggers': ['why can you see this',
                           'how do you have my info',
                           'privacy',
                           'is my data safe',
                           'why does smartcredit know',
                           'what about my personal information',
                           'how did you get my name',
                           'data privacy'],
              'answer': 'Get My Money Back uses the identity details you already gave SmartCredit — like '
                        "your name and address — and matches them against California's public "
                        "unclaimed-property list. We're not pulling new private data to do this; "
                        "the state's owner-name records are publicly published, and we simply "
                        "compare them to your profile to flag potential matches. We don't sell "
                        'your information, and you stay in control: you decide which matches to '
                        'act on, and you file directly with the state. For specifics on how your '
                        "data is handled, see SmartCredit's privacy notice."},
             {'intent': 'what_is_pine_ai',
              'triggers': ['what is maxai',
                           'who is maxai',
                           'what is max',
                           "what's maxai",
                           'who are you',
                           'maxai',
                           'max'],
              'answer': "MaxAI is your SmartCredit assistant for unclaimed property. I search the "
                        "state's records for potential matches in your name and walk you through "
                        'claiming them — for free, directly with the State of California at '
                        'claimit.ca.gov. I never charge a fee, never hold your funds, and never '
                        'file on your behalf: you stay in control and the state confirms ownership. '
                        'Remember you should never have to pay a percentage to recover money that '
                        'is already yours.'},
             {'intent': 'what_is_smartcredit_role',
              'triggers': ['what does smartcredit do here',
                           'do you file for me',
                           'do you take my money',
                           "what is smartcredit's role",
                           'are you the state',
                           'do you handle my claim',
                           'are you affiliated with california'],
              'answer': 'Think of Get My Money Back as a helpful guide, not a middleman. We surface '
                        "potential matches and hand you off to the state's official site — we "
                        'never file the claim for you, never hold or touch your funds, and never '
                        "charge a finder's fee. SmartCredit is not affiliated with the State of "
                        'California; the state alone verifies ownership and pays you directly. '
                        "You're always free, and encouraged, to verify any match straight with "
                        'California at claimit.ca.gov.'},
             {'intent': 'no_matches_found',
              'triggers': ['no matches',
                           'nothing found',
                           "didn't find anything",
                           'i have no results',
                           'empty results',
                           'why no matches',
                           'found nothing'],
              'answer': "No matches today is good news in its own way — it means we didn't spot "
                        'California unclaimed property tied to your details right now. New '
                        "property is reported to the state regularly and we're expanding to more "
                        "states, so it's worth checking back; we'll surface anything new in your "
                        "matches. You can also search the state's official site yourself anytime, "
                        'for free, at claimit.ca.gov, including under a former name or a previous '
                        "address. There's never a fee to look or to claim."},
             {'intent': 'verify_with_state',
              'triggers': ['how do i verify',
                           'can i check with the state',
                           'confirm with california',
                           'double check this match',
                           'is this confirmed',
                           'official site',
                           'state controller contact'],
              'answer': 'Yes, please do — verifying directly with the state is always a good idea. '
                        'The official California site is claimit.ca.gov, run by the State '
                        "Controller's Office, where you can search the same records, confirm a "
                        'potential match is really yours, and file for free. Because our matches '
                        'are potential until the state verifies them, claimit.ca.gov is the final '
                        "source of truth on what you're owed. If anything we show doesn't line up "
                        "with the state's records, trust the state."}]}
