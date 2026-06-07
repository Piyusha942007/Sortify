import datetime

# Mock Stats
stats = {
    "composition": {
        "Personal": 20,
        "Promotions": 18,
        "Social": 12,
        "Updates": 10
    },
    "total_sorted": 247,
    "total_emails": 307,
    "replies_drafted": 41,
    "unsubscribed_senders": 19,
    "threats_blocked": 2,
    "time_saved_sorting": "3h 12m",
    "time_saved_drafts": "1h 45m",
    "time_saved_total_mins": 297  # 192 mins + 105 mins
}

# 5 Active Smart Rules
rules = [
    {"id": 101, "user_id": "demo_user", "label": "Finance/Invoices", "domain": "stripe.com", "reply_template": None},
    {"id": 102, "user_id": "demo_user", "label": "University/Grades", "domain": "registrar.edu", "reply_template": None},
    {"id": 103, "user_id": "demo_user", "label": "Work/Updates", "domain": "slack.com", "reply_template": "Acknowledge message receipt and say I will check it in 1 hour."},
    {"id": 104, "user_id": "demo_user", "label": "Food Delivery", "domain": "ubereats.com", "reply_template": None},  # NL rule
    {"id": 105, "user_id": "demo_user", "label": "Campus/Placements", "domain": "careeroffice.edu", "reply_template": None}  # NL rule
]

# Unsubscribed Senders lists
# 14 auto-unsubscribed (conf >= 0.85)
unsubscribed_done = [
    {"id": 1, "sender": "Pinterest Digest", "sender_email": "digest@pinterest.com", "subject": "Pins you might like this week", "confidence": 0.95, "date_unsubscribed": "2026-06-06 14:23:11", "mailto_link": "mailto:unsubscribe@pinterest.com", "http_link": "https://pinterest.com/unsub"},
    {"id": 2, "sender": "Duolingo", "sender_email": "duo@duolingo.com", "subject": "Don't lose your 15-day streak!", "confidence": 0.92, "date_unsubscribed": "2026-06-05 09:12:45", "mailto_link": "mailto:unsub@duolingo.com", "http_link": "https://duolingo.com/unsubscribe"},
    {"id": 3, "sender": "Lyft Promotions", "sender_email": "no-reply@lyftmail.com", "subject": "Get 15% off your next 3 rides", "confidence": 0.88, "date_unsubscribed": "2026-06-05 18:30:00", "mailto_link": None, "http_link": "https://lyft.com/unsub"},
    {"id": 4, "sender": "Quora Digest", "sender_email": "digest-noreply@quora.com", "subject": "Why do programming languages use semicolons?", "confidence": 0.94, "date_unsubscribed": "2026-06-04 11:05:12", "mailto_link": "mailto:unsubscribe@quora.com", "http_link": "https://quora.com/unsub"},
    {"id": 5, "sender": "Goodreads", "sender_email": "info@goodreads.com", "subject": "June's most anticipated new releases", "confidence": 0.89, "date_unsubscribed": "2026-06-04 08:00:00", "mailto_link": "mailto:unsub@goodreads.com", "http_link": "https://goodreads.com/unsub"},
    {"id": 6, "sender": "Adobe Systems", "sender_email": "creativecloud@adobe.com", "subject": "Introducing new AI features in Photoshop", "confidence": 0.87, "date_unsubscribed": "2026-06-03 16:40:15", "mailto_link": None, "http_link": "https://adobe.com/unsub"},
    {"id": 7, "sender": "Grammarly Weekly", "sender_email": "weekly@grammarly.com", "subject": "Your writing stats for last week", "confidence": 0.86, "date_unsubscribed": "2026-06-03 10:15:22", "mailto_link": "mailto:unsubscribe@grammarly.com", "http_link": "https://grammarly.com/unsub"},
    {"id": 8, "sender": "Medium Digest", "sender_email": "noreply@medium.com", "subject": "10 python design patterns you should know", "confidence": 0.91, "date_unsubscribed": "2026-06-02 07:11:04", "mailto_link": "mailto:unsub@medium.com", "http_link": "https://medium.com/unsub"},
    {"id": 9, "sender": "Product Hunt", "sender_email": "hello@producthunt.com", "subject": "Meet Sortify: The AI Email Triage App", "confidence": 0.90, "date_unsubscribed": "2026-06-02 12:45:00", "mailto_link": None, "http_link": "https://producthunt.com/unsubscribe"},
    {"id": 10, "sender": "Figma Newsletter", "sender_email": "news@figma.com", "subject": "Config 2026 announcements & tickets", "confidence": 0.88, "date_unsubscribed": "2026-06-01 15:30:29", "mailto_link": "mailto:unsub@figma.com", "http_link": "https://figma.com/unsub"},
    {"id": 11, "sender": "Uber Promos", "sender_email": "uber@uber.com", "subject": "Your weekend ride discount is expiring", "confidence": 0.93, "date_unsubscribed": "2026-05-31 19:20:10", "mailto_link": None, "http_link": "https://uber.com/unsub"},
    {"id": 12, "sender": "Coursera Announcements", "sender_email": "learn@coursera.org", "subject": "New courses from top universities", "confidence": 0.85, "date_unsubscribed": "2026-05-30 09:05:41", "mailto_link": "mailto:unsub@coursera.org", "http_link": "https://coursera.org/unsub"},
    {"id": 13, "sender": "Meetup Updates", "sender_email": "info@meetup.com", "subject": "8 new Tech meetups near you this week", "confidence": 0.90, "date_unsubscribed": "2026-05-29 11:15:33", "mailto_link": "mailto:unsubscribe@meetup.com", "http_link": "https://meetup.com/unsub"},
    {"id": 14, "sender": "Substack Feed", "sender_email": "substack@substack.com", "subject": "Read the latest essays from your subscriptions", "confidence": 0.89, "date_unsubscribed": "2026-05-28 08:30:00", "mailto_link": "mailto:unsub@substack.com", "http_link": "https://substack.com/unsub"}
]

