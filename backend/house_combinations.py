"""
House Combinations Management System
Database tables and API endpoints for managing house specifications and combinations
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sqlite3
import json

router = APIRouter()


class HouseSpecification(BaseModel):
    house_number: int
    specifications: List[str]

class HouseCombination(BaseModel):
    houses: List[int]
    positive_prediction: str
    negative_prediction: str
    combination_name: str
    is_active: bool = True

class GenerateRequest(BaseModel):
    theme: Optional[str] = None
    max_per_theme: int = 10
    massive: bool = False

def init_house_combinations_db():
    """Initialize house combinations database tables"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    # House specifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS house_specifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            house_number INTEGER UNIQUE NOT NULL,
            specifications TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # House combinations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS house_combinations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            houses TEXT NOT NULL,
            positive_prediction TEXT NOT NULL,
            negative_prediction TEXT NOT NULL,
            combination_name TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert comprehensive house specifications
    default_specs = {
        1: ["personality", "health", "appearance", "self", "vitality", "head", "brain", "identity", "physical body", "constitution", "temperament", "general well-being", "life force", "ego", "individuality", "first impressions", "leadership", "initiative", "independence", "self-confidence", "personal magnetism", "physical strength", "longevity", "birth circumstances", "early life"],
        
        2: ["wealth", "family", "speech", "food", "savings", "face", "early childhood", "accumulated wealth", "liquid assets", "bank balance", "movable property", "precious metals", "jewelry", "family traditions", "family values", "immediate family", "spouse's family", "voice quality", "speaking ability", "oral communication", "eating habits", "taste preferences", "nutrition", "mouth", "teeth", "tongue", "throat", "neck", "right eye", "death circumstances", "family lineage", "ancestral wealth", "financial security", "material possessions", "self-worth through possessions"],
        
        3: ["communication", "siblings", "short travels", "courage", "hands", "writing", "younger siblings", "neighbors", "local community", "short journeys", "day trips", "commuting", "correspondence", "letters", "emails", "phone calls", "media", "journalism", "publishing", "books", "magazines", "newspapers", "broadcasting", "advertising", "marketing", "sales", "negotiations", "contracts", "agreements", "manual skills", "craftsmanship", "hobbies", "interests", "mental courage", "initiative", "enterprise", "efforts", "attempts", "shoulders", "arms", "hands", "fingers", "lungs", "nervous system", "hearing", "ears", "performing arts", "music", "dance", "drama"],
        
        4: ["home", "mother", "property", "vehicles", "happiness", "education", "chest", "domestic life", "family home", "real estate", "land", "buildings", "immovable property", "homeland", "native place", "roots", "foundations", "maternal relatives", "maternal grandfather", "nurturing", "emotional security", "comfort", "peace of mind", "contentment", "inner happiness", "emotional well-being", "basic education", "schooling", "learning environment", "academic foundation", "cars", "boats", "conveyances", "transportation", "heart", "chest", "lungs", "breasts", "emotional heart", "feelings", "sentiments", "patriotism", "loyalty", "tradition", "culture", "heritage", "end of life", "final resting place", "graves", "burial grounds"],
        
        5: ["creativity", "children", "education", "romance", "speculation", "intelligence", "offspring", "pregnancy", "childbirth", "parenting", "creative expression", "artistic abilities", "entertainment", "recreation", "games", "sports", "gambling", "lottery", "stock market", "investments", "speculation", "risk-taking", "higher education", "college", "university", "academic achievements", "learning", "knowledge", "wisdom", "intelligence", "mental abilities", "memory", "concentration", "love affairs", "romantic relationships", "dating", "courtship", "pleasure", "enjoyment", "fun", "hobbies", "interests", "past life karma", "spiritual practices", "mantras", "meditation", "devotion", "bhakti", "stomach", "digestive system", "liver", "gall bladder", "spine", "back"],
        
        6: ["health issues", "service", "enemies", "debts", "litigation", "daily work", "diseases", "illness", "medical problems", "chronic conditions", "infections", "injuries", "accidents", "surgery", "hospitals", "doctors", "medicine", "healing", "recovery", "employment", "job", "workplace", "colleagues", "subordinates", "servants", "employees", "daily routine", "work schedule", "office environment", "open enemies", "opponents", "competitors", "rivals", "conflicts", "disputes", "arguments", "fights", "wars", "battles", "loans", "borrowing", "financial obligations", "mortgages", "credit", "legal cases", "court proceedings", "lawyers", "judges", "police", "crime", "theft", "robbery", "maternal uncles", "step-mother", "obstacles", "difficulties", "challenges", "struggles", "hard work", "effort", "service to others", "social service", "charity", "helping others", "waist", "intestines", "kidneys", "appendix"],
        
        7: ["marriage", "partnerships", "business", "spouse", "public relations", "life partner", "marital life", "wedding", "married life", "husband", "wife", "business partnerships", "joint ventures", "collaborations", "alliances", "contracts", "agreements", "negotiations", "deals", "public image", "reputation", "fame", "popularity", "public dealings", "customers", "clients", "audience", "masses", "general public", "foreign countries", "foreign travel", "foreign residence", "immigration", "export-import", "international business", "diplomacy", "ambassadors", "foreign relations", "trade", "commerce", "buying and selling", "markets", "shops", "retail business", "sexual relationships", "physical intimacy", "passion", "desire", "lower abdomen", "reproductive organs", "kidneys", "bladder", "death", "longevity", "life span"],
        
        8: ["transformation", "occult", "longevity", "unearned income", "inheritance", "research", "obstacles", "sudden events", "unexpected changes", "upheavals", "crises", "emergencies", "accidents", "shocks", "surprises", "mysteries", "secrets", "hidden things", "underground", "buried treasures", "archaeology", "investigation", "detective work", "research work", "deep study", "analysis", "psychology", "psychiatry", "psychoanalysis", "occult sciences", "astrology", "numerology", "palmistry", "tarot", "spiritualism", "mediumship", "ghosts", "spirits", "supernatural", "paranormal", "magic", "tantra", "black magic", "witchcraft", "death", "mortality", "funeral rites", "cremation", "burial", "life after death", "rebirth", "reincarnation", "insurance money", "lottery winnings", "gambling gains", "spouse's money", "partner's wealth", "dowry", "alimony", "wills", "legacies", "chronic diseases", "incurable ailments", "mental illness", "depression", "anxiety", "phobias", "sexual organs", "excretory system", "anus", "rectum", "prostate", "menstruation", "surgery", "operations"],
        
        9: ["luck", "spirituality", "higher learning", "father", "dharma", "long travels", "fortune", "destiny", "fate", "providence", "divine grace", "blessings", "good karma", "merit", "virtue", "righteousness", "moral values", "ethics", "principles", "beliefs", "philosophy", "religion", "faith", "devotion", "worship", "prayers", "rituals", "ceremonies", "pilgrimages", "holy places", "temples", "churches", "mosques", "spiritual teachers", "gurus", "mentors", "guides", "wisdom", "knowledge", "learning", "education", "universities", "higher studies", "research", "publishing", "writing", "books", "literature", "law", "legal profession", "judges", "courts", "justice", "paternal relatives", "paternal grandfather", "father-in-law", "long distance travel", "foreign countries", "immigration", "settlement abroad", "dreams", "visions", "intuition", "prophecy", "divination", "hips", "thighs", "liver", "arterial system"],
        
        10: ["career", "reputation", "authority", "government", "status", "profession", "occupation", "job", "business", "work", "employment", "livelihood", "income source", "success", "achievements", "accomplishments", "recognition", "fame", "honor", "prestige", "social status", "rank", "position", "title", "designation", "promotion", "advancement", "progress", "ambition", "goals", "objectives", "targets", "public image", "public recognition", "media attention", "publicity", "awards", "prizes", "trophies", "medals", "certificates", "degrees", "qualifications", "skills", "expertise", "specialization", "mastery", "leadership", "management", "administration", "supervision", "control", "power", "influence", "authority figures", "bosses", "superiors", "government officials", "politicians", "ministers", "officers", "bureaucrats", "civil servants", "public service", "social service", "community work", "mother's father", "maternal grandfather", "knees", "bones", "joints", "skeletal system", "skin"],
        
        11: ["gains", "friends", "aspirations", "elder siblings", "income", "social network", "profits", "earnings", "financial gains", "monetary benefits", "winnings", "prizes", "rewards", "bonuses", "commissions", "dividends", "interest", "returns on investment", "business profits", "trade gains", "salary increases", "promotions", "raises", "friendship", "social circle", "companions", "associates", "colleagues", "allies", "supporters", "well-wishers", "benefactors", "patrons", "sponsors", "social groups", "clubs", "societies", "organizations", "communities", "networks", "connections", "contacts", "relationships", "hopes", "wishes", "desires", "dreams", "ambitions", "goals", "objectives", "expectations", "fulfillment of desires", "realization of dreams", "achievement of goals", "success in endeavors", "older brothers", "older sisters", "paternal uncles", "father's siblings", "step-children", "adopted children", "left ear", "calves", "shins", "ankles", "circulatory system", "blood circulation"],
        
        12: ["losses", "spirituality", "foreign lands", "expenses", "isolation", "moksha", "expenditure", "spending", "outflow of money", "financial losses", "wastage", "charity", "donations", "giving", "philanthropy", "generosity", "sacrifice", "renunciation", "letting go", "release", "liberation", "freedom", "detachment", "solitude", "seclusion", "retreat", "meditation", "contemplation", "introspection", "self-reflection", "inner journey", "spiritual practices", "yoga", "pranayama", "dhyana", "samadhi", "enlightenment", "self-realization", "God-realization", "union with divine", "transcendence", "nirvana", "foreign countries", "distant lands", "overseas", "abroad", "immigration", "emigration", "exile", "banishment", "deportation", "foreign settlement", "life abroad", "hospitals", "asylums", "prisons", "jails", "confinement", "imprisonment", "detention", "quarantine", "rehabilitation centers", "monasteries", "ashrams", "hermitages", "secluded places", "hidden enemies", "secret opponents", "backstabbers", "betrayers", "conspiracies", "plots", "schemes", "scandals", "secrets", "confidential matters", "private affairs", "behind-the-scenes activities", "subconscious mind", "unconscious", "dreams", "sleep", "bed", "bedroom", "sexual pleasures", "physical intimacy", "left eye", "feet", "toes", "lymphatic system", "immune system", "final liberation"]
    }
    
    for house_num, specs in default_specs.items():
        cursor.execute(
            "INSERT OR REPLACE INTO house_specifications (house_number, specifications) VALUES (?, ?)",
            (house_num, json.dumps(specs))
        )
    
    # Insert some default combinations
    default_combinations = [
        {
            "houses": [2, 8],
            "positive_prediction": "Expect unearned income through investments, insurance, or inheritance. Financial gains from hidden sources.",
            "negative_prediction": "Financial losses through hidden factors, tax issues, or unexpected expenses. Avoid risky investments.",
            "combination_name": "Wealth + Transformation"
        },
        {
            "houses": [2, 9],
            "positive_prediction": "Financial support from paternal sources or through spiritual/educational pursuits. Lucky money gains.",
            "negative_prediction": "Financial strain due to paternal issues or religious/educational expenses.",
            "combination_name": "Wealth + Fortune"
        },
        {
            "houses": [5, 9],
            "positive_prediction": "Success in creative projects, education, or children-related matters. Spiritual growth through learning.",
            "negative_prediction": "Challenges with children's education or creative blocks. Conflicts between beliefs and creativity.",
            "combination_name": "Creativity + Fortune"
        },
        {
            "houses": [7, 10],
            "positive_prediction": "Career advancement through partnerships or marriage. Business success with spouse or partners.",
            "negative_prediction": "Career conflicts due to partnership issues. Professional reputation affected by relationship problems.",
            "combination_name": "Partnership + Career"
        }
    ]
    
    for combo in default_combinations:
        cursor.execute(
            "INSERT OR IGNORE INTO house_combinations (houses, positive_prediction, negative_prediction, combination_name) VALUES (?, ?, ?, ?)",
            (json.dumps(combo["houses"]), combo["positive_prediction"], combo["negative_prediction"], combo["combination_name"])
        )
    
    conn.commit()
    conn.close()


