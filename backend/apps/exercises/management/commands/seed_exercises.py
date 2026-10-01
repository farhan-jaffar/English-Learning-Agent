from django.core.management.base import BaseCommand
from apps.exercises.models import Exercise, TopicTag
from apps.authentication.models import Language

EXERCISES_DATA = [
    # A1 - Beginner
    {
        "title": "Introduce Yourself",
        "prompt_text": "Introduce yourself to a new classmate. Say your name, where you are from, your favorite hobby, and why you want to learn English.",
        "skill_focus": Exercise.SkillFocus.MIXED,
        "topic_tags": ["self-introduction", "hobbies", "basics"],
        "cefr_level": "A1",
        "vocabulary_hints": ["name", "from", "hobby", "student", "learn", "family", "like"],
        "min_duration_seconds": 15,
        "max_duration_seconds": 60,
    },
    {
        "title": "My Daily Morning Routine",
        "prompt_text": "Describe what you usually do in the morning from the moment you wake up until you start work or study.",
        "skill_focus": Exercise.SkillFocus.GRAMMAR,
        "topic_tags": ["daily routine", "present simple", "time"],
        "cefr_level": "A1",
        "vocabulary_hints": ["wake up", "breakfast", "shower", "coffee", "brush teeth", "morning"],
        "min_duration_seconds": 20,
        "max_duration_seconds": 60,
    },
    {
        "title": "Favorite Foods",
        "prompt_text": "Talk about two of your favorite foods. Describe what they taste like and when you like to eat them.",
        "skill_focus": Exercise.SkillFocus.VOCABULARY,
        "topic_tags": ["food", "preferences", "taste"],
        "cefr_level": "A1",
        "vocabulary_hints": ["delicious", "sweet", "spicy", "restaurant", "cook", "ingredients"],
        "min_duration_seconds": 15,
        "max_duration_seconds": 60,
    },
    # A2 - Elementary
    {
        "title": "A Memorable Weekend Trip",
        "prompt_text": "Tell a short story about a trip or weekend outing you took recently. Use past tense verbs to explain where you went and what happened.",
        "skill_focus": Exercise.SkillFocus.GRAMMAR,
        "topic_tags": ["past events", "travel", "storytelling"],
        "cefr_level": "A2",
        "vocabulary_hints": ["traveled", "visited", "enjoyed", "arrived", "weather", "hotel", "scenery"],
        "min_duration_seconds": 30,
        "max_duration_seconds": 90,
    },
    {
        "title": "Describing Your Hometown",
        "prompt_text": "Describe the town or city where you grew up. Mention the weather, the people, and what visitors should see.",
        "skill_focus": Exercise.SkillFocus.FLUENCY,
        "topic_tags": ["geography", "hometown", "culture"],
        "cefr_level": "A2",
        "vocabulary_hints": ["population", "neighborhood", "historic", "parks", "crowded", "peaceful"],
        "min_duration_seconds": 30,
        "max_duration_seconds": 90,
    },
    {
        "title": "Future Plans and Goals",
        "prompt_text": "Explain what you are planning to achieve over the next six months in your studies or personal life.",
        "skill_focus": Exercise.SkillFocus.GRAMMAR,
        "topic_tags": ["future tense", "ambitions", "planning"],
        "cefr_level": "A2",
        "vocabulary_hints": ["going to", "plan to", "hope", "career", "improve", "schedule"],
        "min_duration_seconds": 30,
        "max_duration_seconds": 90,
    },
    # B1 - Intermediate
    {
        "title": "Remote Work vs Office Work",
        "prompt_text": "Discuss the advantages and disadvantages of working remotely compared to working in a traditional office. Conclude with your personal preference.",
        "skill_focus": Exercise.SkillFocus.FLUENCY,
        "topic_tags": ["workplace", "technology", "comparison"],
        "cefr_level": "B1",
        "vocabulary_hints": ["flexibility", "commute", "productivity", "collaboration", "work-life balance", "distraction"],
        "min_duration_seconds": 45,
        "max_duration_seconds": 120,
    },
    {
        "title": "Handling a Difficult Customer or Situation",
        "prompt_text": "Describe a situation where you faced an unexpected challenge or misunderstanding. How did you resolve it?",
        "skill_focus": Exercise.SkillFocus.VOCABULARY,
        "topic_tags": ["conflict resolution", "storytelling", "problem-solving"],
        "cefr_level": "B1",
        "vocabulary_hints": ["misunderstanding", "resolution", "patience", "compromise", "negotiation", "outcome"],
        "min_duration_seconds": 45,
        "max_duration_seconds": 120,
    },
    {
        "title": "Impact of Social Media on Friendships",
        "prompt_text": "Share your perspective on whether social media has made people feel more connected or more isolated. Give specific examples.",
        "skill_focus": Exercise.SkillFocus.MIXED,
        "topic_tags": ["society", "digital life", "relationships"],
        "cefr_level": "B1",
        "vocabulary_hints": ["connected", "isolated", "algorithms", "interaction", "meaningful", "superficial"],
        "min_duration_seconds": 45,
        "max_duration_seconds": 120,
    },
    # B2 - Upper Intermediate
    {
        "title": "Artificial Intelligence in Everyday Life",
        "prompt_text": "Analyze how artificial intelligence is transforming education and modern jobs. Weigh the efficiency benefits against ethical concerns.",
        "skill_focus": Exercise.SkillFocus.VOCABULARY,
        "topic_tags": ["artificial intelligence", "ethics", "workplace transformation"],
        "cefr_level": "B2",
        "vocabulary_hints": ["automation", "disruption", "ethical dilemma", "efficiency", "augmentation", "cognition"],
        "min_duration_seconds": 60,
        "max_duration_seconds": 120,
    },
    {
        "title": "Urban Sustainability and Green Cities",
        "prompt_text": "Propose three pragmatic initiatives that municipal governments should implement to reduce carbon emissions and improve urban living conditions.",
        "skill_focus": Exercise.SkillFocus.FLUENCY,
        "topic_tags": ["sustainability", "environment", "public policy"],
        "cefr_level": "B2",
        "vocabulary_hints": ["infrastructure", "carbon footprint", "renewable energy", "transit", "biodiversity", "sustainability"],
        "min_duration_seconds": 60,
        "max_duration_seconds": 120,
    },
    {
        "title": "Overcoming Professional Adversity",
        "prompt_text": "Reflect on a setback you experienced. Discuss how resilience and emotional intelligence enabled you to rebound and grow.",
        "skill_focus": Exercise.SkillFocus.PRONUNCIATION,
        "topic_tags": ["leadership", "emotional intelligence", "resilience"],
        "cefr_level": "B2",
        "vocabulary_hints": ["resilience", "adversity", "perseverance", "emotional intelligence", "perspective", "growth mindset"],
        "min_duration_seconds": 60,
        "max_duration_seconds": 120,
    },
    # C1 - Advanced
    {
        "title": "The Economics of Higher Education",
        "prompt_text": "Critique the contemporary model of higher education financing. To what extent should tertiary education be publicly funded, and what are the macroeconomic ramifications?",
        "skill_focus": Exercise.SkillFocus.VOCABULARY,
        "topic_tags": ["macroeconomics", "education", "public policy"],
        "cefr_level": "C1",
        "vocabulary_hints": ["macroeconomic", "tertiary education", "subsidize", "inequity", "intellectual capital", "socioeconomic mobility"],
        "min_duration_seconds": 60,
        "max_duration_seconds": 120,
    },
    {
        "title": "Algorithmic Bias and Digital Sovereignty",
        "prompt_text": "Examine the tension between corporate proprietary algorithmic governance and personal data autonomy. Deliver a structured argument proposing an international regulatory framework.",
        "skill_focus": Exercise.SkillFocus.FLUENCY,
        "topic_tags": ["digital rights", "governance", "jurisprudence"],
        "cefr_level": "C1",
        "vocabulary_hints": ["algorithmic bias", "sovereignty", "transparency", "accountability", "jurisprudence", "ubiquitous"],
        "min_duration_seconds": 60,
        "max_duration_seconds": 120,
    },
    # C2 - Mastery
    {
        "title": "Philosophical Inquiry: Determinism vs Agency",
        "prompt_text": "Elucidate the philosophical debate between strict causal determinism and moral agency in modern neuroscience. Synthesize nuanced viewpoints with rhetorical clarity.",
        "skill_focus": Exercise.SkillFocus.MIXED,
        "topic_tags": ["philosophy", "neuroscience", "epistemology"],
        "cefr_level": "C2",
        "vocabulary_hints": ["epistemology", "determinism", "agency", "neurobiology", "phenomenology", "contingent", "indispensable"],
        "min_duration_seconds": 60,
        "max_duration_seconds": 120,
    },
]

class Command(BaseCommand):
    help = 'Seeds initial exercise bank with CEFR-graded speaking prompts'

    def handle(self, *args, **options):
        created_count = 0
        english, _ = Language.objects.get_or_create(
            code='en-US',
            defaults={'name': 'English (US)', 'is_active': True}
        )

        for data in EXERCISES_DATA:
            item = dict(data)
            tag_names = item.pop('topic_tags', [])
            item['language'] = english

            obj, created = Exercise.objects.get_or_create(
                title=item['title'],
                language=english,
                defaults=item
            )
            tag_objs = []
            for name in tag_names:
                tag, _ = TopicTag.objects.get_or_create(name=name)
                tag_objs.append(tag)
            obj.topic_tags.set(tag_objs)

            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded {created_count} exercises (Total available: {Exercise.objects.count()}).'
            )
        )