# 5 pending review (conf 0.50-0.84)
unsubscribed_queue = [
    {"id": 15, "sender": "HackerNews Digest", "sender_email": "hn-digest@hn.com", "subject": "Top posts: Show HN: Sortify AI", "confidence": 0.82, "date": "2026-06-07 09:41:21", "mailto_link": "mailto:unsub@hn.com", "http_link": "https://hn.com/unsub"},
    {"id": 16, "sender": "FreeCodeCamp", "sender_email": "newsletter@freecodecamp.org", "subject": "Learn Python algorithms in 10 hours", "confidence": 0.76, "date": "2026-06-07 08:12:00", "mailto_link": "mailto:unsub@freecodecamp.org", "http_link": "https://freecodecamp.org/unsubscribe"},
    {"id": 17, "sender": "StackOverflow Updates", "sender_email": "answers@stackoverflow.com", "subject": "Weekly digest: javascript questions you can answer", "confidence": 0.68, "date": "2026-06-06 23:45:00", "mailto_link": None, "http_link": "https://stackoverflow.com/unsub"},
    {"id": 18, "sender": "Skillshare", "sender_email": "classes@skillshare.com", "subject": "Start your 1-month premium trial now!", "confidence": 0.74, "date": "2026-06-06 17:30:10", "mailto_link": "mailto:unsub@skillshare.com", "http_link": "https://skillshare.com/unsub"},
    {"id": 19, "sender": "Dev.to Weekly", "sender_email": "weekly@dev.to", "subject": "Why junior developers struggle with git hooks", "confidence": 0.80, "date": "2026-06-06 10:20:00", "mailto_link": "mailto:unsub@dev.to", "http_link": "https://dev.to/unsub"}
]

# 2 Phishing Flags
phishing_flags = [
    {
        "id": "phish_1",
        "sender": "Netflix Support <billing-support@netflix-update-billing.com>",
        "subject": "URGENT: Your Netflix subscription is suspended. Update your payment details immediately.",
        "threat_description": "Spoofed billing domain. Phishing link detected attempting to steal credit card details. Urgent language requesting instant sign-in.",
        "received_at": "2026-06-07 09:12:00"
    },
    {
        "id": "phish_2",
        "sender": "Chase Alerts <alert-security@chase-bank-verify-access.com>",
        "subject": "Warning: Unusual login attempt detected. Confirm your identity within 24 hours.",
        "threat_description": "Suspected lookalike domain mismatching Chase Bank official servers. Target URL mimics login portal to harvest credentials.",
        "received_at": "2026-06-06 20:05:00"
    }
]