# Initialize database on module load (after function is defined)
try:
    init_house_combinations_db()
except Exception as e:
    print(f"Warning: Could not initialize house combinations database: {e}")


@router.get("/house-specifications")
async def get_house_specifications():
    """Get all house specifications"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM house_specifications ORDER BY house_number")
    rows = cursor.fetchall()
    conn.close()
    
    specs = []
    for row in rows:
        specs.append({
            "id": row[0],
            "house_number": row[1],
            "specifications": json.loads(row[2]),
            "created_at": row[3],
            "updated_at": row[4]
        })
    
    return {"specifications": specs}

@router.put("/house-specifications/{house_number}")
async def update_house_specification(
    house_number: int, 
    spec: HouseSpecification
):
    """Update house specifications"""
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE house_specifications SET specifications = ?, updated_at = CURRENT_TIMESTAMP WHERE house_number = ?",
        (json.dumps(spec.specifications), house_number)
    )
    
    if cursor.rowcount == 0:
        cursor.execute(
            "INSERT INTO house_specifications (house_number, specifications) VALUES (?, ?)",
            (house_number, json.dumps(spec.specifications))
        )
    
    conn.commit()
    conn.close()
    
    return {"message": "House specification updated successfully"}

@router.get("/house-combinations")
async def get_house_combinations():
    """Get all house combinations"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM house_combinations ORDER BY id")
    rows = cursor.fetchall()
    conn.close()
    
    combinations = []
    for row in rows:
        combinations.append({
            "id": row[0],
            "houses": json.loads(row[1]),
            "positive_prediction": row[2],
            "negative_prediction": row[3],
            "combination_name": row[4],
            "is_active": bool(row[5]),
            "created_at": row[6],
            "updated_at": row[7]
        })
    
    return {"combinations": combinations}

