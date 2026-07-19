"""
Skill Forge AI — Python-based heuristic intelligence for course creation.
Generates suggestions for tags, descriptions, outcomes, prerequisites, etc.
No external API keys needed.
"""
import re
import random


class SkillForgeAI:
    """AI-powered course content generation using heuristic methods."""

    # Knowledge base for category-specific suggestions
    CATEGORY_OUTCOMES = {
        'programming': [
            'Write clean, maintainable code following industry best practices',
            'Debug and troubleshoot common programming errors efficiently',
            'Build real-world projects from scratch',
            'Understand core programming concepts and design patterns',
        ],
        'web development': [
            'Build responsive, modern web applications from scratch',
            'Implement RESTful APIs and understand client-server architecture',
            'Deploy web applications to production environments',
            'Master both frontend and backend development workflows',
        ],
        'data science': [
            'Analyze and visualize complex datasets using industry-standard tools',
            'Build predictive models using machine learning algorithms',
            'Clean, preprocess, and transform raw data for analysis',
            'Communicate data-driven insights effectively',
        ],
        'design': [
            'Create visually compelling designs using modern design principles',
            'Build interactive prototypes for web and mobile applications',
            'Apply color theory, typography, and layout fundamentals',
            'Develop a professional design portfolio',
        ],
        'business': [
            'Develop strategic thinking and business analysis skills',
            'Create and present compelling business proposals',
            'Understand market dynamics and competitive analysis',
            'Apply project management methodologies effectively',
        ],
        'marketing': [
            'Create data-driven marketing strategies',
            'Master social media and content marketing techniques',
            'Analyze marketing metrics and optimize campaigns',
            'Build and manage effective marketing funnels',
        ],
        'default': [
            'Master the core concepts and fundamentals of this subject',
            'Apply learned skills to real-world scenarios and projects',
            'Build a strong foundation for advanced learning',
            'Develop practical expertise through hands-on exercises',
        ],
    }

    LEVEL_PREREQUISITES = {
        'beginner': [
            'No prior experience required',
            'Basic computer literacy',
            'Willingness to learn and practice',
        ],
        'intermediate': [
            'Basic understanding of the subject fundamentals',
            '3-6 months of hands-on experience',
            'Familiarity with core concepts and terminology',
        ],
        'advanced': [
            'Strong foundation in the subject area',
            '1+ years of practical experience',
            'Understanding of intermediate-level concepts',
            'Experience with real-world projects',
        ],
        'all_levels': [
            'No specific prerequisites — suitable for all skill levels',
            'A computer with internet access',
            'Enthusiasm and dedication to learning',
        ],
    }

    COMMON_TAGS = {
        'programming': ['coding', 'software', 'development', 'algorithms', 'debugging'],
        'web development': ['html', 'css', 'javascript', 'frontend', 'backend', 'fullstack'],
        'data science': ['python', 'analytics', 'machine-learning', 'statistics', 'visualization'],
        'design': ['ui', 'ux', 'figma', 'creative', 'visual-design', 'prototyping'],
        'business': ['strategy', 'management', 'leadership', 'entrepreneurship'],
        'marketing': ['digital-marketing', 'seo', 'social-media', 'content', 'branding'],
    }

    def _get_category_key(self, category_name):
        """Match category name to knowledge base key."""
        if not category_name:
            return 'default'
        cat_lower = category_name.lower()
        for key in self.CATEGORY_OUTCOMES:
            if key in cat_lower:
                return key
        return 'default'

    def _extract_keywords(self, text):
        """Extract meaningful keywords from text."""
        if not text:
            return []
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to',
            'for', 'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are',
            'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'shall', 'can', 'this', 'that', 'these', 'those', 'i', 'you',
            'he', 'she', 'it', 'we', 'they', 'how', 'what', 'which',
            'who', 'whom', 'your', 'our', 'their', 'its', 'my',
        }
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return [w for w in words if w not in stop_words][:15]

    def generate_tags(self, title, description=''):
        """Generate SEO tags from course title and description."""
        keywords = self._extract_keywords(f"{title} {description}")
        # Deduplicate while preserving order
        seen = set()
        tags = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                tags.append(kw)
        return tags[:10]

    def generate_summary(self, title, description=''):
        """Generate a course summary."""
        if description and len(description) > 50:
            # Use first 2 sentences of description
            sentences = re.split(r'[.!?]+', description)
            summary = '. '.join(s.strip() for s in sentences[:2] if s.strip())
            if summary:
                return summary + '.'

        return (
            f"This comprehensive course on {title} provides hands-on training "
            f"with practical projects and real-world applications. Master essential "
            f"skills and advance your career with expert-guided instruction."
        )

    def generate_learning_outcomes(self, title, category_name=''):
        """Generate learning outcomes based on title and category."""
        cat_key = self._get_category_key(category_name)
        outcomes = self.CATEGORY_OUTCOMES.get(cat_key, self.CATEGORY_OUTCOMES['default'])

        # Customize first outcome with course title
        customized = [f"Gain comprehensive understanding of {title}"]
        customized.extend(random.sample(outcomes, min(3, len(outcomes))))
        return customized

    def generate_prerequisites(self, title, skill_level='all_levels'):
        """Generate prerequisites based on skill level."""
        prereqs = self.LEVEL_PREREQUISITES.get(skill_level, self.LEVEL_PREREQUISITES['all_levels'])
        return prereqs

    def generate_highlights(self, title, description=''):
        """Generate course highlights."""
        keywords = self._extract_keywords(title)
        base_highlights = [
            f"Comprehensive coverage of {title}",
            "Hands-on projects and practical exercises",
            "Certificate of completion upon finishing",
            "Lifetime access to course materials",
            "Expert instructor guidance and support",
        ]

        if keywords:
            base_highlights.insert(1, f"Deep dive into {', '.join(keywords[:3])}")

        return base_highlights[:5]

    def generate_description(self, title, category_name='', skill_level='all_levels'):
        """Generate a course description suggestion."""
        level_text = {
            'beginner': 'designed for beginners with no prior experience',
            'intermediate': 'designed for learners with foundational knowledge',
            'advanced': 'designed for experienced practitioners',
            'all_levels': 'suitable for learners at all skill levels',
        }

        level = level_text.get(skill_level, level_text['all_levels'])

        return (
            f"Welcome to {title}! This course is {level}. "
            f"Through a carefully structured curriculum, you'll gain practical skills "
            f"and deep understanding that you can immediately apply in your work.\n\n"
            f"The course features hands-on projects, real-world examples, and "
            f"comprehensive exercises designed to reinforce your learning. "
            f"By the end of this course, you'll have the confidence and skills "
            f"to tackle real challenges in this field.\n\n"
            f"Start your learning journey today and take the next step in your career!"
        )

    def suggest_module_titles(self, title, num_modules=5):
        """Suggest module titles based on course title."""
        keywords = self._extract_keywords(title)
        templates = [
            "Introduction to {topic}",
            "Getting Started with {topic}",
            "Core Concepts of {topic}",
            "{topic} Fundamentals",
            "Advanced {topic} Techniques",
            "Practical {topic} Projects",
            "Best Practices in {topic}",
            "Real-World {topic} Applications",
        ]

        topic = ' '.join(keywords[:2]).title() if keywords else title

        suggestions = []
        for i, template in enumerate(templates[:num_modules]):
            suggestions.append(template.format(topic=topic))

        return suggestions

    def calculate_duration_display(self, total_seconds):
        """Format duration for display with AI branding."""
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60

        if hours > 0:
            duration = f"{hours}h {minutes}m"
        elif minutes > 0:
            duration = f"{minutes} minutes"
        else:
            duration = "Less than 1 minute"

        return f"Skill Forge AI calculated: {duration} of content"

    def suggest_quiz_questions(self, topic, num_questions=4):
        """Generate template quiz questions for a topic."""
        templates = [
            {
                'text': f'What is the primary purpose of {topic}?',
                'options': ['To improve performance', 'To reduce complexity', 'To enhance security', 'All of the above'],
                'correct': 'D',
                'explanation': f'Understanding the core purpose of {topic} helps build a strong foundation.',
            },
            {
                'text': f'Which of the following is a key concept in {topic}?',
                'options': ['Abstraction', 'Encapsulation', 'Modularity', 'All of the above'],
                'correct': 'D',
                'explanation': f'These are all fundamental concepts that apply to {topic}.',
            },
            {
                'text': f'What is a common best practice when working with {topic}?',
                'options': ['Skip testing', 'Write documentation', 'Avoid version control', 'Ignore errors'],
                'correct': 'B',
                'explanation': 'Documentation is essential for maintaining and scaling any project.',
            },
            {
                'text': f'Which approach is recommended for learning {topic}?',
                'options': ['Theory only', 'Practice only', 'Balanced theory and practice', 'Memorization'],
                'correct': 'C',
                'explanation': 'A balanced approach combining theory with hands-on practice yields the best results.',
            },
        ]

        return templates[:num_questions]