# 20 Live Action Log events
live_logs = [
    "✦ Sortify AI v2 initialization complete (Demo Mode activated).",
    "[Smart Rules] Synced 5 rules successfully.",
    "[Phishing Detector] Scan finished. 2 potential threats flagged in quarantine.",
    "[Unsubscribe Agent] Automatically processed 14 high-confidence newsletters.",
    "[Overview] Weekly statistics and heatmap metrics loaded.",
    "[Gemini AI] Auto-drafted replies generated for Work/Updates.",
    "[Smart Rules] Applied Finance/Invoices label to 4 emails from stripe.com.",
    "[Snooze Agent] Checked snooze timers. No expired snoozes found.",
    "[Unsubscribe Agent] 5 newsletter senders queued for manual review.",
    "[Gemini AI] Suggested rule: 'Move stripe.com emails to Finance/Invoices' with confidence 96%.",
    "[Smart Rules] Applied University/Grades to 3 emails from registrar.edu.",
    "[Plugin System] Phishing Detector scanned 60 items in inbox.",
    "[Overview] Heatmap data rendering peak hours: Tuesdays at 10 AM.",
    "[Unsubscribe Agent] Unsubscribed from 'Pinterest Digest' (digest@pinterest.com).",
    "[Snooze Agent] Email 'Meeting coordinates' snoozed until 2026-06-08 09:00:00.",
    "[Gemini AI] Thread summary generated for thread ID 'th_10' in 0.4s.",
    "[Rule Learner] Tracked manual Gmail move: Stripe domain to 'Finance/Invoices'.",
    "[Auto-Reply] Auto-drafted reply for Slack alert: 'Checking in 1 hour...'",
    "[Cleanup Assistant] Scanned promotions: 12 emails ready to archive.",
    "[System] Demo mode session verified. Operational latency set to 1.2s."
]

# 60 Mock Emails
# Personal: 20, Promotions: 18, Social: 12, Updates: 10
emails = []

# Helper to generate dates
def get_date(hours_ago):
    dt = datetime.datetime.now() - datetime.timedelta(hours=hours_ago)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# PERSONAL (20)
