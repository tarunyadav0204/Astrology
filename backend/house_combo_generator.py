"""
House Combination Generator
Automatically generates house combinations using house specifications
"""

import sqlite3
import json
import itertools
from typing import List, Dict, Tuple, Set
from collections import defaultdict

class HouseCombinationGenerator:
    def __init__(self):
        self.house_specs = self._load_house_specifications()
        self.combination_templates = self._define_combination_templates()
    
    def _load_house_specifications(self) -> Dict[int, List[str]]:
        """Load house specifications from database"""
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        cursor.execute("SELECT house_number, specifications FROM house_specifications")
        rows = cursor.fetchall()
        conn.close()
        
        specs = {}
        for row in rows:
            specs[row[0]] = json.loads(row[1])
        return specs
    
    def _define_combination_templates(self) -> List[Dict]:
        """Define templates for generating combinations"""
        return [
            # Wealth combinations
            {
                "theme": "wealth",
                "keywords": ["wealth", "money", "income", "gains", "profits", "financial"],
                "houses": [2, 8, 11],
                "positive_template": "Financial gains through {method}. {benefit}.",
                "negative_template": "Financial challenges with {area}. {warning}."
            },
            # Career combinations
            {
                "theme": "career",
                "keywords": ["career", "profession", "work", "job", "business", "employment"],
                "houses": [6, 10, 11],
                "positive_template": "Career advancement in {method}. {benefit}.",
                "negative_template": "Professional challenges in {area}. {warning}."
            },
            # Relationship combinations
            {
                "theme": "relationships",
                "keywords": ["marriage", "spouse", "partnership", "relationships", "love"],
                "houses": [5, 7, 8],
                "positive_template": "Harmonious relationships through {method}. {benefit}.",
                "negative_template": "Relationship tensions regarding {area}. {warning}."
            },
            # Health combinations
            {
                "theme": "health",
                "keywords": ["health", "disease", "illness", "medical", "healing", "body"],
                "houses": [1, 6, 8],
                "positive_template": "Health improvements through {method}. {benefit}.",
                "negative_template": "Health concerns with {area}. {warning}."
            },
            # Education combinations
            {
                "theme": "education",
                "keywords": ["education", "learning", "knowledge", "study", "academic"],
                "houses": [4, 5, 9],
                "positive_template": "Educational success in {method}. {benefit}.",
                "negative_template": "Learning challenges with {area}. {warning}."
            },
            # Spiritual combinations
            {
                "theme": "spirituality",
                "keywords": ["spirituality", "dharma", "religion", "meditation", "divine"],
                "houses": [9, 12],
                "positive_template": "Spiritual growth through {method}. {benefit}.",
                "negative_template": "Spiritual obstacles in {area}. {warning}."
            }
        ]
    
    def _find_common_keywords(self, house1: int, house2: int, theme_keywords: List[str]) -> List[str]:
        """Find common keywords between two houses that match theme"""
        specs1 = set(self.house_specs.get(house1, []))
        specs2 = set(self.house_specs.get(house2, []))
        common = specs1.intersection(specs2)
        
        # Filter by theme keywords
        theme_related = []
        for keyword in common:
            if any(theme_word in keyword.lower() for theme_word in theme_keywords):
                theme_related.append(keyword)
        
        return theme_related
    
    def _generate_prediction_text(self, houses: List[int], template: Dict, is_positive: bool) -> str:
        """Generate prediction text based on house combination and template"""
        theme_keywords = template["keywords"]
        
        # Find relevant specifications
        relevant_specs = []
        for house in houses:
            house_specs = self.house_specs.get(house, [])
            for spec in house_specs:
                if any(keyword in spec.lower() for keyword in theme_keywords):
                    relevant_specs.append(spec)
        
        if not relevant_specs:
            return f"General {template['theme']} influence from houses {', '.join(map(str, houses))}"
        
        # Select most relevant specs
        primary_spec = relevant_specs[0] if relevant_specs else template["theme"]
        
        if is_positive:
            method = primary_spec
            benefit = f"Enhanced {template['theme']} prospects"
            return template["positive_template"].format(method=method, benefit=benefit)
        else:
            area = primary_spec
            warning = f"Exercise caution in {template['theme']} matters"
            return template["negative_template"].format(area=area, warning=warning)
    
    def generate_combinations_for_theme(self, theme: str, max_combinations: int = 20) -> List[Dict]:
        """Generate combinations for a specific theme"""
        template = next((t for t in self.combination_templates if t["theme"] == theme), None)
        if not template:
            return []
        
        combinations = []
        theme_houses = template["houses"]
        
        # Generate 2-house combinations
        for house1, house2 in itertools.combinations(theme_houses, 2):
            common_keywords = self._find_common_keywords(house1, house2, template["keywords"])
            if common_keywords:
                combo = {
                    "houses": [house1, house2],
                    "combination_name": f"{theme.title()} - Houses {house1} & {house2}",
                    "positive_prediction": self._generate_prediction_text([house1, house2], template, True),
                    "negative_prediction": self._generate_prediction_text([house1, house2], template, False),
                    "theme": theme,
                    "common_keywords": common_keywords[:3]  # Top 3 keywords
                }
                combinations.append(combo)
        
        # Generate 3-house combinations if theme has enough houses
        if len(theme_houses) >= 3:
            for house_combo in itertools.combinations(theme_houses, 3):
                combo = {
                    "houses": list(house_combo),
                    "combination_name": f"{theme.title()} - Houses {', '.join(map(str, house_combo))}",
                    "positive_prediction": self._generate_prediction_text(list(house_combo), template, True),
                    "negative_prediction": self._generate_prediction_text(list(house_combo), template, False),
                    "theme": theme
                }
                combinations.append(combo)
        
        return combinations[:max_combinations]
    
    def generate_massive_combinations(self) -> List[Dict]:
        """Generate multiple meaningful combinations per house pair using all specifications"""
        all_combinations = []
        
        # Generate multiple combinations per house pair
        for house1 in range(1, 13):
            for house2 in range(house1 + 1, 13):
                combos = self._create_combination_from_specs(house1, house2)
                all_combinations.extend(combos)
                print(f"Generated {len(combos)} combinations for houses {house1}-{house2}")
        
        return all_combinations
    
    def _create_combination_from_specs(self, *houses) -> List[Dict]:
        """Create multiple meaningful combinations per house pair using different specifications"""
        house_list = list(houses)
        combinations = []
        
        if len(house_list) < 2:
            return []
        
        # Get specifications for both houses
        house1_specs = self.house_specs.get(house_list[0], [])
        house2_specs = self.house_specs.get(house_list[1], [])
        
        if not house1_specs or not house2_specs:
            return []
        
        # Create combinations using different specification pairs
        # Limit to top 8 specs from each house to avoid explosion
        for i, spec1 in enumerate(house1_specs[:8]):
            for j, spec2 in enumerate(house2_specs[:8]):
                if spec1 != spec2:  # Avoid identical specs
                    combo = self._create_spec_pair_combination(house_list[0], house_list[1], spec1, spec2)
                    if combo:
                        combinations.append(combo)
                        
                        # Limit combinations per house pair to prevent database explosion
                        if len(combinations) >= 3:
                            break
            if len(combinations) >= 3:
                break
        
        return combinations
    
    def _create_spec_pair_combination(self, house1: int, house2: int, spec1: str, spec2: str) -> Dict:
        """Create a combination from a specific pair of specifications"""
        # Generate meaningful predictions based on specification types
        positive_pred = self._generate_positive_prediction(house1, house2, spec1, spec2)
        negative_pred = self._generate_negative_prediction(house1, house2, spec1, spec2)
        
        return {
            "houses": [house1, house2],
            "combination_name": f"Houses {house1}-{house2} - {spec1.title()} & {spec2.title()}",
            "positive_prediction": positive_pred,
            "negative_prediction": negative_pred
        }
    
    def _generate_positive_prediction(self, house1: int, house2: int, spec1: str, spec2: str) -> str:
        """Generate specific, actionable positive predictions"""
        # Create meaningful combinations based on actual house pairs
        specific_combos = {
            (2, 11): {
                ('wealth', 'gains'): "Significant wealth accumulation through multiple income streams. Expect salary increases and profitable investments.",
                ('savings', 'income'): "Strong financial growth period. Your savings will multiply through smart investments and additional income sources.",
                ('family', 'friends'): "Family connections lead to profitable opportunities. Friends become valuable business partners or provide lucrative referrals."
            },
            (1, 10): {
                ('personality', 'career'): "Your personal brand and reputation drive major career advancement. Leadership opportunities and public recognition await.",
                ('health', 'authority'): "Physical vitality enhances professional performance. Your energy and presence command respect and open doors.",
                ('appearance', 'reputation'): "Your image and charisma become powerful career assets. Expect promotions and high-profile opportunities."
            },
            (5, 9): {
                ('creativity', 'luck'): "Creative projects bring unexpected fortune. Your artistic talents or innovative ideas attract investors and opportunities.",
                ('children', 'spirituality'): "Children bring spiritual joy and good fortune. Family blessings multiply through younger generation's success.",
                ('education', 'wisdom'): "Higher learning opens doors to prosperity. Advanced degrees or certifications lead to lucrative career paths."
            },
            (7, 8): {
                ('marriage', 'transformation'): "Partnership undergoes positive transformation. Relationship deepens and becomes source of mutual growth and prosperity.",
                ('business', 'inheritance'): "Business partnerships yield transformative profits. Expect joint ventures to generate substantial wealth.",
                ('spouse', 'occult'): "Partner's hidden talents or resources emerge. Spouse becomes key to unlocking new income sources."
            },
            (4, 10): {
                ('property', 'career'): "Real estate investments boost professional status. Property dealings become lucrative career focus.",
                ('home', 'reputation'): "Home-based business or remote work enhances reputation. Domestic stability supports career growth.",
                ('mother', 'authority'): "Maternal support or women mentors accelerate career advancement. Female connections prove professionally valuable."
            },
            (6, 11): {
                ('service', 'gains'): "Service-oriented work brings substantial profits. Helping others becomes your path to wealth accumulation.",
                ('health', 'income'): "Health-related business or wellness focus generates multiple income streams. Fitness investments pay dividends.",
                ('enemies', 'friends'): "Former competitors become allies. Previous obstacles transform into profitable partnerships."
            }
        }
        
        # Check for specific meaningful combinations
        house_pair = (min(house1, house2), max(house1, house2))
        if house_pair in specific_combos:
            for (s1, s2), prediction in specific_combos[house_pair].items():
                if (s1 in spec1.lower() and s2 in spec2.lower()) or (s1 in spec2.lower() and s2 in spec1.lower()):
                    return prediction
        
        # Fallback to meaningful general predictions
        return self._create_meaningful_prediction(spec1, spec2, True)
    
    def _generate_negative_prediction(self, house1: int, house2: int, spec1: str, spec2: str) -> str:
        """Generate specific, actionable negative predictions"""
        # Create meaningful negative combinations
        negative_combos = {
            (2, 12): {
                ('wealth', 'expenses'): "Excessive spending threatens financial stability. Avoid luxury purchases and monitor cash flow carefully.",
                ('savings', 'losses'): "Investment losses possible. Diversify portfolio and avoid high-risk ventures during this period.",
                ('family', 'isolation'): "Family financial disputes may arise. Keep personal and family finances separate to avoid conflicts."
            },
            (6, 8): {
                ('health', 'transformation'): "Health issues require immediate attention. Avoid ignoring symptoms - early intervention prevents serious complications.",
                ('enemies', 'occult'): "Hidden enemies may cause significant problems. Be cautious of secretive dealings and protect confidential information.",
                ('disease', 'longevity'): "Chronic health conditions need careful management. Focus on preventive care and lifestyle modifications."
            },
            (7, 12): {
                ('marriage', 'losses'): "Relationship expenses strain finances. Wedding or partnership costs may exceed budget - plan carefully.",
                ('partnership', 'expenses'): "Business partnerships involve unexpected costs. Review all agreements and maintain separate accounts.",
                ('spouse', 'foreign'): "Partner's travel or relocation creates emotional distance. Communication becomes crucial for relationship stability."
            },
            (10, 12): {
                ('career', 'losses'): "Professional setbacks possible. Avoid major career moves and focus on consolidating current position.",
                ('reputation', 'isolation'): "Public image may suffer from withdrawal or mistakes. Maintain professional visibility and address issues promptly.",
                ('authority', 'expenses'): "Leadership role involves costly responsibilities. Budget carefully for professional obligations and appearances."
            }
        }
        
        # Check for specific negative combinations
        house_pair = (min(house1, house2), max(house1, house2))
        if house_pair in negative_combos:
            for (s1, s2), prediction in negative_combos[house_pair].items():
                if (s1 in spec1.lower() and s2 in spec2.lower()) or (s1 in spec2.lower() and s2 in spec1.lower()):
                    return prediction
        
        # Fallback to meaningful general predictions
        return self._create_meaningful_prediction(spec1, spec2, False)
    
    def _create_meaningful_prediction(self, spec1: str, spec2: str, is_positive: bool) -> str:
        """Create meaningful predictions for any specification pair"""
        if is_positive:
            return f"Favorable developments in {spec1} support growth in {spec2}. Strategic focus on both areas yields significant benefits."
        else:
            return f"Challenges in {spec1} may impact {spec2}. Careful planning and resource management needed to navigate this period successfully."
    
    def _find_matching_spec(self, specs: List[str], keywords: List[str]) -> str:
        """Find specification that matches any of the keywords"""
        for spec in specs:
            if any(keyword in spec.lower() for keyword in keywords):
                return spec
        return None
    
    def _generate_spec_based_prediction(self, houses: List[int], specs: List[str], is_positive: bool) -> str:
        """Generate prediction based on house specifications"""
        if not specs:
            return f"General influence from houses {', '.join(map(str, houses))}"
        
        primary_spec = specs[0]
        house_str = ', '.join(map(str, houses))
        
        # Categorize specifications
        wealth_terms = ['wealth', 'money', 'income', 'gains', 'profits', 'financial', 'savings', 'assets']
        career_terms = ['career', 'profession', 'work', 'job', 'business', 'employment', 'success']
        health_terms = ['health', 'disease', 'illness', 'medical', 'healing', 'body', 'physical']
        relationship_terms = ['marriage', 'spouse', 'partnership', 'relationships', 'love', 'family']
        education_terms = ['education', 'learning', 'knowledge', 'study', 'academic', 'wisdom']
        spiritual_terms = ['spirituality', 'dharma', 'religion', 'meditation', 'divine', 'moksha']
        
        category = "general"
        if any(term in primary_spec.lower() for term in wealth_terms):
            category = "wealth"
        elif any(term in primary_spec.lower() for term in career_terms):
            category = "career"
        elif any(term in primary_spec.lower() for term in health_terms):
            category = "health"
        elif any(term in primary_spec.lower() for term in relationship_terms):
            category = "relationship"
        elif any(term in primary_spec.lower() for term in education_terms):
            category = "education"
        elif any(term in primary_spec.lower() for term in spiritual_terms):
            category = "spiritual"
        
        if is_positive:
            templates = {
                "wealth": f"Favorable period for {primary_spec} through houses {house_str}. Financial growth and prosperity indicated.",
                "career": f"Professional advancement in {primary_spec} matters. Success through houses {house_str} influence.",
                "health": f"Positive developments in {primary_spec}. Healing and recovery through houses {house_str}.",
                "relationship": f"Harmonious {primary_spec} experiences. Beneficial relationships through houses {house_str}.",
                "education": f"Educational success in {primary_spec}. Knowledge expansion through houses {house_str}.",
                "spiritual": f"Spiritual growth through {primary_spec}. Divine blessings via houses {house_str}.",
                "general": f"Positive developments in {primary_spec}. Beneficial outcomes through houses {house_str}."
            }
        else:
            templates = {
                "wealth": f"Exercise caution with {primary_spec} matters. Potential financial challenges from houses {house_str}.",
                "career": f"Professional obstacles in {primary_spec} areas. Career challenges through houses {house_str}.",
                "health": f"Health concerns regarding {primary_spec}. Medical attention needed for houses {house_str} issues.",
                "relationship": f"Relationship tensions in {primary_spec} matters. Conflicts through houses {house_str} influence.",
                "education": f"Learning difficulties with {primary_spec}. Educational obstacles via houses {house_str}.",
                "spiritual": f"Spiritual challenges in {primary_spec} path. Purification needed through houses {house_str}.",
                "general": f"Challenges with {primary_spec} matters. Obstacles through houses {house_str} influence."
            }
        
        return templates.get(category, templates["general"])
    
    def generate_all_combinations(self, max_per_theme: int = 10) -> List[Dict]:
        """Generate combinations for all themes"""
        all_combinations = []
        
        for template in self.combination_templates:
            theme_combinations = self.generate_combinations_for_theme(template["theme"], max_per_theme)
            all_combinations.extend(theme_combinations)
        
        return all_combinations
    
    def generate_custom_combinations(self, house_pairs: List[Tuple[int, int]]) -> List[Dict]:
        """Generate combinations for custom house pairs"""
        combinations = []
        
        for house1, house2 in house_pairs:
            # Find best matching theme
            best_theme = None
            max_matches = 0
            
            for template in self.combination_templates:
                matches = len(self._find_common_keywords(house1, house2, template["keywords"]))
                if matches > max_matches:
                    max_matches = matches
                    best_theme = template
            
            if best_theme:
                combo = {
                    "houses": [house1, house2],
                    "combination_name": f"Custom - Houses {house1} & {house2}",
                    "positive_prediction": self._generate_prediction_text([house1, house2], best_theme, True),
                    "negative_prediction": self._generate_prediction_text([house1, house2], best_theme, False),
                    "theme": best_theme["theme"]
                }
                combinations.append(combo)
        
        return combinations
    
    def save_generated_combinations(self, combinations: List[Dict]) -> int:
        """Save generated combinations to database"""
        conn = sqlite3.connect('astrology.db')
        cursor = conn.cursor()
        
        saved_count = 0
        for combo in combinations:
            try:
                cursor.execute(
                    "INSERT INTO house_combinations (houses, positive_prediction, negative_prediction, combination_name, is_active) VALUES (?, ?, ?, ?, ?)",
                    (
                        json.dumps(combo["houses"]),
                        combo["positive_prediction"],
                        combo["negative_prediction"],
                        combo["combination_name"],
                        True
                    )
                )
                saved_count += 1
            except sqlite3.IntegrityError:
                # Skip duplicates
                continue
        
        conn.commit()
        conn.close()
        return saved_count

def generate_and_save_combinations(massive=False):
    """Main function to generate and save combinations"""
    generator = HouseCombinationGenerator()
    
    if massive:
        # Generate ALL possible combinations
        all_combinations = generator.generate_massive_combinations()
    else:
        # Generate combinations for all themes
        all_combinations = generator.generate_all_combinations(max_per_theme=8)
    
    # Save to database
    saved_count = generator.save_generated_combinations(all_combinations)
    
    print(f"Generated {len(all_combinations)} combinations")
    print(f"Saved {saved_count} new combinations to database")
    
    return all_combinations

def generate_massive_combinations():
    """Generate massive amount of combinations"""
    return generate_and_save_combinations(massive=True)

if __name__ == "__main__":
    combinations = generate_and_save_combinations()
    for combo in combinations[:5]:  # Show first 5 examples
        print(f"\n{combo['combination_name']}:")
        print(f"Houses: {combo['houses']}")
        print(f"Positive: {combo['positive_prediction']}")
        print(f"Negative: {combo['negative_prediction']}")