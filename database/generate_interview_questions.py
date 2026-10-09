"""
Generates a curated interview-question bank for the Mock Interview / AI Chat
Bot feature, organized by the same 19 domains used in the job-postings
knowledge base (database/generate_job_postings.py).

Note on sourcing: these questions are written/curated by a human-reviewed
process rather than pulled live from Kaggle/Google Dataset Search/Hugging
Face at build time. That's a deliberate choice for the same reasons as the
job-postings dataset (see docs/job_posting_schema.md): live scraping of
those sources has no stable schema, no licensing guarantee for redistribution,
and no way to guarantee question quality/relevance to internship-level
candidates -- a build that "sometimes downloads garbage" is worse than a
curated, versioned bank. The questions themselves reflect real, commonly
asked technical and behavioral interview questions for each field (the kind
you'd find repeated across genuine interview-prep sources), not invented
nonsense. If a real Kaggle/HF dataset is later chosen, swap the DOMAIN_*
dicts below for a loader over that dataset -- nothing downstream
(seed_interview_questions.py, the interview agent) needs to change, since
they only depend on the final JSON shape.

Run:
    python database/generate_interview_questions.py

Output:
    database/interview_questions.json
"""
import json
import os

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "interview_questions.json")

# Shared behavioral pool -- applicable across every domain.
BEHAVIORAL_QUESTIONS = [
    "Tell me about a time you had to learn something completely new in a short amount of time. How did you approach it?",
    "Describe a project you're proud of. What was your specific contribution?",
    "Tell me about a time you disagreed with a teammate or group member. How did you handle it?",
    "Describe a situation where you had to meet a tight deadline. What did you do?",
    "Tell me about a mistake you made on a project and what you learned from it.",
    "How do you prioritize when you have multiple assignments or tasks due around the same time?",
    "Describe a time you had to explain something technical to someone non-technical.",
    "Tell me about a time you received critical feedback. How did you respond?",
    "What's a skill you've worked on improving over the past year, and how did you go about it?",
    "Describe a time you worked in a team where someone wasn't pulling their weight. What did you do?",
    "Tell me about a time you had to make a decision without all the information you wanted.",
    "Why are you interested in this field, and what draws you to internships specifically right now?",
    "Describe a time you had to advocate for your own idea or approach when others disagreed.",
    "Tell me about a project that didn't go as planned. What would you do differently?",
    "How do you handle working on something you're not immediately good at?",
    "Describe a time you had to ask for help. How did you decide who to ask and how?",
    "What's something outside of coursework that you've taught yourself, and why?",
    "Tell me about a time you had to balance quality with a deadline.",
    "How would a teammate from a past project describe working with you?",
    "Where do you see the skills from this internship fitting into your longer-term goals?",
]

