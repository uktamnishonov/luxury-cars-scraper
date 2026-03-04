# Car Data Filtering

This module filters car data from JSONL files based on configurable rules.

## Quick Start

### Basic Usage

```bash
# Filter with default config (defined in car_filter.py)
PYTHONPATH=. python3 -m parser.filtering.car_filter data/details/cars_data_20260302_072841.jsonl

# Or run directly as a script
python3 parser/filtering/car_filter.py data/details/cars_data_20260302_072841.jsonl

# Specify output file
PYTHONPATH=. python3 -m parser.filtering.car_filter data/details/cars_data_20260302_072841.jsonl -o data/details/filtered_cars.jsonl

# Override default minimum year for all brands
PYTHONPATH=. python3 -m parser.filtering.car_filter data/details/cars_data_20260302_072841.jsonl --min-year 2020

# Add price filters (in 10,000 KRW units, e.g., 3000 = 30,000,000 KRW)
PYTHONPATH=. python3 -m parser.filtering.car_filter data/details/cars_data_20260302_072841.jsonl --min-price 3000 --max-price 15000

# Add mileage filters (in km)
PYTHONPATH=. python3 -m parser.filtering.car_filter data/details/cars_data_20260302_072841.jsonl --max-mileage 100000
```

## Configuration

### Easy Config (Edit `car_filter.py`)

Open [parser/filtering/car_filter.py](parser/filtering/car_filter.py) and modify the configuration section at the top:

```python
# ============================================================================
# FILTER CONFIGURATION - Easy to modify
# ============================================================================

BRAND_YEAR_FILTERS = {
    # Brand name: minimum year (inclusive)
    # Note: Brand names in data are translated to English
    "BMW": 2018,
    "Mercedes-Benz": 2018,  # Shows as "Mercedes-Benz" in data
    "Porsche": 2018,
    "Land Rover": 2018,  # Includes Range Rover models
    "Cadillac": 2020,
}

# Default minimum year for brands not specified above
DEFAULT_MIN_YEAR = None  # Set to a year (e.g., 2018) or None to skip

# Additional filters (set to None to disable)
MIN_PRICE = None  # Minimum price in 10,000 KRW
MAX_PRICE = None  # Maximum price
MAX_MILEAGE = None  # Maximum mileage in km
MIN_MILEAGE = None  # Minimum mileage in km
```

### Current Filter Rules

- **BMW, Mercedes-Benz, Porsche, Land Rover**: Year >= 2018
- **Cadillac**: Year >= 2020

### To Modify Filters:

1. **Change year requirements**: Edit the numbers in `BRAND_YEAR_FILTERS`
2. **Add new brand**: Add a new line like `"Brand Name": 2020,`
3. **Remove brand filter**: Delete the line or comment it out with `#`
4. **Add price filter**: Set `MIN_PRICE = 3000` (for 30M KRW minimum)
5. **Add mileage filter**: Set `MAX_MILEAGE = 100000` (for 100k km maximum)

## Output

- Filtered data is saved to a new JSONL file with timestamp
- Original file is never modified
- Statistics are logged showing:
  - Total cars processed
  - Cars that passed filters
  - Rejection breakdown by filter type
  - Pass rate percentage

## Examples

### Example 1: Only keep 2020+ luxury cars

```python
BRAND_YEAR_FILTERS = {
    "BMW": 2020,
    "Mercedes-Benz": 2020,
    "Porsche": 2020,
    "Land Rover": 2020,
    "Cadillac": 2020,
}
```

### Example 2: Filter by price and mileage too

```python
MIN_PRICE = 5000  # Minimum 50M KRW
MAX_PRICE = 20000  # Maximum 200M KRW
MAX_MILEAGE = 80000  # Maximum 80k km
```

### Example 3: Apply same year to ALL brands

```python
BRAND_YEAR_FILTERS = {}  # Clear specific filters
DEFAULT_MIN_YEAR = 2019  # All brands must be 2019+
```
