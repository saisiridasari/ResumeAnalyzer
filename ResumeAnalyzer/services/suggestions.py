class SuggestionEngine:

    CERT_RECOMMENDATIONS = {
        'aws': ['AWS Certified Solutions Architect', 'AWS Certified Developer', 'AWS Cloud Practitioner'],
        'azure': ['Microsoft Certified: Azure Fundamentals (AZ-900)', 'Azure Administrator (AZ-104)', 'Azure Developer (AZ-204)'],
        'gcp': ['Google Cloud Associate Cloud Engineer', 'Google Cloud Professional Cloud Architect'],
        'security': ['CompTIA Security+', 'CISSP', 'CEH (Certified Ethical Hacker)', 'CISM'],
        'grc': ['CISA', 'CRISC', 'ISO 27001 Lead Auditor', 'CISM'],
        'project management': ['PMP (Project Management Professional)', 'PMI-ACP', 'Certified Scrum Master'],
        'devops': ['Docker Certified Associate', 'Certified Kubernetes Administrator (CKA)', 'HashiCorp Terraform Associate'],
        'data': ['Google Data Analytics Certificate', 'IBM Data Science Professional', 'Tableau Desktop Specialist'],
        'ml': ['TensorFlow Developer Certificate', 'AWS Machine Learning Specialty', 'Azure AI Engineer Associate'],
    }

    ATS_TIPS = [
        'Use standard section headers like "Experience", "Education", "Skills".',
        'Include exact keywords from the job description in your resume.',
        'Avoid tables, columns, headers/footers — ATS systems struggle to parse them.',
        'Use a clean, single-column layout for maximum ATS compatibility.',
        'Quantify achievements with numbers (e.g., "Reduced load time by 40%").',
        'Save your resume as a PDF or DOCX — both are ATS-friendly.',
        'Spell out acronyms at least once (e.g., "Machine Learning (ML)").',
        'Include a dedicated Skills section with a clear, scannable list.',
        'Match your job title to the one in the job description where truthful.',
        'Remove graphics, images, and fancy formatting that ATS cannot read.',
    ]

    def generate(self, match_result: dict, score_result: dict, parsed_resume: dict) -> dict:
        suggestions = {
            'skill_suggestions': self._skill_suggestions(match_result),
            'certification_suggestions': self._cert_suggestions(match_result, parsed_resume),
            'keyword_suggestions': self._keyword_suggestions(match_result),
            'experience_suggestions': self._experience_suggestions(match_result, score_result),
            'education_suggestions': self._education_suggestions(match_result),
            'ats_suggestions': self._ats_suggestions(score_result, parsed_resume),
            'project_suggestions': self._project_suggestions(match_result, parsed_resume),
            'overall_action_plan': self._action_plan(match_result, score_result),
            'strengths': self._identify_strengths(match_result, score_result),
            'priority_level': self._get_priority(score_result['overall'])
        }
        return suggestions

    def _skill_suggestions(self, match_result: dict) -> list:
        missing = match_result.get('skill_match', {}).get('missing', [])
        suggestions = []
        for skill in missing[:10]:
            suggestions.append({
                'skill': skill,
                'action': f'Add "{skill}" to your Skills section if you have experience with it.',
                'priority': 'High'
            })
        return suggestions

    def _cert_suggestions(self, match_result: dict, parsed_resume: dict) -> list:
        missing_certs = match_result.get('certification_match', {}).get('missing_certifications', [])
        matched_skills = match_result.get('skill_match', {}).get('matched', [])
        suggestions = []

        for cert in missing_certs[:3]:
            suggestions.append({
                'certification': cert.title(),
                'reason': 'Required or preferred in the job description',
                'priority': 'High'
            })

        for skill_domain, certs in self.CERT_RECOMMENDATIONS.items():
            if any(skill_domain in s.lower() for s in matched_skills):
                for cert in certs[:1]:
                    entry = {'certification': cert, 'reason': f'Complements your {skill_domain} skills', 'priority': 'Medium'}
                    if entry not in suggestions:
                        suggestions.append(entry)

        return suggestions[:6]

    def _keyword_suggestions(self, match_result: dict) -> list:
        missing_kws = match_result.get('keyword_match', {}).get('missing_keywords', [])
        suggestions = []
        for kw in missing_kws[:10]:
            suggestions.append({
                'keyword': kw,
                'action': f'Include the term "{kw}" naturally in your experience bullets or summary.',
                'section': 'Summary or Experience'
            })
        return suggestions

    def _experience_suggestions(self, match_result: dict, score_result: dict) -> list:
        exp_data = match_result.get('experience_match', {})
        suggestions = []

        resume_years = exp_data.get('resume_years', 0)
        required_years = exp_data.get('required_years', 0)

        if required_years > 0 and resume_years < required_years:
            gap = required_years - resume_years
            suggestions.append(
                f'You are approximately {gap:.0f} year(s) short of the required experience. '
                f'Consider highlighting freelance, internship, or project experience to bridge this gap.'
            )

        if not exp_data.get('has_relevant_experience'):
            suggestions.append(
                'No clear work experience was detected. Ensure your experience section uses '
                'standard headers and includes dates (Month YYYY – Month YYYY format).'
            )

        exp_score = score_result['breakdown']['experience']['score']
        if exp_score < 60:
            suggestions.append(
                'Strengthen your experience section with specific, quantified achievements '
                '(e.g., "Reduced deployment time by 35%" or "Managed a team of 5 engineers").'
            )

        suggestions.append(
            'Use the STAR method (Situation, Task, Action, Result) for each bullet point to maximize impact.'
        )

        return suggestions[:5]

    def _education_suggestions(self, match_result: dict) -> list:
        edu_data = match_result.get('education_match', {})
        suggestions = []

        if edu_data.get('status') == 'Below requirement':
            suggestions.append(
                f'The role may prefer a {edu_data.get("required_level", "higher")} degree. '
                f'Emphasize relevant certifications, bootcamps, and practical projects to compensate.'
            )

        if not edu_data.get('field_match'):
            suggestions.append(
                'Your education field may not directly match the job requirements. '
                'Highlight transferable coursework, projects, or self-study in your summary.'
            )

        return suggestions

    def _ats_suggestions(self, score_result: dict, parsed_resume: dict) -> list:
        suggestions = []
        ats_score = score_result.get('ats_score', 0)

        if ats_score < 60:
            suggestions.extend(self.ATS_TIPS[:5])
        elif ats_score < 80:
            suggestions.extend(self.ATS_TIPS[:3])
        else:
            suggestions.extend(self.ATS_TIPS[:2])

        if not parsed_resume.get('email') or parsed_resume.get('email') == 'Not Found':
            suggestions.append('Ensure your email address is clearly visible in the header of your resume.')

        if not parsed_resume.get('phone') or parsed_resume.get('phone') == 'Not Found':
            suggestions.append('Add a phone number to your resume contact section.')

        if not parsed_resume.get('linkedin'):
            suggestions.append('Add your LinkedIn profile URL to your contact section.')

        return suggestions[:7]

    def _project_suggestions(self, match_result: dict, parsed_resume: dict) -> list:
        suggestions = []
        missing_skills = match_result.get('skill_match', {}).get('missing', [])
        projects = parsed_resume.get('projects', [])

        if missing_skills:
            top_missing = missing_skills[:3]
            skills_str = ', '.join(top_missing)
            suggestions.append(
                f'Build a portfolio project using {skills_str} to demonstrate hands-on experience with these required skills.'
            )

        if len(projects) < 2:
            suggestions.append(
                'Add 2-3 significant projects to your resume with clear descriptions, '
                'technologies used, and quantifiable outcomes.'
            )

        suggestions.append(
            'Host your projects on GitHub and include the repository link in your resume. '
            'Recruiters value seeing real, working code.'
        )

        suggestions.append(
            'For each project, describe: what it does, the tech stack used, your specific role, '
            'and measurable impact or outcomes.'
        )

        return suggestions[:4]

    def _action_plan(self, match_result: dict, score_result: dict) -> list:
        overall = score_result['overall']
        plan = []

        if overall >= 85:
            plan = [
                'Your profile is an excellent match. Tailor your summary to mirror the job description language.',
                'Prepare STAR-format stories for each matched skill to ace behavioral interviews.',
                'Research the company culture, product, and recent news for interview preparation.',
            ]
        elif overall >= 70:
            plan = [
                'Strong match. Address the missing skills by updating your resume with any relevant experience.',
                'Add 2-3 keywords from the JD into your professional summary.',
                'Pursue any recommended certifications to strengthen your profile.',
            ]
        elif overall >= 55:
            plan = [
                'Good foundation. Focus on filling the skill gaps identified in the analysis.',
                'Rewrite 3-5 experience bullet points to include JD keywords.',
                'Add a targeted professional summary that directly addresses the role requirements.',
                'Pursue at least one relevant certification to strengthen your application.',
            ]
        elif overall >= 40:
            plan = [
                'Significant skill gaps exist. Prioritize learning the top 5 missing skills.',
                'Complete an online course or project for each critical missing skill.',
                'Rewrite your resume from scratch with this specific JD in mind.',
                'Network with professionals in this role to gain informational interview insights.',
            ]
        else:
            plan = [
                'Major gaps between your current profile and this role.',
                'Consider applying for junior or adjacent roles to build relevant experience.',
                'Create a 3-6 month learning plan focused on the top missing skills.',
                'Build portfolio projects demonstrating the required technical skills.',
                'Consider informational interviews to understand what it takes to qualify for this role.',
            ]

        return plan

    def _identify_strengths(self, match_result: dict, score_result: dict) -> list:
        strengths = []
        breakdown = score_result.get('breakdown', {})

        if breakdown.get('skills', {}).get('score', 0) >= 70:
            matched = match_result.get('skill_match', {}).get('matched', [])
            strengths.append(f'Strong technical skill alignment — {len(matched)} matching skills detected.')

        if breakdown.get('experience', {}).get('score', 0) >= 70:
            years = match_result.get('experience_match', {}).get('resume_years', 0)
            strengths.append(f'Solid experience profile with {years} year(s) of relevant experience.')

        if breakdown.get('education', {}).get('score', 0) >= 70:
            edu_level = match_result.get('education_match', {}).get('resume_level', '')
            strengths.append(f'{edu_level} degree meets or exceeds the education requirement.')

        if breakdown.get('certifications', {}).get('score', 0) >= 70:
            certs = match_result.get('certification_match', {}).get('resume_certifications', [])
            if certs:
                strengths.append(f'Strong certification profile: {", ".join(certs[:3])}.')

        if not strengths:
            strengths.append('You have foundational qualifications. Focus on the improvement areas to increase your match score.')

        return strengths

    def _get_priority(self, score: float) -> str:
        if score >= 85:
            return 'apply_now'
        elif score >= 70:
            return 'apply_with_minor_updates'
        elif score >= 55:
            return 'update_before_applying'
        elif score >= 40:
            return 'significant_updates_needed'
        return 'major_reskilling_required'
