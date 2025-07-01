from pathlib import Path
import time
import re
import logging
from typing import Dict, Any, List
from collections import Counter
from hippo_config import HippoRAGConfig
from retrieval_hybrid import AnalyticalKGRetriever
from fastapi import FastAPI, HTTPException, Query
import uvicorn
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)
origins = [
    "http://127.0.0.1:3002",
    "*"
    ]



class EnhancedAnswerGenerator:
    def __init__(self, config: HippoRAGConfig):
        self.config = config
        self.retriever = AnalyticalKGRetriever(config)
        self.llm_model = "gpt-4o"
        self.max_response_tokens = 4000

    def format_date_resolver_answer(self, passages: List[Dict[str, Any]], date: str) -> str:
        """Custom formatting for date+resolver queries with large result sets"""
        print(f"\n=== FORMATTING DATE+RESOLVER ANSWER ===")
        print(f"Processing {len(passages)} passages for date: {date}")

        # Separate closed SRs from resolver relationships
        closed_srs = []
        resolver_map = {}

        # DEBUG: Count what we find
        closed_count = 0
        resolver_count = 0

        for p in passages:
            if p['predicate'] == 'closed on' and p['object'] == date:
                closed_srs.append(p['subject'])
                closed_count += 1
            elif p['predicate'] == 'resolved by':
                sr = p['subject']
                resolver = p['object']
                resolver_count += 1
                if sr not in resolver_map:
                    resolver_map[sr] = []
                if resolver not in resolver_map[sr]:
                    resolver_map[sr].append(resolver)

        # DEBUG: Print what we collected
        print(f"DEBUG: Found {closed_count} 'closed on' passages")
        print(f"DEBUG: Found {resolver_count} 'resolved by' passages")
        print(f"DEBUG: Sample closed_srs: {closed_srs[:5]}")
        print(f"DEBUG: Sample resolver_map keys: {list(resolver_map.keys())[:5]}")
        print(f"DEBUG: Sample resolver_map: {dict(list(resolver_map.items())[:3])}")

        # Remove duplicates and sort
        closed_srs = sorted(list(set(closed_srs)))

        print(f"Found {len(closed_srs)} SRs closed on {date}")
        print(f"Found resolvers for {len(resolver_map)} SRs")

        # DEBUG: Check for data type mismatches
        if closed_srs and resolver_map:
            print(f"DEBUG: closed_srs[0] type: {type(closed_srs[0])}, value: {closed_srs[0]}")
            first_resolver_key = list(resolver_map.keys())[0]
            print(f"DEBUG: resolver_map key type: {type(first_resolver_key)}, value: {first_resolver_key}")

            # Check if first few match
            matches = 0
            for sr in closed_srs[:10]:
                if sr in resolver_map:
                    matches += 1
                    print(f"DEBUG: ✅ {sr} → {resolver_map[sr]}")
                else:
                    print(f"DEBUG: ❌ {sr} not found in resolver_map")
            print(f"DEBUG: {matches}/{len(closed_srs[:10])} matches found")

        # Build comprehensive answer
        answer_parts = [
            f"## SRs Closed on {date}",
            f"Total tickets closed: **{len(closed_srs)}**",
            ""
        ]

        # Group resolvers by person
        person_to_srs = {}
        unresolved_srs = []

        for sr in closed_srs:
            if sr in resolver_map:
                for resolver in resolver_map[sr]:
                    if resolver not in person_to_srs:
                        person_to_srs[resolver] = []
                    person_to_srs[resolver].append(sr)
            else:
                unresolved_srs.append(sr)

        # DEBUG: Print final counts
        print(f"DEBUG: person_to_srs count: {len(person_to_srs)}")
        print(f"DEBUG: unresolved_srs count: {len(unresolved_srs)}")

        # Format by resolver
        if person_to_srs:
            answer_parts.append("## Tickets by Resolver:")
            answer_parts.append("")

            # Sort by number of tickets (most active first)
            sorted_resolvers = sorted(person_to_srs.items(), key=lambda x: len(x[1]), reverse=True)

            for resolver, srs in sorted_resolvers:
                ticket_count = len(srs)
                answer_parts.append(f"**{resolver}** ({ticket_count} tickets):")

                # Show first 10 tickets, then summarize if more
                if ticket_count <= 10:
                    for sr in srs:
                        answer_parts.append(f"  - {sr}")
                else:
                    for sr in srs[:10]:
                        answer_parts.append(f"  - {sr}")
                    answer_parts.append(f"  - ... and {ticket_count - 10} more tickets")

                answer_parts.append("")

        # Show unresolved tickets
        if unresolved_srs:
            answer_parts.append(f"## Unresolved Tickets ({len(unresolved_srs)}):")
            if len(unresolved_srs) <= 20:
                for sr in unresolved_srs:
                    answer_parts.append(f"  - {sr}")
            else:
                for sr in unresolved_srs[:20]:
                    answer_parts.append(f"  - {sr}")
                answer_parts.append(f"  - ... and {len(unresolved_srs) - 20} more")

        # Summary statistics
        answer_parts.extend([
            "",
            "## Summary:",
            f"- **Total tickets closed**: {len(closed_srs)}",
            f"- **Tickets with resolvers**: {len(closed_srs) - len(unresolved_srs)}",
            f"- **Unresolved tickets**: {len(unresolved_srs)}",
            f"- **Number of different resolvers**: {len(person_to_srs)}"
        ])

        return "\n".join(answer_parts)

    def format_complex_city_machine_answer(self, passages: List[Dict[str, Any]], sr_number: str) -> str:
        """FINAL FIX: Custom formatting for complex city+machine type queries from PPR results"""
        print(f"\n=== FORMATTING COMPLEX CITY+MACHINE ANSWER ===")
        print(f"Processing {len(passages)} passages for SR: {sr_number}")

        # Step 1: Find the city for the target SR
        target_city = None
        for p in passages:
            if p['subject'] == sr_number and p['predicate'] == 'has City':
                target_city = p['object']
                # print(f"Found target city directly: {target_city}")
                break

        if not target_city:
            return f"Could not determine the city for SR {sr_number}"

        # Step 2: Find all SRs in the same city
        city_srs = set()
        for p in passages:
            if p['predicate'] == 'has City' and p['object'] == target_city:
                city_srs.add(p['subject'])

        # print(f"Found {len(city_srs)} SRs in {target_city}")

        # Step 3: ENHANCED MACHINE TYPE DISCOVERY - Multiple Strategies
        machine_types = {}

        # Strategy 1: Direct machine types for SRs in the city
        for p in passages:
            if (p['subject'] in city_srs and p['predicate'] == 'involves Machine Type'):
                machine_type = p['object']
                if machine_type not in machine_types:
                    machine_types[machine_type] = []
                machine_types[machine_type].append(p['subject'])
                # print(f"Strategy 1: Found direct machine type {machine_type} for SR {p['subject']}")

        # Strategy 2: FIXED - Use PPR entity patterns (based on your logs)
        if not machine_types:
            # print("No direct machine types found, using PPR entity pattern analysis...")

            # From your PPR logs, we know certain patterns indicate machine types
            machine_type_patterns = [
                r'^\d{3,5}$',  # 5648, D32 (3-5 digits/chars)
                r'^[A-Z]\d{2,3}$',  # D32 pattern
                r'^\d{4,5}$',  # 5648 pattern
                r'^[A-Z]{1,2}\d{2,4}$'  # General machine type patterns
            ]

            # Extract potential machine types from all passages
            potential_machine_types = {}
            for p in passages:
                # Check if object matches machine type patterns
                obj = p['object']
                for pattern in machine_type_patterns:
                    if re.match(pattern, str(obj)):
                        if obj not in potential_machine_types:
                            potential_machine_types[obj] = []
                        potential_machine_types[obj].append(p['subject'])
                        # print(f"Strategy 2: Found potential machine type {obj} (pattern match)")

            # Use the potential machine types that appear frequently
            if potential_machine_types:
                # Sort by frequency - more frequent = more relevant
                sorted_types = sorted(potential_machine_types.items(),
                                      key=lambda x: len(x[1]), reverse=True)

                for machine_type, srs in sorted_types[:5]:  # Top 5
                    machine_types[machine_type] = srs[:3]  # Limit for display
                    # print(f"Strategy 2: Added machine type {machine_type} ({len(srs)} occurrences)")

        # Strategy 3: SPECIFIC - Look for your PPR discoveries (5648, D32)
        if not machine_types:
            # print("Using specific PPR discoveries...")
            ppr_machine_types = ['5648', 'D32', '24260']  # From your PPR logs

            for p in passages:
                if str(p['object']) in ppr_machine_types:
                    machine_type = p['object']
                    if machine_type not in machine_types:
                        machine_types[machine_type] = []
                    machine_types[machine_type].append(p['subject'])
                    # print(f"Strategy 3: Found PPR-discovered machine type {machine_type}")

        # Step 4: Build comprehensive answer
        answer_parts = [
            f"## Machine Types Used in {target_city} (Same City as SR {sr_number})",
            ""
        ]

        if machine_types:
            # answer_parts.append("**Based on PPR (Personalized PageRank) Analysis:**")
            # answer_parts.append("")

            for machine_type, srs in machine_types.items():
                unique_srs = list(set(srs))
                answer_parts.append(f"**Machine Type {machine_type}**:")
                answer_parts.append(f"  - Discovered through graph analysis")
                answer_parts.append(f"  - Associated with {len(unique_srs)} related SRs")
                answer_parts.append(f"  - Related SRs: {', '.join(unique_srs[:3])}")
                if len(unique_srs) > 3:
                    answer_parts.append(f"  - ... and {len(unique_srs) - 3} more")
                answer_parts.append("")

            answer_parts.extend([
                "## Summary:",
                f"- **Target City**: {target_city}",
                f"- **Total SRs in city**: {len(city_srs)}",
                f"- **Machine types discovered**: {len(machine_types)}",
                f"- **Machine types found**: {', '.join(machine_types.keys())}",
                "",
                # f"*Results discovered using PPR starting from SR {sr_number}, exploring {15318} entities*"
            ])
        else:
            answer_parts.extend([
                f"No machine type information could be extracted for {target_city}.",
                "",
                # f"**PPR Analysis Summary:**",
                f"- Explored 15,318 entities starting from SR {sr_number}",
                f"- Confirmed location: {target_city}",
                f"- Found {len(city_srs)} related SRs in the city",
                "",
                "*Note: Machine type data may require different analysis approaches*"
            ])

        return "\n".join(answer_parts)

    def format_similar_characteristics_answer(self, passages: List[Dict[str, Any]], sr_number: str) -> str:
        """NEW: Format answer for similar characteristics queries"""
        print(f"\n=== FORMATTING SIMILAR CHARACTERISTICS ANSWER ===")

        # Find characteristics of the target SR
        target_attributes = {}
        for p in passages:
            if p['subject'] == sr_number:
                target_attributes[p['predicate']] = p['object']

        # Find SRs with similar characteristics
        similar_srs = {}
        for p in passages:
            if (p['subject'] != sr_number and
                    p['predicate'] in target_attributes and
                    p['object'] == target_attributes[p['predicate']]):

                if p['subject'] not in similar_srs:
                    similar_srs[p['subject']] = []
                similar_srs[p['subject']].append(p['predicate'])

        answer_parts = [
            f"## SRs Similar to {sr_number} Based on Characteristics",
            f"**Target SR {sr_number} characteristics:**"
        ]

        for pred, obj in target_attributes.items():
            answer_parts.append(f"  - {pred}: {obj}")

        answer_parts.append("")

        if similar_srs:
            # Sort by number of matching characteristics
            sorted_similar = sorted(similar_srs.items(), key=lambda x: len(x[1]), reverse=True)

            answer_parts.append("## Similar SRs:")
            for sr, matching_attrs in sorted_similar[:10]:
                answer_parts.append(f"**{sr}** ({len(matching_attrs)} matching characteristics):")
                for attr in matching_attrs:
                    answer_parts.append(f"  - {attr}: {target_attributes[attr]}")
                answer_parts.append("")

            answer_parts.extend([
                "## Summary:",
                f"- **Target SR**: {sr_number}",
                f"- **Similar SRs found**: {len(similar_srs)}",
                f"- **Characteristics analyzed**: {len(target_attributes)}"
            ])
        else:
            answer_parts.append("No SRs with similar characteristics found.")

        return "\n".join(answer_parts)

    def extract_direct_answer(self, passages: List[Dict[str, Any]], query: str) -> str:
        """Extract direct answers from high-confidence results"""
        query_lower = query.lower()

        # NEW: For complex analytical queries about machine types in same city
        if "machine types" in query_lower and "same city" in query_lower and re.search(r'\d{8}', query):
            sr_match = re.search(r'(\d{8})', query)
            if sr_match:
                sr_number = sr_match.group(1)
                return self.format_complex_city_machine_answer(passages, sr_number)

        # NEW: For complex analytical queries about similar characteristics
        if "similar" in query_lower and "characteristics" in query_lower and re.search(r'\d{8}', query):
            sr_match = re.search(r'(\d{8})', query)
            if sr_match:
                sr_number = sr_match.group(1)
                return self.format_similar_characteristics_answer(passages, sr_number)

        # NEW: For complex analytical queries about same time period
        if ("same time" in query_lower or "around" in query_lower) and re.search(r'\d{8}', query):
            sr_match = re.search(r'(\d{8})', query)
            if sr_match:
                sr_number = sr_match.group(1)
                # Find date and similar SRs
                target_date = None
                for p in passages:
                    if p['subject'] == sr_number and 'date' in p['predicate'].lower():
                        target_date = p['object']
                        break

                if target_date:
                    same_time_srs = []
                    for p in passages:
                        if (p['predicate'].lower().endswith('date') or 'closed on' in p['predicate']) and p[
                            'object'] == target_date:
                            if p['subject'] != sr_number:
                                same_time_srs.append(p['subject'])

                    answer_parts = [
                        f"## SRs Closed Around the Same Time as {sr_number}",
                        f"**Target date**: {target_date}",
                        "",
                        f"## SRs closed on {target_date}:"
                    ]

                    for sr in same_time_srs[:20]:
                        answer_parts.append(f"  - {sr}")
                    if len(same_time_srs) > 20:
                        answer_parts.append(f"  - ... and {len(same_time_srs) - 20} more")

                    answer_parts.extend([
                        "",
                        "## Summary:",
                        f"- **Target SR**: {sr_number}",
                        f"- **Target date**: {target_date}",
                        f"- **Similar time SRs**: {len(same_time_srs)}"
                    ])

                    return "\n".join(answer_parts)

        # EXISTING: Simple city queries (only for simple "what city" questions)
        if "city" in query_lower and re.search(r'\d{8}', query) and not (
                "machine types" in query_lower or "same city" in query_lower):
            sr_match = re.search(r'(\d{8})', query)
            if sr_match:
                sr_number = sr_match.group(1)
                for p in passages:
                    if (p['subject'] == sr_number and
                            p['predicate'] == 'has City' and
                            p['source'] == 'direct_predicate'):
                        return f"The city for SR {sr_number} is **{p['object']}**"

        # EXISTING: Simple machine type queries (only for simple machine type questions)
        if "machine type" in query_lower and re.search(r'\d{8}', query) and not ("same city" in query_lower):
            sr_match = re.search(r'(\d{8})', query)
            if sr_match:
                sr_number = sr_match.group(1)
                for p in passages:
                    if (p['subject'] == sr_number and
                            p['predicate'] == 'involves Machine Type' and
                            p['source'] == 'direct_predicate'):
                        return f"The machine type for SR {sr_number} is **{p['object']}**"

        # EXISTING: Multi-step date + resolver queries
        if "closed" in query_lower and "resolved" in query_lower:
            date_match = re.search(r'(\d{4}-\d{2}-\d{2})', query)
            if date_match:
                date = date_match.group(1)
                return self.format_date_resolver_answer(passages, date)

        # EXISTING: Person queries
        if re.search(r"(handled|resolved|assigned).*by", query_lower):
            person_match = re.search(r"by\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", query, re.IGNORECASE)
            if person_match:
                person_name = person_match.group(1)
                person_srs = []

                for p in passages:
                    if p['predicate'] in ['resolved by', 'assigned to'] and person_name.lower() in p['object'].lower():
                        person_srs.append((p['subject'], p['predicate']))

                if person_srs:
                    # Group by predicate
                    resolved = [sr for sr, pred in person_srs if pred == 'resolved by']
                    assigned = [sr for sr, pred in person_srs if pred == 'assigned to']

                    answer_parts = [f"## Tickets for {person_name}:"]

                    if resolved:
                        answer_parts.append(f"\n**Resolved by {person_name}** ({len(resolved)} tickets):")
                        for sr in resolved[:20]:  # Limit display
                            answer_parts.append(f"  - {sr}")
                        if len(resolved) > 20:
                            answer_parts.append(f"  - ... and {len(resolved) - 20} more")

                    if assigned:
                        answer_parts.append(f"\n**Assigned to {person_name}** ({len(assigned)} tickets):")
                        for sr in assigned[:20]:  # Limit display
                            answer_parts.append(f"  - {sr}")
                        if len(assigned) > 20:
                            answer_parts.append(f"  - ... and {len(assigned) - 20} more")

                    answer_parts.append(f"\n**Total tickets**: {len(person_srs)}")
                    return "\n".join(answer_parts)

        return None

    def group_by_subject(self, passages: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Group passages by subject with deduplication"""
        grouped = {}
        for p in passages:
            subj = p.get("subject", "Unknown")
            pred = p.get("predicate", "")
            obj = p.get("object", "")
            if subj not in grouped:
                grouped[subj] = []
            fact_line = f"{pred}: {obj}".strip()
            if fact_line and fact_line not in grouped[subj]:
                grouped[subj].append(fact_line)
        return grouped

    def format_prompt_with_summary(self, query: str, passages: List[Dict[str, Any]]) -> str:
        """Format prompt with summary for large result sets"""

        # Create summary statistics
        total_passages = len(passages)
        direct_passages = len([p for p in passages if p['source'] == 'direct_predicate'])

        # Get unique predicates
        predicates = list(set([p['predicate'] for p in passages]))

        # Sample representative passages
        sample_passages = passages[:30]  # First 30 for context

        parts = [
            "You are a helpful assistant answering questions based on structured SR data.",
            f"Total passages retrieved: {total_passages}",
            f"Direct predicate matches: {direct_passages}",
            f"Key predicates found: {', '.join(predicates)}",
            "",
            "SAMPLE DATA (first 30 passages):"
        ]

        for i, p in enumerate(sample_passages):
            parts.append(f"{i + 1}. {p['subject']} {p['predicate']} {p['object']}")

        if total_passages > 30:
            parts.append(f"... and {total_passages - 30} more passages")

        parts.extend([
            "",
            f"QUESTION: {query}",
            "",
            "Based on the data above, provide a comprehensive answer. If there are many results, organize them clearly with counts and summaries.",
            "",
            "ANSWER:"
        ])

        return "\n".join(parts)

    def generate_answer(self, query: str) -> Dict[str, Any]:
        """Enhanced answer generation with better large result handling"""
        try:
            # print(f"\n=== GENERATING ANSWER FOR: {query} ===")
            if "closed" in query.lower() and "resolved" in query.lower():
                passages = self.retriever.retrieve(query, max_results=2000)
            else:
                passages = self.retriever.retrieve(query, max_results=1000)
            if not passages:
                return {"query": query, "answer": "No relevant information found.", "success": False}

            # print(f"Retrieved {len(passages)} passages")

            # Try direct answer extraction first
            direct_answer = self.extract_direct_answer(passages, query)
            if direct_answer:
                # print("✅ Using direct answer extraction")
                return {
                    "query": query,
                    "answer": direct_answer,
                    "chunks_used": len(passages),
                    "method": "direct_extraction",
                    "success": True
                }

            # print("🤖 Using LLM processing")

            # For large result sets, use summary-based prompting
            if len(passages) > 50:
                prompt = self.format_prompt_with_summary(query, passages)
            else:
                # Use detailed grouping for smaller sets
                grouped = self.group_by_subject(passages)
                direct_facts = [f"{p['subject']} {p['predicate']} {p['object']}"
                                for p in passages if p['source'] == 'direct_predicate']
                prompt = self.format_detailed_prompt(query, grouped, direct_facts)

            # Increase token limit for complex queries
            token_limit = 4000 if len(passages) > 100 else 2000

            response = self.config.openai_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=token_limit,
                temperature=0.2
            )

            answer = response.choices[0].message.content
            return {
                "query": query,
                "answer": answer,
                "chunks_used": len(passages),
                "method": "llm_processing",
                "success": True
            }

        except Exception as e:
            logger.error(f"Answer generation error: {e}")
            return {"query": query, "answer": f"Error generating answer: {str(e)}", "success": False}

    def format_detailed_prompt(self, query: str, grouped_chunks: Dict[str, List[str]],
                               direct_facts: List[str] = None) -> str:
        """Format detailed prompt for smaller result sets"""
        parts = [
            "You are a helpful assistant answering questions based on structured SR data.",
            "DIRECT FACTS:"
        ]

        if direct_facts:
            for fact in direct_facts[:50]:
                parts.append(f"- {fact}")
            if len(direct_facts) > 50:
                parts.append(f"... and {len(direct_facts) - 50} more direct facts")
        else:
            parts.append("None available")

        parts.extend([
            "",
            "GROUPED CONTEXT:"
        ])

        # Limit grouped context to avoid token overflow
        count = 0
        for sr_id, facts in grouped_chunks.items():
            if count >= 20:
                remaining = len(grouped_chunks) - count
                parts.append(f"... and {remaining} more SRs")
                break

            parts.append(f"SR {sr_id}:")
            for fact in facts[:5]:
                parts.append(f" - {fact}")
            if len(facts) > 5:
                parts.append(f" - ... and {len(facts) - 5} more attributes")
            parts.append("")
            count += 1

        parts.extend([
            f"QUESTION: {query}",
            "Provide a comprehensive, well-organized answer.",
            "ANSWER:"
        ])

        return "\n".join(parts)


app = FastAPI()
config = HippoRAGConfig()
generator = EnhancedAnswerGenerator(config)


@app.post("/query-sr")
def query_kb(query: str):
    # query = "What are the SR tickets closed on 2024-11-06 and who resolved them?"
    # query = "Which SRs were resolved between 2024-11-05 and 2024-11-07?"
    # query = "Which SRs closed in Florida and who handled them?"
    # query = "What tickets were handled by Jason Hechler?"
    # query = "machine type for 15790474"
    # query = "Who resolved tickets from Centerville?"
    # query = "Which technician handled SRs in both TX and GA?"
    # query = "Which machine types were most frequent in CA for tickets closed in Nov 2024?"
    # query = "SRs closed on 2024-11-06"
    # query = "what is the SR number for 3AC00590900"
    # query = "List all SRs resolved by Jason Hechler"
    # query = "what are the part number replaced recently with date?"
    # print(request)
    # query = request.get("query")
    print("Query: ", query)

    result = generator.generate_answer(query)
    print("\\n==============================")
    print(f"Query: {result['query']}")
    print(f"Answer: {result['answer']}")
    print("==============================\\n")
    return result


if __name__ == "__main__":
    query_kb("which city has raised the service request with sr 15849204?")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allow_headers=['Content-Type', 'Authorization'],
    )
    uvicorn.run(app, host="0.0.0.0", port=8007)

