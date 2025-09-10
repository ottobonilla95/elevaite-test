"""
Mitie Database Integration Module

This module provides database access and business logic for Mitie quote calculations.
It implements the Elevate Logic Queries requirements with proper separation of concerns.
"""

import json
import logging
import os
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logger = logging.getLogger(__name__)


class MitieDatabase:
    """
    Database access layer for Mitie rate card data.
    
    Handles all SQL queries and database connections for the Mitie calculation system.
    """
    
    def __init__(self, db_url: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            db_url: Database URL. If None, will try to get from environment variables.
        """
        if not db_url:
            db_url = self._get_db_url_from_env()
        
        try:
            self.engine = create_engine(db_url, pool_pre_ping=True)
            logger.info("Mitie database connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise
    
    def _get_db_url_from_env(self) -> str:
        """Get database URL from environment variables with fallbacks."""
        # First try the dedicated Mitie database URL
        db_url = os.getenv("MITIE_DB_URL")

        if not db_url:
            # Fallback to agent studio database URL
            db_url = os.getenv("AGENT_STUDIO_DATABASE_URL")

        if not db_url:
            db_url = os.getenv("DATABASE_URL")
        
        if not db_url:
            # Fallback to individual components - use mitie_db as default database
            host = os.getenv("DB_HOST", "localhost")
            port = os.getenv("DB_PORT", "5432")
            database = os.getenv("DB_NAME", "mitie_db")  # Default to mitie_db for Mitie tools
            username = os.getenv("DB_USER", "postgres")
            password = os.getenv("DB_PASSWORD", "12345")

            db_url = f"postgresql://{username}:{password}@{host}:{port}/{database}"
        
        return db_url
    
    def get_config(self, config_type: str, config_key: str) -> Dict[str, Any]:
        """
        Get configuration from mitie_config table.
        
        Args:
            config_type: Type of configuration (e.g., 'steel_tonnage', 'regional_uplift')
            config_key: Specific configuration key (e.g., '25m_lattice', 'london')
            
        Returns:
            Configuration dictionary or empty dict if not found
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT config_value
                        FROM mitie_config
                        WHERE config_type = :type AND config_key = :key AND (is_active = true OR is_active IS NULL)
                    """),
                    {"type": config_type, "key": config_key}
                )
                row = result.fetchone()

                if row:
                    config_value = row[0]
                    # If it's already a dict/list (from JSON column), return as-is
                    if isinstance(config_value, (dict, list)):
                        return config_value
                    # If it's a string, parse it as JSON
                    elif isinstance(config_value, str):
                        return json.loads(config_value)
                    else:
                        # For other types (int, float, bool), return as-is
                        return config_value
                else:
                    logger.warning(f"Configuration not found: {config_type}.{config_key}")
                    return {}
                    
        except (SQLAlchemyError, json.JSONDecodeError) as e:
            logger.error(f"Error getting config {config_type}.{config_key}: {e}")
            return {}
    
    def get_rate_item(self, item_code: str) -> Optional[float]:
        """
        Get rate from mitie_rate_items table.
        
        Args:
            item_code: Item code (e.g., '11.16', '1.01')
            
        Returns:
            Rate as float or None if not found
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT rate
                        FROM mitie_rate_items
                        WHERE item_code = :code AND (is_active = true OR is_active IS NULL)
                        LIMIT 1
                    """),
                    {"code": item_code}
                )
                row = result.fetchone()
                
                if row:
                    return float(row[0])
                else:
                    logger.warning(f"Rate item not found: {item_code}")
                    return None
                    
        except (SQLAlchemyError, ValueError) as e:
            logger.error(f"Error getting rate item {item_code}: {e}")
            return None
    
    def get_rate_items_by_category(self, category: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get rate items by category.
        
        Args:
            category: Category name (e.g., 'preliminaries', 'power_lighting')
            limit: Maximum number of items to return
            
        Returns:
            List of rate item dictionaries
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT item_code, description, rate, unit_type
                        FROM mitie_rate_items
                        WHERE category = :category AND (is_active = true OR is_active IS NULL)
                        ORDER BY item_code
                        LIMIT :limit
                    """),
                    {"category": category, "limit": limit}
                )
                
                return [
                    {
                        "item_code": row[0],
                        "description": row[1],
                        "rate": float(row[2]),
                        "unit_type": row[3]
                    }
                    for row in result
                ]
                
        except SQLAlchemyError as e:
            logger.error(f"Error getting rate items for category {category}: {e}")
            return []
    
    def get_preferred_supplier_rate(self, product_type: str, specifications: str) -> Optional[float]:
        """
        Get preferred supplier rate.
        
        Args:
            product_type: Product type (e.g., 'Elara', 'TSC', 'Lancaster')
            specifications: Product specifications to match
            
        Returns:
            Rate as float or None if not found
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT rate 
                        FROM mitie_preferred_items 
                        WHERE product_type = :type 
                        AND (specifications ILIKE :specs OR description ILIKE :specs)
                        AND (is_active = true OR is_active IS NULL)
                        ORDER BY rate
                        LIMIT 1
                    """),
                    {"type": product_type, "specs": f"%{specifications}%"}
                )
                row = result.fetchone()
                
                if row:
                    return float(row[0])
                else:
                    logger.warning(f"Preferred supplier item not found: {product_type} - {specifications}")
                    return None
                    
        except (SQLAlchemyError, ValueError) as e:
            logger.error(f"Error getting preferred supplier rate {product_type} - {specifications}: {e}")
            return None
    
    def search_rate_items(self, search_term: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search rate items by description.
        
        Args:
            search_term: Term to search for in descriptions
            limit: Maximum number of results
            
        Returns:
            List of matching rate items
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(
                    text("""
                        SELECT item_code, description, rate, category, unit_type
                        FROM mitie_rate_items 
                        WHERE description ILIKE :search AND (is_active = true OR is_active IS NULL)
                        ORDER BY rate
                        LIMIT :limit
                    """),
                    {"search": f"%{search_term}%", "limit": limit}
                )
                
                return [
                    {
                        "item_code": row[0],
                        "description": row[1],
                        "rate": float(row[2]),
                        "category": row[3],
                        "unit_type": row[4]
                    }
                    for row in result
                ]
                
        except SQLAlchemyError as e:
            logger.error(f"Error searching rate items for '{search_term}': {e}")
            return []
    
    def health_check(self) -> bool:
        """
        Check if database connection is healthy.
        
        Returns:
            True if database is accessible, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.fetchone() is not None
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


class MitieCalculationError(Exception):
    """Custom exception for Mitie calculation errors."""
    pass


class MitieCalculator:
    """
    Business logic layer for Mitie quote calculations.
    
    Implements the Elevate Logic Queries requirements for quote generation.
    """
    
    # Project classification keywords
    ACTIVE_KEYWORDS = ["rooftop", "enclosure", "lighting", "power supply", "antenna", "equipment"]
    PASSIVE_KEYWORDS = ["monopole", "lattice", "foundation", "steelwork", "concrete", "civil"]
    
    # Risk classification keywords
    CRITICAL_RISK_KEYWORDS = ["lattice tower", "remote highlands", "unknown ground", "challenging access"]
    RISK_ALERT_KEYWORDS = ["crane hire", "removal dependency", "complex installation"]
    
    def __init__(self, db: MitieDatabase):
        """
        Initialize calculator with database connection.
        
        Args:
            db: MitieDatabase instance
        """
        self.db = db
        logger.info("Mitie calculator initialized")
    
    def classify_project_type(self, technical_scope: str) -> str:
        """
        Classify project as active, passive, or mixed based on technical scope.
        
        Args:
            technical_scope: Technical scope description from RFQ
            
        Returns:
            Project type: 'active', 'passive', or 'mixed'
        """
        if not technical_scope:
            logger.warning("Empty technical scope provided, defaulting to 'mixed'")
            return "mixed"
        
        scope_lower = technical_scope.lower()
        
        has_active = any(keyword in scope_lower for keyword in self.ACTIVE_KEYWORDS)
        has_passive = any(keyword in scope_lower for keyword in self.PASSIVE_KEYWORDS)
        
        if has_active and has_passive:
            project_type = "mixed"
        elif has_active:
            project_type = "active"
        elif has_passive:
            project_type = "passive"
        else:
            project_type = "mixed"  # Default to mixed if unclear
        
        logger.info(f"Project classified as: {project_type}")
        return project_type

    def calculate_steel_tonnage_cost(self, tower_specs: Dict[str, str]) -> Dict[str, Any]:
        """
        Calculate steel cost with engineering validation flag.

        Args:
            tower_specs: Dictionary with 'tower_type' and 'height' keys

        Returns:
            Dictionary with steel cost calculation details
        """
        tower_type = tower_specs.get("tower_type", "").lower()
        height = tower_specs.get("height", "").lower()

        if not tower_type or not height:
            logger.warning("Incomplete tower specifications provided")
            return {
                "amount": 0,
                "validation_required": True,
                "error": "Incomplete tower specifications"
            }

        # Construct database key
        steel_key = f"{height}_{tower_type}"
        steel_config = self.db.get_config("steel_tonnage", steel_key)

        # If monopole config not found, try lattice as fallback (monopoles often use lattice tonnage)
        if not steel_config and tower_type == "monopole":
            fallback_key = f"{height}_lattice"
            steel_config = self.db.get_config("steel_tonnage", fallback_key)
            if steel_config:
                logger.info(f"Using lattice configuration as fallback for monopole: {fallback_key}")
                steel_key = fallback_key

        if not steel_config:
            logger.warning(f"Steel tonnage configuration not found for: {steel_key}")
            return {
                "amount": 0,
                "validation_required": True,
                "error": f"Unknown tower specification: {height} {tower_type}"
            }

        tonnage = steel_config.get("tonnage", 0)
        rate_per_tonne = steel_config.get("rate_per_tonne", 1200)

        if tonnage <= 0:
            logger.warning(f"Invalid tonnage configuration: {tonnage}")
            return {
                "amount": 0,
                "validation_required": True,
                "error": "Invalid tonnage configuration"
            }

        base_cost = tonnage * rate_per_tonne
        marked_up_cost = base_cost * 1.20  # +20% markup as per Elevate Logic

        result = {
            "tonnage": tonnage,
            "rate_per_tonne": rate_per_tonne,
            "base_cost": base_cost,
            "marked_up_cost": marked_up_cost,
            "amount": marked_up_cost,
            "validation_required": True,  # Always flag for engineering validation
            "description": f"{height.title()} {tower_type.title()} Tower - {tonnage} tonnes",
            "markup_rate": 0.20
        }

        logger.info(f"Steel tonnage calculated: {tonnage}t × £{rate_per_tonne} = £{marked_up_cost:.2f}")
        return result

    def apply_regional_uplift(self, postcode: str, base_costs: Dict[str, float]) -> Dict[str, Any]:
        """
        Apply regional uplift to all cost categories.

        Args:
            postcode: Site postcode
            base_costs: Dictionary of base costs by category

        Returns:
            Dictionary with regional uplift details
        """
        if not postcode or not base_costs:
            return {
                "region": "Unknown",
                "percentage": 0,
                "amount": 0,
                "applied_to": "none"
            }

        # Extract postcode prefix - try 2 chars first, then 1 char
        postcode_clean = postcode.upper().strip()
        postcode_prefix_2 = postcode_clean[:2] if len(postcode_clean) >= 2 else postcode_clean
        postcode_prefix_1 = postcode_clean[:1] if len(postcode_clean) >= 1 else ""

        # Check London/South East (+10%)
        london_config = self.db.get_config("regional_uplift", "london")
        london_postcodes = london_config.get("postcodes", []) if london_config else []

        # Try 2-character prefix first (for EC, NW, SE, SW, WC), then 1-character (for E, N, W)
        is_london = (postcode_prefix_2 in london_postcodes) or (postcode_prefix_1 in london_postcodes)

        if london_config and is_london:
            uplift_rate = london_config.get("uplift", 0.10)
            region = "London/South East"
        else:
            # Check Remote/Rural (+12-15%)
            remote_config = self.db.get_config("regional_uplift", "remote")
            remote_postcodes = remote_config.get("postcodes", []) if remote_config else []

            # Add IV (Inverness) to remote postcodes if not already there
            if "IV" not in remote_postcodes:
                remote_postcodes.append("IV")

            # Try 2-character prefix first, then 1-character for remote areas
            is_remote = (postcode_prefix_2 in remote_postcodes) or (postcode_prefix_1 in remote_postcodes)

            if remote_config and is_remote:
                # Use maximum uplift for remote areas
                uplift_rate = remote_config.get("uplift_max", remote_config.get("uplift", 0.15))
                region = "Remote/Rural"
            else:
                # Yorkshire/Midlands/Standard (0%)
                uplift_rate = 0.0
                region = "Yorkshire/Midlands"

        # Apply uplift to all cost categories
        total_base = sum(base_costs.values())
        uplift_amount = total_base * uplift_rate

        result = {
            "region": region,
            "percentage": uplift_rate * 100,
            "amount": uplift_amount,
            "applied_to": "all_categories",
            "postcode": postcode
        }

        logger.info(f"Regional uplift applied: {region} +{uplift_rate*100:.1f}% = £{uplift_amount:.2f}")
        return result

    def calculate_preliminaries(self, project_type: str, work_subtotal: float) -> Dict[str, Any]:
        """
        Calculate preliminaries based on project type and work subtotal.

        Args:
            project_type: 'active', 'passive', or 'mixed'
            work_subtotal: Work subtotal before preliminaries

        Returns:
            Dictionary with preliminaries calculation details
        """
        if project_type == "active":
            # Active works: fixed amount
            active_config = self.db.get_config("preliminaries", "active_fixed")
            amount = active_config.get("amount", 2258.53)

            result = {
                "type": "active_fixed",
                "amount": amount,
                "basis": "Active works fixed rate",
                "work_subtotal": work_subtotal
            }

            logger.info(f"Active preliminaries applied: £{amount:.2f}")
            return result

        else:
            # Passive/Mixed works: banded calculation
            passive_config = self.db.get_config("preliminaries", "passive_bands")
            bands = passive_config.get("bands", [])
            cap = passive_config.get("cap", 7500)

            if not bands:
                logger.warning("No passive preliminaries bands configured, using fallback")
                return {
                    "type": "passive_fallback",
                    "amount": 2258.53,
                    "basis": "Fallback minimum",
                    "work_subtotal": work_subtotal
                }

            # Find appropriate band
            for band in bands:
                if band["min"] <= work_subtotal <= band["max"]:
                    calculated_amount = band["amount"]
                    final_amount = min(calculated_amount, cap)

                    result = {
                        "type": "passive_banded",
                        "work_subtotal": work_subtotal,
                        "band": f"£{band['min']:,}-{band['max']:,}",
                        "calculated_amount": calculated_amount,
                        "amount": final_amount,
                        "cap_applied": calculated_amount > cap,
                        "cap_amount": cap
                    }

                    logger.info(f"Passive preliminaries: £{work_subtotal:.2f} → {result['band']} → £{final_amount:.2f}")
                    return result

            # If over highest band, calculate proportionally but cap
            if work_subtotal > 20000:
                # Proportional calculation based on highest band
                base_rate = 3776 / 20000  # Rate from highest band
                calculated_amount = work_subtotal * base_rate
                final_amount = min(calculated_amount, cap)

                result = {
                    "type": "passive_banded",
                    "work_subtotal": work_subtotal,
                    "band": "£20k+",
                    "calculated_amount": calculated_amount,
                    "amount": final_amount,
                    "cap_applied": calculated_amount > cap,
                    "cap_amount": cap
                }

                logger.info(f"Passive preliminaries (over £20k): £{work_subtotal:.2f} → £{final_amount:.2f} (capped)")
                return result

            # Fallback to minimum
            logger.warning(f"No suitable preliminaries band found for £{work_subtotal:.2f}, using minimum")
            return {
                "type": "passive_fallback",
                "amount": 2258.53,
                "basis": "Fallback minimum",
                "work_subtotal": work_subtotal
            }

    def get_markup_rates(self, is_framework_account: bool = False) -> Dict[str, float]:
        """
        Get markup rates with framework account adjustments.

        Args:
            is_framework_account: Whether client is on framework agreement

        Returns:
            Dictionary of markup rates by category
        """
        markup_config = self.db.get_config("markup_rates", "standard")

        # Default rates if config not found
        base_rates = {
            "materials_labour": markup_config.get("materials_labour", 0.20),
            "subcontractors": markup_config.get("subcontractors", 0.15),
            "preferred_supplier": markup_config.get("preferred_supplier", 0.19)
        }

        # Apply framework reduction if applicable
        if is_framework_account:
            framework_config = self.db.get_config("markup_rates", "framework_reduction")
            reduction = framework_config.get("reduction", 0.10)

            # Apply 10% reduction across all categories
            adjusted_rates = {
                category: rate * (1 - reduction)
                for category, rate in base_rates.items()
            }

            logger.info(f"Framework account markup reduction applied: -{reduction*100:.0f}%")
            return adjusted_rates

        return base_rates

    def calculate_risk_contingency(self, risk_factors: str, subtotal_after_markups: float) -> Dict[str, Any]:
        """
        Calculate risk-based contingency with cap.

        Args:
            risk_factors: Risk factors description from RFQ
            subtotal_after_markups: Subtotal after markups and preliminaries

        Returns:
            Dictionary with contingency calculation details
        """
        if not risk_factors:
            risk_factors = ""

        risk_factors_lower = risk_factors.lower()

        # Determine risk level based on keywords
        if any(keyword in risk_factors_lower for keyword in self.CRITICAL_RISK_KEYWORDS):
            risk_level = "critical"
            rate = 0.15
        elif any(keyword in risk_factors_lower for keyword in self.RISK_ALERT_KEYWORDS):
            risk_level = "risk_alert"
            rate = 0.10
        else:
            risk_level = "standard"
            rate = 0.05

        # Get contingency cap from config
        cap_config = self.db.get_config("contingency_rules", "cap_amount")
        cap_amount = cap_config if isinstance(cap_config, (int, float)) else 25000

        # Calculate contingency
        calculated_amount = subtotal_after_markups * rate
        final_amount = min(calculated_amount, cap_amount)

        result = {
            "risk_level": risk_level,
            "rate": rate,
            "calculated_amount": calculated_amount,
            "final_amount": final_amount,
            "cap_applied": calculated_amount > cap_amount,
            "cap_amount": cap_amount,
            "subtotal_base": subtotal_after_markups
        }

        logger.info(f"Contingency calculated: {risk_level} ({rate*100:.0f}%) = £{final_amount:.2f}")
        if result["cap_applied"]:
            logger.info(f"Contingency cap applied: £{calculated_amount:.2f} → £{final_amount:.2f}")

        return result

    def is_framework_account(self, client_name: str) -> bool:
        """
        Check if client is a framework account.

        Args:
            client_name: Client name from RFQ

        Returns:
            True if client is on framework agreement
        """
        if not client_name:
            return False

        framework_accounts = self.db.get_config("framework_accounts", "list")

        if not framework_accounts:
            logger.warning("No framework accounts configured")
            return False

        client_name_lower = client_name.lower()

        # Check if any framework account name is contained in client name
        for account in framework_accounts:
            if account.lower() in client_name_lower:
                logger.info(f"Framework account detected: {account}")
                return True

        return False

    def extract_tower_specifications(self, technical_scope: str) -> Dict[str, str]:
        """
        Extract tower specifications from technical scope.

        Args:
            technical_scope: Technical scope description

        Returns:
            Dictionary with tower_type and height
        """
        if not technical_scope:
            return {"tower_type": "", "height": ""}

        scope_lower = technical_scope.lower()

        # Extract tower type
        tower_type = ""
        if "lattice" in scope_lower:
            tower_type = "lattice"
        elif "monopole" in scope_lower:
            tower_type = "monopole"
        elif "guyed" in scope_lower:
            tower_type = "guyed"

        # Extract height - look for tower height specifically, not foundation dimensions
        height = ""
        import re

        print(f"DEBUG: Extracting tower height from: {scope_lower[:200]}...")

        # Look for tower height patterns - prioritize "tower" context
        tower_height_patterns = [
            r'(\d+)\s*m\s+lattice\s+tower',  # "30m lattice tower"
            r'(\d+)\s*m\s+lattice\s+structure',  # "30m lattice structure"
            r'(\d+)\s*m\s+tower',            # "30m tower"
            r'tower.*?(\d+)\s*m',            # "tower ... 30m"
            r'(\d+)\s*m(?:etre)?s?\s+(?:lattice|monopole|guyed)',  # "30m lattice"
            r'tower\s+height:\s*(\d+)\s*m',  # "Tower Height: 30m"
            r'height:\s*(\d+)\s*m\s+lattice',  # "Height: 30m lattice"
        ]

        for i, pattern in enumerate(tower_height_patterns):
            height_match = re.search(pattern, scope_lower)
            if height_match:
                height_value = height_match.group(1)
                height = f"{height_value}m"
                print(f"DEBUG: Found height '{height}' using pattern {i+1}: {pattern}")
                break

        # Fallback to any height if no tower-specific height found, but exclude foundation dimensions
        if not height:
            # Look for heights but exclude foundation context
            all_height_matches = re.findall(r'(\d+(?:\.\d+)?)\s*m(?:etre)?s?', scope_lower)
            print(f"DEBUG: All height matches found: {all_height_matches}")

            for height_value in all_height_matches:
                height_float = float(height_value)
                # Only use if it's a reasonable tower height (15m-50m) and not foundation size (1-5m)
                if 15 <= height_float <= 50:
                    height = f"{height_value}m"
                    print(f"DEBUG: Using fallback height: {height}")
                    break

        result = {"tower_type": tower_type, "height": height}

        if tower_type and height:
            logger.info(f"Tower specifications extracted: {height} {tower_type}")
        else:
            logger.warning(f"Could not extract complete tower specifications from: {technical_scope[:100]}...")

        return result

    def validate_calculation_inputs(self, rfq_data: Dict[str, Any]) -> List[str]:
        """
        Validate RFQ data for calculation requirements.

        Args:
            rfq_data: RFQ data dictionary

        Returns:
            List of validation warnings/errors
        """
        warnings = []

        # Check required fields
        required_fields = ["technical_scope"]
        for field in required_fields:
            if not rfq_data.get(field):
                warnings.append(f"Missing required field: {field}")

        # Check optional but important fields
        if not rfq_data.get("site_postcode"):
            warnings.append("No postcode provided - regional uplift cannot be applied")

        if not rfq_data.get("client_name"):
            warnings.append("No client name provided - framework account detection disabled")

        # Validate postcode format if provided
        postcode = rfq_data.get("site_postcode", "")
        if postcode and len(postcode) < 2:
            warnings.append("Invalid postcode format - regional uplift may be incorrect")

        return warnings
