"""
Generates a curated, structured dataset of 150-200 sample internship/job
postings for the internship knowledge base (Milestone 2, M2.1).

The postings are synthetic (built from domain templates + a company/location
pool) rather than scraped, so the dataset is free of copyright/ToS concerns
and reproducible (fixed random seed). Each posting follows the standard
job-posting schema used across the project (see docs/job_posting_schema.md).

Run:
    python database/generate_job_postings.py

Output:
    database/job_postings.json
"""
import json
import os
import random

random.seed(42)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "job_postings.json")

COMPANIES = [
    "Nimbus Systems", "Corelogic Labs", "Bluepeak Technologies", "Verdant Robotics",
    "Skyline Analytics", "Northbridge Software", "Ferrous Dynamics", "Solace Health Tech",
    "Cobalt Cloud Works", "Meridian Fintech", "Auroraworks", "Greenline Mobility",
    "Lucent Data Co", "Stratos Aerospace", "Riverstone Consulting", "Pinegrove Retail",
    "Quanta Semiconductors", "Brightloop Media", "Ironvale Manufacturing", "Wavecrest Biotech",
    "Cedarpoint Energy", "Vantage Logistics", "Hearthstone Edtech", "Fablecraft Studios",
    "Trueline Insurance", "Copperleaf Agritech", "Nightowl Security", "Sunveil Solar",
    "Cascade Water Works", "Ridgeback Automotive",
]

LOCATIONS = [
    "Bengaluru, India", "Hyderabad, India", "Pune, India", "Gurugram, India",
    "Chennai, India", "Mumbai, India", "Noida, India", "Ahmedabad, India",
    "Kolkata, India", "Remote (India)", "Jaipur, India", "Coimbatore, India",
]

EDUCATION_LEVELS = [
    "Pursuing B.Tech/B.E.", "Pursuing B.Tech/B.E. or M.Tech", "Pursuing B.Sc/B.Tech",
    "Pursuing any Bachelor's degree", "Pursuing MBA", "Pursuing M.Tech/M.S.",
]

EXPERIENCE_LEVELS = [
    "No prior experience required", "0-6 months of relevant project/internship experience preferred",
    "Prior internship experience preferred but not mandatory", "1 semester of relevant coursework or project work",
]