personal_data = [
    ("Mom", "mom@gmail.com", "Sunday Roast plans", "Hey honey, just wanted to check if you're coming over for Sunday roast this weekend? Let me know if you can bring some dessert! Love, Mom.", 1),
    ("Alex Rivers", "alex.rivers@outlook.com", "Project update & coffee?", "Hey! It's been a while. Do you have some time this week to grab coffee? I wanted to show you the latest mockups for the app design we discussed.", 2),
    ("Professor Vance", "dvance@university.edu", "Research assistantship application", "Dear Student, I have reviewed your application for the research assistant position. Your background in Python and NLP looks promising. Are you available for a brief interview tomorrow at 2 PM?", 3),
    ("Sarah Jenkins", "sarah.j@gmail.com", "Photos from our road trip!", "Oh my gosh, we had so much fun! Here are the photos from the Grand Canyon trip. Let's plan the next one soon, maybe Yosemite in the fall?", 5),
    ("John Doe", "john.doe@gmail.com", "Can you review this resume?", "Hey, I'm applying for a software engineering internship and was wondering if you could take a quick look at my resume? I've attached it below. Thanks!", 6),
    ("Emma Watson", "emma@gmail.com", "Book recommendation", "Hey, you mentioned you were looking for a good sci-fi book. I just finished 'Project Hail Mary' and it was absolutely incredible! You should definitely check it out.", 8),
    ("Grandpa", "grandpa@yahoo.com", "Happy Birthday!", "Happy birthday, kiddo! Hope you have a wonderful day and a great year ahead. Let me know when you receive the card I sent in the mail.", 12),
    ("Landlord", "management@cityapartments.com", "Lease Renewal Option", "Hello, your lease at Apartment 4B is expiring in 60 days. Please let us know if you plan to renew by the end of the month. The new rent rate is attached.", 14),
    ("David Lee", "david.lee@gmail.com", "Weekend basketball?", "Hey, we are getting a group together for basketball at the park this Saturday at 10 AM. Can you make it? Let me know so we have enough players.", 16),
    ("Katie Smith", "katie@gmail.com", "Dinner party RSVP", "Hey! Just wanted to confirm that I will be coming to your dinner party on Friday. I'll bring a bottle of wine. Can't wait!", 18),
    ("Dr. Lisa Kudrow", "lkudrow@dentalclinic.com", "Appointment Confirmation", "Dear Patient, this is a friendly reminder of your upcoming dental cleaning on June 15th at 9:00 AM. Please call us if you need to reschedule.", 20),
    ("Brian O'Conner", "brian@fastcars.com", "Car repair quote", "Hey, I took a look at the brakes. It's going to cost about $250 for the pads and labor. Let me know if you want me to go ahead with the repair.", 22),
    ("Uncle Bob", "bob@gmail.com", "Family reunion details", "Hey everyone, the family reunion will be held at Lake Tahoe this year from July 10-15. Please RSVP so we can finalize the cabin bookings.", 24),
    ("Rachel Green", "rachel@bloomingdales.com", "Fashion advice needed", "Hey, I'm working on a new collection layout and would love to get your opinion on these design choices. Are you free for a call tomorrow morning?", 26),
    ("Lisa Simpson", "lisa@springfield.org", "Saxophone recital", "Hi! My jazz band recital is this Thursday evening at the community center. I would be so happy if you could come and watch us play!", 28),
    ("Peter Parker", "peter@dailybugle.com", "Freelance photos submission", "Hey Mr. Jameson, here are the photos of Spider-Man you requested for the front page. Hope the quality is sufficient. Let me know about the payment.", 30),
    ("Bruce Wayne", "bruce@waynecorp.com", "Charity Gala Invitation", "You are cordially invited to the annual Wayne Foundation Charity Gala on Friday evening. Black tie attire required. RSVP by Wednesday.", 36),
    ("Clark Kent", "clark@dailyplanet.com", "Interview notes", "Hey, here are the notes from my interview with the city mayor. I think there are some really interesting points here for the front page story.", 40),
    ("Tony Stark", "tony@starkindustries.com", "Internship opportunity", "Kid, saw your project on GitHub. Impressive work with the email agent. How would you like to do some freelance development for Stark Industries? Let me know.", 48),
    ("Steve Rogers", "steve@avengers.org", "Gym training session", "Hey, let's hit the gym tomorrow morning at 6 AM. Consistency is key. Don't be late!", 72)
]

for i, (name, email, subj, body, hrs) in enumerate(personal_data):
    emails.append({
        "id": f"msg_p_{i}",
        "thread_id": f"th_p_{i}",
        "sender": f"{name} <{email}>",
        "sender_email": email,
        "subject": subj,
        "body": body,
        "snippet": body[:80] + "...",
        "category": "Personal",
        "date": get_date(hrs),
        "label": None,
        "snoozed_until": None,
        "reason": None,
        "thread_messages": [
            {"sender": f"{name} <{email}>", "body": body, "date": get_date(hrs)}
        ]
    })

