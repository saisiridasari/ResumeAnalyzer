import re
import spacy
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    from spacy.cli import download
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

for pkg in ['stopwords', 'punkt', 'punkt_tab']:
    try:
        nltk.data.find(f'corpora/{pkg}')
    except LookupError:
        try:
            nltk.download(pkg, quiet=True)
        except Exception:
            pass

TECH_SKILLS = {
    # Languages
    'python', 'java', 'javascript', 'typescript', 'c', 'c++', 'c#', 'ruby', 'php', 'go',
    'golang', 'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl', 'bash', 'shell',
    'powershell', 'groovy', 'lua', 'dart', 'elixir', 'haskell', 'clojure', 'f#', 'vba',
    # Web Frameworks
    'react', 'reactjs', 'angular', 'angularjs', 'vue', 'vuejs', 'next.js', 'nextjs',
    'nuxt.js', 'django', 'flask', 'fastapi', 'spring', 'spring boot', 'express', 'expressjs',
    'node.js', 'nodejs', 'laravel', 'rails', 'ruby on rails', 'asp.net', '.net', 'blazor',
    'gatsby', 'svelte', 'ember', 'backbone', 'jquery', 'bootstrap', 'tailwind', 'tailwindcss',
    # Databases
    'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'redis', 'elasticsearch',
    'cassandra', 'oracle', 'sqlite', 'mariadb', 'dynamodb', 'firebase', 'neo4j',
    'couchdb', 'influxdb', 'mssql', 'sql server',
    # Cloud & DevOps
    'aws', 'amazon web services', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes',
    'k8s', 'terraform', 'ansible', 'jenkins', 'ci/cd', 'gitlab', 'github actions',
    'circleci', 'travis ci', 'helm', 'istio', 'prometheus', 'grafana', 'elk', 'nginx',
    'apache', 'linux', 'ubuntu', 'centos', 'debian', 'rhel',
    # ML/AI
    'machine learning', 'deep learning', 'nlp', 'natural language processing',
    'computer vision', 'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'sklearn',
    'pandas', 'numpy', 'matplotlib', 'seaborn', 'jupyter', 'spark', 'hadoop',
    'airflow', 'mlflow', 'hugging face', 'transformers', 'bert', 'gpt',
    # Security
    'cybersecurity', 'information security', 'network security', 'penetration testing',
    'ethical hacking', 'soc', 'siem', 'splunk', 'wireshark', 'nmap', 'metasploit',
    'iso 27001', 'nist', 'gdpr', 'pci dss', 'hipaa', 'grc', 'risk assessment',
    'vulnerability assessment', 'iam', 'sso', 'mfa', 'zero trust', 'ids', 'ips', 'firewall',
    'cissp', 'ceh', 'security+', 'cism', 'cisa',
    # Mobile
    'android', 'ios', 'react native', 'flutter', 'xamarin', 'ionic',
    # Tools & Other
    'git', 'jira', 'confluence', 'agile', 'scrum', 'kanban', 'devops', 'microservices',
    'rest api', 'graphql', 'soap', 'grpc', 'kafka', 'rabbitmq', 'celery', 'redis',
    'html', 'css', 'html5', 'css3', 'sass', 'less', 'webpack', 'vite', 'rollup',
    'oauth', 'jwt', 'ssl', 'tls', 'api', 'mvc', 'mvvm', 'oop', 'solid', 'design patterns',
    'tableau', 'power bi', 'excel', 'sap', 'salesforce', 'hubspot', 'zapier',
    'figma', 'sketch', 'adobe xd', 'photoshop', 'illustrator',
    # Soft Skills (limited set for matching)
    'communication', 'leadership', 'teamwork', 'problem solving', 'critical thinking',
    'project management', 'time management', 'collaboration', 'presentation',
    'analytical skills', 'attention to detail', 'adaptability', 'creativity',
}

SKILL_ALIASES = {
    'reactjs': 'react',
    'react.js': 'react',
    'node.js': 'nodejs',
    'node js': 'nodejs',
    'vue.js': 'vuejs',
    'next.js': 'nextjs',
    'scikit-learn': 'sklearn',
    'sci-kit learn': 'sklearn',
    'kubernetes': 'k8s',
    'amazon web services': 'aws',
    'google cloud platform': 'gcp',
    'google cloud': 'gcp',
    'microsoft azure': 'azure',
    'postgresql': 'postgres',
    'ms sql': 'mssql',
    'sql server': 'mssql',
    'c sharp': 'c#',
    'golang': 'go',
    'natural language processing': 'nlp',
    'machine learning': 'ml',
    'deep learning': 'dl',
    'artificial intelligence': 'ai',
    'information security': 'infosec',
    'ruby on rails': 'rails',
    'spring boot': 'springboot',
}


