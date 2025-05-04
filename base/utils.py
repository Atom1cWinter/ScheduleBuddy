def sort_sections_by_survey(survey, sections):
    """Sort sections based on how well they match the user's survey preferences."""
    def calculate_score(section):
        score = 0

        # Time preference scoring
        if survey.time_distribution == "morning" and section.begins and section.begins < "12:00:00":
            score += 3
        elif survey.time_distribution == "afternoon" and section.begins and "12:00:00" <= section.begins < "16:00:00":
            score += 2
        elif survey.time_distribution == "evening" and section.begins and section.begins >= "16:00:00":
            score += 1

        # Night class preference
        if not survey.night_classes_ok and section.begins and section.begins >= "18:00:00":
            score -= 5

        # Day preference scoring
        preferred_days = {
            'MWF': ['mo', 'we', 'fr'],
            'TTH': ['tu', 'th'],
            'Spread': ['mo', 'tu', 'we', 'th', 'fr']
        }.get(survey.preferred_distribution, [])

        if section.mo and 'mo' in preferred_days:
            score += 1
        if section.tu and 'tu' in preferred_days:
            score += 1
        if section.we and 'we' in preferred_days:
            score += 1
        if section.th and 'th' in preferred_days:
            score += 1
        if section.fr and 'fr' in preferred_days:
            score += 1

        return score

    # Annotate sections with scores and sort them
    sections_with_scores = [(section, calculate_score(section)) for section in sections]
    sorted_sections = sorted(sections_with_scores, key=lambda x: x[1], reverse=True)

    return [section for section, score in sorted_sections]