from typing import Dict, Any, List

class GeodeticCalculator:
    """Maps Zodiacal degrees to terrestrial locations using Koorma Chakra"""
    
    def __init__(self):
        # Koorma Chakra: Map 27 Nakshatras to geographic directions
        self.nakshatra_directions = {
            'Ashwini': 'East', 'Bharani': 'Southeast', 'Krittika': 'South',
            'Rohini': 'Central', 'Mrigashira': 'Southwest', 'Ardra': 'West',
            'Punarvasu': 'Northwest', 'Pushya': 'North', 'Ashlesha': 'Northeast',
            'Magha': 'East', 'Purva Phalguni': 'Southeast', 'Uttara Phalguni': 'South',
            'Hasta': 'Central', 'Chitra': 'Southwest', 'Swati': 'West',
            'Vishakha': 'Northwest', 'Anuradha': 'North', 'Jyeshtha': 'Northeast',
            'Mula': 'East', 'Purva Ashadha': 'Southeast', 'Uttara Ashadha': 'South',
            'Shravana': 'Central', 'Dhanishta': 'Southwest', 'Shatabhisha': 'West',
            'Purva Bhadrapada': 'Northwest', 'Uttara Bhadrapada': 'North', 'Revati': 'Northeast'
        }
        
        # Regional mapping for major countries (keys must match app COUNTRIES name)
        self.regional_mapping = {
            'India': {
                'North': ['Punjab', 'Haryana', 'Himachal Pradesh', 'Uttarakhand', 'Jammu & Kashmir'],
                'South': ['Tamil Nadu', 'Kerala', 'Karnataka', 'Andhra Pradesh', 'Telangana'],
                'East': ['West Bengal', 'Odisha', 'Bihar', 'Jharkhand', 'Assam'],
                'West': ['Gujarat', 'Maharashtra', 'Rajasthan', 'Goa'],
                'Central': ['Madhya Pradesh', 'Chhattisgarh', 'Uttar Pradesh', 'Delhi'],
                'Northeast': ['Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Tripura'],
                'Northwest': ['Punjab', 'Rajasthan', 'Haryana'],
                'Southeast': ['Andhra Pradesh', 'Tamil Nadu', 'Puducherry'],
                'Southwest': ['Kerala', 'Karnataka', 'Goa']
            },
            'USA': {
                'North': ['Montana', 'North Dakota', 'Minnesota', 'Wisconsin', 'Michigan'],
                'South': ['Texas', 'Louisiana', 'Mississippi', 'Alabama', 'Florida'],
                'East': ['New York', 'Pennsylvania', 'Virginia', 'North Carolina', 'South Carolina'],
                'West': ['California', 'Oregon', 'Washington', 'Nevada', 'Arizona'],
                'Central': ['Kansas', 'Nebraska', 'Oklahoma', 'Missouri', 'Iowa'],
                'Northeast': ['Maine', 'Vermont', 'New Hampshire', 'Massachusetts', 'Connecticut'],
                'Northwest': ['Washington', 'Oregon', 'Idaho', 'Montana'],
                'Southeast': ['Georgia', 'Florida', 'South Carolina', 'Alabama'],
                'Southwest': ['Arizona', 'New Mexico', 'Nevada', 'Southern California']
            },
            'UK': {
                'North': ['Scotland', 'Northumberland', 'Cumbria', 'Durham'],
                'South': ['Cornwall', 'Devon', 'Dorset', 'Hampshire', 'Sussex', 'Kent'],
                'East': ['Norfolk', 'Suffolk', 'Essex', 'Lincolnshire', 'Cambridgeshire'],
                'West': ['Wales', 'Cornwall', 'Somerset', 'Gloucestershire', 'Herefordshire'],
                'Central': ['Midlands', 'West Midlands', 'East Midlands', 'Northamptonshire'],
                'Northeast': ['North East England', 'Yorkshire', 'Durham'],
                'Northwest': ['North West England', 'Lancashire', 'Cumbria', 'Merseyside'],
                'Southeast': ['South East England', 'Kent', 'Surrey', 'Sussex'],
                'Southwest': ['South West England', 'Devon', 'Cornwall', 'Somerset']
            },
            'China': {
                'North': ['Heilongjiang', 'Jilin', 'Liaoning', 'Inner Mongolia', 'Beijing'],
                'South': ['Guangdong', 'Guangxi', 'Hainan', 'Yunnan', 'Fujian'],
                'East': ['Jiangsu', 'Zhejiang', 'Shanghai', 'Shandong', 'Anhui'],
                'West': ['Xinjiang', 'Tibet', 'Qinghai', 'Gansu', 'Sichuan'],
                'Central': ['Henan', 'Hubei', 'Hunan', 'Shaanxi', 'Shanxi'],
                'Northeast': ['Heilongjiang', 'Jilin', 'Liaoning'],
                'Northwest': ['Xinjiang', 'Gansu', 'Ningxia', 'Shaanxi'],
                'Southeast': ['Guangdong', 'Fujian', 'Zhejiang', 'Jiangxi'],
                'Southwest': ['Yunnan', 'Guizhou', 'Sichuan', 'Chongqing', 'Tibet']
            },
            'Japan': {
                'North': ['Hokkaido', 'Aomori', 'Iwate', 'Akita'],
                'South': ['Kyushu', 'Okinawa', 'Kagoshima', 'Miyazaki'],
                'East': ['Kanto', 'Tokyo', 'Chiba', 'Ibaraki', 'Kanagawa'],
                'West': ['Chugoku', 'Hiroshima', 'Yamaguchi', 'Shimane', 'Tottori'],
                'Central': ['Kansai', 'Osaka', 'Kyoto', 'Nara', 'Shiga', 'Mie'],
                'Northeast': ['Tohoku', 'Miyagi', 'Fukushima', 'Yamagata'],
                'Northwest': ['Hokuriku', 'Niigata', 'Toyama', 'Ishikawa', 'Fukui'],
                'Southeast': ['Shikoku', 'Tokushima', 'Kochi', 'Ehime'],
                'Southwest': ['Kyushu', 'Fukuoka', 'Kumamoto', 'Nagasaki', 'Saga']
            },
            'Germany': {
                'North': ['Schleswig-Holstein', 'Hamburg', 'Bremen', 'Lower Saxony', 'Mecklenburg-Vorpommern'],
                'South': ['Bavaria', 'Baden-Württemberg', 'Bavarian Swabia'],
                'East': ['Berlin', 'Brandenburg', 'Saxony', 'Saxony-Anhalt', 'Thuringia'],
                'West': ['North Rhine-Westphalia', 'Rhineland-Palatinate', 'Saarland'],
                'Central': ['Hesse', 'Thuringia', 'Saxony-Anhalt'],
                'Northeast': ['Mecklenburg-Vorpommern', 'Brandenburg', 'Berlin'],
                'Northwest': ['Schleswig-Holstein', 'Hamburg', 'Bremen', 'Lower Saxony'],
                'Southeast': ['Bavaria', 'Upper Palatinate', 'Lower Bavaria'],
                'Southwest': ['Baden-Württemberg', 'Rhineland-Palatinate', 'Saarland']
            },
            'France': {
                'North': ['Hauts-de-France', 'Normandy', 'Île-de-France (north)'],
                'South': ['Provence-Alpes-Côte d\'Azur', 'Occitanie', 'Corsica'],
                'East': ['Grand Est', 'Bourgogne-Franche-Comté', 'Auvergne-Rhône-Alpes (east)'],
                'West': ['Brittany', 'Pays de la Loire', 'Nouvelle-Aquitaine (west)'],
                'Central': ['Centre-Val de Loire', 'Bourgogne', 'Auvergne'],
                'Northeast': ['Grand Est', 'Champagne-Ardenne', 'Alsace', 'Lorraine'],
                'Northwest': ['Brittany', 'Normandy', 'Hauts-de-France'],
                'Southeast': ['Provence-Alpes-Côte d\'Azur', 'Rhône-Alpes', 'Corsica'],
                'Southwest': ['Nouvelle-Aquitaine', 'Occitanie', 'Midi-Pyrénées']
            },
            'Brazil': {
                'North': ['Amazonas', 'Pará', 'Roraima', 'Amapá', 'Acre', 'Rondônia'],
                'South': ['Rio Grande do Sul', 'Santa Catarina', 'Paraná'],
                'East': ['Bahia', 'Pernambuco', 'Alagoas', 'Sergipe', 'Rio Grande do Norte', 'Paraíba', 'Ceará', 'Piauí'],
                'West': ['Mato Grosso', 'Mato Grosso do Sul', 'Rondônia'],
                'Central': ['Distrito Federal', 'Goiás', 'Tocantins', 'Minas Gerais'],
                'Northeast': ['Maranhão', 'Piauí', 'Ceará', 'Rio Grande do Norte', 'Paraíba', 'Pernambuco', 'Alagoas', 'Sergipe', 'Bahia'],
                'Northwest': ['Amazonas', 'Roraima', 'Rondônia'],
                'Southeast': ['São Paulo', 'Rio de Janeiro', 'Minas Gerais', 'Espírito Santo'],
                'Southwest': ['Mato Grosso do Sul', 'Paraná', 'Santa Catarina']
            },
            'Russia': {
                'North': ['Murmansk', 'Arkhangelsk', 'Karelia', 'Komi', 'Yamalo-Nenets'],
                'South': ['Krasnodar', 'Rostov', 'Stavropol', 'North Caucasus', 'Crimea'],
                'East': ['Far East', 'Sakha', 'Kamchatka', 'Primorsky', 'Khabarovsk'],
                'West': ['Kaliningrad', 'Leningrad', 'Pskov', 'Novgorod'],
                'Central': ['Moscow', 'Moscow Oblast', 'Tula', 'Ryazan', 'Vladimir', 'Ivanovo'],
                'Northeast': ['Siberia', 'Sakha', 'Magadan', 'Chukotka'],
                'Northwest': ['Northwestern Federal District', 'Karelia', 'Leningrad Oblast'],
                'Southeast': ['Southern Siberia', 'Altai', 'Tuva', 'Buryatia'],
                'Southwest': ['Volga', 'Rostov', 'Volgograd', 'Krasnodar']
            },
            'Australia': {
                'North': ['Northern Territory', 'North Queensland', 'Kimberley', 'Darwin'],
                'South': ['Tasmania', 'Victoria', 'South Australia', 'Melbourne', 'Adelaide'],
                'East': ['Queensland', 'New South Wales', 'Sydney', 'Brisbane', 'Gold Coast'],
                'West': ['Western Australia', 'Perth', 'Pilbara', 'Kimberley'],
                'Central': ['South Australia (inland)', 'Northern Territory (centre)', 'Alice Springs'],
                'Northeast': ['North Queensland', 'Cairns', 'Townsville', 'Far North Queensland'],
                'Northwest': ['Western Australia (north)', 'Pilbara', 'Kimberley'],
                'Southeast': ['Victoria', 'Canberra', 'ACT', 'Southern NSW'],
                'Southwest': ['Western Australia (south)', 'Perth region', 'Margaret River']
            },
            'New Zealand': {
                'North': ['Northland', 'Auckland', 'Waikato (north)', 'Bay of Plenty'],
                'South': ['Southland', 'Otago', 'Fiordland', 'Invercargill', 'Dunedin'],
                'East': ['East Coast', 'Gisborne', 'Hawke\'s Bay', 'Canterbury (east)', 'Wellington (east)'],
                'West': ['Taranaki', 'Manawatu-Whanganui (west)', 'West Coast', 'Tasman'],
                'Central': ['Waikato', 'Bay of Plenty (inland)', 'Central North Island', 'Canterbury'],
                'Northeast': ['Northland', 'Auckland', 'Coromandel', 'Bay of Plenty'],
                'Northwest': ['Northland (west)', 'Auckland (west)', 'Waikato (west)'],
                'Southeast': ['Wellington', 'Wairarapa', 'Canterbury', 'Otago (east)'],
                'Southwest': ['West Coast', 'Fiordland', 'Southland (west)', 'Otago (west)']
            },
            'Canada': {
                'North': ['Yukon', 'Northwest Territories', 'Nunavut', 'Northern Quebec', 'Northern Ontario'],
                'South': ['Southern Ontario', 'Southern Quebec', 'Maritimes'],
                'East': ['Newfoundland and Labrador', 'Nova Scotia', 'Prince Edward Island', 'New Brunswick', 'Quebec (east)'],
                'West': ['British Columbia', 'Alberta', 'Yukon (south)', 'Western Ontario'],
                'Central': ['Manitoba', 'Saskatchewan', 'Ontario (central)', 'Quebec (central)'],
                'Northeast': ['Nunavut', 'Northern Quebec', 'Labrador'],
                'Northwest': ['Northwest Territories', 'Yukon', 'Northern British Columbia'],
                'Southeast': ['Nova Scotia', 'New Brunswick', 'Prince Edward Island', 'Quebec (south)'],
                'Southwest': ['British Columbia (south)', 'Vancouver Island', 'Lower Mainland', 'Alberta (south)']
            },
            'Mexico': {
                'North': ['Chihuahua', 'Coahuila', 'Nuevo León', 'Sonora', 'Tamaulipas', 'Baja California'],
                'South': ['Chiapas', 'Oaxaca', 'Guerrero', 'Tabasco', 'Yucatán', 'Quintana Roo'],
                'East': ['Veracruz', 'Tabasco', 'Campeche', 'Yucatán', 'Quintana Roo', 'Tamaulipas'],
                'West': ['Baja California', 'Baja California Sur', 'Sinaloa', 'Nayarit', 'Jalisco', 'Colima', 'Michoacán'],
                'Central': ['Mexico City', 'State of Mexico', 'Hidalgo', 'Puebla', 'Tlaxcala', 'Morelos', 'Querétaro', 'Guanajuato'],
                'Northeast': ['Nuevo León', 'Tamaulipas', 'Coahuila', 'San Luis Potosí'],
                'Northwest': ['Baja California', 'Sonora', 'Sinaloa', 'Chihuahua'],
                'Southeast': ['Yucatán', 'Quintana Roo', 'Campeche', 'Chiapas', 'Tabasco'],
                'Southwest': ['Guerrero', 'Oaxaca', 'Chiapas', 'Michoacán', 'Jalisco (south)']
            },
            'Argentina': {
                'North': ['Jujuy', 'Salta', 'Formosa', 'Chaco', 'Misiones', 'Corrientes'],
                'South': ['Patagonia', 'Santa Cruz', 'Tierra del Fuego', 'Chubut', 'Río Negro'],
                'East': ['Buenos Aires (province)', 'Entre Ríos', 'Corrientes', 'Misiones', 'Santa Fe (east)'],
                'West': ['Mendoza', 'San Juan', 'La Rioja', 'Catamarca', 'Neuquén', 'Río Negro (west)'],
                'Central': ['Córdoba', 'Santa Fe', 'Buenos Aires (city)', 'La Pampa', 'San Luis'],
                'Northeast': ['Misiones', 'Corrientes', 'Formosa', 'Chaco'],
                'Northwest': ['Jujuy', 'Salta', 'Tucumán', 'Catamarca', 'La Rioja', 'Santiago del Estero'],
                'Southeast': ['Buenos Aires', 'La Plata', 'Mar del Plata', 'Bahía Blanca'],
                'Southwest': ['Neuquén', 'Río Negro', 'Chubut', 'Santa Cruz', 'Tierra del Fuego']
            },
            'South Africa': {
                'North': ['Limpopo', 'North West', 'Northern Cape (north)', 'Gauteng (north)'],
                'South': ['Western Cape', 'Eastern Cape (south)', 'Garden Route', 'Cape Town region'],
                'East': ['KwaZulu-Natal', 'Eastern Cape', 'Mpumalanga (east)', 'Free State (east)'],
                'West': ['Northern Cape', 'Western Cape (west)', 'West Coast', 'Namibia border'],
                'Central': ['Free State', 'Gauteng', 'Johannesburg', 'Pretoria', 'North West'],
                'Northeast': ['Limpopo', 'Mpumalanga', 'Kruger region', 'Bushveld'],
                'Northwest': ['North West', 'Northern Cape', 'Limpopo (west)'],
                'Southeast': ['KwaZulu-Natal', 'Eastern Cape', 'Durban', 'Port Elizabeth'],
                'Southwest': ['Western Cape', 'Cape Town', 'Overberg', 'Karoo']
            },
            'Nigeria': {
                'North': ['Kano', 'Kaduna', 'Katsina', 'Zamfara', 'Sokoto', 'Jigawa', 'Borno', 'Yobe'],
                'South': ['Lagos', 'Rivers', 'Delta', 'Akwa Ibom', 'Cross River', 'Bayelsa'],
                'East': ['Enugu', 'Abia', 'Imo', 'Ebonyi', 'Cross River', 'Akwa Ibom'],
                'West': ['Lagos', 'Ogun', 'Oyo', 'Osun', 'Ondo', 'Ekiti', 'Kwara'],
                'Central': ['Abuja', 'Niger', 'Plateau', 'Kogi', 'Benue', 'Nasarawa'],
                'Northeast': ['Borno', 'Yobe', 'Adamawa', 'Gombe', 'Bauchi', 'Taraba'],
                'Northwest': ['Sokoto', 'Zamfara', 'Kebbi', 'Kano', 'Kaduna', 'Katsina'],
                'Southeast': ['Abia', 'Imo', 'Anambra', 'Enugu', 'Ebonyi', 'Rivers'],
                'Southwest': ['Lagos', 'Ogun', 'Oyo', 'Osun', 'Ondo', 'Ekiti']
            },
            'Egypt': {
                'North': ['Alexandria', 'Beheira', 'Kafr El Sheikh', 'Damietta', 'Dakahlia', 'Matrouh'],
                'South': ['Aswan', 'Luxor', 'Qena', 'Sohag', 'Red Sea (south)', 'Upper Egypt'],
                'East': ['Red Sea', 'Sinai', 'Suez', 'Ismailia', 'Port Said', 'Sharqia'],
                'West': ['Matrouh', 'New Valley', 'Giza (west)', 'Western Desert'],
                'Central': ['Cairo', 'Giza', 'Faiyum', 'Beni Suef', 'Minya', 'Asyut'],
                'Northeast': ['Port Said', 'Ismailia', 'North Sinai', 'Sharqia'],
                'Northwest': ['Alexandria', 'Matrouh', 'Beheira', 'Delta (west)'],
                'Southeast': ['Red Sea', 'Aswan', 'Luxor', 'Qena', 'Sohag'],
                'Southwest': ['New Valley', 'Luxor (west)', 'Aswan (west)']
            },
            'Saudi Arabia': {
                'North': ['Northern Borders', 'Jawf', 'Tabuk', 'Ha\'il'],
                'South': ['Najran', 'Jizan', 'Asir', 'Al Baha'],
                'East': ['Eastern Province', 'Dammam', 'Qatif', 'Al Ahsa', 'Riyadh (east)'],
                'West': ['Makkah', 'Madinah', 'Tabuk (west)', 'Red Sea coast'],
                'Central': ['Riyadh', 'Qassim', 'Al Majma\'ah', 'Wadi ad-Dawasir'],
                'Northeast': ['Northern Borders', 'Jawf', 'Eastern Province (north)'],
                'Northwest': ['Tabuk', 'Madinah', 'Ha\'il', 'Al Ula'],
                'Southeast': ['Eastern Province (south)', 'Najran', 'Asir (east)'],
                'Southwest': ['Asir', 'Al Baha', 'Jizan', 'Makkah (south)', 'Taif']
            },
            'UAE': {
                'North': ['Ras Al Khaimah', 'Umm Al Quwain', 'Ajman', 'Sharjah (north)', 'Fujairah (north)'],
                'South': ['Abu Dhabi (south)', 'Al Ain', 'Dubai (south)', 'Western Region'],
                'East': ['Fujairah', 'Sharjah (east)', 'Dibba', 'Khor Fakkan'],
                'West': ['Abu Dhabi (west)', 'Western Region', 'Liwa', 'Madinat Zayed'],
                'Central': ['Abu Dhabi', 'Dubai', 'Sharjah', 'Ajman', 'Al Ain'],
                'Northeast': ['Ras Al Khaimah', 'Fujairah', 'Dibba Al Fujairah'],
                'Northwest': ['Umm Al Quwain', 'Ajman', 'Sharjah', 'Dubai (north)'],
                'Southeast': ['Al Ain', 'Fujairah (south)', 'Oman border'],
                'Southwest': ['Abu Dhabi (southwest)', 'Liwa', 'Western Region', 'Saudi border']
            },
            'Turkey': {
                'North': ['Black Sea region', 'Trabzon', 'Samsun', 'Zonguldak', 'Istanbul (north)'],
                'South': ['Mediterranean', 'Antalya', 'Mersin', 'Adana', 'Hatay', 'Muğla'],
                'East': ['Eastern Anatolia', 'Van', 'Erzurum', 'Kars', 'Ağrı', 'Bitlis'],
                'West': ['Aegean', 'İzmir', 'Aydın', 'Muğla', 'Balıkesir', 'Çanakkale'],
                'Central': ['Central Anatolia', 'Ankara', 'Konya', 'Kayseri', 'Sivas', 'Eskişehir'],
                'Northeast': ['Trabzon', 'Rize', 'Artvin', 'Erzurum (north)', 'Giresun'],
                'Northwest': ['Istanbul', 'Kocaeli', 'Sakarya', 'Bursa', 'Tekirdağ', 'Edirne'],
                'Southeast': ['Southeastern Anatolia', 'Gaziantep', 'Şanlıurfa', 'Mardin', 'Diyarbakır'],
                'Southwest': ['Aegean coast', 'Muğla', 'Denizli', 'Burdur', 'Antalya (west)']
            },
            'Indonesia': {
                'North': ['North Sumatra', 'Aceh', 'Riau Islands', 'North Kalimantan'],
                'South': ['South Sumatra', 'Lampung', 'Bengkulu', 'South Kalimantan', 'East Nusa Tenggara'],
                'East': ['Papua', 'West Papua', 'Maluku', 'North Maluku', 'East Nusa Tenggara'],
                'West': ['West Sumatra', 'Bengkulu', 'Lampung (west)', 'Sumatra (west coast)'],
                'Central': ['Central Java', 'Yogyakarta', 'Central Kalimantan', 'Central Sulawesi'],
                'Northeast': ['North Maluku', 'North Sulawesi', 'Papua (north)', 'Halmahera'],
                'Northwest': ['Aceh', 'North Sumatra', 'Riau', 'Riau Islands'],
                'Southeast': ['East Nusa Tenggara', 'Maluku', 'Southeast Sulawesi', 'Papua (south)'],
                'Southwest': ['South Sumatra', 'Bengkulu', 'Lampung', 'Java (south)', 'Bali (south)']
            },
            'Thailand': {
                'North': ['Chiang Mai', 'Chiang Rai', 'Lampang', 'Lamphun', 'Mae Hong Son', 'Nan'],
                'South': ['Phuket', 'Krabi', 'Phang Nga', 'Trang', 'Satun', 'Songkhla', 'Pattani'],
                'East': ['Chonburi', 'Rayong', 'Chanthaburi', 'Trat', 'Sa Kaeo'],
                'West': ['Tak', 'Kanchanaburi', 'Ratchaburi', 'Phetchaburi', 'Myanmar border'],
                'Central': ['Bangkok', 'Ayutthaya', 'Pathum Thani', 'Nakhon Pathom', 'Suphan Buri', 'Saraburi'],
                'Northeast': ['Isan', 'Nakhon Ratchasima', 'Ubon Ratchathani', 'Khon Kaen', 'Udon Thani'],
                'Northwest': ['Tak', 'Mae Hong Son', 'Chiang Mai (west)', 'Myanmar border'],
                'Southeast': ['Rayong', 'Chanthaburi', 'Trat', 'Chonburi (east)', 'Cambodia border'],
                'Southwest': ['Phetchaburi', 'Prachuap Khiri Khan', 'Chumphon', 'Ranong', 'Andaman coast']
            },
            'South Korea': {
                'North': ['Gangwon', 'Gyeonggi (north)', 'Incheon (north)', 'DMZ region'],
                'South': ['Busan', 'South Gyeongsang', 'South Jeolla', 'Jeju', 'Gwangju'],
                'East': ['Gangwon (east)', 'North Gyeongsang (east)', 'Pohang', 'Ulleungdo'],
                'West': ['Incheon', 'Gyeonggi (west)', 'North Chungcheong (west)', 'South Chungcheong', 'North Jeolla'],
                'Central': ['Seoul', 'Gyeonggi', 'Daejeon', 'North Chungcheong', 'South Chungcheong'],
                'Northeast': ['Gangwon', 'North Gyeongsang (north)', 'Sokcho', 'Goseong'],
                'Northwest': ['Incheon', 'Gyeonggi (northwest)', 'Ganghwa', 'Yellow Sea coast'],
                'Southeast': ['Busan', 'Ulsan', 'South Gyeongsang', 'North Gyeongsang (south)'],
                'Southwest': ['South Jeolla', 'North Jeolla', 'Gwangju', 'Mokpo', 'Jeju']
            },
            'Philippines': {
                'North': ['Ilocos', 'Cagayan Valley', 'Cordillera', 'Batanes', 'Luzon (north)'],
                'South': ['Mindanao', 'Davao', 'Zamboanga', 'SOCCSKSARGEN', 'Caraga'],
                'East': ['Eastern Visayas', 'Bicol', 'Caraga', 'Davao (east)', 'Pacific coast'],
                'West': ['Ilocos (west)', 'Pangasinan', 'Zambales', 'Palawan', 'Mindoro (west)'],
                'Central': ['Metro Manila', 'Central Luzon', 'Calabarzon', 'Central Visayas', 'Cebu'],
                'Northeast': ['Cagayan Valley', 'Isabela', 'Cagayan', 'Batanes', 'Aurora'],
                'Northwest': ['Ilocos Norte', 'Ilocos Sur', 'La Union', 'Pangasinan', 'South China Sea coast'],
                'Southeast': ['Eastern Visayas', 'Davao', 'Surigao', 'Leyte', 'Samar'],
                'Southwest': ['Palawan', 'Western Visayas', 'Negros', 'Mindanao (west)', 'Zamboanga']
            },
            'Italy': {
                'North': ['Lombardy', 'Piedmont', 'Veneto', 'Trentino-Alto Adige', 'Friuli-Venezia Giulia', 'Liguria', 'Emilia-Romagna'],
                'South': ['Sicily', 'Calabria', 'Puglia', 'Basilicata', 'Campania (south)'],
                'East': ['Friuli-Venezia Giulia', 'Veneto', 'Marche', 'Abruzzo', 'Puglia'],
                'West': ['Piedmont', 'Liguria', 'Tuscany', 'Lazio', 'Campania (west)', 'Sardinia'],
                'Central': ['Tuscany', 'Umbria', 'Marche', 'Lazio', 'Abruzzo'],
                'Northeast': ['Veneto', 'Friuli', 'Trentino', 'Emilia-Romagna (north)'],
                'Northwest': ['Piedmont', 'Liguria', 'Lombardy (west)', 'Aosta Valley'],
                'Southeast': ['Puglia', 'Basilicata', 'Calabria', 'Sicily (east)'],
                'Southwest': ['Sardinia', 'Sicily (west)', 'Calabria (west)', 'Campania']
            },
            'Spain': {
                'North': ['Galicia', 'Asturias', 'Cantabria', 'Basque Country', 'Navarre', 'La Rioja'],
                'South': ['Andalusia', 'Murcia', 'Canary Islands', 'Ceuta', 'Melilla'],
                'East': ['Catalonia', 'Valencia', 'Balearic Islands', 'Murcia (east)', 'Aragon (east)'],
                'West': ['Galicia', 'Castile and León (west)', 'Extremadura', 'Portugal border'],
                'Central': ['Madrid', 'Castile-La Mancha', 'Castile and León', 'Aragon'],
                'Northeast': ['Catalonia', 'Aragon', 'Navarre', 'Basque Country'],
                'Northwest': ['Galicia', 'Asturias', 'Cantabria', 'León', 'Castile and León (northwest)'],
                'Southeast': ['Valencia', 'Murcia', 'Andalusia (east)', 'Balearic Islands'],
                'Southwest': ['Andalusia (west)', 'Extremadura', 'Huelva', 'Seville', 'Cádiz']
            },
            'Pakistan': {
                'North': ['Khyber Pakhtunkhwa', 'Gilgit-Baltistan', 'Azad Kashmir', 'Islamabad', 'Punjab (north)'],
                'South': ['Sindh', 'Balochistan (south)', 'Karachi', 'Thatta', 'Badin'],
                'East': ['Punjab (east)', 'Islamabad', 'Azad Kashmir', 'India border'],
                'West': ['Balochistan', 'Khyber Pakhtunkhwa (west)', 'FATA', 'Afghanistan border'],
                'Central': ['Punjab', 'Islamabad', 'Faisalabad', 'Sargodha', 'Multan'],
                'Northeast': ['Azad Kashmir', 'Gilgit-Baltistan', 'Khyber Pakhtunkhwa (north)', 'Hazara'],
                'Northwest': ['Khyber Pakhtunkhwa', 'FATA', 'Balochistan (north)', 'Chitral'],
                'Southeast': ['Sindh (east)', 'Punjab (south)', 'Bahawalpur', 'India border'],
                'Southwest': ['Balochistan', 'Gwadar', 'Makran', 'Karachi (west)', 'Iran border']
            },
            'Bangladesh': {
                'North': ['Rajshahi', 'Rangpur', 'Mymensingh', 'Sylhet (north)', 'Dinajpur'],
                'South': ['Barisal', 'Khulna (south)', 'Patuakhali', 'Bagerhat', 'Coastal belt'],
                'East': ['Chittagong', 'Sylhet', 'Comilla', 'Noakhali', 'Brahmanbaria'],
                'West': ['Rajshahi', 'Khulna', 'Jessore', 'Kushtia', 'India border (west)'],
                'Central': ['Dhaka', 'Tangail', 'Gazipur', 'Narayanganj', 'Munshiganj', 'Manikganj'],
                'Northeast': ['Sylhet', 'Mymensingh (north)', 'Netrokona', 'Sunamganj', 'Habiganj'],
                'Northwest': ['Rajshahi', 'Rangpur', 'Bogra', 'Naogaon', 'India border'],
                'Southeast': ['Chittagong', 'Cox\'s Bazar', 'Feni', 'Noakhali', 'Chittagong Hill Tracts'],
                'Southwest': ['Khulna', 'Satkhira', 'Jessore', 'Bagerhat', 'Sundarbans']
            },
            'Nepal': {
                'North': ['Himalayan', 'Karnali', 'Gandaki (north)', 'Province 1 (north)', 'Tibet border'],
                'South': ['Province 2', 'Lumbini (south)', 'Terai', 'India border (south)'],
                'East': ['Province 1', 'Bagmati (east)', 'Koshi', 'Sagarmatha', 'India border (east)'],
                'West': ['Karnali', 'Sudurpashchim', 'Lumbini (west)', 'India border (west)'],
                'Central': ['Bagmati', 'Kathmandu Valley', 'Nawalpur', 'Chitwan', 'Makwanpur'],
                'Northeast': ['Province 1', 'Sagarmatha', 'Koshi', 'Taplejung', 'Sankhuwasabha'],
                'Northwest': ['Karnali', 'Sudurpashchim', 'Dolpa', 'Humla', 'Darchula'],
                'Southeast': ['Province 2', 'Janakpur', 'Saptari', 'Siraha', 'Morang'],
                'Southwest': ['Lumbini', 'Rupandehi', 'Kapilvastu', 'Banke', 'Bardiya']
            },
            'Iran': {
                'North': ['Gilan', 'Mazandaran', 'Golestan', 'North Khorasan', 'Alborz', 'Tehran (north)'],
                'South': ['Hormozgan', 'Bushehr', 'Fars (south)', 'Kohgiluyeh-Boyer Ahmad', 'Coastal'],
                'East': ['Khorasan', 'South Khorasan', 'Razavi Khorasan', 'Sistan and Baluchestan', 'Afghanistan border'],
                'West': ['Kurdistan', 'Kermanshah', 'Ilam', 'Lorestan', 'West Azerbaijan', 'Iraq border'],
                'Central': ['Tehran', 'Isfahan', 'Yazd', 'Qom', 'Markazi', 'Qazvin'],
                'Northeast': ['North Khorasan', 'Razavi Khorasan', 'Golestan', 'Turkmenistan border'],
                'Northwest': ['West Azerbaijan', 'East Azerbaijan', 'Ardabil', 'Zanjan', 'Turkey border'],
                'Southeast': ['Sistan and Baluchestan', 'Kerman (east)', 'Hormozgan (east)', 'Pakistan border'],
                'Southwest': ['Khuzestan', 'Bushehr', 'Chaharmahal and Bakhtiari', 'Iraq border', 'Kuwait border']
            },
            'Israel': {
                'North': ['Northern District', 'Galilee', 'Golan Heights', 'Haifa (north)', 'Acre'],
                'South': ['Southern District', 'Negev', 'Eilat', 'Arava', 'Red Sea'],
                'East': ['Jordan Valley', 'West Bank', 'Jerusalem (east)', 'Dead Sea', 'Jordan border'],
                'West': ['Coastal plain', 'Tel Aviv', 'Haifa', 'Netanya', 'Ashdod', 'Mediterranean'],
                'Central': ['Central District', 'Tel Aviv', 'Jerusalem', 'Ramla', 'Lod', 'Modi\'in'],
                'Northeast': ['Golan Heights', 'Upper Galilee', 'Jordan border (north)', 'Sea of Galilee'],
                'Northwest': ['Haifa', 'Western Galilee', 'Acre', 'Mediterranean coast (north)'],
                'Southeast': ['Negev (east)', 'Arava', 'Eilat', 'Jordan border (south)', 'Red Sea'],
                'Southwest': ['Negev (west)', 'Gaza border', 'Be\'er Sheva', 'Mediterranean (south)', 'Sinai border']
            },
            'Vietnam': {
                'North': ['Hanoi', 'Red River Delta', 'Northern Midlands', 'Ha Giang', 'Lao Cai', 'Cao Bang'],
                'South': ['Mekong Delta', 'Ho Chi Minh City', 'Ba Ria-Vung Tau', 'Ca Mau', 'Soc Trang'],
                'East': ['Central Coast', 'Da Nang', 'Nha Trang', 'Phu Yen', 'Binh Dinh', 'South China Sea'],
                'West': ['Northwest', 'Central Highlands', 'Mekong (west)', 'Cambodia border', 'Laos border'],
                'Central': ['Central Vietnam', 'Thua Thien-Hue', 'Quang Nam', 'Quang Ngai', 'Binh Dinh', 'Phu Yen'],
                'Northeast': ['Quang Ninh', 'Lang Son', 'Cao Bang', 'Bac Kan', 'Thai Nguyen', 'China border'],
                'Northwest': ['Lai Chau', 'Son La', 'Dien Bien', 'Lao Cai (west)', 'Laos border'],
                'Southeast': ['Ho Chi Minh City', 'Dong Nai', 'Binh Duong', 'Ba Ria-Vung Tau', 'Binh Phuoc'],
                'Southwest': ['Mekong Delta (west)', 'An Giang', 'Kien Giang', 'Cambodia border', 'Gulf of Thailand']
            },
            'Malaysia': {
                'North': ['Perlis', 'Kedah', 'Penang', 'Perak (north)', 'Kelantan', 'Terengganu (north)'],
                'South': ['Johor', 'Malacca', 'Negeri Sembilan (south)', 'Singapore border'],
                'East': ['Kelantan', 'Terengganu', 'Pahang (east)', 'East Malaysia (Sabah, Sarawak east coast)'],
                'West': ['Penang', 'Perak', 'Selangor (west)', 'Malacca (west)', 'Strait of Malacca'],
                'Central': ['Kuala Lumpur', 'Selangor', 'Negeri Sembilan', 'Pahang (central)', 'Cameron Highlands'],
                'Northeast': ['Kelantan', 'Terengganu', 'Perak (northeast)', 'Thailand border'],
                'Northwest': ['Perlis', 'Kedah', 'Penang', 'Perak (northwest)', 'Langkawi'],
                'Southeast': ['Johor (east)', 'Pahang (south)', 'Tioman', 'East coast (south)'],
                'Southwest': ['Malacca', 'Negeri Sembilan', 'Johor (west)', 'Strait (south)']
            },
            'Chile': {
                'North': ['Arica y Parinacota', 'Tarapacá', 'Antofagasta', 'Atacama', 'Coquimbo (north)'],
                'South': ['Los Lagos', 'Aysén', 'Magallanes', 'Chiloé', 'Patagonia', 'Tierra del Fuego'],
                'East': ['Andes border', 'Mendoza border', 'Argentina border', 'Mountain regions'],
                'West': ['Coast', 'Valparaiso', 'Coquimbo', 'Atacama coast', 'Antofagasta coast', 'Pacific'],
                'Central': ['Santiago', 'Valparaiso', 'O\'Higgins', 'Maule', 'Ñuble', 'Biobío'],
                'Northeast': ['Altiplano', 'Atacama (east)', 'Argentina border (north)'],
                'Northwest': ['Arica', 'Iquique', 'Antofagasta', 'Pacific (north)'],
                'Southeast': ['Araucanía', 'Los Ríos', 'Los Lagos', 'Chiloé', 'Argentina border (south)'],
                'Southwest': ['Coast (south)', 'Los Lagos (coast)', 'Chiloé', 'Pacific (south)']
            },
            'Colombia': {
                'North': ['La Guajira', 'Cesar', 'Magdalena', 'Atlántico', 'Bolívar (north)', 'Caribbean coast'],
                'South': ['Putumayo', 'Amazonas', 'Vaupés', 'Guainía', 'Nariño (south)', 'Ecuador border'],
                'East': ['Meta', 'Vichada', 'Arauca', 'Casanare', 'Guainía', 'Venezuela border'],
                'West': ['Chocó', 'Valle del Cauca (west)', 'Nariño (west)', 'Pacific coast'],
                'Central': ['Cundinamarca', 'Boyacá', 'Tolima', 'Huila', 'Caldas', 'Risaralda', 'Quindío', 'Antioquia'],
                'Northeast': ['North Santander', 'Arauca', 'Cesar', 'Bolívar', 'Venezuela border'],
                'Northwest': ['Córdoba', 'Sucre', 'Bolívar', 'Antioquia (north)', 'Chocó (north)', 'Caribbean'],
                'Southeast': ['Amazonas', 'Vaupés', 'Guaviare', 'Putumayo', 'Brazil border'],
                'Southwest': ['Nariño', 'Cauca', 'Valle del Cauca', 'Pacific', 'Ecuador border']
            },
            'Kenya': {
                'North': ['Turkana', 'Marsabit', 'Samburu', 'Isiolo', 'Laikipia', 'Rift Valley (north)'],
                'South': ['Kajiado', 'Narok', 'Kisii', 'Migori', 'Tanzania border', 'Coastal (south)'],
                'East': ['Coast', 'Garissa', 'Tana River', 'Lamu', 'Kilifi', 'Mombasa', 'Taita-Taveta'],
                'West': ['Western', 'Nyanza', 'Kisumu', 'Kakamega', 'Bungoma', 'Busia', 'Uganda border'],
                'Central': ['Nairobi', 'Kiambu', 'Murang\'a', 'Kirinyaga', 'Nyeri', 'Nyandarua', 'Nakuru'],
                'Northeast': ['Mandera', 'Wajir', 'Garissa', 'Isiolo', 'Ethiopia border', 'Somalia border'],
                'Northwest': ['West Pokot', 'Turkana (west)', 'Uganda border', 'Sudan border'],
                'Southeast': ['Coast (south)', 'Taita-Taveta', 'Tanzania border', 'Indian Ocean'],
                'Southwest': ['Narok', 'Kisii', 'Migori', 'Tanzania border', 'Lake Victoria']
            },
            'Poland': {
                'North': ['Pomerania', 'West Pomerania', 'Warmia-Masuria', 'Baltic coast', 'Gdańsk', 'Szczecin'],
                'South': ['Lesser Poland', 'Silesia', 'Subcarpathian', 'Świętokrzyskie', 'Carpathians'],
                'East': ['Lublin', 'Podlaskie', 'Subcarpathian (east)', 'Belarus border', 'Ukraine border'],
                'West': ['Lubusz', 'Greater Poland (west)', 'Lower Silesia (west)', 'Germany border'],
                'Central': ['Masovian', 'Warsaw', 'Łódź', 'Kuyavia-Pomerania', 'Greater Poland'],
                'Northeast': ['Warmia-Masuria', 'Podlaskie', 'Suwałki', 'Lithuania border', 'Kaliningrad border'],
                'Northwest': ['West Pomerania', 'Pomerania', 'Gdańsk', 'Baltic', 'Germany border'],
                'Southeast': ['Subcarpathian', 'Lesser Poland (east)', 'Ukraine border', 'Slovakia border'],
                'Southwest': ['Lower Silesia', 'Opole', 'Silesia', 'Czech border', 'Germany border']
            },
            'Ukraine': {
                'North': ['Chernihiv', 'Sumy', 'Kyiv (north)', 'Zhytomyr (north)', 'Belarus border'],
                'South': ['Odessa', 'Mykolaiv', 'Kherson', 'Zaporizhzhia (south)', 'Crimea', 'Black Sea'],
                'East': ['Kharkiv', 'Luhansk', 'Donetsk', 'Dnipropetrovsk (east)', 'Russia border'],
                'West': ['Lviv', 'Volyn', 'Ivano-Frankivsk', 'Ternopil', 'Poland border', 'EU border'],
                'Central': ['Kyiv', 'Cherkasy', 'Poltava', 'Kirovohrad', 'Vinnytsia', 'Dnipropetrovsk'],
                'Northeast': ['Sumy', 'Kharkiv (north)', 'Chernihiv (east)', 'Russia border'],
                'Northwest': ['Volyn', 'Rivne', 'Zhytomyr', 'Poland border', 'Belarus border'],
                'Southeast': ['Donetsk', 'Luhansk', 'Zaporizhzhia', 'Dnipropetrovsk (south)', 'Sea of Azov'],
                'Southwest': ['Odessa (west)', 'Vinnytsia (south)', 'Moldova border', 'Romania border', 'Black Sea']
            },
        }
    
    def get_affected_regions(self, nakshatra: str, country: str = 'India') -> Dict[str, Any]:
        """Get geographic regions affected by planetary position in nakshatra"""
        direction = self.nakshatra_directions.get(nakshatra, 'Unknown')
        regions = self.regional_mapping.get(country, {}).get(direction, [])
        
        return {
            'nakshatra': nakshatra,
            'direction': direction,
            'country': country,
            'affected_regions': regions,
            'interpretation': f"{nakshatra} influences {direction} regions of {country}"
        }
    
    def analyze_planetary_impact(self, planet_data: Dict[str, Any], country: str = 'India') -> Dict[str, Any]:
        """Analyze geographic impact of a planet's position"""
        nakshatra = planet_data.get('nakshatra', {}).get('name', 'Unknown')
        planet_name = planet_data.get('name', 'Unknown')
        
        region_data = self.get_affected_regions(nakshatra, country)
        
        # Determine impact type based on planet
        impact_types = {
            'Saturn': 'Delays, restrictions, structural changes',
            'Mars': 'Conflicts, accidents, heat-related events',
            'Rahu': 'Sudden changes, foreign influences, technology',
            'Ketu': 'Spiritual movements, epidemics, isolation',
            'Jupiter': 'Growth, prosperity, legal matters',
            'Venus': 'Arts, entertainment, financial markets',
            'Mercury': 'Communication, trade, transportation',
            'Sun': 'Government, authority, leadership',
            'Moon': 'Public mood, agriculture, water resources',
            'Uranus': 'Revolution, innovation, sudden upheavals',
            'Neptune': 'Deception, spirituality, oil/gas',
            'Pluto': 'Transformation, power struggles, nuclear matters'
        }
        
        return {
            **region_data,
            'planet': planet_name,
            'impact_type': impact_types.get(planet_name, 'General influence'),
            'prediction': f"{planet_name} in {nakshatra} suggests {impact_types.get(planet_name, 'influence')} in {region_data['direction']} {country}"
        }
    
    def get_nakshatra_from_longitude(self, longitude: float) -> str:
        """Convert longitude to nakshatra name"""
        nakshatras = [
            'Ashwini', 'Bharani', 'Krittika', 'Rohini', 'Mrigashira', 'Ardra', 'Punarvasu',
            'Pushya', 'Ashlesha', 'Magha', 'Purva Phalguni', 'Uttara Phalguni', 'Hasta',
            'Chitra', 'Swati', 'Vishakha', 'Anuradha', 'Jyeshtha', 'Mula', 'Purva Ashadha',
            'Uttara Ashadha', 'Shravana', 'Dhanishta', 'Shatabhisha', 'Purva Bhadrapada',
            'Uttara Bhadrapada', 'Revati'
        ]
        
        nakshatra_span = 360 / 27
        nak_index = int(longitude / nakshatra_span)
        return nakshatras[nak_index % 27]
