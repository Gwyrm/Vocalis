#!/usr/bin/env python3
"""
Comprehensive test suite for LLM-powered prescription parser
Tests various natural language formats to validate extraction
"""

import asyncio
import json
from voice_utils import parse_prescription_text

# Test cases covering different formats and variations
TEST_CASES = [
    # === Basic French Formats ===
    {
        "name": "Basic inline format",
        "input": "amoxicilline 500mg trois fois par jour, 7 jours",
        "expected_fields": ["medication", "dosage", "duration"]
    },
    {
        "name": "Parenthetical format",
        "input": "amoxicilline (500mg) trois fois par jour pendant 7 jours",
        "expected_fields": ["medication", "dosage", "duration"]
    },
    {
        "name": "Structured format",
        "input": "Medicament: amoxicilline\nDosage: 500mg\nFrequence: trois fois par jour\nDuree: 7 jours",
        "expected_fields": ["medication", "dosage", "duration"]
    },

    # === Different Dosage Units ===
    {
        "name": "Dosage in grams",
        "input": "paracetamol 1g deux fois par jour, 5 jours",
        "expected_fields": ["medication", "dosage", "duration"]
    },
    {
        "name": "Dosage in milliliters",
        "input": "sirop pour la toux 5ml quatre fois par jour, 10 jours",
        "expected_fields": ["medication", "dosage", "duration"]
    },
    {
        "name": "Dosage in micrograms",
        "input": "fentanyl 25mcg tous les trois jours",
        "expected_fields": ["medication", "dosage"]
    },
    {
        "name": "Dosage in drops",
        "input": "gouttes pour les yeux 2 gouttes trois fois par jour, 14 jours",
        "expected_fields": ["medication", "dosage", "duration"]
    },

    # === Different Duration Formats ===
    {
        "name": "Duration in weeks",
        "input": "azithromycine 250mg une fois par jour, 2 semaines",
        "expected_fields": ["medication", "dosage", "duration"]
    },
    {
        "name": "Duration in months",
        "input": "metformine 500mg deux fois par jour, 3 mois",
        "expected_fields": ["medication", "dosage", "duration"]
    },
    {
        "name": "Long duration",
        "input": "lisinopril 10mg chaque jour, 90 jours",
        "expected_fields": ["medication", "dosage", "duration"]
    },

    # === Complex Instructions ===
    {
        "name": "With meals instruction",
        "input": "amoxicilline 500mg trois fois par jour avec les repas, 7 jours",
        "expected_fields": ["medication", "dosage", "duration", "special_instructions"]
    },
    {
        "name": "Without meals instruction",
        "input": "metronidazole 250mg trois fois par jour a jeun, 7 jours",
        "expected_fields": ["medication", "dosage", "duration", "special_instructions"]
    },
    {
        "name": "Multiple instructions",
        "input": "warfarine 5mg chaque soir, 30 jours, eviter l'alcool, ne pas combiner avec aspirine",
        "expected_fields": ["medication", "dosage", "duration", "special_instructions"]
    },
    {
        "name": "Bedtime instruction",
        "input": "loratadine 10mg avant le coucher, 30 jours",
        "expected_fields": ["medication", "dosage", "duration", "special_instructions"]
    },

    # === Variations and Typos ===
    {
        "name": "Missing spaces",
        "input": "amoxicilline500mg3xpar jour 7jours",
        "expected_fields": ["medication", "dosage", "duration"]
    },
    {
        "name": "Extra punctuation",
        "input": "amoxicilline... 500mg!!! trois fois par jour... 7 jours!!!",
        "expected_fields": ["medication", "dosage", "duration"]
    },
    {
        "name": "Mixed case",
        "input": "AMOXICILLINE 500MG Trois fois par jour, 7 JOURS",
        "expected_fields": ["medication", "dosage", "duration"]
    },
    {
        "name": "With patient name",
        "input": "Patient Jean Dupont: amoxicilline 500mg trois fois par jour, 7 jours",
        "expected_fields": ["patient_name", "medication", "dosage", "duration"]
    },

    # === Medical Abbreviations ===
    {
        "name": "With abbreviations",
        "input": "Rx: amoxicilline 500mg x3/jour x 7j",
        "expected_fields": ["medication", "dosage", "duration"]
    },
    {
        "name": "With slash notation",
        "input": "amoxicilline 500mg 3x/jour 7 jours",
        "expected_fields": ["medication", "dosage", "duration"]
    },

    # === Natural Language Variations ===
    {
        "name": "Natural language 1",
        "input": "Prescrire de l'amoxicilline a dose de 500 milligrammes, trois fois par jour avec repas, durant une semaine",
        "expected_fields": ["medication", "dosage", "duration"]
    },
    {
        "name": "Natural language 2",
        "input": "Prendre 500mg d'amoxicilline matin midi et soir pendant sept jours",
        "expected_fields": ["medication", "dosage", "duration"]
    },
    {
        "name": "Doctor's shorthand",
        "input": "Amoxi 500 x3 qd x7d",
        "expected_fields": ["medication", "dosage", "duration"]
    },

    # === Edge Cases ===
    {
        "name": "Zero dosage (should be invalid)",
        "input": "amoxicilline 00mg trois fois par jour, 7 jours",
        "expected_fields": ["medication", "dosage", "duration"],
        "should_be_invalid": True
    },
    {
        "name": "Zero value (should be invalid)",
        "input": "amoxicilline 0mg trois fois par jour, 7 jours",
        "expected_fields": ["medication", "dosage", "duration"],
        "should_be_invalid": True
    },
    {
        "name": "Missing dosage",
        "input": "amoxicilline trois fois par jour, 7 jours",
        "expected_fields": ["medication", "duration"],
        "should_be_invalid": True
    },
    {
        "name": "Missing medication",
        "input": "500mg trois fois par jour, 7 jours",
        "expected_fields": ["dosage", "duration"],
        "should_be_invalid": True
    },

    # === Real-world Examples ===
    {
        "name": "Real prescription 1",
        "input": "Amoxicilline 500mg à prendre 3 fois par jour avec les repas pendant 7 jours. En cas d'allergie à la pénicilline, contacter le médecin.",
        "expected_fields": ["medication", "dosage", "duration", "special_instructions"]
    },
    {
        "name": "Real prescription 2",
        "input": "Ibuprofen 400mg tous les 6-8 heures au besoin pour la douleur. Ne pas dépasser 3200mg par jour. Maximum 10 jours sans avis medical.",
        "expected_fields": ["medication", "dosage", "special_instructions"]
    },
    {
        "name": "Real prescription 3",
        "input": "Metformine 500mg deux fois par jour avec les repas. Augmenter graduellement a 1000mg deux fois par jour apres une semaine selon tolerance.",
        "expected_fields": ["medication", "dosage", "special_instructions"]
    },
    {
        "name": "Real prescription 4",
        "input": "Lisinopril 10mg chaque matin pour l'hypertension. Continu. Faire controler tension arterielle regulierement.",
        "expected_fields": ["medication", "dosage", "special_instructions"]
    },
]


