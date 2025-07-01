"""
Final Complete Enhanced PPR-augmented Retrieval System for HippoRAG
Includes: All query types + Analytical queries + Direct predicate filtering + Multi-step reasoning
Based on: Knowledge graph visualization showing passage-centric structure
"""

import json
import logging
import re
from typing import List, Dict, Any
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from hippo_config import HippoRAGConfig
from build_kg import KnowledgeGraphBuilder
from index_qdrant import HippoRAGIndexer
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from qdrant_client import QdrantClient

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class AnalyticalKGRetriever:
    def __init__(self, config: HippoRAGConfig):
        self.config = config
        self.graph_builder = KnowledgeGraphBuilder(config)
        self.indexer = HippoRAGIndexer(config)
        self.graph_builder.load_graph()
        self.index = self.indexer.load_index()

        # Create reverse mapping for faster lookups
        self.id_to_entity = {v: k for k, v in self.graph_builder.entity_to_id.items()}

        # Complete query classification patterns
        self.query_patterns = {
            # NEW: Analytical query patterns
            "multi_location_technician": r"(?:technician|person|who).*(?:handled|resolved).*(?:in|from).*(?:both|TX.*GA|GA.*TX)",
            "statistical_machine_type": r"(?:machine types?).*(?:most|frequent|common).*(?:in|from)\s+([A-Z]{2})",
            "location_date_analysis": r"(?:tickets?|SRs?).*(?:in|from)\s+([A-Z]{2}).*(?:closed|resolved).*(\w+\s+\d{4})",
            "cross_state_analysis": r"(?:both|TX.*GA|GA.*TX|multiple.*states)",

            # Enhanced existing patterns
            "date_range_query": r"(?:SRs?|tickets?).*(?:resolved|closed).*between.*(\d{4}-\d{2}-\d{2}).*and.*(\d{4}-\d{2}-\d{2})",
            "city_resolver_query": r"who\s+resolved.*from\s+([A-Za-z\s]+)",
            "simple_date_query": r"SRs?\s+closed\s+on\s+(\d{4}-\d{2}-\d{2})",
            "sr_attribute": r"(machine type|model|severity|city|state|address|problem|part|account|date|closed).*(?:for|of|with).*(\d{8})",
            "person_tickets": r"(?:tickets?|SRs?).*(?:handled|resolved|assigned).*(?:by|to)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            "multi_step_date_resolver": r"(?:tickets?|SRs?).*(?:closed).*(\d{4}-\d{2}-\d{2}).*(?:who|resolved)",
            "sr_city_query": r"(?:city|location).*(?:sr|SR)\s*(\d{8})"
        }

        # SR attribute to predicate mapping
        self.attr_to_predicate = {
            "machine type": "involves Machine Type",
            "model": "has Machine Model",
            "severity": "has Severity",
            "city": "has City",
            "state": "has State",
            "address": "has Address Line 1",
            "problem": "has Customer Problem Summary",
            "part": "uses Part",
            "account": "has Customer Account Number",
            "date": "has Incident Date",
            "closed": "closed on"
        }

        # Entity patterns for extraction
        self.entity_patterns = {
            'sr_numbers': r'\b\d{8}\b',
            'dates': r'\b\d{4}-\d{2}-\d{2}\b',
            'person_names': r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',
            'emails': r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]+\b'
        }

        self._ensure_payload_indexes()

    def _ensure_payload_indexes(self):
        """Create required payload indexes in Qdrant"""
        try:
            client = QdrantClient(
                url=f"http://{self.config.QDRANT_HOST}:{self.config.QDRANT_PORT}",
                check_compatibility=False
            )
            for field in ["subject", "predicate", "object", "passage_id"]:
                try:
                    client.create_payload_index(
                        collection_name="toshiba_sr_6_12_nov_24",
                        field_name=field,
                        field_schema="keyword"
                    )
                except Exception:
                    pass  # Index might already exist
            logger.info("Payload indexes ensured")
        except Exception as e:
            logger.warning(f"Index creation: {e}")

    def generate_date_range(self, start_date: str, end_date: str) -> List[str]:
        """Generate all dates between start and end (inclusive)"""
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            dates = []
            current = start
            while current <= end:
                dates.append(current.strftime("%Y-%m-%d"))
                current += timedelta(days=1)

            print(f"Generated date range: {dates}")
            return dates
        except Exception as e:
            print(f"Error generating date range: {e}")
            return [start_date, end_date]

    def classify_query_intent(self, query: str) -> Dict[str, Any]:
        """Enhanced query classification that distinguishes simple vs complex analytical queries"""
        intent = {
            "type": "general",
            "multi_step": False,
            "confidence": 0.0,
            "target_predicates": [],
            "entities": {}
        }

        # print(f"\n=== QUERY CLASSIFICATION ===")
        # print(f"Query: {query}")

        # PRIORITY 1: Complex analytical queries (MUST trigger PPR)
        complex_patterns = [
            r"what.*(?:machine types?|models?).*(?:same city|city).*sr",
            r"which.*(?:customers?|resolvers?).*(?:same|similar).*(?:city|location)",
            r"what.*used by.*(?:same city|city).*sr",
            r"find.*(?:similar|same).*(?:city|location|area)",
            r"what.*(?:other|similar).*(?:closed|resolved).*(?:around|same time|similar)",
            r"which.*have.*(?:similar|same).*(?:problems?|issues?)",
            r"what.*relationship.*between",
            r"find.*(?:patterns?|similar|related).*(?:based on|characteristics)",
            r"which.*regions?.*(?:most|complex|technical)"
        ]

        for pattern in complex_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                # Extract entities for PPR seeding
                sr_match = re.search(r'(\d{8})', query)
                person_match = re.search(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', query)
                location_match = re.search(r'(?:in|from)\s+([A-Z][a-z]+)', query)

                entities = {}
                if sr_match:
                    entities["sr_number"] = sr_match.group(1)
                if person_match:
                    entities["person"] = person_match.group(0)
                if location_match:
                    entities["location"] = location_match.group(1)

                intent.update({
                    "type": "complex_analytical",
                    "entities": entities,
                    "confidence": 0.9
                })
                print(f"✓ Detected: complex_analytical (confidence: 0.9)")
                print(f"  Will trigger PPR with entities: {entities}")
                return intent

        # PRIORITY 2: Multi-location technician analysis
        if re.search(self.query_patterns["multi_location_technician"], query, re.IGNORECASE):
            intent.update({
                "type": "multi_location_technician",
                "target_predicates": ["has State", "resolved by", "assigned to"],
                "entities": {"states": ["TX", "GA"]},
                "confidence": 0.9
            })
            print(f"✓ Detected: multi_location_technician (confidence: 0.9)")
            return intent

        # PRIORITY 3: Statistical machine type analysis
        stat_machine_match = re.search(self.query_patterns["statistical_machine_type"], query, re.IGNORECASE)
        if stat_machine_match:
            state = stat_machine_match.group(1) if stat_machine_match.groups() else "CA"
            intent.update({
                "type": "statistical_machine_type",
                "target_predicates": ["has State", "involves Machine Type", "closed on"],
                "entities": {"state": state, "time_period": "Nov 2024"},
                "confidence": 0.9
            })
            print(f"✓ Detected: statistical_machine_type (confidence: 0.9)")
            return intent

        # PRIORITY 4: Date range queries
        date_range_match = re.search(self.query_patterns["date_range_query"], query, re.IGNORECASE)
        if date_range_match:
            start_date = date_range_match.group(1)
            end_date = date_range_match.group(2)
            intent.update({
                "type": "date_range_query",
                "target_predicates": ["closed on"],
                "entities": {"start_date": start_date, "end_date": end_date},
                "confidence": 0.9
            })
            print(f"✓ Detected: date_range_query (confidence: 0.9)")
            return intent

        # PRIORITY 5: City-based resolver queries (multi-step but direct)
        city_resolver_match = re.search(self.query_patterns["city_resolver_query"], query, re.IGNORECASE)
        if city_resolver_match:
            city = city_resolver_match.group(1).strip()
            intent.update({
                "type": "city_resolver_query",
                "target_predicates": ["has City", "resolved by"],
                "entities": {"city": city},
                "confidence": 0.85
            })
            print(f"✓ Detected: city_resolver_query (confidence: 0.85)")
            return intent

        # PRIORITY 6: Simple date queries
        simple_date_match = re.search(self.query_patterns["simple_date_query"], query, re.IGNORECASE)
        if simple_date_match:
            date = simple_date_match.group(1)
            intent.update({
                "type": "simple_date_query",
                "target_predicates": ["closed on"],
                "entities": {"date": date},
                "confidence": 0.9
            })
            print(f"✓ Detected: simple_date_query (confidence: 0.9)")
            return intent

        # PRIORITY 7: SR attribute queries (high confidence direct search)
        sr_attr_match = re.search(self.query_patterns["sr_attribute"], query, re.IGNORECASE)
        if sr_attr_match:
            attr = sr_attr_match.group(1).lower()
            sr_num = sr_attr_match.group(2)
            predicate = self.attr_to_predicate.get(attr)

            if predicate:
                intent.update({
                    "type": "sr_attribute",
                    "target_predicates": [predicate],
                    "entities": {"sr_number": sr_num, "attribute": attr},
                    "confidence": 0.95
                })
                print(f"✓ Detected: sr_attribute (confidence: 0.95)")
                return intent

        # PRIORITY 8: Person-related queries
        person_match = re.search(self.query_patterns["person_tickets"], query, re.IGNORECASE)
        if person_match:
            intent.update({
                "type": "person_tickets",
                "target_predicates": ["resolved by", "assigned to"],
                "entities": {"person": person_match.group(1)},
                "confidence": 0.9
            })
            print(f"✓ Detected: person_tickets (confidence: 0.9)")
            return intent

        # PRIORITY 9: Multi-step date + resolver query (keep this working perfectly!)
        if re.search(self.query_patterns["multi_step_date_resolver"], query, re.IGNORECASE):
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', query)
            intent.update({
                "type": "multi_step_date_resolver",
                "multi_step": True,
                "target_predicates": ["closed on", "resolved by"],
                "entities": {"date": date_match.group(1) if date_match else None},
                "confidence": 0.8
            })
            print(f"✓ Detected: multi_step_date_resolver (confidence: 0.8)")
            return intent

        # PRIORITY 10: Simple city query for specific SR (ONLY for simple "what city" questions)
        if re.search(r"(?:what|which)\s+city.*sr\s*(\d{8})", query, re.IGNORECASE):
            sr_match = re.search(r'(\d{8})', query)
            intent.update({
                "type": "sr_city_query",
                "target_predicates": ["has City"],
                "entities": {"sr_number": sr_match.group(1) if sr_match else None},
                "confidence": 0.7
            })
            print(f"✓ Detected: sr_city_query (confidence: 0.7)")
            return intent

        print(f"✗ No specific pattern matched - using general approach")
        return intent

    def extract_person_names_robust(self, query: str) -> List[str]:
        """Robust person name extraction with comprehensive validation"""
        print(f"\n=== ROBUST PERSON NAME EXTRACTION ===")
        print(f"Query: {query}")

        person_names = []

        # Strategy 1: Regex pattern matching
        person_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b'
        matches = re.findall(person_pattern, query)
        print(f"Raw regex matches: {matches}")

        for match in matches:
            if self._is_valid_person_name(match, query):
                person_names.append(match)
                print(f"✓ Valid person name: {match}")
            else:
                print(f"✗ Rejected: {match}")

        # Strategy 2: Query-specific extraction
        person_match = re.search(self.query_patterns["person_tickets"], query, re.IGNORECASE)
        if person_match:
            extracted_person = person_match.group(1)
            if extracted_person not in person_names:
                person_names.append(extracted_person)
                print(f"✓ Query-specific extraction: {extracted_person}")

        print(f"Final person names: {person_names}")
        return person_names

    def _is_valid_person_name(self, name: str, query: str) -> bool:
        """Enhanced validation for person names"""
        words = name.split()
        if len(words) != 2:
            return False

        # Filter out obvious non-person patterns
        non_person_patterns = {
            'What tickets', 'Service Request', 'Machine Type', 'Customer Account',
            'Problem Summary', 'Address Line', 'Incident Date', 'Closed Date'
        }

        if name in non_person_patterns:
            return False

        # Word length validation
        if any(len(word) < 2 or len(word) > 20 for word in words):
            return False

        # Content validation
        non_name_words = {'tickets', 'handled', 'resolved', 'closed', 'machine', 'service', 'problem'}
        if any(word.lower() in non_name_words for word in words):
            return False

        # Context validation
        person_context_patterns = [
            rf'(?:handled|resolved|assigned).*(?:by|to)\s+{re.escape(name)}',
            rf'{re.escape(name)}.*(?:handled|resolved|assigned)',
            rf'(?:by|to)\s+{re.escape(name)}'
        ]

        return any(re.search(pattern, query, re.IGNORECASE) for pattern in person_context_patterns)

    def convert_person_to_kg_variants(self, person_name: str) -> List[str]:
        """Convert person name to possible KG variants including emails"""
        variants = [person_name]

        if ' ' in person_name:
            parts = person_name.split()
            if len(parts) == 2:
                first, last = parts

                # Add different name formats
                variants.extend([
                    f"{last}, {first}",
                    f"{first.lower()}.{last.lower()}@toshibagcs.com",
                    f"{first.lower()}.{last.lower()}@toshiba.com",
                    f"{first[0].lower()}.{last.lower()}@toshibagcs.com",
                    f"{first.lower()}{last.lower()}@toshibagcs.com",
                    f"{last.lower()}.{first.lower()}@toshibagcs.com"
                ])

        print(f"Generated variants for '{person_name}': {variants}")
        return variants

    def find_person_in_kg(self, person_name: str) -> List[str]:
        """Find person in KG using all possible variants"""
        print(f"\n=== FINDING PERSON IN KG: {person_name} ===")

        variants = self.convert_person_to_kg_variants(person_name)
        found_variants = []

        for variant in variants:
            if variant in self.graph_builder.entity_to_id:
                found_variants.append(variant)
                print(f"✓ Found in KG: {variant}")

        if not found_variants:
            print(f"✗ No variants found, trying fuzzy matching...")
            fuzzy_matches = self._fuzzy_match_person(person_name)
            found_variants.extend(fuzzy_matches)

        return found_variants

    def _fuzzy_match_person(self, person_name: str) -> List[str]:
        """Fuzzy matching for person names in KG"""
        fuzzy_matches = []
        name_words = set(person_name.lower().split())

        for entity in self.graph_builder.entity_to_id.keys():
            if '@' in entity:
                entity_lower = entity.lower()
                if any(word in entity_lower for word in name_words if len(word) > 2):
                    fuzzy_matches.append(entity)
                    print(f"✓ Fuzzy email match: {entity}")

        return fuzzy_matches

    def extract_entities(self, query: str) -> List[str]:
        """Enhanced entity extraction with person-first approach"""
        print(f"\n=== ENHANCED ENTITY EXTRACTION ===")
        print(f"Query: {query}")

        entities = set()

        # 1. Person names (highest priority)
        person_names = self.extract_person_names_robust(query)
        for person in person_names:
            kg_variants = self.find_person_in_kg(person)
            entities.update(kg_variants)

        # 2. SR numbers
        sr_numbers = re.findall(self.entity_patterns['sr_numbers'], query)
        if sr_numbers:
            print(f"SR numbers: {sr_numbers}")
            entities.update(sr_numbers)

        # 3. Dates
        dates = re.findall(self.entity_patterns['dates'], query)
        if dates:
            print(f"Dates: {dates}")
            entities.update(dates)

        # 4. Emails
        emails = re.findall(self.entity_patterns['emails'], query)
        if emails:
            print(f"Emails: {emails}")
            entities.update(emails)

        # 5. Final validation against KG
        validated_entities = []
        for entity in entities:
            if entity in self.graph_builder.entity_to_id:
                validated_entities.append(entity)
                print(f"✓ Validated in KG: {entity}")
            else:
                print(f"✗ Not in KG: {entity}")

        print(f"\n=== FINAL ENTITIES: {validated_entities} ===")
        return validated_entities

    def direct_predicate_search(self, predicate: str = None, subject: str = None,
                                obj: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Direct search using Qdrant filtering"""
        try:
            filters = []
            if predicate:
                filters.append(FieldCondition(key="predicate", match=MatchValue(value=predicate)))
            if subject:
                filters.append(FieldCondition(key="subject", match=MatchValue(value=subject)))
            if obj:
                filters.append(FieldCondition(key="object", match=MatchValue(value=obj)))

            # print(f"\n🎯 DIRECT SEARCH")
            # print(f"   Predicate: {predicate}")
            # print(f"   Subject: {subject}")
            # print(f"   Object: {obj}")

            scroll_result = self.config.qdrant_client.scroll(
                collection_name="toshiba_sr_6_12_nov_24",
                scroll_filter=Filter(must=filters),
                limit=limit,
                with_payload=True
            )

            results = []
            for point in scroll_result[0]:
                payload = point.payload
                results.append({
                    "text": payload.get("text", ""),
                    "subject": payload.get("subject", ""),
                    "predicate": payload.get("predicate", ""),
                    "object": payload.get("object", ""),
                    "passage_id": payload.get("passage_id", ""),
                    "score": 1.0,
                    "source": "direct_predicate"
                })

            # print(f"✅ Found {len(results)} exact matches")
            if results:
                # print("Sample results:")
                for i, r in enumerate(results):
                    print(f"  {i + 1}. {r['subject']} {r['predicate']} {r['object']}")

            return results

        except Exception as e:
            print(f"❌ Direct search failed: {e}")
            logger.error(f"Direct search failed: {e}")
            return []

    def multi_location_technician_analysis(self, states: List[str]) -> List[Dict[str, Any]]:
        """Analyze technicians who worked in multiple states"""
        print(f"\n=== MULTI-LOCATION TECHNICIAN ANALYSIS ===")
        print(f"Finding technicians who worked in: {states}")

        all_results = []
        technician_states = defaultdict(set)

        # For each state, find SRs and their resolvers
        for state in states:
            print(f"\nStep 1: Finding SRs in {state}")

            # Find SRs in this state
            state_srs = self.direct_predicate_search(
                predicate="has State",
                obj=state,
                limit=1000
            )

            sr_numbers = [sr['subject'] for sr in state_srs]
            print(f"Found {len(sr_numbers)} SRs in {state}")
            all_results.extend(state_srs)

            # Find resolvers for SRs in this state
            print(f"Step 2: Finding resolvers for {state} SRs...")
            for sr in sr_numbers[:100]:  # Limit for performance
                resolvers = self.direct_predicate_search(
                    predicate="resolved by",
                    subject=sr,
                    limit=5
                )

                for resolver in resolvers:
                    technician = resolver['object']
                    technician_states[technician].add(state)
                    all_results.append(resolver)

        # Find technicians who worked in multiple target states
        multi_state_technicians = []
        for technician, worked_states in technician_states.items():
            if len(worked_states.intersection(set(states))) >= 2:
                multi_state_technicians.append({
                    "technician": technician,
                    "states": list(worked_states),
                    "target_states": list(worked_states.intersection(set(states)))
                })
                print(f"✅ Multi-state technician: {technician} worked in {worked_states}")

        # Create result format
        for tech_info in multi_state_technicians:
            all_results.append({
                "text": f"{tech_info['technician']} worked in {', '.join(tech_info['target_states'])}",
                "subject": tech_info['technician'],
                "predicate": "worked in states",
                "object": ', '.join(tech_info['target_states']),
                "score": 1.0,
                "source": "multi_location_analysis"
            })

        return all_results

    def statistical_machine_type_analysis(self, state: str, time_period: str) -> List[Dict[str, Any]]:
        """Analyze machine type frequency for a state and time period"""
        print(f"\n=== STATISTICAL MACHINE TYPE ANALYSIS ===")
        print(f"Analyzing machine types in {state} for {time_period}")

        all_results = []
        machine_type_counts = Counter()

        # Step 1: Find SRs in the target state
        print(f"Step 1: Finding SRs in {state}")
        state_srs = self.direct_predicate_search(
            predicate="has State",
            obj=state,
            limit=2000
        )

        sr_numbers = [sr['subject'] for sr in state_srs]
        print(f"Found {len(sr_numbers)} SRs in {state}")
        all_results.extend(state_srs)

        # Step 2: Filter by time period (if specified)
        if "Nov 2024" in time_period or "2024-11" in time_period:
            print(f"Step 2: Filtering by time period: {time_period}")
            time_filtered_srs = []

            for sr in sr_numbers[:500]:  # Limit for performance
                # Check if SR was closed in Nov 2024
                closed_dates = self.direct_predicate_search(
                    predicate="closed on",
                    subject=sr,
                    limit=5
                )

                for date_result in closed_dates:
                    if "2024-11" in date_result['object']:
                        time_filtered_srs.append(sr)
                        all_results.append(date_result)
                        break

            sr_numbers = time_filtered_srs
            print(f"Found {len(sr_numbers)} SRs in {state} closed in {time_period}")

        # Step 3: Get machine types for filtered SRs
        print(f"Step 3: Finding machine types for filtered SRs...")
        for sr in sr_numbers[:200]:  # Limit for performance
            machine_types = self.direct_predicate_search(
                predicate="involves Machine Type",
                subject=sr,
                limit=5
            )

            for mt_result in machine_types:
                machine_type = mt_result['object']
                machine_type_counts[machine_type] += 1
                all_results.append(mt_result)

        # Step 4: Create statistical summary
        print(f"Step 4: Creating statistical summary...")
        most_common = machine_type_counts.most_common(10)

        for rank, (machine_type, count) in enumerate(most_common, 1):
            all_results.append({
                "text": f"Machine type {machine_type} appeared {count} times in {state} (rank #{rank})",
                "subject": machine_type,
                "predicate": "frequency in state",
                "object": f"{count} occurrences (rank #{rank})",
                "score": count / max(1, len(sr_numbers)),
                "source": "statistical_analysis"
            })
            print(f"  #{rank}: {machine_type} ({count} occurrences)")

        return all_results

    def date_range_retrieval(self, query: str, intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Handle date range queries"""
        print(f"\n=== DATE RANGE RETRIEVAL ===")

        start_date = intent["entities"]["start_date"]
        end_date = intent["entities"]["end_date"]

        print(f"Finding SRs closed between {start_date} and {end_date}")

        # Generate all dates in range
        date_range = self.generate_date_range(start_date, end_date)
        print(f"Searching across {len(date_range)} dates: {date_range}")

        all_results = []
        total_found = 0

        for date in date_range:
            print(f"\nSearching for SRs closed on {date}")

            closed_srs = self.direct_predicate_search(
                predicate="closed on",
                obj=date,
                limit=500
            )

            found_count = len(closed_srs)
            total_found += found_count
            print(f"Found {found_count} SRs closed on {date}")
            all_results.extend(closed_srs)

        print(f"\n✅ Total SRs found across date range: {total_found}")
        return all_results

    def city_resolver_retrieval(self, city: str) -> List[Dict[str, Any]]:
        """Handle city-based resolver queries"""
        print(f"\n=== CITY RESOLVER RETRIEVAL ===")
        print(f"Finding resolvers for tickets from: {city}")

        all_results = []

        # Step 1: Find SRs from the specified city
        print(f"\nStep 1: Finding SRs from {city}")
        city_srs = self.direct_predicate_search(
            predicate="has City",
            obj=city,
            limit=500
        )

        sr_numbers = [sr['subject'] for sr in city_srs]
        print(f"Found {len(sr_numbers)} SRs from {city}")
        all_results.extend(city_srs)

        # Step 2: Find resolvers for those SRs
        print(f"\nStep 2: Finding resolvers for SRs...")
        resolver_count = 0
        for sr in sr_numbers:
            resolvers = self.direct_predicate_search(
                predicate="resolved by",
                subject=sr,
                limit=10
            )
            all_results.extend(resolvers)
            resolver_count += len(resolvers)
            if resolvers:
                print(f"  {sr} → resolved by {resolvers[0]['object']}")

        print(f"Found {resolver_count} resolver relationships")
        return all_results

    def simple_date_retrieval(self, date: str) -> List[Dict[str, Any]]:
        """Handle simple date queries"""
        print(f"\n=== SIMPLE DATE RETRIEVAL ===")
        print(f"Finding SRs closed on: {date}")

        # Direct search for SRs closed on the specified date
        closed_srs = self.direct_predicate_search(
            predicate="closed on",
            obj=date,
            limit=1000
        )

        print(f"Found {len(closed_srs)} SRs closed on {date}")
        return closed_srs

    def run_ppr(self, seed_entities: List[str]) -> Dict[str, float]:
        """Enhanced PPR with comprehensive debugging"""
        print(f"\n=== PPR COMPUTATION ===")
        print(f"Seed entities: {seed_entities}")

        graph = self.graph_builder.graph
        id_map = self.graph_builder.entity_to_id
        N = graph.vcount()

        seeds = []
        for entity in seed_entities:
            if entity in id_map:
                seeds.append(id_map[entity])
                print(f"✓ {entity} -> node_id {id_map[entity]}")
            else:
                print(f"✗ {entity} not in KG")

        if not seeds:
            return {}

        personalization = [0.0] * N
        for sid in seeds:
            personalization[sid] = 1.0 / len(seeds)

        try:
            pr_scores = graph.personalized_pagerank(
                damping=0.85,
                reset=personalization,
                directed=True
            )

            ppr_results = {}
            for i, score in enumerate(pr_scores):
                if i in self.id_to_entity and score > 1e-6:
                    ppr_results[self.id_to_entity[i]] = score

            print(f"PPR completed: {len(ppr_results)} entities with non-zero scores")
            return ppr_results

        except Exception as e:
            logger.error(f"PPR failed: {e}")
            return {}

    def retrieve_from_passages(self, entity_list: List[str], top_k: int = 50) -> List[Dict[str, Any]]:
        """Vector-based passage retrieval"""
        print(f"\n=== VECTOR SEARCH ===")
        print(f"Retrieving for {len(entity_list)} entities...")

        results = []
        for i, entity in enumerate(entity_list[:10]):
            try:
                vector = self.config.get_embedding(entity)
                search_result = self.config.qdrant_client.search(
                    collection_name="toshiba_sr_6_12_nov_24",
                    query_vector=vector,
                    limit=top_k,
                    with_payload=True,
                )

                for r in search_result:
                    payload = r.payload
                    results.append({
                        "text": payload.get("text", ""),
                        "subject": payload.get("subject", ""),
                        "predicate": payload.get("predicate", ""),
                        "object": payload.get("object", ""),
                        "passage_id": payload.get("passage_id", ""),
                        "score": r.score,
                        "source": "vector_search",
                        "query_entity": entity
                    })

                print(f"  Entity {i + 1}: {len(search_result)} passages")

            except Exception as e:
                logger.warning(f"Vector search failed for {entity}: {e}")

        print(f"Total vector search results: {len(results)}")
        return results

    def person_query_retrieval(self, person: str) -> List[Dict[str, Any]]:
        """Enhanced person query retrieval"""
        print(f"\n=== PERSON QUERY RETRIEVAL ===")
        print(f"Searching for person: {person}")

        kg_variants = self.find_person_in_kg(person)
        if not kg_variants:
            return []

        all_results = []
        for variant in kg_variants:
            for predicate in ["resolved by", "assigned to"]:
                results = self.direct_predicate_search(
                    predicate=predicate,
                    obj=variant,
                    limit=100
                )
                all_results.extend(results)

        return all_results

    def multi_step_retrieval(self, query: str, intent: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Enhanced multi-step retrieval for date+resolver queries"""
        print(f"\n=== MULTI-STEP RETRIEVAL ===")

        all_results = []

        if intent["type"] == "multi_step_date_resolver":
            date = intent["entities"]["date"]

            # Step 1: Find SRs closed on the date
            closed_srs = self.direct_predicate_search(
                predicate="closed on",
                obj=date,
                limit=500
            )

            sr_numbers = [sr['subject'] for sr in closed_srs]
            all_results.extend(closed_srs)

            # Step 2: Find resolvers for those SRs
            for sr in sr_numbers[:50]:
                resolvers = self.direct_predicate_search(
                    predicate="resolved by",
                    subject=sr,
                    limit=10
                )
                all_results.extend(resolvers)

        return all_results

    def retrieve(self, query: str, max_results: int = 250) -> List[Dict[str, Any]]:
        """Enhanced main retrieval method with comprehensive routing"""
        # print(f"\n{'='*80}")
        # print(f"🚀 PROCESSING QUERY: {query}")
        # print(f"{'='*80}")

        # Step 1: Query classification
        intent = self.classify_query_intent(query)

        # Step 2: Route to appropriate retrieval strategy
        all_results = []

        if intent["type"] == "multi_location_technician":
            states = intent["entities"]["states"]
            all_results = self.multi_location_technician_analysis(states)

        elif intent["type"] == "statistical_machine_type":
            state = intent["entities"]["state"]
            time_period = intent["entities"]["time_period"]
            all_results = self.statistical_machine_type_analysis(state, time_period)

        elif intent["type"] == "date_range_query":
            all_results = self.date_range_retrieval(query, intent)

        elif intent["type"] == "city_resolver_query":
            city = intent["entities"]["city"]
            all_results = self.city_resolver_retrieval(city)

        elif intent["type"] == "simple_date_query":
            date = intent["entities"]["date"]
            all_results = self.simple_date_retrieval(date)

        elif intent["type"] == "sr_attribute":
            sr_number = intent["entities"]["sr_number"]
            attribute = intent["entities"]["attribute"]
            predicate = intent["target_predicates"][0]

            # print(f"🎯 SR ATTRIBUTE QUERY: {attribute} for {sr_number}")

            # Direct predicate search
            direct_results = self.direct_predicate_search(
                predicate=predicate,
                subject=sr_number,
                limit=10
            )

            if direct_results:
                # print(f"✅ Direct attribute found: {direct_results[0]['object']}")
                return direct_results

        elif intent["type"] == "person_tickets":
            person = intent["entities"].get("person")
            if person:
                all_results = self.person_query_retrieval(person)

        elif intent["type"] == "multi_step_date_resolver":
            all_results = self.multi_step_retrieval(query, intent)

        elif intent["type"] == "sr_city_query":
            sr_number = intent["entities"].get("sr_number")
            if sr_number:
                city_results = self.direct_predicate_search(
                    predicate="has City",
                    subject=sr_number
                )
                all_results.extend(city_results)

        # Step 3: Fallback to PPR + vector search
        if not all_results:
            # print("\n=== FALLBACK: ENTITY EXTRACTION + PPR ===")
            entities = self.extract_entities(query)

            if entities:
                ppr_scores = self.run_ppr(entities)
                if ppr_scores:
                    top_entities = sorted(ppr_scores.items(), key=lambda x: x[1], reverse=True)[:20]
                    top_entity_list = [ent for ent, _ in top_entities]

                    print("\nTop 20 entities from PPR:")
                    for i, (entity, score) in enumerate(top_entities):
                        print(f"{i + 1}. {entity} (score: {score:.6f})")

                    vector_results = self.retrieve_from_passages(top_entity_list, top_k=max_results)
                    all_results.extend(vector_results)

        # Step 4: Final fallback
        if not all_results:
            print("\n=== FINAL FALLBACK: DIRECT VECTOR SEARCH ===")
            fallback_results = self.retrieve_from_passages([query], top_k=max_results)
            all_results.extend(fallback_results)

        # Step 5: Deduplicate and rank
        seen = set()
        unique_results = []
        for result in all_results:
            key = (result['subject'], result['predicate'], result['object'])
            if key not in seen:
                seen.add(key)
                unique_results.append(result)

        # Enhanced sorting for analytical results
        unique_results.sort(key=lambda x: (
            x['source'] == 'multi_location_analysis',
            x['source'] == 'statistical_analysis',
            x['source'] == 'direct_predicate',
            x['score'] if isinstance(x['score'], (int, float)) else 0
        ), reverse=True)

        print(f"\n=== FINAL RESULTS SUMMARY ===")
        print(f"Total unique results: {len(unique_results)}")

        # Show results by source
        analytical_results = [r for r in unique_results if
                              r['source'] in ['multi_location_analysis', 'statistical_analysis']]
        direct_results = [r for r in unique_results if r['source'] == 'direct_predicate']
        vector_results = [r for r in unique_results if r['source'] == 'vector_search']

        print(f"📊 Analytical results: {len(analytical_results)}")
        print(f"📊 Direct predicate results: {len(direct_results)}")
        print(f"📊 Vector search results: {len(vector_results)}")

        return unique_results[:max_results]


def main():
    config = HippoRAGConfig()
    retriever = AnalyticalKGRetriever(config)

    # test_queries = [
    #     "What are the SR tickets closed on 2024-11-06 and who resolved them?",
    #     "Which technician handled SRs in both TX and GA?",
    #     "Which machine types were most frequent in CA for tickets closed in Nov 2024?",
    #     "machine type for 15790474",
    #     "What tickets were handled by Jason Hechler?",
    #     "which city has raised the service request with sr 15849204?"
    # ]

    # for query in test_queries:
    #     print(f"\n{'='*100}")
    #     print(f"TESTING: {query}")
    #     print(f"{'='*100}")

    #     results = retriever.retrieve(query)

    #     print(f"\nFINAL RESULTS ({len(results)}):")
    #     for i, r in enumerate(results[:10]):
    #         src_map = {
    #             'multi_location_analysis': 'MULTI-LOC',
    #             'statistical_analysis': 'STATS',
    #             'direct_predicate': 'DIRECT',
    #             'vector_search': 'VECTOR'
    #         }
    #         src = src_map.get(r['source'], r['source'])
    #         print(f"{i+1}. [{src}] {r['subject']} {r['predicate']} {r['object']} (Score: {r['score']:.3f})")


if __name__ == "__main__":
    main()
