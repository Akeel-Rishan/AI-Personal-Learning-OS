"""Seed the initial AI/ML skill graph and platform achievements."""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Achievement, Skill, SkillPrerequisite


SKILLS: tuple[dict[str, str | int | float], ...] = (
    {"name": "Python Fundamentals", "slug": "python-fundamentals", "category": "programming", "difficulty_level": 1, "estimated_hours": 20},
    {"name": "Python OOP", "slug": "python-oop", "category": "programming", "difficulty_level": 2, "estimated_hours": 15},
    {"name": "Python Data Structures", "slug": "python-data-structures", "category": "programming", "difficulty_level": 2, "estimated_hours": 10},
    {"name": "Git & Version Control", "slug": "git-version-control", "category": "programming", "difficulty_level": 1, "estimated_hours": 8},
    {"name": "NumPy", "slug": "numpy", "category": "data-science", "difficulty_level": 2, "estimated_hours": 15},
    {"name": "Pandas", "slug": "pandas", "category": "data-science", "difficulty_level": 2, "estimated_hours": 20},
    {"name": "Data Visualization", "slug": "data-visualization", "category": "data-science", "difficulty_level": 2, "estimated_hours": 12},
    {"name": "SQL Fundamentals", "slug": "sql-fundamentals", "category": "data-science", "difficulty_level": 1, "estimated_hours": 15},
    {"name": "Exploratory Data Analysis", "slug": "exploratory-data-analysis", "category": "data-science", "difficulty_level": 2, "estimated_hours": 15},
    {"name": "Statistics Fundamentals", "slug": "statistics-fundamentals", "category": "mathematics", "difficulty_level": 2, "estimated_hours": 20},
    {"name": "Probability Theory", "slug": "probability-theory", "category": "mathematics", "difficulty_level": 2, "estimated_hours": 15},
    {"name": "Linear Algebra", "slug": "linear-algebra", "category": "mathematics", "difficulty_level": 3, "estimated_hours": 25},
    {"name": "Calculus for ML", "slug": "calculus-for-ml", "category": "mathematics", "difficulty_level": 3, "estimated_hours": 20},
    {"name": "Machine Learning Fundamentals", "slug": "ml-fundamentals", "category": "ml", "difficulty_level": 3, "estimated_hours": 30},
    {"name": "Supervised Learning", "slug": "supervised-learning", "category": "ml", "difficulty_level": 3, "estimated_hours": 25},
    {"name": "Unsupervised Learning", "slug": "unsupervised-learning", "category": "ml", "difficulty_level": 3, "estimated_hours": 20},
    {"name": "Model Evaluation", "slug": "model-evaluation", "category": "ml", "difficulty_level": 2, "estimated_hours": 12},
    {"name": "Feature Engineering", "slug": "feature-engineering", "category": "ml", "difficulty_level": 3, "estimated_hours": 18},
    {"name": "Deep Learning Fundamentals", "slug": "deep-learning-fundamentals", "category": "ml", "difficulty_level": 3, "estimated_hours": 35},
    {"name": "Neural Networks", "slug": "neural-networks", "category": "ml", "difficulty_level": 3, "estimated_hours": 30},
    {"name": "NLP Fundamentals", "slug": "nlp-fundamentals", "category": "ml", "difficulty_level": 3, "estimated_hours": 25},
    {"name": "Computer Vision", "slug": "computer-vision", "category": "ml", "difficulty_level": 3, "estimated_hours": 25},
    {"name": "LLMs & Generative AI", "slug": "llms-generative-ai", "category": "ml", "difficulty_level": 3, "estimated_hours": 30},
    {"name": "Agentic AI", "slug": "agentic-ai", "category": "ml", "difficulty_level": 3, "estimated_hours": 25},
    {"name": "Docker", "slug": "docker", "category": "devops", "difficulty_level": 2, "estimated_hours": 12},
    {"name": "MLOps Fundamentals", "slug": "mlops-fundamentals", "category": "devops", "difficulty_level": 3, "estimated_hours": 20},
    {"name": "FastAPI", "slug": "fastapi", "category": "devops", "difficulty_level": 2, "estimated_hours": 15},
    {"name": "Cloud Basics", "slug": "cloud-basics", "category": "devops", "difficulty_level": 2, "estimated_hours": 15},
)

