"""
Кеш переводов с корейского на английский
Разделен по категориям для более эффективного поиска
"""

# Производители автомобилей
BRAND = {
    "현대": "Hyundai",
    "제네시스": "Genesis",
    "기아": "Kia",
    "쉐보레(GM대우)": "Chevrolet (GM Daewoo)",
    "르노코리아(삼성)": "Renault Korea (Samsung)",
    "KG모빌리티(쌍용)": "KG Mobility (Ssangyong)",
    "BMW": "BMW",
    "GMC": "GMC",
    "닛산": "Nissan",
    "다이하쯔": "Daihatsu",
    "닷지": "Dodge",
    "도요타": "Toyota",
    "동풍소콘": "Dongfeng Sokon",
    "람보르기니": "Lamborghini",
    "랜드로버": "Land Rover",
    "렉서스": "Lexus",
    "MG로버": "MG Rover",
    "로터스": "Lotus",
    "롤스로이스": "Rolls-Royce",
    "르노": "Renault",
    "링컨": "Lincoln",
    "마세라티": "Maserati",
    "마이바흐": "Maybach",
    "마쯔다": "Mazda",
    "맥라렌": "McLaren",
    "머큐리": "Mercury",
    "미니": "Mini",
    "미쯔비시": "Mitsubishi",
    "미쯔오까": "Mitsuoka",
    "벤츠": "Benz",
    "벤틀리": "Bentley",
    "볼보": "Volvo",
    "부가티": "Bugatti",
    "북기은상": "North Korea Silver Award",
    "뷰익": "Buick",
    "사브": "Saab",
    "사이언": "Scion",
    "새턴": "Saturn",
    "쉐보레": "Chevrolet",
    "스마트": "Smart",
    "스바루": "Subaru",
    "스즈키": "Suzuki",
    "시트로엥/DS": "Citroen/DS",
    "아우디": "Audi",
    "알파 로메오": "Alfa Romeo",
    "애스턴마틴": "Aston Martin",
    "어큐라": "Acura",
    "오펠": "Opel",
    "올즈모빌": "Oldsmobile",
    "이네오스": "Ineos",
    "이스즈": "Isuzu",
    "인피니티": "Infiniti",
    "재규어": "Jaguar",
    "지프": "Jeep",
    "캐딜락": "Cadillac",
    "코닉세그": "Koenigsegg",
    "크라이슬러": "Chrysler",
    "테슬라": "Tesla",
    "파가니": "Pagani",
    "페라리": "Ferrari",
    "포드": "Ford",
    "포르쉐": "Porsche",
    "포톤": "Photon",
    "폭스바겐": "Volkswagen",
    "폰티악": "Pontiac",
    "폴스타": "Polestar",
    "푸조": "Peugeot",
    "피아트": "Fiat",
    "험머": "Hummer",
    "혼다": "Honda",
    "BYD": "BYD",
    "신위안": "Xinyuan",
}

# Модели (можно добавлять по мере необходимости)
MODEL = {
    "소나타": "Sonata",
    "그랜저": "Grandeur",
    "아반떼": "Avante",
    "투싼": "Tucson",
    "싼타페": "Santa Fe",
    "팰리세이드": "Palisade",
    "쏘렌토": "Sorento",
    "스포티지": "Sportage",
    "카니발": "Carnival",
    "모하비": "Mohave",
    "K5": "K5",
    "K7": "K7",
    "K8": "K8",
    "K9": "K9",
    "G70": "G70",
    "G80": "G80",
    "G90": "G90",
    "GV70": "GV70",
    "GV80": "GV80",
    "램픽업": "Ram Pickup",
}

# Типы топлива
FUEL = {
    "가솔린": "Gasoline",
    "디젤": "Diesel",
    "LPG": "LPG",
    "전기": "Electric",
    "하이브리드": "Hybrid",
    "플러그인하이브리드": "Plug-in Hybrid",
    "수소": "Hydrogen",
    "가솔린+LPG": "Gasoline + LPG",
}

# Коробки передач
TRANSMISSION = {
    "오토": "Automatic",
    "자동": "Automatic",
    "수동": "Manual",
    "CVT": "CVT",
    "DCT": "DCT",
    "AMT": "AMT",
}

# Типы кузова
CAR_TYPE = {
    "대형차": "Large vehicles",
    "스포츠카": "Sports car",
    "승합차": "Van",
    "중형차": "Mid-size car",
    "화물차": "Truck",
}

# Цвета
COLOR = {
    "검정색": "Black",
    "녹색": "Green",
    "은하색": "Galaxy",
    "은회색": "Silver Gray",
    "자주색": "Purple",
    "쥐색": "Mouse Gray",
    "청색": "Blue",
    "흰색투톤": "White Two-Tone",
    "노란색": "Yellow",
    "빨간색": "Red",
    "은색": "Silver",
    "주황색": "Orange",
    "흰색": "White",
}

# Регионы/Области
REGION = {
    "서울": "Seoul",
    "경기": "Gyeonggi",
    "인천": "Incheon",
    "부산": "Busan",
    "대구": "Daegu",
    "대전": "Daejeon",
    "광주": "Gwangju",
    "울산": "Ulsan",
    "세종": "Sejong",
    "강원": "Gangwon",
    "충북": "Chungbuk",
    "충남": "Chungnam",
    "전북": "Jeonbuk",
    "전남": "Jeonnam",
    "경북": "Gyeongbuk",
    "경남": "Gyeongnam",
    "제주": "Jeju",
}

# Комплектации/Опции (добавляйте по мере необходимости)
CONFIGURATION = {
    "디럭스": "Deluxe",
    "프리미엄": "Premium",
    "익스클루시브": "Exclusive",
    "노블레스": "Noblesse",
    "스페셜": "Special",
    "럭셔리": "Luxury",
    "스포츠": "Sports",
}

# Общие термины
GENERAL = {
    "신차": "New Car",
    "중고차": "Used Car",
    "일반": "General",
    "인증": "Certified",
    "수입": "Import",
    "국산": "Domestic",
}

# Мета-словарь для быстрого доступа
# Ключи соответствуют полям из FIELDS_TO_EXTRACT
CATEGORY_MAP = {
    "brand": BRAND,
    "model": MODEL,
    "fuel": FUEL,
    "transmission": TRANSMISSION,
    "car_type": CAR_TYPE,
    "color": COLOR,
    "region": REGION,
    "configuration": CONFIGURATION,
    "grade": CONFIGURATION,
}

# Fallback словарь для полей без категории
DEFAULT = {}