# Each domain defines: title pool, required skills pool, preferred skills pool,
# responsibilities pool, qualifications pool, and a short description template.
DOMAINS = {
    "Software Engineering": {
        "titles": ["Software Engineering Intern", "Backend Developer Intern", "Full-Stack Developer Intern", "Platform Engineering Intern"],
        "required": ["Python", "Java", "Data Structures & Algorithms", "REST APIs", "Git", "SQL"],
        "preferred": ["Docker", "Kubernetes", "Microservices", "CI/CD", "AWS", "System Design basics"],
        "responsibilities": [
            "Build and maintain backend services used by the core product",
            "Write unit and integration tests for new features",
            "Participate in code reviews with the engineering team",
            "Debug and fix production issues under mentorship",
            "Contribute to internal developer tooling",
        ],
        "qualifications": ["Strong fundamentals in data structures and algorithms", "Comfortable working in a Linux/Unix environment"],
        "field": "Computer Science / Information Technology",
        "desc": "Work alongside our engineering team to build and ship real features in a production codebase, with a focus on backend services and clean, tested code.",
    },
    "Web Development": {
        "titles": ["Frontend Developer Intern", "Web Development Intern", "UI Engineering Intern"],
        "required": ["JavaScript", "HTML", "CSS", "React"],
        "preferred": ["TypeScript", "Next.js", "Tailwind CSS", "Redux", "Accessibility (a11y)"],
        "responsibilities": [
            "Build responsive UI components from design specs",
            "Optimize page load performance and accessibility",
            "Collaborate with designers to implement pixel-accurate interfaces",
            "Fix cross-browser compatibility issues",
        ],
        "qualifications": ["Portfolio of at least one web project (personal or academic)", "Comfortable with Git-based workflows"],
        "field": "Computer Science / Information Technology",
        "desc": "Join our web team to build fast, accessible, and delightful user interfaces used by thousands of customers.",
    },
    "Data Science & Analytics": {
        "titles": ["Data Science Intern", "Data Analyst Intern", "Business Intelligence Intern"],
        "required": ["Python", "SQL", "Pandas", "Data Visualization", "Statistics"],
        "preferred": ["Scikit-learn", "Power BI/Tableau", "A/B Testing", "R"],
        "responsibilities": [
            "Clean and analyze large datasets to surface actionable insights",
            "Build dashboards for internal stakeholders",
            "Support experiments and A/B tests with statistical analysis",
            "Present findings to cross-functional teams",
        ],
        "qualifications": ["Coursework or projects involving statistics or data analysis", "Comfortable with Excel/SQL for data wrangling"],
        "field": "Statistics / Computer Science / Mathematics",
        "desc": "Help turn raw data into decisions — you'll work with real company datasets to answer concrete business questions.",
    },
    "Machine Learning / AI": {
        "titles": ["Machine Learning Intern", "AI Research Intern", "Applied ML Intern"],
        "required": ["Python", "Machine Learning fundamentals", "NumPy", "PyTorch or TensorFlow"],
        "preferred": ["NLP", "Computer Vision", "MLOps", "Model deployment experience"],
        "responsibilities": [
            "Prototype and evaluate ML models for a specific product use case",
            "Prepare and preprocess training datasets",
            "Run experiments and document results",
            "Collaborate with engineers to move models toward production",
        ],
        "qualifications": ["Coursework in machine learning or a completed ML project", "Familiarity with model evaluation metrics"],
        "field": "Computer Science / Data Science",
        "desc": "Work on applied machine learning problems with real product impact, from experimentation through to deployment support.",
    },
    "Embedded Systems / IoT": {
        "titles": ["Embedded Systems Intern", "IoT Engineering Intern", "Firmware Developer Intern"],
        "required": ["C", "Embedded C", "Microcontrollers", "Circuit basics"],
        "preferred": ["Arduino", "Raspberry Pi", "RTOS", "PCB design (KiCad/Altium)"],
        "responsibilities": [
            "Develop and test firmware for embedded devices",
            "Assist with PCB bring-up and hardware debugging",
            "Integrate sensors and actuators into prototypes",
            "Document hardware-software interfaces",
        ],
        "qualifications": ["Hands-on project experience with microcontrollers", "Basic understanding of digital logic design"],
        "field": "Electronics / Electrical / Computer Engineering",
        "desc": "Get hands-on with real hardware — you'll help build and debug firmware for devices that ship to real users.",
    },
    "Mechanical Engineering": {
        "titles": ["Mechanical Design Intern", "Manufacturing Engineering Intern", "R&D Engineering Intern"],
        "required": ["CAD (SolidWorks/AutoCAD)", "Engineering drawing", "Material science basics"],
        "preferred": ["FEA/CFD simulation", "GD&T", "Prototyping / 3D printing"],
        "responsibilities": [
            "Design and iterate on mechanical components using CAD tools",
            "Support prototyping and testing of new parts",
            "Assist in root-cause analysis for manufacturing defects",
            "Document design specifications and test results",
        ],
        "qualifications": ["Academic or personal projects involving CAD design", "Basic understanding of manufacturing processes"],
        "field": "Mechanical Engineering",
        "desc": "Support our R&D team in designing, prototyping, and testing mechanical components from concept to first article.",
    },
    "Electrical Engineering": {
        "titles": ["Electrical Engineering Intern", "Power Systems Intern", "Controls Engineering Intern"],
        "required": ["Circuit analysis", "MATLAB/Simulink", "Basic power electronics"],
        "preferred": ["PLC programming", "SCADA basics", "Motor control"],
        "responsibilities": [
            "Support design and testing of electrical control systems",
            "Assist with simulation of power/control circuits",
            "Document test procedures and results",
        ],
        "qualifications": ["Coursework in circuits or control systems", "Familiarity with lab measurement equipment"],
        "field": "Electrical Engineering",
        "desc": "Work with our controls team on real electrical systems, from simulation through to bench testing.",
    },
    "Cloud / DevOps": {
        "titles": ["DevOps Intern", "Cloud Engineering Intern", "Site Reliability Intern"],
        "required": ["Linux fundamentals", "Git", "Basic scripting (Bash/Python)"],
        "preferred": ["AWS/Azure/GCP", "Docker", "Kubernetes", "Terraform", "CI/CD pipelines"],
        "responsibilities": [
            "Support cloud infrastructure provisioning and monitoring",
            "Improve CI/CD pipeline reliability",
            "Assist in writing infrastructure-as-code",
            "Help triage and resolve deployment issues",
        ],
        "qualifications": ["Basic understanding of networking and Linux", "Curiosity about infrastructure and automation"],
        "field": "Computer Science / Information Technology",
        "desc": "Help keep our infrastructure fast and reliable — you'll work directly with the systems that run production.",
    },
    "Cybersecurity": {
        "titles": ["Cybersecurity Intern", "Security Analyst Intern", "Application Security Intern"],
        "required": ["Networking fundamentals", "Security fundamentals", "Linux basics"],
        "preferred": ["Penetration testing tools", "OWASP Top 10", "Scripting (Python)"],
        "responsibilities": [
            "Assist with vulnerability assessments on internal applications",
            "Support security awareness and documentation efforts",
            "Monitor security alerts under supervision",
        ],
        "qualifications": ["Coursework or self-study in security fundamentals", "Familiarity with common vulnerability types"],
        "field": "Computer Science / Information Security",
        "desc": "Support our security team in identifying and remediating real vulnerabilities across our applications.",
    },
    "Product Management": {
        "titles": ["Product Management Intern", "Associate Product Intern"],
        "required": ["Written communication", "Basic data analysis", "Prioritization frameworks"],
        "preferred": ["SQL basics", "Wireframing tools (Figma)", "User research experience"],
        "responsibilities": [
            "Support the product team in gathering and synthesizing user feedback",
            "Help write product requirement documents",
            "Analyze feature usage data to inform roadmap decisions",
        ],
        "qualifications": ["Strong written and verbal communication", "Interest in user-centred problem solving"],
        "field": "Any discipline (Business/CS/Design background preferred)",
        "desc": "Work closely with product managers and engineers to shape features from idea to launch.",
    },
    "UI/UX Design": {
        "titles": ["UI/UX Design Intern", "Product Design Intern"],
        "required": ["Figma", "Visual design fundamentals", "Wireframing"],
        "preferred": ["User research", "Prototyping", "Design systems experience"],
        "responsibilities": [
            "Create wireframes and high-fidelity mockups for new features",
            "Support user research and usability testing sessions",
            "Maintain and extend the design system",
        ],
        "qualifications": ["Portfolio showcasing design projects", "Basic understanding of design principles"],
        "field": "Design / HCI / Any discipline with a design portfolio",
        "desc": "Join our design team to craft interfaces that are both usable and delightful, from research through to pixel-perfect handoff.",
    },
    "Marketing": {
        "titles": ["Digital Marketing Intern", "Growth Marketing Intern", "Content Marketing Intern"],
        "required": ["Content writing", "Social media basics", "Basic analytics (Google Analytics)"],
        "preferred": ["SEO", "Email marketing tools", "Canva/basic design"],
        "responsibilities": [
            "Assist in planning and executing digital marketing campaigns",
            "Track and report on campaign performance metrics",
            "Create content for social media and email channels",
        ],
        "qualifications": ["Strong written communication", "Interest in brand and growth marketing"],
        "field": "Any discipline (Marketing/Business preferred)",
        "desc": "Help plan and run real marketing campaigns, and see the impact of your work in live performance metrics.",
    },
    "Finance": {
        "titles": ["Finance Intern", "Investment Analyst Intern", "FP&A Intern"],
        "required": ["Excel", "Financial statement basics", "Basic accounting"],
        "preferred": ["Financial modeling", "PowerPoint", "SQL basics"],
        "responsibilities": [
            "Support monthly financial reporting and reconciliation",
            "Assist in building financial models and forecasts",
            "Research market and industry trends for internal reports",
        ],
        "qualifications": ["Coursework in finance or accounting", "Strong attention to detail"],
        "field": "Finance / Commerce / Economics",
        "desc": "Get exposure to real financial planning and analysis work supporting company-wide decision-making.",
    },
    "Human Resources": {
        "titles": ["HR Intern", "Talent Acquisition Intern", "People Operations Intern"],
        "required": ["Communication skills", "MS Office/Google Workspace", "Organization skills"],
        "preferred": ["ATS tools experience", "Basic labor law awareness"],
        "responsibilities": [
            "Support recruitment coordination and candidate communication",
            "Help organize onboarding for new hires",
            "Maintain HR documentation and records",
        ],
        "qualifications": ["Strong interpersonal skills", "Interest in people operations"],
        "field": "Any discipline (HR/Psychology/Business preferred)",
        "desc": "Support our people team across recruitment, onboarding, and day-to-day HR operations.",
    },
    "Operations / Supply Chain": {
        "titles": ["Operations Intern", "Supply Chain Intern", "Logistics Intern"],
        "required": ["Excel", "Analytical thinking", "Process documentation"],
        "preferred": ["SQL basics", "Inventory management systems", "Basic forecasting"],
        "responsibilities": [
            "Support process improvement initiatives across operations",
            "Track key operational metrics and prepare reports",
            "Coordinate with vendors/warehouses on logistics issues",
        ],
        "qualifications": ["Strong organizational skills", "Comfort working with spreadsheets and data"],
        "field": "Any discipline (Operations/Supply Chain/Business preferred)",
        "desc": "Work on real operational bottlenecks — you'll help streamline processes that the whole company depends on.",
    },
    "Biotechnology": {
        "titles": ["Biotech Research Intern", "Lab Research Intern"],
        "required": ["Lab safety fundamentals", "Basic molecular biology techniques"],
        "preferred": ["PCR", "Cell culture", "Data recording/ELN tools"],
        "responsibilities": [
            "Assist in running lab experiments under supervision",
            "Maintain accurate lab notebooks and data records",
            "Support sample preparation and basic analysis",
        ],
        "qualifications": ["Coursework in biology/biotechnology", "Comfortable following lab protocols precisely"],
        "field": "Biotechnology / Life Sciences",
        "desc": "Get hands-on lab experience supporting ongoing research projects under experienced scientists.",
    },
    "Civil Engineering": {
        "titles": ["Civil Engineering Intern", "Structural Design Intern", "Site Engineering Intern"],
        "required": ["AutoCAD", "Engineering drawing", "Basic structural analysis"],
        "preferred": ["STAAD Pro/ETABS", "Site survey experience", "Project scheduling tools"],
        "responsibilities": [
            "Support structural drawing preparation and review",
            "Assist with site visits and progress documentation",
            "Help prepare quantity estimates and reports",
        ],
        "qualifications": ["Coursework in structural analysis or design", "Willingness to do occasional site visits"],
        "field": "Civil Engineering",
        "desc": "Support our engineering team across design and site coordination for active construction projects.",
    },
    "Content & Writing": {
        "titles": ["Content Writing Intern", "Technical Writing Intern", "Editorial Intern"],
        "required": ["Strong writing skills", "Research skills", "Editing/proofreading"],
        "preferred": ["SEO writing", "Basic HTML/Markdown", "Experience with CMS tools"],
        "responsibilities": [
            "Write and edit articles, product copy, or documentation",
            "Research topics thoroughly before drafting content",
            "Collaborate with subject-matter experts to ensure accuracy",
        ],
        "qualifications": ["A portfolio or writing samples", "Comfortable taking editorial feedback"],
        "field": "Any discipline (English/Journalism/Communications preferred)",
        "desc": "Write content that real users and customers read every day, with direct editorial mentorship.",
    },
    "Sales & Business Development": {
        "titles": ["Sales Intern", "Business Development Intern"],
        "required": ["Communication skills", "Basic CRM usage", "Comfort with cold outreach"],
        "preferred": ["Excel/Google Sheets for pipeline tracking", "Prior sales/club leadership experience"],
        "responsibilities": [
            "Support lead generation and outreach efforts",
            "Assist in preparing sales collateral and pitch decks",
            "Track pipeline data in the CRM",
        ],
        "qualifications": ["Strong verbal communication", "Comfortable with rejection and follow-up"],
        "field": "Any discipline (Business preferred)",
        "desc": "Get real front-line sales experience, from outreach to pipeline tracking, mentored by our BD team.",
    },
}