DOMAIN_QUESTIONS = {
    "Software Engineering": [
        "Explain the difference between a stack and a queue, and give a real use case for each.",
        "What is the time complexity of common operations (insert, search, delete) on a hash map, and why?",
        "Walk me through how you would debug a function that's producing incorrect output intermittently.",
        "What is the difference between a process and a thread?",
        "Explain what a REST API is and what makes an API RESTful.",
        "What's the difference between SQL and NoSQL databases, and when would you choose one over the other?",
        "Explain what Git rebase does and how it's different from a merge.",
        "How would you design a rate limiter for an API?",
        "What is Big-O notation, and why does it matter when choosing a data structure or algorithm?",
        "What's the difference between synchronous and asynchronous code execution?",
        "How do you approach writing unit tests for a new feature?",
        "What is a race condition, and how can it be avoided?",
        "Explain the concept of Big-O for a nested loop over an array of size n.",
        "What's the difference between an abstract class and an interface?",
        "How would you optimize a slow SQL query?",
        "Describe how a hash table handles collisions.",
        "What is dependency injection, and why is it useful?",
        "Walk me through how you'd approach a coding problem you've never seen before.",
    ],
    "Web Development": [
        "What's the difference between `let`, `const`, and `var` in JavaScript?",
        "Explain the CSS box model.",
        "What is the virtual DOM, and why do frameworks like React use it?",
        "How does the browser's event loop work?",
        "What's the difference between `==` and `===` in JavaScript?",
        "Explain what CORS is and why browsers enforce it.",
        "What's the difference between server-side rendering and client-side rendering?",
        "How would you make a website accessible to users relying on screen readers?",
        "What is a promise in JavaScript, and how does it differ from a callback?",
        "How does responsive design work, and what tools do you use to implement it?",
        "What's the purpose of semantic HTML?",
        "How would you debug a page that's loading slowly?",
        "Explain how React's component lifecycle (or hooks like useEffect) works.",
        "What's the difference between local storage, session storage, and cookies?",
        "How do you manage state in a moderately complex frontend application?",
        "What is a single-page application, and what are its trade-offs?",
        "How would you optimize the load time of an image-heavy web page?",
        "What's your process for making sure a UI matches a design spec closely?",
    ],
    "Data Science & Analytics": [
        "Walk me through how you would approach a dataset with a lot of missing values.",
        "What's the difference between correlation and causation, and why does it matter in analysis?",
        "Explain what a p-value is in plain language.",
        "How would you detect and handle outliers in a dataset?",
        "What's the difference between a left join and an inner join in SQL?",
        "How would you explain a complex analysis finding to a non-technical stakeholder?",
        "What's the difference between mean, median, and when each is more appropriate?",
        "How would you design an A/B test for a new feature?",
        "What is overfitting, and how would you detect it in a model or analysis?",
        "Walk me through your process for exploratory data analysis on a new dataset.",
        "What's the difference between a bar chart and a histogram, and when would you use each?",
        "How would you validate whether a dataset is representative of the population you care about?",
        "Explain the difference between supervised and unsupervised learning.",
        "How would you handle a dataset that's highly imbalanced (e.g. 99% one class)?",
        "What SQL would you write to find the second-highest value in a column?",
        "How do you decide which visualization to use for a given dataset or question?",
    ],
    "Machine Learning / AI": [
        "Explain the bias-variance tradeoff.",
        "What's the difference between precision and recall, and when would you prioritize one over the other?",
        "Walk me through how gradient descent works.",
        "What is overfitting, and what are some ways to prevent it?",
        "Explain the difference between a CNN and an RNN, and when you'd use each.",
        "What's the difference between L1 and L2 regularization?",
        "How would you evaluate whether a classification model is good enough to deploy?",
        "What is transfer learning, and why is it useful?",
        "Explain what an embedding is in the context of NLP.",
        "How would you approach a project where you don't have much labeled data?",
        "What's the difference between batch and stochastic gradient descent?",
        "How do you decide on a train/validation/test split for a project?",
        "What is a confusion matrix, and what does each cell tell you?",
        "Explain how a decision tree makes a prediction.",
        "What ethical considerations come up when deploying a machine learning model that affects real people?",
    ],
    "Embedded Systems / IoT": [
        "What's the difference between a microcontroller and a microprocessor?",
        "Explain the difference between polling and interrupt-driven I/O.",
        "What is debouncing, and why is it needed for physical buttons?",
        "How would you debug a firmware issue that only happens intermittently?",
        "What's the difference between UART, SPI, and I2C communication protocols?",
        "How do you manage memory constraints on a resource-limited microcontroller?",
        "What is an RTOS, and when would you use one instead of bare-metal code?",
        "Walk me through how you'd bring up a new PCB for the first time.",
        "What's the difference between analog and digital signals, and how does an ADC bridge them?",
        "How would you approach power optimization for a battery-powered IoT device?",
        "What is a watchdog timer, and why is it used?",
        "How do you handle noisy sensor data in an embedded system?",
    ],
    "Mechanical Engineering": [
        "Walk me through your design process when starting a new mechanical component.",
        "What factors do you consider when selecting a material for a part?",
        "Explain the difference between stress and strain.",
        "How would you approach tolerance stack-up in an assembly with multiple parts?",
        "What's the difference between static and dynamic loading?",
        "How do you validate a design before committing to manufacturing it?",
        "What is FEA (finite element analysis), and what are its limitations?",
        "Walk me through GD&T and why it matters for manufacturability.",
        "How would you diagnose unexpected vibration in a mechanical assembly?",
        "What trade-offs do you consider between 3D printing and CNC machining for a prototype?",
    ],
    "Electrical Engineering": [
        "Explain Ohm's Law and how you'd use it to size a resistor in a circuit.",
        "What's the difference between series and parallel circuits?",
        "How would you troubleshoot a circuit that isn't behaving as simulated?",
        "What is the purpose of a capacitor in a power supply circuit?",
        "Explain the difference between AC and DC, and where each is typically used.",
        "What's the difference between open-loop and closed-loop control systems?",
        "How would you approach reducing electrical noise in a sensitive circuit?",
        "What is impedance, and why does it matter in circuit design?",
        "Walk me through how you'd read and interpret a circuit schematic you haven't seen before.",
    ],
    "Cloud / DevOps": [
        "What's the difference between a container and a virtual machine?",
        "Explain what CI/CD is and why it matters.",
        "What's the difference between horizontal and vertical scaling?",
        "How would you debug a service that's failing intermittently in production?",
        "What is infrastructure as code, and what problem does it solve?",
        "Explain the difference between blue-green deployment and rolling deployment.",
        "What's the purpose of a load balancer?",
        "How would you approach setting up monitoring/alerting for a new service?",
        "What's the difference between a public and private subnet in cloud networking?",
        "How do you approach securing secrets (API keys, passwords) in a deployment pipeline?",
    ],
    "Cybersecurity": [
        "Explain the difference between authentication and authorization.",
        "What is SQL injection, and how would you prevent it?",
        "Walk me through how you'd approach a basic vulnerability assessment of a web application.",
        "What's the difference between symmetric and asymmetric encryption?",
        "What is a man-in-the-middle attack, and how does HTTPS help prevent it?",
        "Explain what the principle of least privilege means and why it matters.",
        "What's the difference between a vulnerability, a threat, and a risk?",
        "How would you respond if you discovered a security incident in progress?",
        "What is cross-site scripting (XSS), and how would you defend against it?",
    ],
    "Product Management": [
        "Walk me through how you would prioritize a backlog of feature requests.",
        "Tell me about a product you use regularly. What would you improve about it, and why?",
        "How would you measure whether a new feature was successful after launch?",
        "How do you decide what NOT to build?",
        "Walk me through how you'd write a one-page spec for a new feature.",
        "How would you handle a disagreement between engineering and design about scope?",
        "What data would you want before deciding whether to build a requested feature?",
        "How do you gather and synthesize user feedback into actionable next steps?",
    ],
    "UI/UX Design": [
        "Walk me through your design process from a brief to a final mockup.",
        "How do you decide when a design needs user testing versus when you can trust your judgment?",
        "What makes a design system valuable for a growing product?",
        "Tell me about a time feedback significantly changed your design direction.",
        "How do you balance aesthetics with usability?",
        "What accessibility considerations do you build into your designs by default?",
        "How would you redesign a feature you find confusing in an app you use often?",
        "Walk me through how you'd conduct a quick usability test on a new flow.",
    ],
    "Marketing": [
        "How would you measure the success of a marketing campaign?",
        "Walk me through how you'd plan a campaign for a limited budget.",
        "What's the difference between brand marketing and performance marketing?",
        "How do you decide which channel to prioritize for a given campaign goal?",
        "Tell me about a piece of marketing (ad, campaign, post) you thought was particularly effective, and why.",
        "How would you approach growing an audience from scratch on a new channel?",
        "What metrics would you track for an email marketing campaign, and why those?",
    ],
    "Finance": [
        "Walk me through the three financial statements and how they connect.",
        "What's the difference between gross margin and net margin?",
        "How would you build a simple financial model for a new product launch?",
        "What is the time value of money, and why does it matter in financial decisions?",
        "How would you evaluate whether a company's financials look healthy?",
        "What's the difference between CapEx and OpEx?",
        "Walk me through how you'd reconcile a discrepancy in monthly numbers.",
    ],
    "Human Resources": [
        "How would you handle a conflict between two team members?",
        "Walk me through how you'd screen resumes for a role with 200+ applicants.",
        "What would you do if a new hire's onboarding wasn't going well?",
        "How do you balance confidentiality with transparency in HR communications?",
        "What questions would you ask to assess culture fit without introducing bias?",
        "How would you handle a situation where a manager wants to make an unfair decision about an employee?",
    ],
    "Operations / Supply Chain": [
        "Walk me through how you'd identify a bottleneck in a process.",
        "How would you approach forecasting demand for a product with seasonal variation?",
        "What metrics would you track to evaluate the health of a supply chain?",
        "How would you handle a vendor that's consistently late on deliveries?",
        "Walk me through how you'd design a process improvement from problem to rollout.",
        "What trade-offs come up between holding more inventory versus less?",
    ],
    "Biotechnology": [
        "Walk me through the steps of PCR and what each step accomplishes.",
        "How do you ensure reproducibility in a lab experiment?",
        "What's the difference between in vitro and in vivo studies?",
        "How would you troubleshoot an experiment that isn't giving the expected results?",
        "What safety protocols do you consider essential when working with biological samples?",
        "Walk me through how you'd design a control group for an experiment.",
    ],
    "Civil Engineering": [
        "Walk me through the key considerations when designing a structural element.",
        "What's the difference between dead load and live load?",
        "How do you approach a site visit to assess project progress?",
        "What factors influence material selection for a structural project?",
        "How would you handle a discrepancy between the design drawings and site conditions?",
        "What's the purpose of a factor of safety in structural design?",
    ],
    "Content & Writing": [
        "Walk me through your process from a topic idea to a published piece.",
        "How do you adjust your writing style for different audiences?",
        "Tell me about a piece you wrote that required research on an unfamiliar topic. How did you approach it?",
        "How do you handle editorial feedback that you disagree with?",
        "What makes a headline or opening line effective, in your view?",
        "How would you fact-check a claim you're not sure about before publishing?",
    ],
    "Sales & Business Development": [
        "Walk me through how you'd research a prospect before reaching out.",
        "How do you handle rejection during outreach, and how does it affect your approach going forward?",
        "What would you do if a prospect went quiet after seeming interested?",
        "How do you tailor your pitch for different types of prospects?",
        "Walk me through how you'd qualify whether a lead is worth pursuing.",
        "What metrics would you track to evaluate your own outreach effectiveness?",
    ],
}


def build_bank():
    bank = []
    qid = 1

    for domain, questions in DOMAIN_QUESTIONS.items():
        for q in questions:
            bank.append({
                "id": qid,
                "domain": domain,
                "category": "technical",
                "question_text": q,
                "difficulty": "medium",
            })
            qid += 1

        # Attach the full shared behavioral pool to every domain too, tagged
        # with that domain so a set for "Data Science & Analytics" pulls
        # behavioral questions alongside its technical ones from one place.
        for q in BEHAVIORAL_QUESTIONS:
            bank.append({
                "id": qid,
                "domain": domain,
                "category": "behavioral",
                "question_text": q,
                "difficulty": None,
            })
            qid += 1

    return bank


def main():
    bank = build_bank()
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(bank, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(bank)} interview questions -> {OUTPUT_PATH}")
    by_domain = {}
    for q in bank:
        by_domain[q["domain"]] = by_domain.get(q["domain"], 0) + 1
    for domain, count in sorted(by_domain.items()):
        print(f"  {domain:<28} {count}")


if __name__ == "__main__":
    main()