# PROMOTIONS (18)
promotions_data = [
    ("Amazon Deals", "deals@amazon.com", "Lightning Deals of the day: Up to 40% off electronics", "Don't miss out on today's lightning deals! Save on headphones, smart home devices, and laptops. Free shipping for Prime members.", 1),
    ("Uber Eats", "promo@ubereats.com", "Hungry? Here is 20% off your next lunch order", "Craving something delicious? Order now and get 20% off your next meal using code LUNCH20. Valid today only.", 2),
    ("Spotify Promo", "offers@spotify.com", "Get 3 months of Premium free!", "Listen to music ad-free, offline, and on-demand. Try Premium free for 3 months. Cancel anytime.", 4),
    ("Nike Store", "nike@nike-news.com", "New arrivals: The ultimate running shoes are here", "Step up your game with the brand new Nike Air Zoom. Engineered for maximum speed and comfort. Shop the collection today.", 7),
    ("Grammarly", "offers@grammarly.com", "Upgrade to Premium and save 50%", "Write with confidence. Grammarly Premium helps you improve clarity, tone, and vocabulary. Get 50% off today.", 9),
    ("Duolingo offers", "no-reply@duolingo.com", "Unlock Super Duolingo: 60% off annual plan", "Learn languages faster with no ads, unlimited hearts, and personalized practice. Subscribe now and save big.", 11),
    ("Netflix Offers", "info@netflix.com", "Top movies pick for you this weekend", "Check out what's trending on Netflix this week. From action blockbusters to award-winning documentaries. Watch now.", 13),
    ("Airbnb Promos", "noreply@airbnb.com", "Plan your summer getaway: Unique cabins under $100", "Escape to nature. Discover unique cabins, treehouses, and beachfront homes at incredible prices. Book your stay now.", 15),
    ("Domino's Pizza", "pizza@dominos.com", "Buy 1 Get 1 Free pizza this Tuesday!", "It's Tuesday! Order any medium or large pizza and get a second one absolutely free. Order online now.", 17),
    ("LinkedIn Premium", "premium@linkedin.com", "Try LinkedIn Premium free for 1 month", "Stand out to recruiters, see who viewed your profile, and learn new skills with LinkedIn Learning. Start your free trial.", 19),
    ("Codecademy Offers", "offers@codecademy.com", "Start learning Web Development for 40% off", "Learn HTML, CSS, JavaScript, and React. Upgrade to Pro today and save 40% on your annual membership.", 21),
    ("GitHub Shop", "shop@github.com", "Get your Octocat hoodie: 15% discount code", "Show your developer pride. Use code OCTO15 to get 15% off all hoodies, t-shirts, and mugs in the GitHub shop.", 23),
    ("Coursera Offers", "promo@coursera.org", "Save $100 on Coursera Plus annual subscription", "Get unlimited access to over 7,000 courses, professional certificates, and degrees from top universities. Subscribe now.", 25),
    ("Medium offers", "offers@medium.com", "Support independent writers: Join Medium Premium", "Get unlimited access to all stories on Medium. Read expert analysis, tutorials, and personal stories. Cancel anytime.", 32),
    ("PlayStation Store", "newsletter@playstation.com", "Summer Sale: Save up to 70% on top games", "Play has no limits. Save big on the biggest hits of the year on the PlayStation Store. Sale ends soon.", 35),
    ("Udemy Promotions", "udemy@udemy-mail.com", "Courses from $9.99! Learn Python, Web Dev, and more", "Upgrade your skills. Choose from over 200,000 video courses. Sale ends in 24 hours. Shop now.", 39),
    ("Starbucks Rewards", "starbucks@starbucks-news.com", "Double Star Day is tomorrow!", "Earn stars twice as fast on all hand-crafted beverages and food items. Find your nearest store.", 45),
    ("Adobe Creative", "creative@adobe.com", "Bring your ideas to life with 40% off Creative Cloud", "Get Photoshop, Illustrator, Premiere Pro, and more. Everything you need to create anything you want. Save 40% today.", 50)
]

for i, (name, email, subj, body, hrs) in enumerate(promotions_data):
    # Some match rule 104 (Food Delivery)
    rule_label = None
    if "ubereats.com" in email:
        rule_label = "Food Delivery"
    
    emails.append({
        "id": f"msg_promo_{i}",
        "thread_id": f"th_promo_{i}",
        "sender": f"{name} <{email}>",
        "sender_email": email,
        "subject": subj,
        "body": body,
        "snippet": body[:80] + "...",
        "category": "Promotions",
        "date": get_date(hrs),
        "label": rule_label,
        "snoozed_until": None,
        "reason": None,
        "thread_messages": [
            {"sender": f"{name} <{email}>", "body": body, "date": get_date(hrs)}
        ]
    })

