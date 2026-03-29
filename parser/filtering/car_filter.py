"""
Car data filtering script

This script reads a JSONL file with car data and filters it based on configurable rules.
The filtered results are saved to a new JSONL file.
"""

import json
import argparse
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Ensure project root is importable when running this file directly
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from logger.logging import get_parser_logger

logger = get_parser_logger(__name__)


# ============================================================================
# FILTER CONFIGURATION - Easy to modify
# ============================================================================

BRAND_YEAR_FILTERS = {
    # Brand name: minimum year (inclusive)
    # Note: Brand names in data are translated to English
    # "BMW": 2018,
    # "Mercedes-Benz": 2018,  # Shows as "Mercedes-Benz" in data
    # "Porsche": 2018,
    # "Land Rover": 2018,  # Includes Range Rover models
    "Cadillac": 2020,
}

# Default minimum year for brands not specified above
DEFAULT_MIN_YEAR = (
    2019  # Set to a year (e.g., 2018) to filter all brands, or None to skip
)

# Additional filters (set to None to disable)
MIN_PRICE = None  # Minimum price in 10,000 KRW (e.g., 1000 = 10,000,000 KRW)
MAX_PRICE = None  # Maximum price
MAX_MILEAGE = None  # Maximum mileage in km
MIN_MILEAGE = None  # Minimum mileage in km

# ============================================================================


class CarDataFilter:
    """Filter car data based on configurable rules"""

    def __init__(
        self,
        input_file: str,
        output_file: Optional[str] = None,
        brand_year_filters: Optional[Dict[str, int]] = None,
        default_min_year: Optional[int] = None,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        min_mileage: Optional[int] = None,
        max_mileage: Optional[int] = None,
    ):
        """
        Initialize the filter with configuration

        Args:
            input_file: Path to input JSONL file
            output_file: Path to output JSONL file (auto-generated if None)
            brand_year_filters: Dict mapping brand names to minimum years
            default_min_year: Default minimum year for brands not in filters
            min_price: Minimum price filter
            max_price: Maximum price filter
            min_mileage: Minimum mileage filter
            max_mileage: Maximum mileage filter
        """
        self.input_file = Path(input_file)

        # Auto-generate output filename if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_file = (
                self.input_file.parent / f"filtered_cars_{timestamp}.jsonl"
            )
        else:
            self.output_file = Path(output_file)

        self.brand_year_filters = brand_year_filters or BRAND_YEAR_FILTERS
        self.default_min_year = default_min_year or DEFAULT_MIN_YEAR
        self.min_price = min_price or MIN_PRICE
        self.max_price = max_price or MAX_PRICE
        self.min_mileage = min_mileage or MIN_MILEAGE
        self.max_mileage = max_mileage or MAX_MILEAGE

        self.stats = {
            "total": 0,
            "filtered": 0,
            "rejected_by_year": 0,
            "rejected_by_price": 0,
            "rejected_by_mileage": 0,
            "rejected_by_missing_data": 0,
        }

    def _check_year_filter(self, car_data: dict) -> bool:
        """Check if car passes year filter"""
        details = car_data.get("details", {})
        brand = details.get("brand")
        year = details.get("year")

        if year is None:
            return False

        # Check brand-specific filter
        if brand in self.brand_year_filters:
            min_year = self.brand_year_filters[brand]
            if year < min_year:
                return False

        # Check default filter
        elif self.default_min_year is not None:
            if year < self.default_min_year:
                return False

        return True

    def _check_price_filter(self, car_data: dict) -> bool:
        """Check if car passes price filter"""
        details = car_data.get("details", {})
        price = details.get("price")

        if price is None:
            return True  # Don't reject if price is missing

        if self.min_price is not None and price < self.min_price:
            return False

        if self.max_price is not None and price > self.max_price:
            return False

        return True

    def _check_mileage_filter(self, car_data: dict) -> bool:
        """Check if car passes mileage filter"""
        details = car_data.get("details", {})
        mileage = details.get("mileage")

        if mileage is None:
            return True  # Don't reject if mileage is missing

        if self.min_mileage is not None and mileage < self.min_mileage:
            return False

        if self.max_mileage is not None and mileage > self.max_mileage:
            return False

        return True

    def passes_filters(self, car_data: dict) -> tuple[bool, str]:
        """
        Check if car data passes all filters

        Returns:
            (passes, reason) - True if passes, False otherwise with rejection reason
        """
        details = car_data.get("details", {})

        # Check for required data
        if not details:
            return False, "missing_data"

        # Year filter (most important)
        if not self._check_year_filter(car_data):
            return False, "year"

        # Price filter
        if not self._check_price_filter(car_data):
            return False, "price"

        # Mileage filter
        if not self._check_mileage_filter(car_data):
            return False, "mileage"

        return True, ""

    def filter_cars(self) -> int:
        """
        Filter cars from input file and save to output file

        Returns:
            Number of cars that passed filters
        """
        logger.info(f"Reading cars from: {self.input_file}")
        logger.info(f"Output will be saved to: {self.output_file}")
        logger.info("Applied filters:")
        logger.info(f"  Brand-year filters: {self.brand_year_filters}")
        if self.default_min_year:
            logger.info(f"  Default min year: {self.default_min_year}")
        if self.min_price or self.max_price:
            logger.info(f"  Price range: {self.min_price} - {self.max_price}")
        if self.min_mileage or self.max_mileage:
            logger.info(f"  Mileage range: {self.min_mileage} - {self.max_mileage}")

        if not self.input_file.exists():
            logger.error(f"Input file not found: {self.input_file}")
            return 0

        # Process the file
        with open(self.input_file, "r", encoding="utf-8") as infile, open(
            self.output_file, "w", encoding="utf-8"
        ) as outfile:

            for line_num, line in enumerate(infile, 1):
                try:
                    car_data = json.loads(line.strip())
                    self.stats["total"] += 1

                    passes, reason = self.passes_filters(car_data)

                    if passes:
                        outfile.write(json.dumps(car_data, ensure_ascii=False) + "\n")
                        self.stats["filtered"] += 1
                    else:
                        # Track rejection reasons
                        if reason == "year":
                            self.stats["rejected_by_year"] += 1
                        elif reason == "price":
                            self.stats["rejected_by_price"] += 1
                        elif reason == "mileage":
                            self.stats["rejected_by_mileage"] += 1
                        elif reason == "missing_data":
                            self.stats["rejected_by_missing_data"] += 1

                    # Progress logging every 1000 cars
                    if line_num % 1000 == 0:
                        logger.info(
                            f"Processed {line_num} cars, kept {self.stats['filtered']}"
                        )

                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON at line {line_num}: {e}")
                    continue
                except Exception as e:
                    logger.error(f"Error processing line {line_num}: {e}")
                    continue

        self._log_summary()
        return self.stats["filtered"]

    def _log_summary(self):
        """Log filtering summary"""
        logger.info("=" * 60)
        logger.info("FILTERING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total cars processed: {self.stats['total']}")
        logger.info(f"Cars passed filters: {self.stats['filtered']}")
        logger.info(f"Rejection breakdown:")
        logger.info(f"  - By year: {self.stats['rejected_by_year']}")
        logger.info(f"  - By price: {self.stats['rejected_by_price']}")
        logger.info(f"  - By mileage: {self.stats['rejected_by_mileage']}")
        logger.info(f"  - Missing data: {self.stats['rejected_by_missing_data']}")

        if self.stats["total"] > 0:
            pass_rate = (self.stats["filtered"] / self.stats["total"]) * 100
            logger.info(f"Pass rate: {pass_rate:.2f}%")

        logger.info(f"Output saved to: {self.output_file}")
        logger.info("=" * 60)


