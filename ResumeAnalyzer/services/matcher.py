import re
import math
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import nltk
from nltk.corpus import stopwords

for pkg in ['stopwords', 'punkt', 'punkt_tab']:
    try:
        nltk.data.find(f'corpora/{pkg}')
    except LookupError:
        try:
            nltk.download(pkg, quiet=True)
        except Exception:
            pass

EDUCATION_LEVELS = {
    'phd': 6, 'ph.d': 6, 'doctorate': 6, 'doctoral': 6,
    'master': 5, 'mba': 5, 'm.s': 5, 'm.e': 5, 'm.tech': 5, 'm.sc': 5,
    'bachelor': 4, 'b.s': 4, 'b.e': 4, 'b.tech': 4, 'b.sc': 4, 'undergraduate': 4,
    'associate': 3, 'diploma': 2, 'certificate': 1, 'high school': 0,
}


class ResumeMatcher:
    def __init__(self):
        try:
            self.stop_words = list(stopwords.words('english'))
        except LookupError:
            nltk.download('stopwords', quiet=True)
            self.stop_words = list(stopwords.words('english'))

        self.vectorizer = TfidfVectorizer(
            stop_words=self.stop_words,
            ngram_range=(1, 2),
            max_features=5000,
            lowercase=True
        )

    def match(self, parsed_resume: dict, job_description: str,
              resume_skills: list, jd_skills: list) -> dict:

        skill_match = self._match_skills(resume_skills, jd_skills)
        experience_match = self._match_experience(parsed_resume, job_description)
        education_match = self._match_education(parsed_resume, job_description)
        cert_match = self._match_certifications(parsed_resume, job_description)
        keyword_match = self._match_keywords(parsed_resume.get('raw_text', ''), job_description)

        return {
            'skill_match': skill_match,
            'experience_match': experience_match,
            'education_match': education_match,
            'certification_match': cert_match,
            'keyword_match': keyword_match,
            'overall_similarity': self._compute_overall_similarity(
                parsed_resume.get('raw_text', ''), job_description
            )
        }

    def _match_skills(self, resume_skills: list, jd_skills: list) -> dict:
        resume_set = set(s.lower() for s in resume_skills)
        jd_set = set(s.lower() for s in jd_skills)

        if not jd_set:
            return {
                'matched': list(resume_set),
                'missing': [],
                'extra': list(resume_set),
                'score': 100.0,
                'matched_count': len(resume_set),
                'required_count': 0
            }

        matched = resume_set & jd_set
        missing = jd_set - resume_set
        extra = resume_set - jd_set

        # Partial matching for compound skills
        additional_matched = set()
        remaining_missing = set()
        for miss in missing:
            found = False
            for res_skill in resume_set:
                if (miss in res_skill or res_skill in miss) and abs(len(miss) - len(res_skill)) <= 5:
                    additional_matched.add(miss)
                    found = True
                    break
            if not found:
                remaining_missing.add(miss)

        final_matched = matched | additional_matched
        score = (len(final_matched) / len(jd_set)) * 100 if jd_set else 100.0

        return {
            'matched': sorted(list(final_matched)),
            'missing': sorted(list(remaining_missing)),
            'extra': sorted(list(extra)),
            'score': round(min(score, 100.0), 1),
            'matched_count': len(final_matched),
            'required_count': len(jd_set)
        }

    def _match_experience(self, parsed_resume: dict, job_description: str) -> dict:
        resume_years = parsed_resume.get('years_of_experience', 0)

        required_years = 0
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s+)?(?:experience|exp)',
            r'minimum\s+(?:of\s+)?(\d+)\s*years?',
            r'at\s+least\s+(\d+)\s*years?',
            r'(\d+)\s*-\s*\d+\s*years?',
        ]
        for pattern in patterns:
            match = re.search(pattern, job_description, re.IGNORECASE)
            if match:
                required_years = float(match.group(1))
                break

        experience_entries = parsed_resume.get('experience', [])
        has_relevant = len(experience_entries) > 0

        if required_years == 0:
            score = 80.0 if has_relevant else 50.0
        elif resume_years >= required_years:
            score = 100.0
        elif resume_years >= required_years * 0.75:
            score = 80.0
        elif resume_years >= required_years * 0.5:
            score = 60.0
        elif resume_years > 0:
            score = 40.0
        else:
            score = 20.0

        return {
            'resume_years': resume_years,
            'required_years': required_years,
            'has_relevant_experience': has_relevant,
            'experience_entries': experience_entries[:5],
            'score': round(score, 1),
            'status': self._experience_status(resume_years, required_years)
        }

    def _experience_status(self, resume_years: float, required_years: float) -> str:
        if required_years == 0:
            return 'Not specified in JD'
        if resume_years >= required_years:
            return f'Meets requirement ({resume_years} years vs {required_years} required)'
        elif resume_years > 0:
            return f'Below requirement ({resume_years} years vs {required_years} required)'
        return 'No experience detected'

    def _match_education(self, parsed_resume: dict, job_description: str) -> dict:
        education_list = parsed_resume.get('education', [])
        education_text = ' '.join(education_list).lower()
        jd_lower = job_description.lower()

        resume_level = 0
        for degree, level in EDUCATION_LEVELS.items():
            if degree in education_text:
                resume_level = max(resume_level, level)

        required_level = 0
        for degree, level in EDUCATION_LEVELS.items():
            if degree in jd_lower:
                required_level = max(required_level, level)

        relevant_fields = ['computer science', 'information technology', 'software', 'engineering',
                           'data science', 'mathematics', 'statistics', 'business', 'finance',
                           'cybersecurity', 'information systems', 'electrical']
        field_match = any(field in education_text for field in relevant_fields)

        if required_level == 0:
            score = 75.0
        elif resume_level >= required_level:
            score = 100.0
        elif resume_level == required_level - 1:
            score = 70.0
        elif resume_level > 0:
            score = 50.0
        else:
            score = 20.0

        if field_match:
            score = min(score + 10, 100.0)

        level_names = {0: 'None', 1: 'Certificate', 2: 'Diploma', 3: 'Associate',
                       4: "Bachelor's", 5: "Master's", 6: 'PhD'}

        return {
            'resume_education': education_list,
            'resume_level': level_names.get(resume_level, 'Unknown'),
            'required_level': level_names.get(required_level, 'Not specified'),
            'field_match': field_match,
            'score': round(score, 1),
            'status': 'Meets requirement' if resume_level >= required_level else 'Below requirement'
        }

    def _match_certifications(self, parsed_resume: dict, job_description: str) -> dict:
        resume_certs = parsed_resume.get('certifications', [])
        resume_cert_text = ' '.join(resume_certs).lower()
        jd_lower = job_description.lower()

        cert_keywords = [
            'aws certified', 'azure certified', 'google certified', 'pmp', 'cissp', 'ceh',
            'cism', 'cisa', 'security+', 'network+', 'ccna', 'ccnp', 'scrum', 'agile',
            'itil', 'six sigma', 'iso 27001', 'comptia', 'rhce', 'cka', 'ckad',
            'terraform', 'kubernetes', 'docker certified', 'java certified',
        ]

        jd_certs = [cert for cert in cert_keywords if cert in jd_lower]
        matched_certs = []
        missing_certs = []

        for cert in jd_certs:
            cert_words = cert.split()
            if any(word in resume_cert_text for word in cert_words if len(word) > 3):
                matched_certs.append(cert)
            else:
                missing_certs.append(cert)

        if not jd_certs:
            score = 70.0 if resume_certs else 50.0
        elif matched_certs:
            score = min((len(matched_certs) / len(jd_certs)) * 100, 100.0)
        else:
            score = 0.0

        return {
            'resume_certifications': resume_certs,
            'required_certifications': jd_certs,
            'matched_certifications': matched_certs,
            'missing_certifications': missing_certs,
            'score': round(score, 1),
            'status': 'Has relevant certifications' if matched_certs else (
                'No specific certs required' if not jd_certs else 'Missing required certifications'
            )
        }

    def _match_keywords(self, resume_text: str, job_description: str) -> dict:
        if not resume_text or not job_description:
            return {'matched_keywords': [], 'missing_keywords': [], 'score': 0.0}

        jd_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', job_description.lower()))
        resume_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', resume_text.lower()))

        try:
            stop = set(stopwords.words('english'))
        except Exception:
            stop = set()

        common_generic = {'with', 'will', 'work', 'able', 'have', 'must', 'well', 'good',
                          'team', 'also', 'into', 'that', 'this', 'from', 'they', 'their',
                          'more', 'both', 'some', 'such', 'been', 'your', 'role', 'using'}
        stop = stop | common_generic

        jd_keywords = jd_words - stop
        resume_keywords = resume_words - stop

        matched = jd_keywords & resume_keywords
        missing = jd_keywords - resume_keywords

        top_missing = sorted(list(missing))[:15]
        top_matched = sorted(list(matched))[:20]

        score = (len(matched) / len(jd_keywords)) * 100 if jd_keywords else 0.0

        return {
            'matched_keywords': top_matched,
            'missing_keywords': top_missing,
            'score': round(min(score, 100.0), 1)
        }

    def _compute_overall_similarity(self, resume_text: str, job_description: str) -> float:
        if not resume_text or not job_description:
            return 0.0
        try:
            vectors = self.vectorizer.fit_transform([resume_text, job_description])
            similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]
            return round(float(similarity) * 100, 1)
        except Exception:
            return 0.0
