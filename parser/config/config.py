"""
Конфигурационный файл для парсера Encar.com
"""

# API endpoints
API_BASE_URL = "https://api.encar.com"
API_LIST_ENDPOINT = "/search/car/list/general"
API_VEHICLE_DETAIL_ENDPOINT = "/v1/readside/vehicle/{id}"


# Параметры поиска
SEARCH_PARAMS = {
    "sell_type": "일반",
    "start_count": 0,
    "current_count": 1000,
}

PARAMS = {
    "람보르기니": "",
    "페라리": "",
    "롤스로이스": "",
    "벤틀리": "",
    "BMW": "",
    "벤츠": "",  # Mercedes-Benz (short form commonly used in Korea)
    "랜드로버": "",
    "포르쉐": "",
    "캐딜락": "",
}


# Настройки изображений
IMAGE_BASE_URL = "https://ci.encar.com"
IMAGE_PARAMS = "?impolicy=heightRate&rh=696&cw=1160&ch=696"

# Настройки переводчика
ENABLE_AUTO_TRANSLATE = True

# Настройки HTTP запросов
REQUEST_TIMEOUT = 30  # Таймаут в секундах
RETRY_ATTEMPTS = 3  # Количество попыток при ошибке
DELAY_BETWEEN_REQUESTS = 0.5  # Задержка между запросами (секунды)

# Параметры данных
FIELDS_TO_EXTRACT = {
    # Basic identification
    "id": ["vehicleId"],
    "vin": ["vin"],
    "vehnumber": ["vehicleNo"],
    # Listing information
    "registDateTime": ["manage", "registDateTime"],
    "modifyDateTime": ["manage", "modifyDateTime"],
    # Vehicle specifications
    "brand": ["category", "manufacturerEnglishName"],
    "model": ["category", "modelGroupEnglishName"],
    "grade": ["category", "gradeEnglishName"],
    "configuration": ["category", "gradeDetailEnglishName"],
    "year": ["category", "formYear"],
    "domestic": ["category", "isDomestic"],
    # Pricing
    "originPrice": ["price", "originalPrice"],
    "price": ["advertisement", "price"],
    # Condition
    "mileage": ["spec", "mileage"],
    "fuel": ["spec", "fuelName"],
    "transmission": ["spec", "transmissionName"],
    "car_type": ["spec", "bodyName"],
    "color": ["spec", "colorName"],
    "seating": ["spec", "seatCount"],
    "displacement": ["spec", "displacement"],
    # Seller Information
    "region": ["contact", "address"],
    "seller_type": ["contact", "sellerCategoryCode"],
    "seller_id": ["contact", "sellerId"],
    "dealer_name": ["contact", "sellerName"],
    "dealer_firm_name": ["contact", "sellerCompanyName"],
    # Special Features
    "encar_diagnosis": ["inspection", "encarDiagnosisYN"],
    "has_ev_battery_info": ["spec", "hasEvBatteryInfo"],
    # Media
    "images": ["photos"],
    "url": ["vehicleId"],
    "diagnosis_report_url": ["vehicleId"],
    "inspection_report_url": ["vehicleId"],
    "accident_report_url": ["vehicleId"],
}
SMALL_FIELDS_TO_EXTRACT = {
    "vehnumber": ["vehicleNo"],
    "brand": ["category", "manufacturerEnglishName"],
    "model": ["category", "modelGroupEnglishName"],
    "grade": ["category", "gradeEnglishName"],
    "configuration": ["category", "gradeDetailEnglishName"],
    "year": ["category", "formYear"],
    "mileage": ["spec", "mileage"],
    "fuel": ["spec", "fuelName"],
    "transmission": ["spec", "transmissionName"],
    "color": ["spec", "colorName"],
    "seating": ["spec", "seatCount"],
    "displacement": ["spec", "displacement"],
    "price": ["advertisement", "price"],
    "region": ["contact", "address"],
    "images": ["photos"],
}

# Словарь опций
OPTIONS = {
    "sunroof": "010",
    "head_lamp_(hid,_led)": "029 075",
    "power_electric_trunk": "059",
    "ghost_door_closing": "080",
    "electric_contacts_side_mirror": "024",
    "aluminum_wheel": "017",
    "roof_rack": "062",
    "thermal_steering_wheel": "082",
    "electric_control_steering_wheel": "083",
    "paddle_shift": "084",
    "steering_wheel_remote_control": "031",
    "ecm_room_mirror": "030",
    "high_pass": "074",
    "power_door_lock": "006",
    "power_steering_wheel": "008",
    "power_windows": "007",
    "airbag_(driver_seat,_passenger_seat)": "026 027",
    "airbag_(side)": "020",
    "airbag_(curtain)": "056",
    "brake_lock_(abs)": "001",
    "anti_-slip_(tcs)": "019",
    "body_posture_control_device_(esc)": "055",
    "tire_air_ap_sensor_(tpms)": "033",
    "lane_departure_alarm_system_(ldws)": "088",
    "electronic_control_suspension_(ecs)": "002",
    "parking_detection_sensor_(front,_rear)": "085 032",
    "rear_alarm_system": "086",
    "rear_camera": "058",
    "360_degree_around_view": "087",
    "cruise_control_(general,_adaptive)": "068 079",
    "head_-up_display_(hud)": "095",
    "electronic_parking_brake_(epb)": "094",
    "automatic_air_conditioner": "023",
    "smart_key": "057",
    "wireless_door_lock": "015",
    "rain_sensor": "081",
    "auto_light": "097",
    "curtain/blind_(back_seat,_rear)": "092 093",
    "navigation": "005",
    "front_seat_av_monitor": "004",
    "back_seat_av_monitor": "054",
    "bluetooth": "096",
    "cd_player": "003",
    "usb_terminal": "072",
    "aux_terminal": "071",
    "leather_sheet": "014",
    "electric_seat_(driver_seat,_passenger_seat)": "021 035",
    "electric_sheet_(back_seat)": "089",
    "heated_seats_(front_seats,_rear_seats)": "022 063",
    "memory_sheet_(driver's_seat,_passenger_seat)": "051 078",
    "ventilation_sheet_(driver's_seat,_passenger_seat)": "034 077",
    "ventilation_sheet_(back_seat)": "090",
    "massage_sheet": "091",
}