PREREQUISITES: tuple[tuple[str, str, str], ...] = (
    ("numpy", "python-fundamentals", "required"),
    ("pandas", "numpy", "required"),
    ("pandas", "python-data-structures", "required"),
    ("ml-fundamentals", "statistics-fundamentals", "required"),
    ("ml-fundamentals", "linear-algebra", "required"),
    ("ml-fundamentals", "numpy", "required"),
    ("ml-fundamentals", "pandas", "required"),
    ("supervised-learning", "ml-fundamentals", "required"),
    ("unsupervised-learning", "ml-fundamentals", "required"),
    ("deep-learning-fundamentals", "ml-fundamentals", "required"),
    ("deep-learning-fundamentals", "calculus-for-ml", "required"),
    ("deep-learning-fundamentals", "linear-algebra", "required"),
    ("neural-networks", "deep-learning-fundamentals", "required"),
    ("llms-generative-ai", "neural-networks", "required"),
    ("llms-generative-ai", "nlp-fundamentals", "required"),
    ("agentic-ai", "llms-generative-ai", "required"),
    ("mlops-fundamentals", "docker", "required"),
    ("mlops-fundamentals", "ml-fundamentals", "required"),
    ("feature-engineering", "pandas", "required"),
    ("feature-engineering", "statistics-fundamentals", "required"),
    ("model-evaluation", "ml-fundamentals", "required"),
    ("exploratory-data-analysis", "pandas", "required"),
    ("exploratory-data-analysis", "statistics-fundamentals", "required"),
    ("exploratory-data-analysis", "data-visualization", "required"),
    ("statistics-fundamentals", "python-fundamentals", "recommended"),
    ("probability-theory", "statistics-fundamentals", "required"),
    ("fastapi", "python-oop", "required"),
    ("python-oop", "python-fundamentals", "required"),
    ("python-data-structures", "python-fundamentals", "required"),
)

ACHIEVEMENTS: tuple[dict[str, str | int], ...] = (
    {"name": "First Step", "description": "Complete your first exercise", "achievement_type": "milestone", "condition_value": 1, "xp_reward": 50},
    {"name": "Week Warrior", "description": "Maintain a 7-day learning streak", "achievement_type": "streak", "condition_value": 7, "xp_reward": 200},
    {"name": "Month Master", "description": "Maintain a 30-day learning streak", "achievement_type": "streak", "condition_value": 30, "xp_reward": 1000},
    {"name": "Skill Unlocked", "description": "Master your first skill", "achievement_type": "skill", "condition_value": 1, "xp_reward": 150},
    {"name": "10 Skills Strong", "description": "Master 10 skills", "achievement_type": "skill", "condition_value": 10, "xp_reward": 500},
    {"name": "Project Builder", "description": "Complete your first project", "achievement_type": "project", "condition_value": 1, "xp_reward": 300},
    {"name": "Assessment Ace", "description": "Score 90%+ on an assessment", "achievement_type": "assessment", "condition_value": 90, "xp_reward": 250},
)


def seed_data() -> None:
    """Insert missing skills, prerequisite edges, and achievements."""

    sync_database_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    engine = create_engine(sync_database_url, pool_pre_ping=True)
    skills_seeded = 0
    prerequisites_seeded = 0
    achievements_seeded = 0

    with Session(engine) as session:
        skills_by_slug = {
            skill.slug: skill for skill in session.scalars(select(Skill)).all()
        }
        for skill_data in SKILLS:
            slug = str(skill_data["slug"])
            if slug not in skills_by_slug:
                skill = Skill(**skill_data)
                session.add(skill)
                skills_by_slug[slug] = skill
                skills_seeded += 1

        session.flush()

        existing_edges = {
            (edge.skill_id, edge.prerequisite_id)
            for edge in session.scalars(select(SkillPrerequisite)).all()
        }
        for skill_slug, prerequisite_slug, importance in PREREQUISITES:
            skill = skills_by_slug[skill_slug]
            prerequisite = skills_by_slug[prerequisite_slug]
            edge_key = (skill.id, prerequisite.id)
            if edge_key not in existing_edges:
                session.add(
                    SkillPrerequisite(
                        skill_id=skill.id,
                        prerequisite_id=prerequisite.id,
                        importance=importance,
                    )
                )
                existing_edges.add(edge_key)
                prerequisites_seeded += 1

        existing_achievement_names = set(
            session.scalars(select(Achievement.name)).all()
        )
        for achievement_data in ACHIEVEMENTS:
            name = str(achievement_data["name"])
            if name not in existing_achievement_names:
                session.add(Achievement(**achievement_data))
                existing_achievement_names.add(name)
                achievements_seeded += 1

        session.commit()

    engine.dispose()
    print(f"Seeded {skills_seeded} skills and {prerequisites_seeded} prerequisites")
    print(f"Seeded {achievements_seeded} achievements")


if __name__ == "__main__":
    seed_data()