def build_postings(target_count: int = 180):
    postings = []
    job_id_counter = 1

    domain_names = list(DOMAINS.keys())

    while len(postings) < target_count:
        domain_name = domain_names[len(postings) % len(domain_names)]
        domain = DOMAINS[domain_name]

        title = random.choice(domain["titles"])
        company = random.choice(COMPANIES)
        location = random.choice(LOCATIONS)

        req_pool_len = len(domain["required"])
        req_k = random.randint(min(3, req_pool_len), req_pool_len)
        required_skills = random.sample(domain["required"], k=req_k)

        pref_pool_len = len(domain["preferred"])
        pref_k = random.randint(min(2, pref_pool_len), pref_pool_len)
        preferred_skills = random.sample(domain["preferred"], k=pref_k)
        responsibilities = random.sample(domain["responsibilities"], k=min(len(domain["responsibilities"]), random.randint(3, len(domain["responsibilities"]))))
        qualifications = domain["qualifications"]

        stipend = random.choice([10000, 12000, 15000, 18000, 20000, 25000, 30000, 35000])
        duration = random.choice(["2 months", "3 months", "6 months"])

        posting = {
            "job_id": f"JOB{job_id_counter:04d}",
            "title": title,
            "company": company,
            "location": location,
            "domain": domain_name,
            "job_description": (
                f"{domain['desc']} This is a {duration} internship based in {location}, "
                f"with a monthly stipend of ₹{stipend:,}."
            ),
            "responsibilities": responsibilities,
            "required_skills": required_skills,
            "preferred_skills": preferred_skills,
            "qualifications": qualifications,
            "experience_requirement": random.choice(EXPERIENCE_LEVELS),
            "education_requirement": f"{random.choice(EDUCATION_LEVELS)} in {domain['field']}",
            "duration": duration,
            "stipend_inr_per_month": stipend,
        }

        # Deduplicate on (title, company, location) so we don't get literal duplicates
        dedup_key = (posting["title"], posting["company"], posting["location"])
        if dedup_key in {(p["title"], p["company"], p["location"]) for p in postings}:
            job_id_counter += 1
            continue

        postings.append(posting)
        job_id_counter += 1

    return postings


def main():
    postings = build_postings(target_count=180)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(postings, f, indent=2, ensure_ascii=False)

    print(f"Generated {len(postings)} job postings -> {OUTPUT_PATH}")

    # Quick sanity summary by domain
    by_domain = {}
    for p in postings:
        by_domain[p["domain"]] = by_domain.get(p["domain"], 0) + 1
    for domain, count in sorted(by_domain.items()):
        print(f"  {domain:<28} {count}")


if __name__ == "__main__":
    main()
