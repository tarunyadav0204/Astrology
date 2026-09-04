"""Typed authoring grammar for the Sutra rule API and admin editor."""
STREAMS=["parashari","jaimini","kp","nadi"]
CHARTS=["D1","D2","D3","D4","D7","D9","D10","D12","D20","D24","D30","D60","bhava_chalit"]
PLANETS=["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"]
HOUSES=list(range(1,13))
SIGNS=["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
KARAKAS=["Atmakaraka","Amatyakaraka","Bhratrikaraka","Matrikaraka","Putrakaraka","Gnatikaraka","Darakaraka"]
ARUDHAS=["Arudha Lagna","Upapada","Dhana Pada","Darapada"]
HOUSE_REFERENCES=["Lagna","Moon","Sun","Arudha Lagna","Upapada","Karakamsa"]
SUBJECT_TYPES={
"planet":{"label":"Planet","streams":["parashari","jaimini","nadi"],"fields":["planet"],"predicates":{"in_sign":"is in sign","in_house":"is in house","in_nakshatra":"is in nakshatra","in_pada":"is in pada","has_condition":"has condition","aspects_planet":"aspects planet"}},
"house_lord":{"label":"House lord","streams":["parashari","nadi"],"fields":["house_reference","house"],"predicates":{"in_sign":"is in sign","in_house":"is in house","in_nakshatra":"is in nakshatra","has_condition":"has condition"}},
"house_occupant":{"label":"House occupant","streams":["parashari","nadi"],"fields":["house_reference","house"],"predicates":{"contains_planet":"contains planet","receives_aspect_from":"receives aspect from"}},
"jaimini_karaka":{"label":"Jaimini karaka","streams":["jaimini"],"fields":["karaka"],"predicates":{"in_sign":"is in sign","in_house":"is in house","in_movable_sign":"is in movable sign","rashi_aspects":"gives rashi aspect to"}},
"arudha_point":{"label":"Arudha / Upapada","streams":["jaimini"],"fields":["arudha","relative_house"],"predicates":{"contains_planet":"contains planet","receives_rashi_aspect_from":"receives rashi aspect from","lord_in_house":"its lord is in house"}},
"kp_cusp":{"label":"KP cusp","streams":["kp"],"fields":["cusp"],"predicates":{"sublord_is":"sub-lord is","sublord_signifies_houses":"sub-lord signifies houses","starlord_is":"star-lord is"}},
"nadi_linkage":{"label":"Nadi linkage","streams":["nadi"],"fields":["planet"],"predicates":{"links_to_planet":"links to planet","activates_phala_house":"activates phala house"}},
"dasha_chain":{"label":"Dasha chain","streams":["parashari","jaimini","nadi"],"fields":["dasha_level"],"predicates":{"lord_is":"lord is","lord_connects_to_house":"lord connects to house"}},
"transit":{"label":"Transit","streams":["parashari","jaimini","kp","nadi"],"fields":["planet"],"predicates":{"transits_sign":"transits sign","activates_house":"activates house","contacts_natal_planet":"contacts natal planet"}},
}
CATEGORIES={"self":["identity","temperament","appearance_presentation","body_vitality","mind","emotions","habits","strengths","shadow_patterns"],"relationships":["partnership_style","spouse_indications","marriage_endurance","love_pattern","family","parents","siblings","friendships"],"career":["work_style","vocation","leadership","public_role","business","recognition","obstacles"],"wealth":["earning_style","accumulation","retention","investments","debt","assets","financial_risk"],"education":["learning_style","subject_aptitude","higher_education","exams","research"],"children":["progeny_promise","parenting_pattern","child_temperament","family_expansion"],"health":["constitution","vulnerability_patterns","recovery","wellbeing_habits"],"home_place":["home_life","property","relocation","foreign_connection"],"spirituality":["dharma","faith","practice","karmic_pattern","inner_growth"],"timing":["dasha_activation","transit_activation","kp_fructification","event_windows"]}
def catalog(): return {"streams":STREAMS,"charts":CHARTS,"planets":PLANETS,"houses":HOUSES,"signs":SIGNS,"karakas":KARAKAS,"arudhas":ARUDHAS,"house_references":HOUSE_REFERENCES,"subject_types":SUBJECT_TYPES,"categories":CATEGORIES,"conditions":["exalted","debilitated","own_sign","combust","retrograde","vargottama","gandanta","strong","weak"],"operators":["equals","not_equals","contains","contains_any","gte","lte","exists","not_exists"]}