@router.post("/house-combinations")
async def create_house_combination(
    combination: HouseCombination
):
    """Create new house combination"""
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO house_combinations (houses, positive_prediction, negative_prediction, combination_name, is_active) VALUES (?, ?, ?, ?, ?)",
        (json.dumps(combination.houses), combination.positive_prediction, combination.negative_prediction, combination.combination_name, combination.is_active)
    )
    conn.commit()
    conn.close()
    
    return {"message": "House combination created successfully"}

@router.put("/house-combinations/{combination_id}")
async def update_house_combination(
    combination_id: int, 
    combination: HouseCombination
):
    """Update house combination"""
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE house_combinations SET houses = ?, positive_prediction = ?, negative_prediction = ?, combination_name = ?, is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (json.dumps(combination.houses), combination.positive_prediction, combination.negative_prediction, combination.combination_name, combination.is_active, combination_id)
    )
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Combination not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "House combination updated successfully"}

@router.delete("/house-combinations/{combination_id}")
async def delete_house_combination(
    combination_id: int
):
    """Delete house combination"""
    
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM house_combinations WHERE id = ?", (combination_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Combination not found")
    
    conn.commit()
    conn.close()
    
    return {"message": "House combination deleted successfully"}

@router.get("/search-combinations")
async def search_house_combinations(
    houses: Optional[str] = None,
    search_text: Optional[str] = None,
    house_logic: str = "AND",
    limit: int = 100
):
    """Search house combinations by houses and text"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    
    query = "SELECT * FROM house_combinations WHERE is_active = TRUE"
    params = []
    
    if houses:
        # Parse houses (e.g., "2,8" or "1,5,9")
        house_list = [int(h.strip()) for h in houses.split(',') if h.strip().isdigit()]
        if house_list:
            # Filter results in Python for exact house matching
            query += " AND id > 0"  # Placeholder to get all results first
    
    if search_text:
        query += " AND (combination_name LIKE ? OR positive_prediction LIKE ? OR negative_prediction LIKE ?)"
        search_pattern = f'%{search_text}%'
        params.extend([search_pattern, search_pattern, search_pattern])
    
    query += " ORDER BY id DESC LIMIT ?"
    params.append(limit)
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    combinations = []
    for row in rows:
        combo_houses = json.loads(row[1])
        
        # Apply house filtering if specified
        if houses:
            house_list = [int(h.strip()) for h in houses.split(',') if h.strip().isdigit()]
            if house_list:
                if house_logic.upper() == "AND":
                    # All specified houses must be present
                    if not all(house in combo_houses for house in house_list):
                        continue
                else:  # OR logic
                    # At least one specified house must be present
                    if not any(house in combo_houses for house in house_list):
                        continue
        
        combinations.append({
            "id": row[0],
            "houses": combo_houses,
            "positive_prediction": row[2],
            "negative_prediction": row[3],
            "combination_name": row[4],
            "is_active": bool(row[5]),
            "created_at": row[6],
            "updated_at": row[7]
        })
    
    return {"combinations": combinations, "total": len(combinations)}

def get_active_house_combinations() -> List[Dict]:
    """Get active house combinations for prediction engine"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute("SELECT houses, positive_prediction, negative_prediction, combination_name FROM house_combinations WHERE is_active = TRUE")
    rows = cursor.fetchall()
    conn.close()
    
    combinations = []
    for row in rows:
        combinations.append({
            "houses": json.loads(row[0]),
            "positive_prediction": row[1],
            "negative_prediction": row[2],
            "combination_name": row[3]
        })
    
    return combinations

def get_house_specifications_dict() -> Dict[int, List[str]]:
    """Get house specifications as dictionary for prediction engine"""
    conn = sqlite3.connect('astrology.db')
    cursor = conn.cursor()
    cursor.execute("SELECT house_number, specifications FROM house_specifications")
    rows = cursor.fetchall()
    conn.close()
    
    specs = {}
    for row in rows:
        specs[row[0]] = json.loads(row[1])
    
    return specs

@router.post("/generate-combinations")
async def generate_house_combinations(request: GenerateRequest):
    """Generate house combinations using house specifications"""
    try:
        from house_combo_generator import HouseCombinationGenerator
        
        generator = HouseCombinationGenerator()
        
        if request.massive:
            combinations = generator.generate_massive_combinations()
        elif request.theme:
            combinations = generator.generate_combinations_for_theme(request.theme, request.max_per_theme)
        else:
            combinations = generator.generate_all_combinations(request.max_per_theme)
        
        saved_count = generator.save_generated_combinations(combinations)
        
        return {
            "message": f"Generated {len(combinations)} combinations, saved {saved_count} new ones",
            "generated_count": len(combinations),
            "saved_count": saved_count,
            "combinations": combinations[:5]  # Show first 5 as preview
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")