from django.core.management.base import BaseCommand
from jobs.models import Skill


class Command(BaseCommand):
    help = "Create the initial CareerBridge skill list"

    def handle(self, *args, **options):
        names = [
            "Python", "Java", "C", "C++", "C#", "PHP", "Ruby", "Go", "Kotlin", "Swift",
            "JavaScript", "TypeScript", "HTML", "CSS", "Bootstrap", "Tailwind CSS",
            "Django", "Flask", "FastAPI", "Laravel", "Spring Boot", "Node.js", "Express.js",
            "Angular", "React", "Vue.js", "REST API", "GraphQL",
            "SQL", "MySQL", "PostgreSQL", "SQLite", "MongoDB", "Redis",
            "Git", "GitHub", "Docker", "Linux", "AWS", "Microsoft Azure", "Google Cloud",
            "Data Analysis", "Data Visualization", "Machine Learning", "Artificial Intelligence",
            "Pandas", "NumPy", "Matplotlib", "Power BI", "Tableau", "Microsoft Excel",
            "UI/UX Design", "Figma", "Cybersecurity", "Software Testing", "Agile", "Scrum",
            "Communication", "Teamwork", "Problem Solving", "Critical Thinking",
            "Time Management", "Leadership", "English", "Thai",
        ]
        created = 0
        for name in names:
            _, was_created = Skill.objects.get_or_create(name=name)
            created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f"Created {created} new skills; {len(names)} skills available."))
