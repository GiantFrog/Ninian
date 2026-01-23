async def get_new_skills(client, skills):
    with open("../../database/feh/skill.json", "r") as existingSkills:
        new_skills = []
        for skill in skills:
            if skill not in existingSkills:
                new_skills.append(skill)
