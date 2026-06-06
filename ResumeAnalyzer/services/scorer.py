class ScoreCalculator:
    WEIGHTS = {
        'skills': 0.50,
        'experience': 0.20,
        'education': 0.15,
        'certifications': 0.10,
        'keywords': 0.05,
    }

    def calculate(self, match_result: dict) -> dict:
        skill_score = match_result.get('skill_match', {}).get('score', 0)
        experience_score = match_result.get('experience_match', {}).get('score', 0)
        education_score = match_result.get('education_match', {}).get('score', 0)
        cert_score = match_result.get('certification_match', {}).get('score', 0)
        keyword_score = match_result.get('keyword_match', {}).get('score', 0)

        overall = (
            skill_score * self.WEIGHTS['skills'] +
            experience_score * self.WEIGHTS['experience'] +
            education_score * self.WEIGHTS['education'] +
            cert_score * self.WEIGHTS['certifications'] +
            keyword_score * self.WEIGHTS['keywords']
        )

        overall = round(min(max(overall, 0), 100), 1)

        return {
            'overall': overall,
            'breakdown': {
                'skills': {
                    'score': round(skill_score, 1),
                    'weight': int(self.WEIGHTS['skills'] * 100),
                    'weighted': round(skill_score * self.WEIGHTS['skills'], 1)
                },
                'experience': {
                    'score': round(experience_score, 1),
                    'weight': int(self.WEIGHTS['experience'] * 100),
                    'weighted': round(experience_score * self.WEIGHTS['experience'], 1)
                },
                'education': {
                    'score': round(education_score, 1),
                    'weight': int(self.WEIGHTS['education'] * 100),
                    'weighted': round(education_score * self.WEIGHTS['education'], 1)
                },
                'certifications': {
                    'score': round(cert_score, 1),
                    'weight': int(self.WEIGHTS['certifications'] * 100),
                    'weighted': round(cert_score * self.WEIGHTS['certifications'], 1)
                },
                'keywords': {
                    'score': round(keyword_score, 1),
                    'weight': int(self.WEIGHTS['keywords'] * 100),
                    'weighted': round(keyword_score * self.WEIGHTS['keywords'], 1)
                }
            },
            'rating': self._get_rating(overall),
            'rating_color': self._get_rating_color(overall),
            'ats_score': self._estimate_ats_score(overall, skill_score, keyword_score),
            'percentile': self._estimate_percentile(overall)
        }

    def _get_rating(self, score: float) -> str:
        if score >= 85:
            return 'Excellent Match'
        elif score >= 70:
            return 'Strong Match'
        elif score >= 55:
            return 'Good Match'
        elif score >= 40:
            return 'Moderate Match'
        elif score >= 25:
            return 'Weak Match'
        return 'Poor Match'

    def _get_rating_color(self, score: float) -> str:
        if score >= 85:
            return '#10b981'
        elif score >= 70:
            return '#3b82f6'
        elif score >= 55:
            return '#f59e0b'
        elif score >= 40:
            return '#f97316'
        return '#ef4444'

    def _estimate_ats_score(self, overall: float, skill_score: float, keyword_score: float) -> float:
        ats = (overall * 0.5 + skill_score * 0.3 + keyword_score * 0.2)
        return round(min(ats, 100), 1)

    def _estimate_percentile(self, score: float) -> int:
        if score >= 85:
            return 92
        elif score >= 70:
            return 78
        elif score >= 55:
            return 58
        elif score >= 40:
            return 38
        elif score >= 25:
            return 20
        return 8