class SkillExtractor:
    def __init__(self):
        self.nlp = nlp
        self.tech_skills = TECH_SKILLS
        self.skill_aliases = SKILL_ALIASES
        try:
            self.stop_words = set(stopwords.words('english'))
        except LookupError:
            nltk.download('stopwords', quiet=True)
            self.stop_words = set(stopwords.words('english'))

    def extract_skills(self, text: str) -> list:
        if not text:
            return []

        text_lower = text.lower()
        found_skills = set()

        # Multi-word skill matching (longest first to avoid partial matches)
        sorted_skills = sorted(self.tech_skills, key=len, reverse=True)
        for skill in sorted_skills:
            pattern = r'\b' + re.escape(skill) + r'\b'
            if re.search(pattern, text_lower):
                normalized = self._normalize_skill(skill)
                found_skills.add(normalized)

        # NLP-based noun phrase extraction
        doc = self.nlp(text[:5000])
        for chunk in doc.noun_chunks:
            chunk_text = chunk.text.lower().strip()
            if chunk_text in self.tech_skills:
                found_skills.add(self._normalize_skill(chunk_text))

        # Named entity extraction for ORG (often tools/companies)
        for ent in doc.ents:
            ent_lower = ent.text.lower().strip()
            if ent.label_ in ('ORG', 'PRODUCT') and ent_lower in self.tech_skills:
                found_skills.add(self._normalize_skill(ent_lower))

        return sorted(list(found_skills))

    def _normalize_skill(self, skill: str) -> str:
        skill = skill.strip().lower()
        return self.skill_aliases.get(skill, skill)

    def get_skill_categories(self, skills: list) -> dict:
        categories = {
            'languages': [],
            'frameworks': [],
            'databases': [],
            'cloud_devops': [],
            'ml_ai': [],
            'security': [],
            'tools': [],
            'soft_skills': [],
            'other': []
        }

        lang_kws = {'python', 'java', 'javascript', 'typescript', 'c', 'c++', 'c#', 'ruby', 'php', 'go',
                    'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'bash', 'shell', 'powershell', 'dart'}
        fw_kws = {'react', 'angular', 'vue', 'nextjs', 'django', 'flask', 'fastapi', 'springboot',
                  'express', 'nodejs', 'laravel', 'rails', 'asp.net', '.net', 'bootstrap', 'tailwindcss'}
        db_kws = {'sql', 'mysql', 'postgresql', 'postgres', 'mongodb', 'redis', 'elasticsearch',
                  'cassandra', 'oracle', 'sqlite', 'dynamodb', 'firebase'}
        cloud_kws = {'aws', 'azure', 'gcp', 'docker', 'k8s', 'terraform', 'ansible', 'jenkins',
                     'ci/cd', 'linux', 'nginx', 'apache'}
        ml_kws = {'ml', 'dl', 'nlp', 'ai', 'tensorflow', 'pytorch', 'keras', 'sklearn',
                  'pandas', 'numpy', 'spark', 'hadoop'}
        sec_kws = {'cybersecurity', 'infosec', 'network security', 'penetration testing',
                   'grc', 'iso 27001', 'nist', 'cissp', 'ceh', 'security+', 'siem', 'splunk',
                   'wireshark', 'firewall', 'ids', 'ips', 'zero trust', 'iam'}
        soft_kws = {'communication', 'leadership', 'teamwork', 'problem solving', 'critical thinking',
                    'project management', 'collaboration', 'adaptability', 'creativity'}

        for skill in skills:
            skill_l = skill.lower()
            if skill_l in lang_kws:
                categories['languages'].append(skill)
            elif skill_l in fw_kws:
                categories['frameworks'].append(skill)
            elif skill_l in db_kws:
                categories['databases'].append(skill)
            elif skill_l in cloud_kws:
                categories['cloud_devops'].append(skill)
            elif skill_l in ml_kws:
                categories['ml_ai'].append(skill)
            elif skill_l in sec_kws:
                categories['security'].append(skill)
            elif skill_l in soft_kws:
                categories['soft_skills'].append(skill)
            else:
                categories['tools'].append(skill)

        return {k: v for k, v in categories.items() if v}
