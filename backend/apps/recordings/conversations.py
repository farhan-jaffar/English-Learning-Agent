"""
Conversational Dialogue Engine for FluentFlow AI English Learning Agent.
Defines roleplay scenarios, initial agent prompts, and multi-turn response generation logic.
"""

SCENARIOS = {
    'job_interview': {
        'id': 'job_interview',
        'title': 'Software Developer Job Interview',
        'persona': 'Sarah Jensen — VP of Engineering',
        'difficulty': 'B2',
        'category': 'Career & Professional',
        'objective': 'Practice answering behavioral interview questions using the STAR method (Situation, Task, Action, Result) with clear technical vocabulary.',
        'opening_message': (
            "Hello and welcome! Thank you for taking the time to speak with me today. "
            "To begin our conversation, could you briefly introduce yourself and tell me about a recent technical project you worked on?"
        ),
        'follow_ups': [
            (
                "That sounds like an interesting project. When you encountered unexpected technical roadblocks or disagreements "
                "within your team during that build, how did you resolve them?"
            ),
            (
                "Excellent reflection. Looking forward, how do you continuously keep your technical skills sharp in such a fast-evolving industry?"
            ),
            (
                "Thank you for sharing your journey. Do you have any questions for me about our engineering culture, development velocity, or roadmap?"
            ),
            (
                "It was a genuine pleasure speaking with you today! Your structured explanations, vocabulary choices, "
                "and steady pacing demonstrated solid professional communication. Our talent team will follow up shortly."
            ),
        ],
    },
    'coffee_shop': {
        'id': 'coffee_shop',
        'title': 'Ordering at a Bustling Urban Café',
        'persona': 'Leo — Friendly Barista',
        'difficulty': 'A2',
        'category': 'Daily Life & Service',
        'objective': 'Practice ordering drinks, asking about milk alternatives, requesting customized snacks, and handling payment interactions.',
        'opening_message': (
            "Good morning! Welcome to Roasters & Co. The espresso grinder is warmed up and ready. "
            "What can I get started for you today?"
        ),
        'follow_ups': [
            (
                "Great choice! Would you like whole milk, oat milk, or almond milk with that? And what size would you prefer—regular or large?"
            ),
            (
                "You got it! We also just pulled freshly baked blueberry scones and warm croissants out of the oven. "
                "Can I tempt you with any pastry or snack today?"
            ),
            (
                "Will that be for here, or to go? And would you like to pay with card, phone, or cash?"
            ),
            (
                "Awesome, your total is $6.50. Give us just two minutes, and your drink will be ready at the pickup bar on your right. "
                "Have a wonderful morning!"
            ),
        ],
    },
    'airport_travel': {
        'id': 'airport_travel',
        'title': 'Airport Check-In & Border Customs',
        'persona': 'Officer Williams — Gate & Border Control Agent',
        'difficulty': 'B1',
        'category': 'Travel & Hospitality',
        'objective': 'Practice explaining your travel itinerary, accommodation plans, and answering customs inquiries clearly and politely.',
        'opening_message': (
            "Next in line, please! Good afternoon. May I please see your passport, boarding pass, and customs declaration form?"
        ),
        'follow_ups': [
            (
                "Thank you. What is the primary purpose of your trip abroad, and how many days do you plan to stay?"
            ),
            (
                "Understood. Where will you be staying during your visit, and are you traveling alone or accompanying colleagues or family?"
            ),
            (
                "Do you have any commercial merchandise, fresh agricultural items, or currency exceeding $10,000 to declare today?"
            ),
            (
                "Everything checks out in order. Here is your stamped passport and boarding pass. "
                "Your departure gate is B14 on the upper level. Have a safe flight and enjoy your trip!"
            ),
        ],
    },
    'tech_debate': {
        'id': 'tech_debate',
        'title': 'The Ethics of Artificial Intelligence Debate',
        'persona': 'Dr. Alistair Finch — Oxford Philosophy & AI Fellow',
        'difficulty': 'C1',
        'category': 'Academic & Debate',
        'objective': 'Formulate and defend nuanced arguments regarding algorithmic accountability, intellectual property, and societal disruption.',
        'opening_message': (
            "Welcome to our colloquium. Today we are critically examining autonomous generative systems. "
            "In your assessment, who should bear legal and moral accountability when an AI agent outputs harmful misinformation or infringes copyright?"
        ),
        'follow_ups': [
            (
                "A compelling premise. However, given that deep neural networks operate as probabilistic black boxes, "
                "how can regulatory frameworks enforce strict transparency without stifling open-source technological innovation?"
            ),
            (
                "Taking into account the macroeconomic consequences on intellectual labor and creative industries, "
                "what fiscal policy or social safety nets do you propose to mitigate systemic workforce displacement?"
            ),
            (
                "A thoroughly articulated synthesis. Your precision of argument, use of sophisticated qualifying clauses, "
                "and academic rhetorical composure demonstrate exceptional mastery of advanced English discourse."
            ),
        ],
    },
}

def get_scenario(scenario_id: str):
    """Retrieve scenario definition by ID or return default."""
    return SCENARIOS.get(scenario_id, SCENARIOS['job_interview'])

def get_all_scenarios():
    """Return catalog of all available dialogue scenarios."""
    return list(SCENARIOS.values())

def generate_coach_follow_up(scenario_id: str, turn_number: int, user_transcript: str = ""):
    """
    Generates the next agent conversational turn.
    turn_number is 1-indexed count of user turns completed so far.
    """
    scenario = get_scenario(scenario_id)
    follow_ups = scenario.get('follow_ups', [])

    if not follow_ups:
        return "Tell me more about that — I'd love to hear your thoughts.", False

    index = min(max(0, turn_number - 1), len(follow_ups) - 1)
    coach_text = follow_ups[index]
    is_concluding = (index >= len(follow_ups) - 1)
    return coach_text, is_concluding