# SOCIAL (12)
social_data = [
    ("LinkedIn", "notifications@linkedin.com", "Sarah Jenkins and 3 others viewed your profile", "See who is looking at your profile and find new career opportunities. Upgrade to Premium to see full details.", 1),
    ("Twitter / X", "info@x.com", "New notification: Elon Musk posted a new tweet", "Elon Musk: 'Sortify AI v2 is looking amazing!' Check out the replies and join the conversation.", 2),
    ("Facebook", "alerts@facebookmail.com", "Mark Zuckerberg tagged you in a photo", "Mark Zuckerberg added a new photo featuring you. Click here to view the photo and write a comment.", 3),
    ("Instagram", "no-reply@instagram.com", "instagram_user started following you", "instagram_user (@user_123) has followed you. View their profile and follow them back.", 5),
    ("Pinterest Alerts", "pins@pinterest.com", "15 new pins matching your design board", "We found some awesome pins that match your 'UI/UX Design' board. Click here to view your personalized feed.", 6),
    ("Reddit Digest", "noreply@redditmail.com", "Trending in r/Python: What is your favorite web framework?", "r/Python: FastAPI vs Flask in 2026. Read the top arguments and join the discussion in the comments.", 9),
    ("GitHub Activity", "noreply@github.com", "[GitHub] Security Alert: dependency vulnerability found", "We found a known security vulnerability in one of your dependencies. Click to view the details and merge PR.", 10),
    ("Discord", "notifications@discordapp.com", "12 unread messages in Sortify AI Server", "You have unread mentions in #general and #announcements in the Sortify AI developer server. Open Discord now.", 12),
    ("Slack Notifications", "notification@slack.com", "[Slack] New message from Alice in #dev-team", "Alice: 'Hey, I just committed the new layout files. Let me know if you run into any build errors.'", 14),
    ("Twitter Alerts", "notify@x.com", "Weekly analytics: Your tweets got 15,000 views", "You are growing! Check out your top performing tweets, link clicks, and follower stats for last week.", 18),
    ("Reddit Notifications", "alerts@redditmail.com", "Reply to your comment in r/webdev", "User 'code_monkey' replied to your comment: 'Totally agree, Vanilla JS with GSAP is super clean!' View thread.", 24),
    ("Meetup", "notifications@meetup.com", "Your RSVP is confirmed for Python Developers Meetup", "You're going! The meetup starts tomorrow at 6:30 PM at the Tech Hub. Don't forget to bring your laptop.", 28)
]

for i, (name, email, subj, body, hrs) in enumerate(social_data):
    rule_label = None
    if "slack.com" in email:
        rule_label = "Work/Updates"
    
    emails.append({
        "id": f"msg_soc_{i}",
        "thread_id": f"th_soc_{i}",
        "sender": f"{name} <{email}>",
        "sender_email": email,
        "subject": subj,
        "body": body,
        "snippet": body[:80] + "...",
        "category": "Social",
        "date": get_date(hrs),
        "label": rule_label,
        "snoozed_until": None,
        "reason": None,
        "thread_messages": [
            {"sender": f"{name} <{email}>", "body": body, "date": get_date(hrs)}
        ]
    })

# UPDATES (10)
# We will make one thread here contain multiple messages to trigger the thread summarizer.
# Thread ID th_up_0 will have 3 messages.
updates_data = [
    ("Stripe Billing", "billing@stripe.com", "Your monthly invoice #10245 is ready", "Your subscription invoice for the developer plan has been processed. The amount of $15.00 has been billed to your card ending in 4242.", 1),
    ("University Registrar", "registrar@registrar.edu", "Official Grades released for Spring Semester", "Dear Student, the official grades for the Spring 2026 semester are now available in your student portal. Please check the Academic Records tab.", 2),
    ("Slack Alerts", "alerts@slack.com", "Security Alert: New login detected from unknown device", "We detected a login to your Slack workspace from a new device in San Francisco, CA. If this was you, no action is needed.", 3),
    ("Campus Placement Office", "placement@careeroffice.edu", "URGENT: Registration deadline for Google campus placements", "Dear Students, the deadline to register for the upcoming Google campus placements is tomorrow at 5:00 PM. Fill out the application form attached.", 4),
    ("Zoom Video", "no-reply@zoom.us", "Scheduled meeting: Project Demo Session", "You have been invited to a scheduled Zoom meeting. Topic: Sortify AI Project Demo. Time: June 10, 2026, 11:00 AM Eastern Time.", 6),
    ("GitHub Actions", "noreply@github.com", "[GitHub] Build Success: workflow run #842", "Workflow run 'Tox Tests & Linting' completed successfully for commit 8f420b9 on main branch. All 14 checks passed.", 8),
    ("Google Cloud Security", "no-reply@google.com", "Security alert for your GCP Project 'sortify-prod'", "A new Service Account key was created for your GCP project. Please ensure this was authorized by an administrator.", 10),
    ("Vercel Deployments", "deployments@vercel.com", "Deployment successful for project 'sortify-web'", "Your project has been deployed successfully to production. Domain: sortify-web.vercel.app. Build time: 48 seconds.", 12),
    ("AWS Billing", "billing@amazon.com", "AWS Monthly Invoice available for download", "Your monthly bill for AWS services for the billing period May 2026 is now available. The total charged is $8.24. View PDF in console.", 15),
    ("DigitalOcean", "alerts@digitalocean.com", "Database Backup Completed", "Your database cluster backup has been completed successfully. The backup file is stored securely in your spaces bucket.", 20)
]