def main():
    """Main function for CLI usage"""
    parser = argparse.ArgumentParser(
        description="Filter car data from JSONL file based on configurable rules"
    )
    parser.add_argument("input_file", help="Path to input JSONL file with car data")
    parser.add_argument(
        "-o",
        "--output",
        help="Path to output JSONL file (auto-generated if not specified)",
    )
    parser.add_argument(
        "--min-year",
        type=int,
        help="Default minimum year for all brands (overrides config)",
    )
    parser.add_argument(
        "--min-price", type=int, help="Minimum price in 10,000 KRW units"
    )
    parser.add_argument(
        "--max-price", type=int, help="Maximum price in 10,000 KRW units"
    )
    parser.add_argument("--min-mileage", type=int, help="Minimum mileage in km")
    parser.add_argument("--max-mileage", type=int, help="Maximum mileage in km")

    args = parser.parse_args()

    # Create filter instance
    car_filter = CarDataFilter(
        input_file=args.input_file,
        output_file=args.output,
        default_min_year=args.min_year,
        min_price=args.min_price,
        max_price=args.max_price,
        min_mileage=args.min_mileage,
        max_mileage=args.max_mileage,
    )

    # Run filtering
    filtered_count = car_filter.filter_cars()

    if filtered_count > 0:
        logger.info(f"✓ Successfully filtered {filtered_count} cars")
    else:
        logger.warning("No cars passed the filters")


if __name__ == "__main__":
    main()