async def run_tests():
    """Run all test cases and report results"""
    print("=" * 80)
    print("LLM PRESCRIPTION PARSER TEST SUITE".center(80))
    print("=" * 80)
    print()

    results = {
        "total": len(TEST_CASES),
        "passed": 0,
        "failed": 0,
        "errors": []
    }

    for i, test_case in enumerate(TEST_CASES, 1):
        test_name = test_case["name"]
        test_input = test_case["input"]
        expected_fields = test_case["expected_fields"]
        should_be_invalid = test_case.get("should_be_invalid", False)

        print(f"Test {i}/{len(TEST_CASES)}: {test_name}")
        print(f"  Input: {test_input[:70]}{'...' if len(test_input) > 70 else ''}")

        try:
            parsed = await parse_prescription_text(test_input)

            # Check if required fields are present
            missing_fields = []
            for field in expected_fields:
                if field not in parsed:
                    missing_fields.append(field)
                elif parsed[field] is None and field in ["medication", "dosage"]:
                    missing_fields.append(f"{field} (null)")

            # Check for zero dosage validation
            has_zero_dosage = False
            if parsed.get("dosage"):
                import re
                dosage_num = re.search(r'(\d+)', parsed["dosage"])
                if dosage_num and int(dosage_num.group(1)) == 0:
                    has_zero_dosage = True

            # Determine pass/fail
            if should_be_invalid:
                # These tests should have missing or invalid fields
                if missing_fields or has_zero_dosage:
                    status = "✓ PASS"
                    results["passed"] += 1
                    print(f"  Status: {status} (correctly identified as invalid)")
                else:
                    status = "✗ FAIL"
                    results["failed"] += 1
                    print(f"  Status: {status} (should be invalid but wasn't)")
            else:
                if missing_fields:
                    status = "✗ FAIL"
                    results["failed"] += 1
                    print(f"  Status: {status}")
                    print(f"  Missing: {', '.join(missing_fields)}")
                elif has_zero_dosage:
                    status = "⚠ WARN"
                    results["failed"] += 1
                    print(f"  Status: {status} (invalid dosage: zero value)")
                else:
                    status = "✓ PASS"
                    results["passed"] += 1
                    print(f"  Status: {status}")

            # Print parsed output
            print(f"  Output:")
            for key, value in parsed.items():
                if value:
                    display_value = value if len(str(value)) <= 60 else str(value)[:57] + "..."
                    print(f"    - {key}: {display_value}")

        except Exception as e:
            status = "✗ ERROR"
            results["failed"] += 1
            results["errors"].append((test_name, str(e)))
            print(f"  Status: {status}")
            print(f"  Error: {str(e)}")

        print()

    # Summary
    print("=" * 80)
    print("TEST SUMMARY".center(80))
    print("=" * 80)
    print(f"Total Tests:   {results['total']}")
    print(f"Passed:        {results['passed']} ✓")
    print(f"Failed:        {results['failed']} ✗")
    print(f"Success Rate:  {(results['passed'] / results['total'] * 100):.1f}%")

    if results["errors"]:
        print()
        print("ERRORS:")
        for test_name, error in results["errors"]:
            print(f"  - {test_name}: {error}")

    print()
    print("=" * 80)

    return results


if __name__ == "__main__":
    try:
        results = asyncio.run(run_tests())
        exit(0 if results["failed"] == 0 else 1)
    except Exception as e:
        print(f"\n✗ Fatal Error: {e}")
        print("\nMake sure Ollama is running:")
        print("  ollama serve")
        exit(1)