for i, (name, email, subj, body, hrs) in enumerate(updates_data):
    rule_label = None
    if "stripe.com" in email:
        rule_label = "Finance/Invoices"
    elif "registrar.edu" in email:
        rule_label = "University/Grades"
    elif "careeroffice.edu" in email:
        rule_label = "Campus/Placements"
    
    # We will make thread 0 contain 3 messages to test the Thread Summarizer!
    thread_messages = [{"sender": f"{name} <{email}>", "body": body, "date": get_date(hrs)}]
    if i == 0:
        thread_messages = [
            {"sender": f"{name} <{email}>", "body": "Initial notice: Your monthly developer plan subscription invoice is being prepared.", "date": get_date(hrs + 4)},
            {"sender": f"{name} <{email}>", "body": "Correction: Your monthly invoice amount will include the 5% early-bird discount.", "date": get_date(hrs + 2)},
            {"sender": f"{name} <{email}>", "body": body, "date": get_date(hrs)}
        ]
        subj = "Your monthly invoice #10245 is ready (Thread)"
        
    emails.append({
        "id": f"msg_up_{i}",
        "thread_id": f"th_up_{i}",
        "sender": f"{name} <{email}>",
        "sender_email": email,
        "subject": subj,
        "body": body,
        "snippet": body[:80] + "...",
        "category": "Updates",
        "date": get_date(hrs),
        "label": rule_label,
        "snoozed_until": None,
        "reason": None,
        "thread_messages": thread_messages
    })

# Weekly stats for last 7 days
weekly_stats = [
    {"date": "Mon", "count": 32},
    {"date": "Tue", "count": 45},
    {"date": "Wed", "count": 28},
    {"date": "Thu", "count": 50},
    {"date": "Fri", "count": 37},
    {"date": "Sat", "count": 15},
    {"date": "Sun", "count": 22}
]

# Top 8 Senders
top_senders = [
    {"sender": "Stripe Invoicing", "domain": "stripe.com", "count": 24},
    {"sender": "Slack Alerts", "domain": "slack.com", "count": 18},
    {"sender": "GitHub Notifications", "domain": "github.com", "count": 15},
    {"sender": "Uber Eats", "domain": "ubereats.com", "count": 12},
    {"sender": "LinkedIn Notifications", "domain": "linkedin.com", "count": 10},
    {"sender": "Netflix Support", "domain": "netflix.com", "count": 8},
    {"sender": "Vercel Deployments", "domain": "vercel.com", "count": 7},
    {"sender": "Zoom Meetings", "domain": "zoom.us", "count": 6}
]

# 7x24 Heatmap data (days 0-6, hours 0-23)
heatmap = []
import random
random.seed(42)
for day in range(7):
    for hour in range(24):
        # Weekdays (1-5), business hours (9-17) get higher counts
        if 1 <= day <= 5 and 9 <= hour <= 17:
            count = random.randint(12, 35)
        elif 1 <= day <= 5:
            count = random.randint(2, 10)
        else: # Weekends
            count = random.randint(1, 8)
        heatmap.append({"day": day, "hour": hour, "count": count})

