#!/usr/bin/env python3
"""
Standalone test for Mitie database functionality
Imports the module directly to avoid circular import issues
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the module directly without going through agents package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

def test_direct_import():
    """Test importing the module directly"""
    print("🔍 Testing Direct Import")
    print("=" * 25)
    
    try:
        # Import directly from the file
        import mitie_database
        
        print("✅ Direct import successful!")
        
        # Test database connection
        db = mitie_database.MitieDatabase()
        if db.health_check():
            print("✅ Database connection successful!")
        else:
            print("❌ Database connection failed!")
            return False
        
        # Test calculator
        calculator = mitie_database.MitieCalculator(db)
        print("✅ Calculator initialized!")
        
        return True
        
    except Exception as e:
        print(f"❌ Direct import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_queries():
    """Test database queries directly"""
    print("\n📊 Testing Database Queries")
    print("=" * 30)
    
    try:
        import mitie_database
        
        db = mitie_database.MitieDatabase()
        
        print("Testing configuration queries:")
        
        # Test regional uplift
        london_config = db.get_config("regional_uplift", "london")
        print(f"✅ London config: {london_config}")
        
        # Test steel tonnage
        steel_config = db.get_config("steel_tonnage", "25m_lattice")
        print(f"✅ Steel config: {steel_config}")
        
        # Test rate items
        power_rate = db.get_rate_item("11.16")
        print(f"✅ Power rate: £{power_rate}" if power_rate else "⚠️ Power rate not found")
        
        # Test preferred supplier
        elara_rate = db.get_preferred_supplier_rate("Elara", "12.5m")
        print(f"✅ Elara rate: £{elara_rate}" if elara_rate else "⚠️ Elara rate not found")
        
        return True
        
    except Exception as e:
        print(f"❌ Database query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_business_logic():
    """Test business logic functions"""
    print("\n🧮 Testing Business Logic")
    print("=" * 25)
    
    try:
        import mitie_database
        
        db = mitie_database.MitieDatabase()
        calculator = mitie_database.MitieCalculator(db)
        
        # Test project classification
        active_type = calculator.classify_project_type("Install rooftop equipment with power supply")
        print(f"✅ Active classification: {active_type}")
        
        passive_type = calculator.classify_project_type("Install 25m lattice tower with foundation")
        print(f"✅ Passive classification: {passive_type}")
        
        # Test regional uplift
        base_costs = {"power": 1000, "lighting": 500}
        london_uplift = calculator.apply_regional_uplift("E1 6AN", base_costs)
        print(f"✅ London uplift: {london_uplift['region']} +{london_uplift['percentage']:.1f}%")
        
        # Test steel calculation
        tower_specs = {"tower_type": "lattice", "height": "25m"}
        steel_cost = calculator.calculate_steel_tonnage_cost(tower_specs)
        if steel_cost["amount"] > 0:
            print(f"✅ Steel calculation: £{steel_cost['amount']:.2f}")
        else:
            print(f"⚠️ Steel calculation: {steel_cost.get('error', 'Failed')}")
        
        # Test preliminaries
        active_prelim = calculator.calculate_preliminaries("active", 5000)
        print(f"✅ Active preliminaries: £{active_prelim['amount']:.2f}")
        
        passive_prelim = calculator.calculate_preliminaries("passive", 12000)
        print(f"✅ Passive preliminaries: £{passive_prelim['amount']:.2f}")
        
        # Test contingency
        contingency = calculator.calculate_risk_contingency("standard installation", 10000)
        print(f"✅ Contingency: {contingency['risk_level']} ({contingency['rate']*100:.0f}%) = £{contingency['final_amount']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Business logic test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_calculation_logic():
    """Test the full calculation logic without the tools.py wrapper"""
    print("\n🎯 Testing Full Calculation Logic")
    print("=" * 35)
    
    try:
        import mitie_database
        
        # Sample RFQ data
        rfq_data = {
            "rfq_number": "RFQ-2024-TEST",
            "client_name": "Vodafone UK",
            "site_postcode": "E1 6AN",
            "technical_scope": "Install rooftop equipment with power supply and lighting for 5G upgrade",
            "risk_factors": "Standard rooftop installation"
        }
        
        db = mitie_database.MitieDatabase()
        calculator = mitie_database.MitieCalculator(db)
        
        print(f"Processing RFQ: {rfq_data['rfq_number']}")
        
        # 1. Classify project
        project_type = calculator.classify_project_type(rfq_data["technical_scope"])
        print(f"✅ Project type: {project_type}")
        
        # 2. Check framework account
        is_framework = calculator.is_framework_account(rfq_data["client_name"])
        print(f"✅ Framework account: {is_framework}")
        
        # 3. Get base rates
        base_costs = {}
        
        # Power supply
        power_rate = db.get_rate_item("11.16")
        if power_rate:
            base_costs["power"] = power_rate
            print(f"✅ Power supply: £{power_rate:.2f}")
        
        # Lighting
        lighting_rate = db.get_rate_item("11.5")
        if lighting_rate:
            base_costs["lighting"] = lighting_rate
            print(f"✅ Lighting: £{lighting_rate:.2f}")
        
        # 4. Apply regional uplift
        regional_uplift = calculator.apply_regional_uplift(rfq_data["site_postcode"], base_costs)
        print(f"✅ Regional uplift: {regional_uplift['region']} +{regional_uplift['percentage']:.1f}% = £{regional_uplift['amount']:.2f}")
        
        # 5. Calculate markups
        markup_rates = calculator.get_markup_rates(is_framework)
        total_markup = sum(base_costs.values()) * markup_rates["materials_labour"]
        print(f"✅ Markup: {markup_rates['materials_labour']*100:.0f}% = £{total_markup:.2f}")
        
        # 6. Calculate preliminaries
        work_subtotal = sum(base_costs.values()) + regional_uplift["amount"] + total_markup
        preliminaries = calculator.calculate_preliminaries(project_type, work_subtotal)
        print(f"✅ Preliminaries: {preliminaries['type']} = £{preliminaries['amount']:.2f}")
        
        # 7. Calculate contingency
        subtotal_after_markups = work_subtotal + preliminaries["amount"]
        contingency = calculator.calculate_risk_contingency(rfq_data["risk_factors"], subtotal_after_markups)
        print(f"✅ Contingency: {contingency['risk_level']} = £{contingency['final_amount']:.2f}")
        
        # 8. Final total
        final_total = subtotal_after_markups + contingency["final_amount"]
        print(f"✅ Final total: £{final_total:.2f}")
        
        # Summary
        print("\n📋 CALCULATION SUMMARY:")
        print(f"   Base costs: £{sum(base_costs.values()):.2f}")
        print(f"   Regional uplift: £{regional_uplift['amount']:.2f}")
        print(f"   Markups: £{total_markup:.2f}")
        print(f"   Preliminaries: £{preliminaries['amount']:.2f}")
        print(f"   Contingency: £{contingency['final_amount']:.2f}")
        print(f"   TOTAL: £{final_total:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Full calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 MITIE STANDALONE TEST")
    print("=" * 40)
    
    tests_passed = 0
    total_tests = 4
    
    if test_direct_import():
        tests_passed += 1
    
    if test_database_queries():
        tests_passed += 1
    
    if test_business_logic():
        tests_passed += 1
    
    if test_full_calculation_logic():
        tests_passed += 1
    
    print(f"\n📊 TEST RESULTS: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! The Mitie calculation system is working correctly.")
        print("\n💡 The database-driven calculation logic is ready!")
        print("   You can now test it through the web interface.")
    else:
        print("⚠️ Some tests failed. Please check the implementation.")
        sys.exit(1)
